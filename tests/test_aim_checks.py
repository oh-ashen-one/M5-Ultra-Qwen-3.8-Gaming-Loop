import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.aim_checks import inspect_aim_contract,require_aim_contracts
from resume_aim_qualification import validate_aim_pause,SOURCE,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


def shot(hit=False,aligned=False,wall=None):
    return dict(time=8.6,keys=['Mouse0'],shotsBefore=0,shotsAfter=1,hitsBefore=0,hitsAfter=int(hit),
        firstRayCollider=wall or ('Rival' if aligned else 'Barrier'),originOverlaps085=[wall] if wall else [],
        targets=[dict(name='Rival',hpBefore=3,hpAfter=2 if hit else 3,colliderRayHit=aligned,
            visualBoundsRayHit=aligned,viewportContainsCenter=aligned,firstRayTarget=aligned and not wall)])


class AimContractTests(unittest.TestCase):
    def test_recovery_admits_only_the_preserved_boundary(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=6,
            task_failures=3,failure_streak=1,overall_deadline_epoch=HARD_CAP_EPOCH,blocker='Halt: Requested stop')
        original=copy.deepcopy(state);validate_aim_pause(state);self.assertEqual(state,original)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('failure_streak',0),
                          ('blocker','runtime fault'),('task_index',7),('overall_deadline_epoch',0)]:
            with self.subTest(key=key),self.assertRaises(Halt):validate_aim_pause({**state,key:value})

    def test_aligned_damage_is_observed(self):
        self.assertTrue(inspect_aim_contract([shot(True,True)],'aligned')['passed'])
        self.assertFalse(inspect_aim_contract([shot(False,True)],'aligned')['passed'])

    def test_wide_cast_hit_outside_visible_aim_is_rejected(self):
        result=inspect_aim_contract([shot(True,False),shot(False,False)],'miss')
        self.assertIn('rival-damage-outside-visible-camera-aim',result['failure'])
        self.assertIn('intentional-miss-causes-damage',result['failure'])

    def test_deliberate_misses_need_real_shots_and_no_damage(self):
        self.assertTrue(inspect_aim_contract([shot(),shot()],'miss')['passed'])
        self.assertFalse(inspect_aim_contract([shot()],'miss')['passed'])
        self.assertFalse(inspect_aim_contract([],'miss')['passed'])

    def test_nearer_cover_blocks_aligned_rival(self):
        for kind,wall in [('wall','CombatValidationWall'),('near-cover','CombatNearCover')]:
            with self.subTest(kind=kind):
                self.assertTrue(inspect_aim_contract([shot(False,True,wall)],kind)['passed'])
                self.assertIn('shot-damages-through-nearer-cover',
                    inspect_aim_contract([shot(True,True,wall)],kind)['failure'])

    def test_near_cover_requires_real_origin_overlap(self):
        e=shot(False,True,'CombatNearCover');e['originOverlaps085']=[]
        self.assertFalse(inspect_aim_contract([e],'near-cover')['passed'])

    def test_promotion_requires_all_scopes_on_current_source(self):
        gate=dict(candidate_commit='current',aim_contracts=[
            dict(scope=k,passed=True,candidate='current') for k in ('aligned','miss','wall','near-cover')])
        self.assertTrue(require_aim_contracts(gate))
        for key,value in [('candidate','old'),('passed',False),('scope','other')]:
            bad=copy.deepcopy(gate);bad['aim_contracts'][0][key]=value
            self.assertFalse(require_aim_contracts(bad))


if __name__=='__main__':unittest.main()
