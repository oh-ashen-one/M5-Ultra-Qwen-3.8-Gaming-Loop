#!/usr/bin/env python3
"""Local lighting and existing-mesh dressing after a preserved visual rejection."""
import copy
import json
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery, ACCEPTED, BLOCKER
from resume_alley_presentation import PATH, REPLAY
from qualify_map_extension import MAP_TASK, outside_distance
from loop_controller.core import Files, Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='340c32fc550e123f5bf73e605ce0a6d3a47c7e2b'
CANDIDATE='ab3a64ef8cb3511dc02ab3c31a88162f6efe76f9'
ROUND='q0072-b5de47c6'
NEEDLE='// 3) Understandable end barriers using the original fence mesh.'


def validate_readability_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=17,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,alley_completed_recovery_attempted=True,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('alley_readability_recovery_attempted'):
        raise Halt('Expected exact preserved scenery visual FIX, not an unrelated fault')
    if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve proven physical inputs')


def add_junction_captures(probe, rows):
    updated=copy.deepcopy(probe)
    added=[]
    for mode,key in [('foot','player'),('vehicle','vehicle')]:
        near=[r for r in rows if r.get('mode')==mode and r.get(key) and
              0<outside_distance(r[key])<=2 and 4<r['time']<probe['duration']]
        if not near:raise Halt('No observed junction crossing to capture')
        row=min(near,key=lambda r:(abs(outside_distance(r[key])-.7),r['time']))
        added.append(round(row['time'],3))
    updated['captures']=sorted(set(updated['captures']+added))
    if replay_identity(updated)!=replay_identity(probe):raise Halt('Capture addition changed physical inputs')
    return updated


class AlleyReadability(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_readability_pause(old)
        bundle=self.store.root/'evidence'/ROUND
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        review=json.loads((bundle/'critic.json').read_text())
        checks=gate.get('regressions',{}).get('regressions',[])
        if (gate.get('candidate_commit')!=CANDIDATE or not gate.get('passed') or len(checks)!=10
                or not all(x['gate'].get('passed') for x in checks)
                or not review.get('ok') or review.get('verdict')!='FIX'):
            raise Halt('Require exact all-ten physical PASS and independent visual FIX')
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Expected preserved accepted fallback')

    def recovery_settings(self):
        return dict(alley_readability_recovery_attempted=True,recovery_route='local-readability-repair',
            recovery_change='Local fill lighting, original prop dressing and service-door wall detail',
            readability_native_budget=1)

    def selected(self,ident,label,instruction,max_lines,images=()):
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        matches=[i+1 for i,line in enumerate(raw.splitlines()) if line.strip()==NEEDLE]
        if len(matches)!=1:raise Halt('Expected one exact insertion boundary')
        edit=SelectedEdit(files,PATH,matches[0],matches[0],max_lines=max_lines)
        self.c.update(output_tokens=4096,model_timeout_seconds=210)
        self.store.set(stage='local-alley-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the sole local Qwen game author. Save only the selected bounded visual edit.',
            instruction+' Insert before the selected comment and preserve the comment. '
            'Keep every current collider, floor, wall, actor, input, camera and mission unchanged. '
            'No generated assets, primitives or new art files. Existing original meshes only. '
            'Use declared local variables, no undefined helper. Save immediately.\nEXACT OLD LINE:\n'+edit.old+
            '\nCURRENT SOURCE:\n'+raw,
            [tool('edit_selected_span','Save the scoped original visual edit.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},
            images=list(images),turns=1,reasoning_effort='low')
        if path.read_text()==raw:
            self.report_blocker('Local readability '+label+' supplied no saved edit',ident)
            raise Halt('Scoped readability edit not saved; prior local source preserved')
        saved=self.checkpoint_source('Local Qwen: alley '+label)
        self.store.set(source_checkpoint=saved,candidate_commit=saved)

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('One exact readability repair only')
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        saved=self.checkpoint_source('Recover qualified local alley for readable lighting and original details')
        self.store.set(source_checkpoint=saved)
        bundle=self.store.root/'evidence'/ROUND
        images=[('ACTUAL prior dark walking alley',bundle/'captures/frame-002.png'),
                ('ACTUAL prior entrance',bundle/'captures/frame-000.png')]
        self.selected(ident,'readable-fill',
            'Actual independent review rejects the near-black alley and unreadable character. '
            'Add two modest warm-neutral Point lights over the alley at world (12,4,12) and (19,4,16), '
            'parented to go, with range18..22, intensity2..3 and no shadows. Choose restrained values '
            'from the actual images; retain the golden-hour key light. Give ONLY ap MeshRenderer a '
            'new Material copied from its sharedMaterial, with neutral medium-dark grey albedo around '
            '(0.30,0.30,0.29), so the road edge and actor silhouette read. Do not modify shared street '
            'materials or global lighting. At most18lines.',26,images)
        self.selected(ident,'entrance-props',
            'Frame the real entrance and give the alley a purpose using exactly three existing original '
            'prop instances: clone GameObject.Find("bollard01") twice, and GameObject.Find("dumpster_a") '
            'once. Desired world horizontal centers: bollards(8,8.8) and(8,19.65), dumpster(16,9.5). '
            'Instantiate complete objects under go preserving world scale/rotation and every existing '
            'collider. Aggregate child Renderer.bounds after cloning and translate each so its X/Z '
            'bounds center equals its target and its minimumY is pavement top0.14. Use clear unique '
            'Alley names. The proven foot/car path has rootZ16.15..17.95; keep that lane empty. '
            'Add no other object or collider and never remove/disable old props. At most32lines.',44)
        self.selected(ident,'service-door-detail',
            'Break up the blank north alley wall with two closed service-door assemblies from the '
            'existing original MeshFilters/MeshRenderers named door00_panel and door00_surround. '
            'Reuse their sharedMesh and sharedMaterial. Place assemblies at worldX12 and18 on the '
            'north wall interiorZ19.92. Original doors face world+X; rotate worldY90 degrees times '
            'each source rotation so the clones face world-Z. Preserve each source lossyScale and '
            'source Renderer.bounds.center.y. For each new mesh, center it at(X,sourceBoundsCenterY,19.92) '
            'by subtracting rotation*Vector3.Scale(mesh.bounds.center,scale) from that target. '
            'Parent to go and use unique AlleyServiceDoor names. Reuse mesh/material only; no scripts, '
            'new colliders or passage through the underlying solid wall. These are closed visual details, '
            'not gameplay objectives. At most30lines.',42)
        old=self.store.get('last_valid_replay')
        if replay_identity(old)!=REPLAY:raise Halt('Proven physical inputs changed')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        scenario=add_junction_captures(old,rows)
        self.store.set(last_valid_replay=scenario)
        self.store.event('local-alley-readability-saved',candidate=self.store.get('source_checkpoint'),
            prior_native_candidate=CANDIDATE,physical_inputs_unchanged=True,
            added_observed_boundary_captures=True,cloud_game_code_authored=False,
            all_ten_and_fresh_critic_required=True)
        return dict(ok=True,scenario=scenario)


if __name__=='__main__':raise SystemExit(main(AlleyReadability))
