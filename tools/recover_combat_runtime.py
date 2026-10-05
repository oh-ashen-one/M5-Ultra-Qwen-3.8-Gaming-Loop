#!/usr/bin/env python3
"""Resume preserved combat evidence after the explicitly authorized supervisor repair."""
import json
import uuid
from copy import deepcopy
from pathlib import Path
from qualify_combat_focus import CombatFocus,COMBAT,REPAIRED,ACCEPTED,combined_probe
from resume_three_day_queue import ThreeDayRunner,main
from resume_mission_review import verified_probe
from loop_controller.core import Halt,read_json,atomic,failure_key
from loop_controller.continuous_tasks import TASKS
from loop_controller.continuous_checks import WORLD_PROBE,MOTOR_PROBE,validate_proposed
from loop_controller.combat_checks import FOOT_PROBE,WALL_PROBE,DRIVE_PROBE,inspect_combat_contract
from loop_controller.delivery_policy import HARD_CAP_EPOCH

ORIGINAL='combat-focus-41bdf148-combined'


class RuntimeRecovery(CombatFocus):
    def validate_recovery(self,old):
        if (old.get('blocker')!='Halt: Resident supervisor did not grant engine handoff' or
            old.get('source_checkpoint')!=REPAIRED or old.get('last_playable_checkpoint')!=ACCEPTED or
            old.get('task_index')!=4 or old.get('task_failures')!=3 or old.get('failure_streak')!=3 or
            old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH):
            raise Halt('Expected exact preserved combat/runtime stop; do not replace other work')

    def recovery_settings(self):return {'combat_runtime_recovery_pending':True}

    def remaining_regressions(self,ident):
        walk=read_json(self.store.root/'evidence'/(ORIGINAL+'-regression-walk')/'scoped-gate.json')
        if not walk.get('passed') or walk.get('candidate_commit')!=REPAIRED:
            raise Halt('Preserved walking regression provenance mismatch')
        checks=[('world',WORLD_PROBE,TASKS[0]),('motor',MOTOR_PROBE,TASKS[1])]
        for label,index in [('courier',2),('failure-retry',3)]:
            task=TASKS[index];accepted=self.store.get('accepted_queue_features',{})[task['id']]
            bundle=self.store.root/accepted['evidence'];gate=read_json(bundle/'scoped-gate.json')
            if not gate.get('passed') or gate.get('candidate_commit')!=accepted['candidate']:
                raise Halt('Accepted regression provenance mismatch: '+label)
            probe=validate_proposed(read_json(bundle/'captures/scenario.json'),task['maximum'],task['coverage'])
            checks.append((label,probe,task))
        results=[{'test':'walk','gate':walk,'reused_unchanged_native_evidence':True}]
        for name,probe,task in checks:
            self.store.set(stage='combat-recovery-regression-'+name);self.store.report()
            _,gate=self.native(task,ident+'-regression-'+name,REPAIRED,probe)
            results.append({'test':name,'gate':gate})
            if not gate.get('passed'):return {'passed':False,'failure':['accepted-baseline-regression'],'regressions':results}
        return {'passed':True,'regressions':results}

    def work(self):
        ident='combat-runtime-'+uuid.uuid4().hex[:8];task=TASKS[4]
        bundle=self.store.root/'evidence'/ORIGINAL;gate=deepcopy(read_json(bundle/'scoped-gate.json'))
        if not gate.get('passed') or gate.get('candidate_commit')!=REPAIRED:raise Halt('Preserve original combined evidence')
        regression=self.remaining_regressions(ident);gate['regressions']=regression
        atomic(bundle/'recovered-regressions.json',regression)
        if not regression['passed']:self.reject_scoped(task,ident,regression,REPAIRED)
        drive=self.store.root/'evidence/combat-focus-9b15f344-after-driving'
        rows=[json.loads(l) for l in (drive/'captures/trace.jsonl').read_text().splitlines()]
        stable=inspect_combat_contract(rows,'driving')
        atomic(drive/'sustained-escape-contract.json',stable)
        gate['sustained_escape_contract']=stable
        self.store.set(stage='fresh-f965-combat-critique');self.store.report()
        review=self.review(task,ident+'-original',bundle,gate)
        atomic(bundle/'recovered-scoped-assessment.json',{'gate':gate,'review':review,'promoted':False})
        if not review.get('ok'):raise Halt('Fresh original-candidate critique incomplete; preserve results')
        self.store.event('original-combat-candidate-reviewed',candidate=REPAIRED,
            baseline_regressions_passed=True,review=review,sustained_escape=stable,promoted=False)
        # A one-sample crossing is a proven missing gameplay requirement. Keep
        # the distance rule and vehicle/world unchanged; local Qwen authors repair.
        self.selected(ident,'sustained-escape-walking-speed',
            'Measured native gameplay: the2m/s rival keeps chasing to the closed street boundary; actual vehicle '
            'distance exceeds the unchanged18m escape rule for only one0.1s sample. Make one small balance correction: '
            'set RIVAL_SPEED to1.0f so the walking rival allows a usable escape interval on this existing short block. '
            'Keep the constant name and float type. Do not alter18m pursuit,16m attacks, HP, car physics, colliders, '
            'source ownership, replay rules or mission. This is ordinary gameplay for all users.',
            start='const float RIVAL_SPEED =',end='const float RIVAL_SPEED =',max_lines=2)
        candidate=self.checkpoint_source('Local Qwen: usable sustained pursuit escape')
        self.store.set(source_checkpoint=candidate,stage='native-sustained-combat');self.store.report()
        after=[self.native_test(ident+'-stable-'+kind,probe,kind,candidate)
            for kind,probe in [('foot',FOOT_PROBE),('wall',WALL_PROBE),('driving',DRIVE_PROBE)]]
        atomic(self.store.root/'combat-sustained-result.json',{'candidate':candidate,'contracts':after,'original_candidate':REPAIRED})
        if not all(v['passed'] for v in after):
            self.reject_scoped(task,ident,{'failure':[f for v in after for f in v.get('failure') or []]},candidate)
        prior,_=verified_probe(self.store.root,task)
        self.store.set(stage='native-sustained-combat-combined');self.store.report()
        new_bundle,new_gate=self.native(task,ident+'-stable-combined',candidate,combined_probe(prior))
        new_gate['combat_contracts']=after
        if new_gate.get('passed'):
            new_gate['regressions']=self.regress(task,ident+'-stable-combined',candidate)
            if not new_gate['regressions']['passed']:new_gate.update(passed=False,failure=new_gate['regressions']['failure'])
        atomic(new_bundle/'scoped-gate.json',new_gate)
        if not new_gate.get('passed'):self.reject_scoped(task,ident,new_gate,candidate)
        self.store.set(stage='fresh-sustained-combat-critique');self.store.report()
        new_review=self.review(task,ident+'-stable-combined',new_bundle,new_gate)
        if not new_review.get('ok') or new_review.get('verdict')!='PASS':self.reject_scoped(task,ident,new_review,candidate)
        self.promote(task,candidate,new_bundle,new_gate,new_review)
        self.store.set(combat_runtime_recovery_pending=False)
        return ThreeDayRunner.work(self)


if __name__=='__main__':raise SystemExit(main(RuntimeRecovery))
