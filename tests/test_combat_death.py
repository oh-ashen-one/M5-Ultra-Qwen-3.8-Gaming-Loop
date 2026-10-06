import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.combat_death_checks import inspect_death
from resume_combat_death import validate_pause, SOURCE, ROUND, ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class CombatDeathTests(unittest.TestCase):
    def evidence(self):
        events = [dict(time=7.5+i*1.7, keys=['Mouse0'], restarts=0, shotsBefore=i, shotsAfter=i+1,
            hitsBefore=i, hitsAfter=i+1, targets=[dict(name='Rival', hpBefore=3-i, hpAfter=2-i,
            colliderRayHit=True, visualBoundsRayHit=True, viewportContainsCenter=True, firstRayTarget=True)]) for i in range(3)]
        rows = [dict(time=11.4+i*.1, restarts=0, rivals=[dict(name='Rival', hp=0, alive=False,
                    renderers=0, colliderEnabled=False)]) for i in range(20)]
        rows += [dict(time=14.5+i*.1, restarts=1, keys=['R'] if i==0 else [], health=100, hits=0,
            shots=0, pursuit=0, rivals=[dict(name='Rival', hp=3, alive=True, renderers=20,
            colliderEnabled=True, position=[2,.14,-.5])]) for i in range(20)]
        return rows, events

    def test_requires_lethal_real_aim_and_full_reset(self):
        rows, events = self.evidence()
        self.assertTrue(inspect_death(rows,events)['passed'])
        for defect in ['only-two-hits', 'off-aim', 'wrong-dead-renderer', 'dead-collider', 'reset-hp', 'reset-position', 'reset-counter']:
            r,e=copy.deepcopy((rows,events))
            if defect=='only-two-hits': e.pop()
            if defect=='off-aim': e[-1]['targets'][0]['firstRayTarget']=False
            if defect=='wrong-dead-renderer': r[0]['rivals'][0]['renderers']=20
            if defect=='dead-collider': r[0]['rivals'][0]['colliderEnabled']=True
            if defect=='reset-hp': r[-1]['rivals'][0]['hp']=0
            if defect=='reset-position': r[-1]['rivals'][0]['position']=[3,.14,-.5]
            if defect=='reset-counter': r[-1]['shots']=3
            with self.subTest(defect=defect): self.assertFalse(inspect_death(r,e)['passed'])
        self.assertFalse(inspect_death(rows,events)['secondary_target_isolation_qualified'])

    def test_exact_boundary_preserves_history(self):
        old=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            stage='combat-hit-target-original-regressions',
            blocker='Halt: Local hit-target dependency and original regressions complete; next qualify the planned moving encounter',
            combat_hit_target_preparation=dict(candidate=SOURCE,original_regressions_passed=True))
        validate_pause(old)
        capacity={**old,'current_round':'q0122-d0f2423b','stage':'native-combat-lethal-reset',
            'blocker':'RuntimeError: Existing shared GPU waiters have priority','combat_death_attempted':True}
        validate_pause(capacity)
        with self.assertRaises(Halt): validate_pause({**capacity,'combat_death_admission_recovered':True})
        for field,value in [('source_checkpoint','other'),('task_failures',0),('overall_deadline_epoch',HARD_CAP_EPOCH+1),('combat_death_attempted',True)]:
            with self.assertRaises(Halt): validate_pause({**old,field:value})


if __name__ == '__main__': unittest.main()
