from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.character_motion_checks import measure,moving_joints,quaternion_angle


class CharacterMotionChecks(unittest.TestCase):
    def sequence(self, animated=False, active=True):
        rows=[]
        for i in range(8):
            angle=math.radians(i*5 if animated else 0)
            joint=dict(path='Player/PlayerVisual/knee_L',
                active=True,localPosition=[0,-.4,0],worldPosition=[i,-.4,0],
                localRotation=[math.sin(angle/2),0,0,math.cos(angle/2)])
            visual=dict(path='Player/PlayerVisual',active=active,joints=[joint])
            rows.append(dict(time=i*.1,player=[i,0,0],characterPresentation=dict(visuals=[visual])))
        return rows

    def test_world_travel_does_not_prove_locomotion(self):
        self.assertFalse(moving_joints(measure(self.sequence(),0,1),['knee'],10))
        self.assertTrue(moving_joints(measure(self.sequence(True),0,1),['knee'],10))

    def test_hidden_or_too_short_motion_is_not_visible_proof(self):
        self.assertFalse(moving_joints(measure(self.sequence(True,False),0,1),['knee'],10))
        self.assertFalse(moving_joints(measure(self.sequence(True),0,.2),['knee'],1))

    def test_quaternion_sign_is_not_a_pose_change(self):
        self.assertEqual(quaternion_angle([0,0,0,1],[0,0,0,-1]),0)
        self.assertAlmostEqual(quaternion_angle([0,0,0,1],[math.sqrt(.5),0,0,math.sqrt(.5)]),90)
        with self.assertRaises(ValueError): quaternion_angle([0,0,0,0],[0,0,0,1])


if __name__=='__main__':unittest.main()
