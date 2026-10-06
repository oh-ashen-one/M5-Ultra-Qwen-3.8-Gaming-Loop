import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.camera_checks import inspect_camera,inspect_target_transitions
from repair_camera_lifecycle import validate_lifecycle_pause,SOURCE as LIFECYCLE_SOURCE,BLOCKER as LIFECYCLE_BLOCKER
from resume_camera_lifecycle_validation import validate_observer_pause,SOURCE as OBSERVER_SOURCE
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from probe_camera_clearance import validate_camera_pause,SOURCE,ACCEPTED,BLOCKER
from repair_camera_clearance import validate_repair_pause,validate_follow_replacement,PROBE,BUILD
from qualify_camera_repair import validate_qualification_pause,require_ordinary_qualification,REGRESSIONS
from continue_game_queue import ReadBoundEdits
from types import SimpleNamespace

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

    def test_polish_cannot_redesign_accepted_mission_or_boarding(self):
        edits=ReadBoundEdits(SimpleNamespace(path=lambda *a,**k:None),polish=True)
        for path in ['Assets/Game/Mission.cs','Assets/Game/VehicleInteraction.cs']:
            with self.assertRaises(ValueError):edits.allowed(path,'change')
        edits.allowed('Art/coupe.py','original geometry')

    def test_clearance_fixture_never_substitutes_for_current_ordinary_regressions(self):
        gate=dict(passed=True,candidate_commit='current',scoped_facts={'mission_anchors':{'passed':True}},
            regressions=dict(passed=True,regressions=[dict(test=n,gate=dict(passed=True,candidate_commit='current')) for n in REGRESSIONS]))
        with patch('qualify_camera_repair.require_combat_contracts',return_value=True),patch('qualify_camera_repair.require_aim_contracts',return_value=True):
            require_ordinary_qualification(gate,'current')
            for key,value in [('acceptance_fixture','camera-clearance'),('candidate_commit','old'),('scoped_facts',{})]:
                with self.assertRaises(Halt):require_ordinary_qualification({**gate,key:value},'current')
            gate['regressions']['regressions'][0]['gate']['candidate_commit']='old'
            with self.assertRaises(Halt):require_ordinary_qualification(gate,'current')

    def test_qualification_requires_exact_pause_and_current_sealed_camera(self):
        state=dict(last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=6,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,camera_repair_attempted=True,
            blocker='Camera geometry passes; ordinary route and fresh visual qualification still required',
            source_checkpoint='current',camera_after_manifest='digest',
            camera_after_probe=dict(passed=True,candidate='current',acceptance_fixture='camera-clearance'))
        validate_qualification_pause(state)
        for key,value in [('camera_qualification_attempted',True),('source_checkpoint','other'),('camera_after_manifest',None),('task_failures',0)]:
            with self.assertRaises(Halt):validate_qualification_pause({**state,key:value})

    def test_actual_target_switches_require_matching_renderer_identities(self):
        rows=[dict(time=t+i*.1,mode=role,cameraGeometry=dict(targetRole=role,
            rendererCacheMatchesTarget=True,expectedRendererCount=count))
            for t,role,count in [(2,'foot',12),(9,'vehicle',30),(22,'foot',12),(25,'foot',12)] for i in range(6)]
        self.assertTrue(inspect_target_transitions(rows)['passed'])
        for index in [0,6,12,18]:
            changed=copy.deepcopy(rows);changed[index]['cameraGeometry']['rendererCacheMatchesTarget']=False
            self.assertFalse(inspect_target_transitions(changed)['passed'])
        changed=copy.deepcopy(rows);changed[6]['cameraGeometry']['targetRole']='foot'
        self.assertFalse(inspect_target_transitions(changed)['passed'])
        self.assertFalse(inspect_target_transitions([])['passed'])

    def test_parent_lifecycle_repair_preserves_exact_failed_qualification(self):
        state=dict(source_checkpoint=LIFECYCLE_SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            camera_qualification_attempted=True,blocker=LIFECYCLE_BLOCKER)
        original=copy.deepcopy(state);validate_lifecycle_pause(state);self.assertEqual(state,original)
        for key,value in [('camera_lifecycle_attempted',True),('source_checkpoint','other'),('task_failures',0),('blocker','resource fault')]:
            with self.assertRaises(Halt):validate_lifecycle_pause({**state,key:value})

    def test_observer_recovery_never_resets_or_reauthors_saved_game(self):
        state=dict(source_checkpoint=OBSERVER_SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            camera_lifecycle_attempted=True,blocker='Halt: Camera repair native runtime failed: compile-build')
        original=copy.deepcopy(state);validate_observer_pause(state);self.assertEqual(state,original)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('camera_observer_recovery_attempted',True),('blocker','resource fault')]:
            with self.assertRaises(Halt):validate_observer_pause({**state,key:value})

if __name__=='__main__':unittest.main()
