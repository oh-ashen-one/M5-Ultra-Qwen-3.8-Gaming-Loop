from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_death_hud_recognition as m
from loop_controller.core import Halt


class HudRecognitionTests(unittest.TestCase):
    def boundary(self):
        return dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            player_death_green_attempted=True,author_completion_claimed=False,
            blocker='Halt: Local death integration needs measured follow-up: courier-pickup: ["death-failure-and-reset-not-visible"]',
            player_death_green_outcome=dict(candidate=m.SOURCE,positive='pending',regressions='pending',
                cases=[dict(case='courier-pickup',setup_passed=True,failure=['death-failure-and-reset-not-visible'])]))

    def test_only_inspected_single_hud_failure_can_resume(self):
        old=self.boundary();m.validate_boundary(old)
        for changes in ({'source_checkpoint':'other'},{'controller_pid':3},{'task_failures':0},
                {'death_hud_recognition_recovered':True},{'author_completion_claimed':True}):
            with self.subTest(changes=changes),self.assertRaises(Halt):
                m.validate_boundary(dict(old,**changes))
        old=self.boundary();old['player_death_green_outcome']['cases'][0]['failure'].append('player-can-fire-while-dead')
        with self.assertRaises(Halt):m.validate_boundary(old)

    def test_original_frames_trace_scenario_and_red_gate_are_sealed(self):
        self.assertEqual(set(m.HASHES),{'gate.json','player-death-gate.json','captures/scenario.json',
            'captures/trace.jsonl','captures/death-injection.json','captures/frame-001.png'})
        self.assertTrue(all(len(x)==64 for x in m.HASHES.values()))


if __name__=='__main__':unittest.main()
