"""CPU-only safety fixtures; do not import MLX or start any application."""
import ast
import os
from pathlib import Path
import secrets
import stat
import tempfile
import unittest


def isolated_function(filename, name, globals_):
    source = ast.parse((Path(__file__).parent / filename).read_text())
    node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(globals_)
    exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), namespace)
    return namespace[name]


class ReadinessGuards(unittest.TestCase):
    def test_renderer_and_headless_worker_boundaries(self):
        classify = isolated_function("unity_smoke.py", "renderer_process", {})
        editor = "/Applications/Unity/Hub/Editor/test/Unity.app/Contents/MacOS/Unity"
        self.assertTrue(classify(editor, "unity", []))
        self.assertTrue(classify(editor, "unity", ["-nographics"]))
        worker = ["-parentPid", "1", "-name", "AssetImportWorkerHW0"]
        self.assertTrue(classify(editor, "unity", worker + ["-force-metal"]))
        self.assertFalse(classify(editor, "unity", worker + ["-nographics"]))
        self.assertTrue(classify(editor, "unity", ["-name", "AssetImportWorkerHW0", "-nographics"]))
        self.assertFalse(classify("/Applications/Unity Hub.app/Contents/MacOS/Unity Hub", "unity hub", []))
        self.assertFalse(classify(editor + "CrashHandler64", "unitycrashhandler64", []))
        self.assertTrue(classify("/Applications/Blender.app/Contents/MacOS/Blender", "blender", []))

    def test_private_token_resume_and_rejections(self):
        token = isolated_function("warmup_resident.py", "session_token", {
            "os": os, "stat": stat, "secrets": secrets})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            original = token(path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(token(path, True), original)
            with self.assertRaises(FileExistsError): token(path)
            path.chmod(0o644)
            with self.assertRaises(RuntimeError): token(path, True)
            path.chmod(0o600)
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(OSError): token(link, True)
            path.write_text("short")
            with self.assertRaises(RuntimeError): token(path, True)


if __name__ == "__main__":
    unittest.main()
