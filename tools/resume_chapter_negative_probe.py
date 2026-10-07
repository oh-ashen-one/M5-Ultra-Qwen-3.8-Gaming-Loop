#!/usr/bin/env python3
"""Fix a negative replay precondition without changing game code or the runtime gate."""
import json
from resume_east_dead_drop import EastDeadDrop,TASK,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.route_chapter import inspect_chapter

SOURCE='f5b4080f64e33bf4bb563ebb573df4266c7e4f37'
ROUND='q0095-8506fee6'
GATE_SHA='6f87b5855958dd67301f0fd41621c2151f0ee8827f9c287b3156f856b8168e97'
TRACE_SHA='38d6b72f5723126f82f730997ae2e8734957cb2f9b9d1e8e18773945c8811354'
ACTIVATION_SHA='c017321b906d1a3a042892581e2586198b9f7e64582905933cf24562040d2fd2'
ACTIVATION_TRACE='4d8ea4db3994e7a897e5b66bda62fc1c289775502cfa3c9d574f37120588fad3'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,east_dead_drop_compile_repair_attempted=True,
        blocker='Halt: Chapter advances without the real courier handoff')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_negative_motion_repair_attempted'):
        raise Halt('Expected exact preserved missing-motion negative probe, not a gameplay failure')

def validate_negative(gate,rows):
    if (gate.get('candidate_commit')!=SOURCE or gate.get('passed')
            or gate.get('failure')!=['input-driven-player-movement']
            or not inspect_chapter(rows,False,False,True)['passed']):
        raise Halt('Only the stationary negative replay precondition is repairable by this scope')

class ChapterNegativeProbeRepair(EastDeadDrop):
    def validate_recovery(self,old):
        validate_pause(old);r=self.store.root/'evidence'
        neg=r/(ROUND+'-inactive-red');active=r/(ROUND+'-activation')
        for p,digest in [(neg/'chapter-gate.json',GATE_SHA),(neg/'captures/trace.jsonl',TRACE_SHA),
                         (active/'chapter-gate.json',ACTIVATION_SHA),(active/'captures/trace.jsonl',ACTIVATION_TRACE)]:
            if sha(p.read_bytes())!=digest:raise Halt('Preserved chapter evidence changed')
        rows=[json.loads(x) for x in (neg/'captures/trace.jsonl').read_text().splitlines()]
        validate_negative(read_json(neg/'chapter-gate.json'),rows)
        gate=read_json(active/'chapter-gate.json')
        if not gate.get('passed') or gate.get('candidate_commit')!=SOURCE:raise Halt('Keep the exact successful activation/reset source')

    def recovery_settings(self):
        return dict(chapter_negative_motion_repair_attempted=True,
            recovery_route='negative-replay-movement-precondition',
            recovery_change='Original173samples remain inactive; add ordinary W movement before remote F without changing game source or runtime movement requirement')

    def work(self):
        ident=self.begin(TASK,'native-chapter-negative-recovery')
        activation=read_json(self.store.root/'evidence'/(ROUND+'-activation')/'captures/scenario.json')
        self.store.event('chapter-negative-precondition-repaired',original_round=ROUND,source_unchanged=SOURCE,
            original_failure='input-driven-player-movement',original_chapter_inactive=True,
            activation_reset_reused=True,cloud_role='external normal-input acceptance only')
        return self.continue_chapter(ident,SOURCE,activation)

if __name__=='__main__':raise SystemExit(main(ChapterNegativeProbeRepair))

