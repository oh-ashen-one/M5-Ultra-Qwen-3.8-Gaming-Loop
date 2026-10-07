#!/usr/bin/env python3
"""Changed ordinary input after measured partial-turn misses; gameplay is unchanged."""
import json
from resume_moving_encounter import MovingEncounter,TASK
from resume_combat_death import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.continuous_checks import validate_proposed
from loop_controller.interception_checks import probes
from qualify_moving_encounter import qualify

SOURCE='c9aa15bdb02f0e81edd04c50598a28dc6092ae00'
ROUND='q0125-2c1e6a12'
FAILURES=['positive-encounter-ending-unverified','three-actual-moving-target-kills-unverified']


def corrected_probe(original):
    probe=probes(original)['positive']
    remove={64.8,66.2,72.2}
    probe['steps']=[s for s in probe['steps'] if s['start'] not in remove]
    # The measured .15s A taps rotate only about81degrees after southward travel.
    # Complete the turn. Between runner1 and2, aim at the still-live original
    # pursuer with ordinary diagonal movement and three actual shots.
    changes=[(64.3,64.35,['A','S']), (64.8,64.89,['Mouse0']), (65,65.09,['Mouse0']),
        (65.2,65.29,['Mouse0']), (65.5,66.716667,['S']), (66.9,67.1,['A']), (72.2,72.4,['A'])]
    probe['steps'] += [dict(start=a,end=b,keys=k) for a,b,k in changes]
    return validate_proposed(probe,100,'mission-core')


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        stage='native-moving-encounter-positive',blocker='Halt: Moving encounter positive needs measured diagnosis: '+json.dumps(FAILURES))
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('moving_replay_recoveries',0):
        raise Halt('Require exact first moving-target input failure and unchanged history')


class InterceptionReplay(MovingEncounter):
    def validate_recovery(self,old):
        validate_pause(old)
        self.resume_capacity=False;self.priority_resume=False;self.transport_recovery=False;self.admission_recovery=False
        base=self.store.root/'evidence'
        self.escape=base/(ROUND+'-exploration');self.failed=base/(ROUND+'-positive')
        good=read_json(self.escape/'moving-encounter-gate.json');bad=read_json(self.failed/'moving-encounter-gate.json')
        if (not good.get('passed') or good.get('candidate_commit')!=SOURCE or
            bad.get('failure')!=FAILURES or bad.get('candidate_commit')!=SOURCE or
            not read_json(self.failed/'gate.json').get('passed')):
            raise Halt('Preserve unrelated runtime, source or contract failures')
        events=[json.loads(x) for x in (self.failed/'captures/aim-shots.jsonl').read_text().splitlines()]
        observed=[(t['hpBefore'],t['hpAfter']) for e in events for t in e['targets'] if
            t['name']=='InterceptRunner1' and t['hpAfter']<t['hpBefore']]
        later=[e for e in events if 69<=e['time']<=76]
        if observed!=[(3,2),(2,1),(1,0)] or len(later)<10 or any(e['firstRayCollider']!='AlleyPavement' for e in later):
            raise Halt('Changed replay requires the measured first-runner success and later pavement misses')
        self.proof={str(p.relative_to(self.store.root)):sha(p.read_bytes()) for root in [self.escape,self.failed]
            for p in [root/'gate.json',root/'moving-encounter-gate.json',root/'captures/trace.jsonl']}

    def wait_for_capacity(self):self.capacity.wait('native-moving-encounter-changed-input')

    def recovery_settings(self):
        return dict(moving_replay_recoveries=1,recovery_route='measured-turn-and-live-pursuer-input-correction',
            recovery_change='Preserve the first-runner real kill and original-rival isolation proof. Later '
            'south-to-west taps stopped about9degrees short; those shots hit pavement. Extend the A taps '
            'and use ordinary movement/Mouse0 against the surviving original pursuer before health reaches '
            'zero. No source, physics, hit-test, health, spawn, timer or acceptance change.')

    def work(self):
        ident=self.begin(TASK,'native-moving-encounter-changed-input')
        for name,digest in self.proof.items():
            if sha((self.store.root/name).read_bytes())!=digest:raise Halt('Original encounter proof changed')
        original=read_json(self.store.root/'evidence/q0120-dc4867c8-positive/captures/scenario.json')
        candidate=corrected_probe(original)
        atomic(self.store.root/'evidence'/(ident+'-input-diagnosis.json'),dict(
            source_unchanged=SOURCE,original_evidence=self.proof,
            facts='First runner HP3->2->1->0; original rival remained rendered/solid. All later shots hit pavement '
                  'with a camera direction about9degrees short of west; surviving pursuer reduced health to0.',
            changed_probe=candidate,prior_escape_runtime_reused=True,new_positive_runtime_required=True))
        qualify(self,ident,SOURCE,self.escape,read_json(self.escape/'moving-encounter-gate.json'),original,
                positive_probe=candidate,prior_escape=True)


if __name__=='__main__':raise SystemExit(main(InterceptionReplay))
