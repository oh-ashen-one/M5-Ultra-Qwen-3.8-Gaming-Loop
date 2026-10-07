#!/usr/bin/env python3
"""Measure current combat on the accepted ordinary-input route without gameplay edits."""
from loop_controller.core import Halt,atomic,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from resume_mission_review import verified_probe
from resume_three_day_queue import ThreeDayRunner,main

SOURCE='2d6648196b32c225009e2f9545b9b60947ed1ceb'
ACCEPTED='81659edb371a6b961d2e09983d88140b9c73d4ff'


def summarize_combat(rows):
    observed=[(r,v) for r in rows for v in r.get('rivals',[]) if v.get('alive')]
    driving=[(r,v) for r,v in observed if r.get('mode')=='vehicle']
    far=[(r,v) for r,v in driving if v['actorDistance']>18]
    damage=[]
    for (before,_),(row,rival) in zip(observed,observed[1:]):
        if row.get('restarts',0)==before.get('restarts',0) and row.get('health',100)<before.get('health',100):
            damage.append({'time':row['time'],'mode':row.get('mode'),'actor_distance':rival['actorDistance'],
                'foot_distance':rival['footDistance'],'unobstructed':rival.get('attackUnobstructed'),
                'first_world_collider':rival.get('firstAttackCollider'),'health':row['health']})
    return {'samples':len(rows),'rival_samples':len(observed),
        'initial_rival':observed[0][1] if observed else None,
        'furthest_driving':{'time':max(driving,key=lambda x:x[1]['actorDistance'])[0]['time'],
            **max(driving,key=lambda x:x[1]['actorDistance'])[1]} if driving else None,
        'pursuit_while_vehicle_over_18m':sorted({r.get('pursuit') for r,v in far}),
        'damage_events':damage,'gameplay_acceptance_claimed':False}


class CombatInspection(ThreeDayRunner):
    def validate_recovery(self,old):
        if (old.get('task_index')!=4 or old.get('source_checkpoint')!=SOURCE
                or old.get('last_playable_checkpoint')!=ACCEPTED or old.get('task_failures')!=0
                or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH
                or not old.get('blocker','').startswith('Halt: Replay-only role supplied no valid finish_task')):
            raise Halt('Only the inspected combat replay-budget stop admits this native diagnostic')

    def recovery_settings(self):return {'combat_inspection_pending':True}

    def work(self):
        import json
        if not self.store.get('combat_inspection_pending'):raise Halt('Diagnostic is one-time only')
        task=dict(id='combat-native-diagnostic',maximum=180,coverage='mission-core',checks=[])
        probe,prior=verified_probe(self.store.root,task)
        probe.update(duration=28,steps=[s for s in probe['steps'] if 'R' not in s['keys']],
                     captures=[3.2,5.2,7.9,9.4,14.8,20,26])
        bundle=self.store.root/'evidence/combat-inspection-2d66481'
        self.store.set(stage='native-combat-diagnostic');self.store.report()
        gate=self.engines.unity(self.project,bundle,probe,SOURCE)
        trace=bundle/'captures/trace.jsonl'
        facts=summarize_combat([json.loads(x) for x in trace.read_text().splitlines()]) if trace.exists() else {}
        atomic(bundle/'combat-observations.json',facts)
        self.store.set(combat_inspection_pending=False,combat_inspection_evidence=str(bundle.relative_to(self.store.root)))
        self.store.event('combat-diagnostic-complete',candidate=SOURCE,native_gate_passed=gate.get('passed'),
                         source_changed=False,counters_changed=False,prior_route=prior)
        raise Halt('Combat diagnostic complete; preserve source for measured small local fixes')


if __name__=='__main__':raise SystemExit(main(CombatInspection))
