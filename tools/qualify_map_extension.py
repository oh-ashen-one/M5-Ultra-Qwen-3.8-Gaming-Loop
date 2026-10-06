"""Bounded native map expansion; never establishes full area or final mission pacing."""
import json
import math
import time
import uuid

from loop_controller.core import Halt, atomic, now, sha, verify_seal, read_json
from loop_controller.continuous_tasks import TASKS
from loop_controller.features import pavement_coverage
from loop_controller.delivery_policy import queue_milestone
from loop_controller.runner import git

MAP_TASK = dict(id='connected-map-extension', phase='world', checks=[], maximum=150,
    coverage='foundation', polish=True, design=True,
    outcome='One connected Chicago street or side-alley extension, walked and driven out and back.',
    instructions='Create only the first small connected extension beyond the existing7x32m corridor. '
    'Read Bootstrap and WorldColliders, then install one compact original C# extension using existing original '
    'street/props meshes and coherent visible pavement. Preserve current core, camera, missions, assets and controls. '
    'Choose a connector away from the existing forward/west collision test routes; a side opening can preserve '
    'those obstacle stops. Do not remove or weaken tests or colliders. Keep support surfaces visibly rendered, '
    'curbs/buildings collidable and junction understandable. No world-sized invisible support as map content. '
    'Submit normal inputs within150seconds that first walk at least6m beyond an old X/Z boundary and walk back '
    'inside, then enter the actual car, drive at least6m beyond an old boundary and drive back inside. Keep each '
    'outside visit visible for at least1second and take captures of walking outside, driving outside and return. '
    'No R teleport/reset during either out-and-back leg. Preserve stationary opening through4seconds. '
    'The old rectangle is X-1..6,Z-2..30. This accepts only one traversed connector, never the whole map or ten-minute mission.')


def outside_distance(position):
    x, _, z = position
    return max(-1-x, x-6, -2-z, z-30, 0)


def accepted_map_images(runner, record):
    from continue_game_queue import review_captures
    bundle=runner.store.root/record['evidence']
    note='game/Notes/map-'+bundle.name+'.json'
    accepted=runner.store.get('last_playable_checkpoint')
    if json.loads(git(runner.repo,'show',accepted+':'+note))!=record:
        raise Halt('Accepted map record differs from its Git note')
    changed=git(runner.repo,'diff','--name-only',record['candidate'],accepted).splitlines()
    if any(not p.startswith('game/Notes/') for p in changed):
        raise Halt('Accepted map comparison is stale for current playable source')
    manifest=verify_seal(bundle/'captures',record['capture_manifest_sha256'])
    gate=read_json(bundle/'scoped-gate.json')
    if manifest.get('candidate')!=record['candidate'] or not gate.get('passed'):
        raise Halt('Accepted map evidence identity mismatch')
    frames,times=review_captures(MAP_TASK,bundle)
    return [('ACTUAL accepted connected map t'+str(times[p.name]),p) for p in frames[:2]]


def inspect_extension(rows):
    failed=[];facts={}
    for mode,key in [('foot','player'),('vehicle','vehicle')]:
        selected=[r for r in rows if r.get('mode')==mode and r.get('time',0)>=4]
        excursions=[]
        for i,row in enumerate(selected):
            p=row.get(key)
            if not isinstance(p,list) or len(p)!=3 or not all(math.isfinite(v) for v in p):
                failed.append(mode+'-invalid-position');continue
            if outside_distance(p)>=6:excursions.append((i,row))
        returning=None
        if len(excursions)>=10:
            first_i,first=excursions[0];last_i,last=excursions[-1]
            returning=next((r for r in selected[last_i+1:] if outside_distance(r[key])==0),None)
            if last['time']-first['time']<1:failed.append(mode+'-outside-duration')
            leg=[r for r in rows if first['time']<=r['time']<=(returning or last)['time']]
            if (not returning or any(r.get('restarts',0)!=first.get('restarts',0) or 'R' in r.get('keys',[]) for r in leg)):
                failed.append(mode+'-physical-return-missing')
        else:failed.append(mode+'-new-space-not-traversed')
        enabled='playerCollisionEnabled' if mode=='foot' else 'vehicleCollisionEnabled'
        penetration='playerPenetration' if mode=='foot' else 'vehiclePenetration'
        if not selected or any(not r.get(enabled) or r.get(penetration,999)>.15 for r in selected):
            failed.append(mode+'-collision-continuity')
        positions=[r[key] for r in selected if isinstance(r.get(key),list) and len(r[key])==3]
        if any(math.dist(a,b)>3 for a,b in zip(positions,positions[1:])):
            failed.append(mode+'-discontinuous-traversal')
        if mode=='foot' and selected and sum(bool(r.get('grounded')) for r in selected)/len(selected)<.95:
            failed.append('walking-not-grounded')
        facts[mode]={'outside_samples':len(excursions),
            'maximum_distance_beyond_old_boundary_m':max([outside_distance(r[key]) for _,r in excursions] or [0]),
            'physical_return_seconds':returning['time'] if returning else None}
    return dict(passed=not failed, failure=failed, old_bounds_xz=[-1,6,-2,30],
                traversal=facts, area_claim='Only observed connected traversal; no gross map-area acceptance')


