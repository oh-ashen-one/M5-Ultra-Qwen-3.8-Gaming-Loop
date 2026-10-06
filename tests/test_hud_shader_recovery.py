import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.core import Files, Store
from resume_hud_shader_recovery import validate_shader, SHADER


class HudShaderRecoveryTests(unittest.TestCase):
    def test_only_exact_original_resource_path_is_added_to_write_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / 'project'; project.mkdir()
            store = Store(root / 'run'); files = Files(project, store)
            self.assertEqual(files.path(SHADER, write=True), project.resolve() / SHADER)
            for path in ['Assets/Resources/Other.shader', 'Assets/LoopHarness/Override.shader',
                         'Assets/Editor/Build.cs', 'Assets/Resources/../LoopHarness/Override.cs']:
                with self.subTest(path=path), self.assertRaises(ValueError): files.path(path, write=True)
            store.db.close()

    def test_shader_cannot_hide_objects_sample_textures_or_use_time(self):
        source = 'Shader "Chicago/HudOpaque" _Color Properties SubShader Pass CGPROGRAM #pragma vertex #pragma fragment UnityObjectToClipPos ENDCG'
        validate_shader(source)
        for token in ['GrabPass', 'tex2D', '_Time', 'discard', '"Queue"="Overlay"', 'Fallback']:
            with self.subTest(token=token), self.assertRaises(ValueError): validate_shader(source + ' ' + token)


if __name__ == '__main__': unittest.main()
