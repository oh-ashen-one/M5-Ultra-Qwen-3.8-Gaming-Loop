import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.camera_checks import inspect_camera
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from probe_camera_clearance import validate_camera_pause,SOURCE,ACCEPTED,BLOCKER
from repair_camera_clearance import validate_repair_pause,validate_follow_replacement,PROBE,BUILD

def observations():
    return [dict(time=start+i*.1,cameraGeometry=dict(available=True,probeHit=True,
        phase=phase,probeCollider='CameraClearanceWall',probeDistance=distance,
        cameraInsideFixture=False,fixtureBetweenTargetAndCamera=False,nearPlaneTouchesFixture=False,
        legacyEndpointCrowding=phase=='endpoint',targetSamples=9,inFrameSamples=9,unobstructedSamples=9))
        for phase,start,distance in [('near',6,.65),('middle',10,3),('endpoint',14,5.4)] for i in range(10)]

class CameraTests(unittest.TestCase):
    def test_measured_clearance_never_accepts_final_game(self):
        result=inspect_camera(observations())
        self.assertTrue(result['passed']);self.assertFalse(result['final_game_accepted'])
        self.assertEqual(result['phases'][0]['legacy_endpoint_predicate_samples'],0)
        self.assertEqual(result['phases'][2]['legacy_endpoint_predicate_samples'],10)

    def test_crossing_and_near_plane_intersections_fail_each_case(self):
        for phase in range(3):
            for key in ['cameraInsideFixture','fixtureBetweenTargetAndCamera','nearPlaneTouchesFixture']:
                rows=observations();rows[phase*10]['cameraGeometry'][key]=True
                self.assertFalse(inspect_camera(rows)['passed'])

    def test_missing_or_invalid_measurements_never_pass(self):
        self.assertFalse(inspect_camera([])['passed'])
        for key,value in [('probeDistance',None),('probeDistance',float('nan')),('probeHit',False),
                          ('cameraInsideFixture',None),('targetSamples',0),('probeCollider','other')]:
            rows=observations()
            for row in rows[:10]:row['cameraGeometry'][key]=value
            self.assertFalse(inspect_camera(rows)['passed'],key)
        rows=observations()
        for row in rows[:10]:row['cameraGeometry']['probeDistance']=1.8
        self.assertFalse(inspect_camera(rows)['passed'])

    def test_visibility_and_endpoint_predicate_are_separate(self):
        rows=observations()
        for row in rows[:10]:row['cameraGeometry']['unobstructedSamples']=0
        result=inspect_camera(rows)
        self.assertEqual(result['phases'][0]['legacy_endpoint_predicate_samples'],0)
        self.assertEqual(result['phases'][0]['minimum_actor_samples_unobstructed'],0)

    def test_only_exact_original_pause_is_admitted_without_reset(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER)
        original=copy.deepcopy(state);validate_camera_pause(state);self.assertEqual(state,original)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('diagnosis_used',False),
                          ('camera_probe_attempted',True),('overall_deadline_epoch',HARD_CAP_EPOCH+1),('blocker','resource fault')]:
            with self.assertRaises(Halt):validate_camera_pause({**state,key:value})

    def test_repair_requires_measured_failure_and_preserves_original_counters(self):
        state=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Scoped camera close-wall evidence recorded; original full-route stop preserved',
            camera_before_probe=dict(candidate=SOURCE,build_id=BUILD,evidence=PROBE,passed=False,
                failure=['near-camera-crosses-obstacle','endpoint-camera-crosses-obstacle']))
        original=copy.deepcopy(state);validate_repair_pause(state);self.assertEqual(state,original)
        for key,value in [('camera_repair_attempted',True),('task_failures',0),('camera_before_probe',{}),('blocker','different fault')]:
            with self.assertRaises(Halt):validate_repair_pause({**state,key:value})

    def test_repair_tool_rejects_fixture_hacks_or_other_source(self):
        span='public class Follow : MonoBehaviour { public Transform target; public Vector3 offset; }\n}'
        validate_follow_replacement(span)
        for text in ['public class Other {}',span+'LoopInput',span+'CameraClearanceWall',span+'.enabled=false',span+'x'*21000]:
            with self.assertRaises(ValueError):validate_follow_replacement(text)

if __name__=='__main__':unittest.main()
