import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_east_dead_drop as m
from loop_controller.core import Halt

class EastDeadDropScopeTests(unittest.TestCase):
    def test_scope_requires_exact_plan_pause_and_preserves_counters(self):
        state=dict(source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,current_round=m.ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=m.HARD_CAP_EPOCH,mission_pacing_design_attempted=True,
            stage='connected-mission-design-saved',
            blocker='Halt: Connected mission design saved; dedicated external acceptance and local source implementation are next')
        before=copy.deepcopy(state);m.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('task_failures',0),('east_dead_drop_implementation_attempted',True),
                          ('overall_deadline_epoch',m.HARD_CAP_EPOCH+1),('source_checkpoint','other')]:
            with self.subTest(key=key),self.assertRaises(Halt):m.validate_pause({**state,key:value})

    def test_module_cannot_write_legacy_state_or_inspect_harness(self):
        valid='class RouteMission { public int RouteStage; public bool RouteComplete; public Transform Cache; public string Objective; }'
        self.assertEqual(m.validate_module(valid),valid)
        for code in ['LoopSignals.Mission = "complete";','LoopSignals.Health += 1;',
                     'LoopSignals.Restarts++;','LoopInput.Replay.id','class LoopSignals {}',
                     'CreatePrimitive(PrimitiveType.Cube)','MissionComplete']:
            with self.subTest(code=code),self.assertRaises(ValueError):m.validate_module(valid+code)
        m.validate_module(valid+' if(LoopSignals.Mission == "complete") { }')

if __name__=='__main__':unittest.main()

