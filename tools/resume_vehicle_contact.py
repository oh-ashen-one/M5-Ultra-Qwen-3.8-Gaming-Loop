#!/usr/bin/env python3
"""Measure unchanged grounded failure, then permit only an evidenced actor-physics repair."""
import json
import math
import uuid
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner,main
from resume_map_traversal import MapTraversalRecovery,ACCEPTED
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK,qualify_one_extension
from loop_controller.core import Files,Halt,atomic,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='f2889dc458343cc5018a6f52de3e67b9f0ad48fe'
CANDIDATE='bd0187d4c05d3c77bb1e60376852cf2851b738b0'
ROUND='q0067-99bd4994'
REPLAY='43879c58b005b9b888e3be11fd0fed8ea5652487937bca44d21b9d10908d91b9'
PATH='Assets/Game/Combat.cs'


def diagnose_contacts(rows):
    samples=[];blocking=[];previous=None
    for row in rows:
        p=row.get('vehiclePhysics') or {}
        if row.get('mode')!='vehicle' or not p.get('available'):continue
        delta=row['time']-previous['time'] if previous else 0
        speed=(math.hypot(row['vehicle'][0]-previous['vehicle'][0],row['vehicle'][2]-previous['vehicle'][2])/delta
               if previous and delta>0 else float('inf'))
        previous=row
        contacts=[c for c in p.get('contacts',[]) if abs(c['normal'][1])<.5
                  and abs(row['time']-c['time'])<.25]
        if not contacts:continue
        sample={k:row.get(k) for k in ('time','keys','vehicle','vehiclePenetration')}
        sample['physics']=p;sample['observed_horizontal_speed']=speed if math.isfinite(speed) else None;samples.append(sample)
        if p.get('throttle',0)>0 and p.get('commandedSpeed',0)>2 and speed<1.5 and any(
                c['collider']=='Rival' and not c['otherHasBody'] for c in contacts):
            blocking.append(sample)
    return dict(utc=now(),static_rival_blocking_samples=len(blocking),
        cause_verified=len(blocking)>=3,first_blocking=blocking[:8],
        contact_names=sorted({c['collider'] for s in samples for c in s['physics']['contacts']}),
        samples=samples[::max(1,len(samples)//20)])


def validate_contact_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=15,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('vehicle_contact_recovery_attempted'):
        raise Halt('Expected exact grounded-driving rejection with preserved prior budget')
    if len(old.get('map_traversal_strategies',[]))!=3 or replay_identity(old['last_valid_replay'])!=REPLAY:
        raise Halt('Preserve all exhausted route strategies and the last observed input sequence')


class VehicleContactRecovery(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_contact_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Accepted fallback tree must remain preserved')

    def recovery_settings(self):
        return dict(vehicle_contact_recovery_attempted=True,recovery_route='cause-based-physics-diagnosis',
            recovery_change='Unchanged-input passive contact measurement; one evidenced local actor-physics repair',
            vehicle_contact_native_budget=1)

    def local_span(self,ident,label,needle,instructions,max_lines):
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        matches=[i+1 for i,line in enumerate(raw.splitlines()) if line.strip()==needle]
        if len(matches)!=1:raise Halt('Expected one exact '+label+' source line')
        edit=SelectedEdit(files,PATH,matches[0],matches[0],max_lines=max_lines)
        self.c.update(output_tokens=2048,model_timeout_seconds=120)
        self.store.set(stage='local-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the sole local game coder. Submit this exact bounded C# repair now.',
            instructions+'\nEXACT OLD SPAN:\n'+edit.old+'\nACTUAL READ-ONLY SOURCE:\n'+raw,
            [tool('edit_selected_span','Save only this bounded source span.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if path.read_text()==raw:
            self.report_blocker('Local '+label+' source repair supplied no change',ident)
            raise Halt('Cause-based source action was not submitted')
        saved=self.checkpoint_source('Local Qwen: '+label)
        self.store.set(source_checkpoint=saved,candidate_commit=saved)

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        diagnosis=self.store.get('vehicle_contact_diagnosis')
        if not diagnosis or not diagnosis['cause_verified'] or self.store.get('vehicle_contact_fix_submitted'):
            raise Halt('Only one contact-proven actor-physics repair is admitted')
        self.local_span(ident,'rival-physical-body','col.isTrigger = false;',
            'Actual native OnCollision callbacks verify a solid static Rival capsule blocks the1200kg '
            'car under throttle, with low actual speed despite commanded speed>2. The Rival currently '
            'has NO Rigidbody, stops within3m of target and behaves as an immovable wall. Repair the '
            'real actor physics minimally: retain this exact non-trigger collider line, then attach a '
            'nonkinematic, gravity-enabled Rigidbody of plausible human mass80kg, freeze rotation so it '
            'stays upright, with moderate linear damping. Let actual collision impulses displace it. '
            'Use only standard UnityEngine APIs and a local variable you declare. Do not change car '
            'physics, collider sizes, layer collisions, hit/health/pursuit signals, attack range or '
            'input/replay. Do not add fake knockback, teleportation, invulnerability or collision bypass. '
            'Preserve all existing chase/fire code in this step. At most8lines.',8)
        self.local_span(ident,'rival-physics-reset','rivalGo.position = RIVAL_SPAWN;',
            'The rival now has a real dynamic Rigidbody. On the existing R retry path, preserve the '
            'original rivalGo.position reset and additionally obtain its existing Rigidbody with a '
            'declared local variable, clear linearVelocity and angularVelocity, and set its position '
            'to RIVAL_SPAWN. Use a null guard. Only this legitimate user reset may reposition the body; '
            'do not change ordinary play, HP, controls, camera or replay. At most6lines.',6)
        scenario=self.store.get('last_valid_replay')
        if replay_identity(scenario)!=REPLAY:raise Halt('Cause-based test must preserve the failed driving inputs')
        self.store.set(vehicle_contact_fix_submitted=True)
        self.store.event('contact-cause-source-repaired',candidate=self.store.get('source_checkpoint'),
            input_replay_unchanged=True,prior_strategies_preserved=3,native_pass_claimed=False)
        return dict(ok=True,scenario=scenario)

    def work(self):
        self.machine.guard();self.store.set(task_design=NEXT_MAP)
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        saved=self.checkpoint_source('Recover local grounded candidate for passive contact diagnosis')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        ident='q%04d-%s-contact'%(self.store.get('rounds',0)+1,uuid.uuid4().hex[:8])
        self.store.set(current_round=ident,rounds=self.store.get('rounds',0)+1,
            stage='native-contact-diagnosis');self.store.report()
        scenario=self.store.get('last_valid_replay')
        bundle,gate=self.native(MAP_TASK,ident,saved,scenario)
        if not gate.get('passed'):
            self.report_blocker('Unchanged-input contact diagnostic failed build/runtime',ident)
            raise Halt('Contact diagnosis native execution failed')
        rows=[json.loads(l) for l in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        diagnosis=diagnose_contacts(rows);diagnosis.update(round=ident,candidate=saved,build_id=gate['build_id'])
        atomic(bundle/'vehicle-contact-diagnosis.json',diagnosis)
        self.store.set(vehicle_contact_diagnosis=diagnosis)
        self.store.event('actual-vehicle-contact-diagnosis',**diagnosis);self.store.report()
        if not diagnosis['cause_verified']:
            self.report_blocker('Contact data does not establish the hypothesized static-rival blocker; inspect measured evidence',ident)
            raise Halt('Do not modify gameplay based on an unverified contact hypothesis')
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,recovery_route='accepted',
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(VehicleContactRecovery))
