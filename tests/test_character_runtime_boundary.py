from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from author_character_runtime import validate_boundary,validate_component,SOURCE,PRIOR,ACCEPTED
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.core import Halt

class CharacterRuntimeBoundary(unittest.TestCase):
    def test_requires_fresh_review_and_preserves_owner_history(self):
        state=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
            last_playable_checkpoint=ACCEPTED,current_round=PRIOR,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Clothed character exported and early native preview saved; inspect actual pixels then author runtime animation',
            clothed_character_preview_outcome=dict(candidate=SOURCE,native_gate=dict(passed=True)),
            clothed_character_cloud_pixel_review=dict(candidate=SOURCE,verdict='FIX'))
        validate_boundary(state)
        for mutation in [dict(controller_pid=2),dict(clothed_character_cloud_pixel_review={}),
                dict(character_foot_runtime_attempted=True),dict(last_playable_checkpoint=SOURCE),
                dict(task_failures=0),dict(overall_deadline_epoch=HARD_CAP_EPOCH+1)]:
            with self.assertRaises(Halt):validate_boundary(dict(state,**mutation))
    def test_presentation_cannot_detect_tests_or_change_physics(self):
        for forbidden in ('LoopInput.Replay','System.IO','LoopRuntime','Physics.Raycast','UnityEditor'):
            with self.assertRaises(Halt):validate_component(forbidden)
        with self.assertRaises(Halt):validate_component('AssetPostprocessor',importer=True)
        with self.assertRaises(Halt):validate_component('#if UNITY_EDITOR\nAssetDatabase.SaveAssets();\n#endif',importer=True)

if __name__=='__main__':unittest.main()
