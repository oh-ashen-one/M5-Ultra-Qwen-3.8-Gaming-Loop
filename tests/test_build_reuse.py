import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.build_reuse import BuildReuse, build_key, tree_digest
from loop_controller.core import Halt


class BuildReuseTests(unittest.TestCase):
    def test_every_source_asset_harness_editor_and_candidate_invalidates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / 'project'; project.mkdir()
            editor = root / 'editor'; editor.write_bytes(b'editor')
            for name in ('Game.cs', 'asset.fbx', 'LoopRuntime.cs'): (project / name).write_bytes(b'original')
            key = build_key(project, editor, 'source')
            for path in [*(project.iterdir()), editor]:
                original = path.read_bytes(); path.write_bytes(b'changed')
                self.assertNotEqual(key, build_key(project, editor, 'source'))
                path.write_bytes(original)
            self.assertNotEqual(key, build_key(project, editor, 'different'))
            self.assertEqual(key, build_key(project, editor, 'source'))

    def test_identical_copy_preserves_executable_and_has_no_runtime_results(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); original = root / 'original'; original.mkdir()
            app = original / 'ChicagoLocalSlice.app'; app.mkdir()
            executable = app / 'player'; executable.write_bytes(b'binary'); executable.chmod(0o755)
            (original / 'build-result.json').write_text('{"passed":true}')
            (original / 'unity-build.log').write_text('compiled')
            cache = BuildReuse(); cache.remember('key', original)
            target = root / 'fresh'; target.mkdir()
            self.assertFalse(cache.restore('different', target))
            self.assertTrue(cache.restore('key', target))
            self.assertEqual(tree_digest(app), tree_digest(target / app.name))
            self.assertFalse((target / 'runtime-result.json').exists())
            executable.write_bytes(b'tampered')
            with self.assertRaises(Halt): cache.restore('key', root / 'later')

    def test_external_symlink_is_not_cacheable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); project = root / 'project'; project.mkdir()
            (project / 'escape').symlink_to(root / 'outside')
            with self.assertRaises(Halt): tree_digest(project)


if __name__ == '__main__': unittest.main()