def qualify_one_extension(runner, *, integrated_builder=False):
    from continue_game_queue import ContinuousRunner, review_captures
    task=MAP_TASK
    while not runner.store.get('accepted_map_extension'):
        runner.machine.guard()
        ident='q%04d-%s'%(runner.store.get('rounds',0)+1,uuid.uuid4().hex[:8])
        runner.store.set(current_round=ident,rounds=runner.store.get('rounds',0)+1,
            stage='local-map-extension',current_task=task['outcome'],next_task='Second connected street and side alley; then meaningful mission pacing')
        runner.store.report()
        # A separate local planner sees exact current APIs before the first topology edit.
        if not integrated_builder and not runner.store.get('map_extension_plan'):
            design=runner.design(task,ident)
            if not design.get('ok'):raise Halt('Map planner did not finish a bounded implementable design')
            runner.store.set(map_extension_plan=design['decision'])
        if integrated_builder:
            runner.store.event('map-design-in-local-builder', separate_plan_claimed=False,
                reason='Preserved read-turn/output-limit planner failures; direct bounded local source action.')
        result=runner.edit(task,ident)
        candidate=runner.checkpoint_source('Local Qwen: first connected map extension')
        runner.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        probe=result.get('scenario') or runner.propose_replay(task,ident)['scenario']
        bundle,gate=runner.native(task,ident,candidate,probe)
        if gate.get('passed'):
            rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            extension=inspect_extension(rows);support=pavement_coverage(bundle)
            driving=[r for r in rows if r.get('mode')=='vehicle']
            supported=bool(driving) and all(any(
                s['min'][0]<=r['vehicle'][0]<=s['max'][0] and
                s['min'][2]<=r['vehicle'][2]<=s['max'][2] and
                abs(s['max'][1]-r['vehicle'][1])<.5 for s in support['surfaces']) for r in driving)
            if not supported:
                extension['passed']=False;extension['failure'].append('vehicle-rendered-support')
            probe_captures=probe['captures']
            for mode,key in [('foot','player'),('vehicle','vehicle')]:
                if not any(abs(r['time']-t)<=.25 and r.get('mode')==mode and
                           outside_distance(r[key])>=6 for t in probe_captures for r in rows):
                    extension['passed']=False;extension['failure'].append(mode+'-outside-capture-missing')
            gate['scoped_facts'].update(map_extension=extension,rendered_walking_support=support)
            if not extension['passed'] or not support['passed']:
                gate.update(passed=False,failure=extension['failure']+([] if support['passed'] else ['rendered-pavement-support']))
        if gate.get('passed'):
            gate['regressions']=runner.regress(TASKS[6],ident,candidate)
            if not gate['regressions']['passed']:gate.update(passed=False,failure=gate['regressions']['failure'])
        atomic(bundle/'scoped-gate.json',gate)
        if not gate.get('passed'):
            runner.reject_scoped(task,ident,gate,candidate);continue
        review=runner.review(task,ident,bundle,gate)
        if not review.get('ok') or review.get('verdict')!='PASS':
            runner.reject_scoped(task,ident,review,candidate);continue
        record=dict(candidate=candidate,evidence=str(bundle.relative_to(runner.store.root)),
            accepted_utc=now(),review=review,scope=task['outcome'],final_game_accepted=False,
            capture_manifest_sha256=sha((bundle/'captures/manifest.json').read_bytes()))
        note=runner.project/'Notes'/('map-'+ident+'.json');atomic(note,record)
        git(runner.repo,'add','--',str(note.relative_to(runner.repo)))
        git(runner.repo,'-c','user.name=Evidence controller',
            '-c','user.email=254017794+oh-ashen-one@users.noreply.github.com','commit','-m',
            'Record native connected-extension PASS; complete map and pacing remain pending')
        saved=git(runner.repo,'rev-parse','HEAD')
        runner.store.set(accepted_map_extension=record,last_playable_checkpoint=saved,
            source_checkpoint=saved,last_verified_progress_epoch=time.time(),last_verified_progress_utc=now())
        frames,times=review_captures(task,bundle)
        queue_milestone(runner.store,'accepted-feature',task,bundle,gate,frames,times,review)
        runner.store.event('map-extension-accepted',**record)
        runner.store.report()
    return runner.store.get('accepted_map_extension')
