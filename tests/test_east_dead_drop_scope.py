import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_east_dead_drop as m
from loop_controller.core import Halt

class EastDeadDropScopeTests(unittest.TestCase):
    def test_full_chapter_keeps_real_courier_anchor_and_input_checks(self):
        self.assertIn('mission_complete',m.TASK['checks'])

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


    def test_compile_recovery_preserves_failed_source_and_does_not_reopen_unrelated_faults(self):
        import resume_east_dead_drop_compile as c
        state=dict(source_checkpoint=c.SOURCE,last_playable_checkpoint=c.ACCEPTED,current_round=c.ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=c.HARD_CAP_EPOCH,east_dead_drop_implementation_attempted=True,
            blocker='Halt: Saved chapter failed additive native activation/reset gate')
        before=copy.deepcopy(state);c.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('task_failures',0),('east_dead_drop_compile_repair_attempted',True),
                          ('blocker','Resource fault'),('source_checkpoint',m.SOURCE)]:
            with self.subTest(key=key),self.assertRaises(Halt):c.validate_pause({**state,key:value})


    def test_negative_repair_requires_inactive_chapter_and_only_the_missing_motion_failure(self):
        import resume_chapter_negative_probe as c
        from test_route_chapter import row
        gate={'candidate_commit':c.SOURCE,'passed':False,'failure':['input-driven-player-movement']}
        rows=[row(1),row(5,keys=('F',))]
        c.validate_negative(gate,rows)
        for changed in [{**gate,'failure':['runtime-exit-or-identity']},{**gate,'passed':True},
                        {**gate,'candidate_commit':'other'}]:
            with self.assertRaises(Halt):c.validate_negative(changed,rows)
        rows[1]['routeChapter']['stage']=1
        with self.assertRaises(Halt):c.validate_negative(gate,rows)
        self.assertTrue(any('W' in step['keys'] for step in m.NO_HANDOFF['steps']))

if __name__=='__main__':unittest.main()
