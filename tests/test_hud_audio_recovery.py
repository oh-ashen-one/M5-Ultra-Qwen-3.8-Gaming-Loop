import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_hud_audio import CANDIDATE,ACCEPTED,REPLAY_STOP,validate_hud_pause,accepted_combat_probe
from loop_controller.core import Halt,atomic,seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.continuous_tasks import TASKS


class HudAudioRecoveryTests(unittest.TestCase):
    def test_admission_preserves_other_stops_and_failure_counts(self):
        state=dict(source_checkpoint=CANDIDATE,last_playable_checkpoint=ACCEPTED,task_index=5,
                   task_failures=0,failure_streak=0,overall_deadline_epoch=HARD_CAP_EPOCH,blocker=REPLAY_STOP)
        before=copy.deepcopy(state)
        validate_hud_pause(state)
        self.assertEqual(state,before)
        for key,value in [('source_checkpoint','different'),('last_playable_checkpoint','different'),
                          ('task_index',6),('task_failures',1),('failure_streak',1),
                          ('overall_deadline_epoch',HARD_CAP_EPOCH+1),('blocker','resource fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                validate_hud_pause({**state,key:value})

    def fixture(self,root):
        bundle=root/'evidence'/'accepted'
        (bundle/'captures').mkdir(parents=True)
        probe=dict(duration=38,steps=[dict(start=4,end=6,keys=['W'])],captures=[3.2,8,24.4,31.7])
        atomic(bundle/'captures/scenario.json',probe)
        seal(bundle/'captures',{'candidate':'local-source','scope':'mission-combat-pursuit'})
        gate=dict(passed=True,candidate_commit='local-source',scope='mission-combat-pursuit')
        atomic(bundle/'scoped-gate.json',gate)
        records={'mission-combat-pursuit':dict(candidate='local-source',scope='mission-combat-pursuit',
                     evidence='evidence/accepted',review={'verdict':'PASS'})}
        return bundle,records,probe,gate

    def test_reuses_sealed_inputs_without_claiming_current_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle,records,probe,_=self.fixture(root)
            result,evidence=accepted_combat_probe(root,TASKS[5],records)
            self.assertEqual(result['steps'],probe['steps'])
            self.assertEqual(result['captures'],probe['captures'])
            self.assertEqual(evidence,'evidence/accepted')
            self.assertNotIn('passed',result)

    def test_tampered_input_scenario_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle,records,_,_=self.fixture(root)
            (bundle/'captures/scenario.json').write_text('{}')
            with self.assertRaises(Halt):accepted_combat_probe(root,TASKS[5],records)

    def test_failed_fixture_or_wrong_source_gate_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle,records,_,gate=self.fixture(root)
            for key,value in [('passed',False),('candidate_commit','different'),('acceptance_fixture',True)]:
                atomic(bundle/'scoped-gate.json',{**gate,key:value})
                with self.subTest(key=key),self.assertRaises(Halt):
                    accepted_combat_probe(root,TASKS[5],records)

    def test_no_reuse_for_new_route_or_unaccepted_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);_,records,_,_=self.fixture(root)
            with self.assertRaises(Halt):accepted_combat_probe(root,TASKS[6],records)
            records['mission-combat-pursuit']['review']['verdict']='FIX'
            with self.assertRaises(Halt):accepted_combat_probe(root,TASKS[5],records)


if __name__=='__main__':unittest.main()

