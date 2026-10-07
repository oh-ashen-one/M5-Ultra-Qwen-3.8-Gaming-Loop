from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import review_player_death_integration as m
from loop_controller.core import Halt


class DeathReviewTests(unittest.TestCase):
    def native(self):
        return dict(candidate=m.SOURCE,cases=[dict(case=name,passed=True,setup_passed=True,
            failure=[],candidate=m.SOURCE,build_id='build',evidence=name) for name in m.CASES],
            positive=dict(passed=True,candidate_commit=m.SOURCE),regressions=dict(passed=True,
                regressions=[dict(test=name,gate=dict(passed=True,candidate_commit=m.SOURCE))
                    for name in m.REGRESSIONS]))

    def test_incomplete_or_fixture_native_proof_cannot_promote(self):
        good=self.native();m.require_complete_native(good)
        for mutate in [lambda d:d['cases'].pop(),
                lambda d:d['cases'][0].update(setup_passed=False),
                lambda d:d['cases'][0].update(candidate='old-source'),
                lambda d:d['cases'][0].update(failure=['player-can-fire-while-dead']),
                lambda d:d['positive'].update(acceptance_fixture='player-death'),
                lambda d:d.update(positive='pending'),
                lambda d:d['regressions']['regressions'].pop(),
                lambda d:d['regressions']['regressions'][0]['gate'].update(passed=False),
                lambda d:d['regressions']['regressions'][0]['gate'].update(candidate_commit='old-source')]:
            bad=copy.deepcopy(good);mutate(bad)
            with self.assertRaises(Halt):m.require_complete_native(bad)

    def test_review_requires_stopped_exact_green_boundary(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,task_index=7,
            task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            death_hud_recognition_recovered=True,player_death_green_outcome=self.native(),
            blocker='Halt: Local death repair passes six zero-health boundaries and healthy gameplay; inspect native failure/reset images')
        m.validate_boundary(old)
        for changes in ({'controller_pid':1},{'player_death_review_attempted':True},
                {'overall_deadline_epoch':m.HARD_CAP_EPOCH+1},{'task_failures':0},
                {'source_checkpoint':'another'},{'blocker':'actual native failure'}):
            with self.subTest(changes=changes),self.assertRaises(Halt):m.validate_boundary(dict(old,**changes))


if __name__=='__main__':unittest.main()
