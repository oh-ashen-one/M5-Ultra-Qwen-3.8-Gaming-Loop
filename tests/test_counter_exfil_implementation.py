from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import implement_counter_exfil as m
from loop_controller.core import Halt

class CounterExfilAuthorTests(unittest.TestCase):
    def test_requires_actual_survey_and_unchanged_history(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            counter_exfil_preflight_attempted=True,
            blocker='Halt: Native westbound geometry recorded; local Qwen must implement the one-incident parent contract',
            counter_exfil_preflight=dict(candidate=m.SOURCE,build_id='actual-build',routes=[{'name':'actual-central'}]))
        m.validate_boundary(old)
        for change in ({'controller_pid':10},{'counter_exfil_source_attempted':True},{'task_failures':0},
                {'counter_exfil_preflight':{}},{'last_playable_checkpoint':'unaccepted'},
                {'overall_deadline_epoch':m.HARD_CAP_EPOCH+1}):
            with self.subTest(change=change),self.assertRaises(Halt):m.validate_boundary(dict(old,**change))
    def test_protects_old_source_and_external_acceptance(self):
        m.validate_source('Assets/Game/CounterExfilRunner.cs','class CounterExfilRunner {}')
        for path in ('Assets/Game/Combat.cs','Assets/Game/Bootstrap.cs','Assets/Game/DeathAuthority.cs',
                     'Assets/Game/InterceptionMission.cs','Assets/LoopHarness/LoopRuntime.cs'):
            with self.subTest(path=path),self.assertRaises(ValueError):m.validate_source(path,'changed')
        for fragment in ('LoopInput.Replay','Time.timeScale','GetCommandLineArgs','System.Reflection','System.IO'):
            with self.subTest(fragment=fragment),self.assertRaises(ValueError):
                m.validate_source('Assets/Game/CounterExfilMission.cs',fragment)

if __name__=='__main__':unittest.main()
