"""Red fixtures for durable boundaries and actual runtime acceptance decisions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from loop_controller.core import Files, Halt, Store, atomic, failure_key, seal, sha, verify_seal
from loop_controller.adapters import evaluate_runtime, sandbox_profile
from loop_controller.model import conservative_prompt_bound
from loop_controller.runner import scenario_for


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name).resolve()
        self.store=Store(self.root/"control")
        self.project=self.root/"project";self.project.mkdir()
        self.files=Files(self.project,self.store)

    def tearDown(self):
        self.store.db.close();self.tmp.cleanup()

    def test_edit_escape_and_protected_paths_are_rejected(self):
        for name in ("../state.sqlite3","/tmp/escape.cs","Assets/Editor/Cheat.cs","Packages/manifest.json",".git/config","Assets/Game/../bad.cs"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                self.files.edit(name,name,sha(b""),content="bad")
        (self.project/"Assets").symlink_to(self.root)
        with self.assertRaises(ValueError):self.files.path("Assets/Game/Bad.cs",write=True)

    def test_stale_edit_does_not_overwrite(self):
        self.files.edit("a","Assets/Game/A.cs",sha(b""),content="first")
        with self.assertRaises(ValueError):self.files.edit("b","Assets/Game/A.cs",sha(b""),content="second")
        self.assertEqual((self.project/"Assets/Game/A.cs").read_text(),"first")

    def test_crash_between_write_and_action_commit_reconciles(self):
        path="Assets/Game/A.cs";after="result"
        self.store.begin_action("a","source-edit",{"path":path,"before":sha(b""),"after":sha(after.encode())})
        atomic(self.project/path,after.encode(),raw=True)
        self.store.db.close();self.store=Store(self.root/"control");self.files=Files(self.project,self.store)
        result=self.files.edit("a",path,sha(b""),content=after)
        self.assertTrue(result["reconciled"])
        self.assertFalse(self.store.incomplete())
        self.assertEqual(self.files.edit("a",path,sha(b""),content=after),result)

    def test_durable_state_survives_process_exit(self):
        code="from loop_controller.core import Store; s=Store(__import__('sys').argv[1]);s.set(stage='compile-play',candidate='abc');__import__('os')._exit(7)"
        result=subprocess.run([sys.executable,"-c",code,str(self.root/"other")],env={**__import__('os').environ,"PYTHONPATH":str(Path(__file__).resolve().parents[1]/"tools")})
        self.assertEqual(result.returncode,7)
        other=Store(self.root/"other")
        self.assertEqual(other.get("candidate"),"abc");other.db.close()

    def test_capture_mutation_and_missing_file_fail(self):
        folder=self.root/"evidence";folder.mkdir();(folder/"frame.png").write_bytes(b"actual")
        digest=seal(folder,{"candidate":"abc"})
        verify_seal(folder,digest)
        (folder/"frame.png").write_bytes(b"different")
        with self.assertRaises(Halt):verify_seal(folder,digest)
        (folder/"frame.png").unlink()
        with self.assertRaises(Halt):verify_seal(folder,digest)

    def runtime_fixture(self,moves=True):
        path=self.root/"capture";path.mkdir(exist_ok=True)
        scenario={"duration":2,"captures":[0.2,1.2],"coverage":"foundation"}
        atomic(path/"runtime-result.json",{"completed":True,"errors":0,"capture_id":"test","graphics":"Metal","duration":2})
        rows=[{"time":i/10,"camera":True,"player":[i/5 if moves else 0,0,0],"vehicle":None,"keys":["W"]} for i in range(21)]
        (path/"trace.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
        # Deliberately synthetic evaluator fixtures, not real image/play evidence.
        for i in range(2):(path/f"frame-{i:03d}.png").write_bytes(b"\x89PNG\r\n\x1a\n"+bytes([i]))
        return path,scenario

    def test_stationary_runtime_rejected_despite_success_sentinel(self):
        path,scenario=self.runtime_fixture(False)
        result=evaluate_runtime(path,scenario,0,"test")
        self.assertFalse(result["passed"]);self.assertIn("input-driven-player-movement",result["failure"])

    def test_numeric_runtime_green_and_wrong_capture_identity_red(self):
        path,scenario=self.runtime_fixture(True)
        self.assertTrue(evaluate_runtime(path,scenario,0,"test")["passed"])
        self.assertFalse(evaluate_runtime(path,scenario,0,"stale")["passed"])
        (path/"frame-001.png").unlink()
        self.assertFalse(evaluate_runtime(path,scenario,0,"test")["passed"])

    def test_critic_context_budget_counts_real_images_separately(self):
        messages=[{"role":"user","content":[{"type":"text","text":"target and actual"},{"type":"image_url","image_url":{"url":"data:image/png;base64,"+"a"*100000}}]}]
        result=conservative_prompt_bound(messages,[])
        self.assertGreater(result,8192);self.assertLess(result,14000)

    def test_replay_rejects_invalid_or_empty_actions(self):
        for steps in ([{"start":0,"end":9999,"keys":["W"]}],[{"start":0,"end":1,"keys":["DeleteEverything"]}]):
            with self.assertRaises(ValueError):scenario_for("foundation",steps)

    def test_failure_fingerprint_ignores_round_identity(self):
        self.assertEqual(failure_key({"compile_errors":["/tmp/r0001-aaaaaaaa/project/Assets/Game/A.cs error CS123"]}),
                         failure_key({"compile_errors":["/tmp/r0002-bbbbbbbb/project/Assets/Game/A.cs error CS123"]}))


if __name__=="__main__":unittest.main()
