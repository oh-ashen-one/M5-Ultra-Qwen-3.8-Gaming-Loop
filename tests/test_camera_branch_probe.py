import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller import camera_branch_probe as probe
from loop_controller.core import Halt,sha
import resume_camera_branch_diagnosis as recovery

ANCHORS='''            Vector3 want = origin + hdir * hDist + Vector3.up * camY;
            Vector3 pos = Vector3.Lerp(transform.position, want,
                                       Mathf.Clamp01(damping * Time.deltaTime));
                    if (!own && v.distance < segLen - clearance)
                        pos = pivot + sd * Mathf.Max(0.05f, v.distance - clearance);
            // Final geometry-aware near-plane guard:
            pos.y = Mathf.Max(pos.y, floorY + 0.08f);
            if (b.Contains(pos)) { pos.y = top + clearance; cramped = true; break; }
            transform.position = pos;
'''


class CameraBranchProbeTests(unittest.TestCase):
    def test_hooks_require_exact_source_and_preserve_original_pose_expressions(self):
        with self.assertRaises(Halt):probe.instrument_source(ANCHORS)
        with patch.object(probe,'SOURCE_SHA',sha(ANCHORS.encode())):
            result=probe.instrument_source(ANCHORS)
            self.assertEqual(result.count('LoopCameraBranchObservation.Record('),5)
            for line in ['pos = pivot + sd * Mathf.Max(0.05f, v.distance - clearance);',
                         'pos.y = Mathf.Max(pos.y, floorY + 0.08f);','transform.position = pos;']:
                self.assertEqual(result.count(line),1)
            self.assertIn('LoopCameraBranchObservation.Segment(v.collider.name,v.distance)',result)
            with self.assertRaises(Halt):probe.instrument_source(result)

    def test_instrumentation_only_changes_the_given_disposable_copy(self):
        with tempfile.TemporaryDirectory() as td,patch.object(probe,'SOURCE_SHA',sha(ANCHORS.encode())):
            base=Path(td);source=base/'author.cs';source.write_text(ANCHORS)
            build=base/'project';path=build/'Assets/Game/Bootstrap.cs';path.parent.mkdir(parents=True);path.write_text(ANCHORS)
            receipt=probe.apply_disposable_hooks(build)
            self.assertEqual(source.read_text(),ANCHORS);self.assertNotEqual(path.read_text(),ANCHORS)
            self.assertFalse(receipt['game_authoring_checkout_changed'])

    def test_passive_trace_cannot_change_the_route_or_camera(self):
        rows=[dict(time=50.,mode='vehicle',keys=['S'],player=[1,2,3],vehicle=[4,5,6],
            cameraGeometry={'cameraPosition':[1,2,3],'cameraForward':[0,0,1]})]
        self.assertTrue(probe.equivalent_trace(rows,copy.deepcopy(rows)))
        for key in ['vehicle','cameraPosition']:
            altered=copy.deepcopy(rows)
            if key=='vehicle':altered[0][key][0]+=.1
            else:altered[0]['cameraGeometry'][key][0]+=.1
            self.assertFalse(probe.equivalent_trace(rows,altered))
        self.assertFalse(probe.equivalent_trace(rows,[]))

    def test_pixel_guard_rejects_identical_pixels_even_with_changed_png_metadata(self):
        from PIL.PngImagePlugin import PngInfo
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.png';b=Path(td)/'b.png';im=Image.new('RGB',(4,4),'black');im.save(a)
            meta=PngInfo();meta.add_text('different','metadata');im.save(b,pnginfo=meta)
            self.assertNotEqual(a.read_bytes(),b.read_bytes());self.assertFalse(probe.changed_pixels(a,b))
            im.putpixel((1,1),(255,255,255));im.save(b);self.assertTrue(probe.changed_pixels(a,b))

    def test_exact_diagnosis_pause_preserves_original_counters_and_deadline(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,
            second_street_attempts=4,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,
            street_camera_micro_attempted=True,blocker='Halt: Explicit controller stop')
        before=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('camera_branch_diagnosis_attempted',True),
                          ('overall_deadline_epoch',recovery.HARD_CAP_EPOCH+1),('blocker','native crash')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})


if __name__=='__main__':unittest.main()
