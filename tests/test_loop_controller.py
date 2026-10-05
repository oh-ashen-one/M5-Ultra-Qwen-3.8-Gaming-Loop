"""Red fixtures for durable boundaries and actual runtime acceptance decisions."""
import hashlib
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from loop_controller.core import Files, Halt, Store, atomic, failure_key, seal, sha, verify_seal
from loop_controller.adapters import evaluate_runtime, sandbox_profile
from loop_controller.model import conservative_prompt_bound, tool, typed_arguments
from loop_controller.runner import Runner, git, scenario_for
from inspect_and_repair_grounding import summarize, grounding_scenario


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name).resolve()
        self.store=Store(self.root/"control")
        self.project=self.root/"project";self.project.mkdir()
        self.files=Files(self.project,self.store)

    def tearDown(self):
        self.store.db.close();self.tmp.cleanup()

    def test_stationary_preflight_rejects_unstable_scaled_or_tilted_physics(self):
        bundle=self.root/'observed';capture=bundle/'captures';capture.mkdir(parents=True)
        atomic(capture/'scene-transforms.json',{'objects':[]})
        base=[dict(time=.6+i*.1,keys=[],player=[0,1,0],hasController=True,grounded=True,
                   playerScale=[1,1,1],playerUp=[0,1,0]) for i in range(12)]
        cases=[{}, {'grounded':False},{'playerScale':[100,100,100]},{'playerUp':[0,0,-1]}]
        for fields in cases:
            (capture/'trace.jsonl').write_text('\n'.join(json.dumps({**r,**fields}) for r in base))
            self.assertEqual(summarize(bundle)['stationary_grounded'],not fields)
        falling=[{**r,'player':[0,1-i*.1,0]} for i,r in enumerate(base)]
        (capture/'trace.jsonl').write_text('\n'.join(json.dumps(r) for r in falling))
        self.assertFalse(summarize(bundle)['stationary_grounded'])
        scenario=grounding_scenario()
        self.assertGreaterEqual(min(s['start'] for s in scenario['steps']),4)
        self.assertGreater(min(scenario['captures']),3)

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

    def test_create_needs_no_hash_and_never_overwrites_existing_paths(self):
        result=self.files.create("new","Assets/Game/A.cs","original")
        self.assertTrue(result["ok"])
        for path in ("Assets/Game/A.cs","Assets/Game/Empty.cs"):
            if path.endswith("Empty.cs"):(self.project/path).write_text("")
            before=(self.project/path).read_bytes()
            with self.assertRaises(ValueError):self.files.create(path,path,"replacement")
            self.assertEqual((self.project/path).read_bytes(),before)

    def test_create_reconciles_committed_bytes_after_interruption(self):
        path="Assets/Game/A.cs";content="created before crash"
        self.store.begin_action("new","source-create",{"path":path,"before":"absent","after":sha(content.encode())})
        atomic(self.project/path,content.encode(),raw=True,exclusive_target=True)
        result=self.files.create("new",path,content)
        self.assertTrue(result["reconciled"]);self.assertFalse(self.store.incomplete())

    def test_atomic_creation_refuses_concurrent_target_and_cleans_its_temp(self):
        p=self.project/"existing.cs";p.write_text("preserve")
        with self.assertRaises(FileExistsError):atomic(p,b"overwrite",raw=True,exclusive_target=True)
        self.assertEqual(p.read_text(),"preserve");self.assertFalse(list(self.project.glob("*.tmp")))

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
        # Deliberately synthetic evaluator fixtures, never actual image/play evidence.
        def chunk(kind,data):return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
        for i in range(2):
            pixels=(b"\x00"+bytes([i,10,20])*320)*180
            png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",320,180,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(pixels))+chunk(b"IEND",b"")
            (path/f"frame-{i:03d}.png").write_bytes(png)
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

    def test_falling_is_rejected_with_and_without_horizontal_input_motion(self):
        path,scenario=self.runtime_fixture(True)
        for horizontal in (False,True):
            rows=[{"time":i/10,"camera":True,"player":[i/5 if horizontal else 0,-i*18,0],
                   "vehicle":None,"keys":["W"]} for i in range(21)]
            (path/"trace.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            result=evaluate_runtime(path,scenario,0,"test")
            self.assertFalse(result["passed"])
            self.assertIn("foundation-fall-below-start",result["failure"])
            if not horizontal:self.assertIn("input-driven-player-movement",result["failure"])
            self.assertEqual(result["player_vertical_drop"],360)

    def test_critic_context_budget_counts_real_images_separately(self):
        messages=[{"role":"user","content":[{"type":"text","text":"target and actual"},{"type":"image_url","image_url":{"url":"data:image/png;base64,"+"a"*100000}}]}]
        result=conservative_prompt_bound(messages,[])
        self.assertGreater(result,8192);self.assertLess(result,14000)

    def test_tokenizer_budget_retains_image_allowance_without_base64_or_byte_inflation(self):
        observed=[]
        def count(text): observed.append(text); return 500
        messages=[{"role":"user","content":[{"type":"text","text":"original source"},{"type":"image_url","image_url":{"url":"data:image/png;base64,"+"z"*100000}}]}]
        self.assertEqual(conservative_prompt_bound(messages,[],count),500+8192+2048)
        self.assertNotIn("z"*100,observed[0]);self.assertIn("original source",observed[0])

    def test_xml_parameter_strings_restore_nested_schema_types_without_altering_source(self):
        schema=tool("test","fixture",{"tasks":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"}},"required":["id"],"additionalProperties":False}},"line":{"type":"integer"},"content":{"type":"string"}})
        source='["source string remains text"]'
        fields={"tasks":'[ {"id":"foundation"} ]',"line":"4","content":source}
        result=typed_arguments({"name":"test","arguments":json.dumps(fields)},[schema])
        self.assertEqual(result,{"tasks":[{"id":"foundation"}],"line":4,"content":source})
        fields["tasks"]='[{"unexpected":true}]'
        with self.assertRaises(ValueError):typed_arguments({"name":"test","arguments":fields},[schema])

    def test_replay_rejects_invalid_or_empty_actions(self):
        for steps in ([{"start":0,"end":9999,"keys":["W"]}],[{"start":0,"end":1,"keys":["DeleteEverything"]}]):
            with self.assertRaises(ValueError):scenario_for("foundation",steps)

    def test_failure_fingerprint_ignores_round_identity(self):
        self.assertEqual(failure_key({"compile_errors":["/tmp/r0001-aaaaaaaa/project/Assets/Game/A.cs error CS123"]}),
                         failure_key({"compile_errors":["/tmp/r0002-bbbbbbbb/project/Assets/Game/A.cs error CS123"]}))

    def source_runner(self):
        repo=self.root/"repo";repo.mkdir()
        git(repo,"init","-q")
        git(repo,"config","user.name","Controller test")
        git(repo,"config","user.email","test@example.invalid")
        project=repo/"game";project.mkdir()
        (project/"fixture.cs").write_text("accepted")
        (repo/"outside.txt").write_text("preserve unrelated repository content")
        git(repo,"add",".");git(repo,"commit","-qm","accepted fixture")
        runner=Runner.__new__(Runner)
        runner.store=self.store;runner.repo=repo;runner.project=project
        runner.c={"push_checkpoints":False,"identical_failure_limit":2,"rollback_limit":1}
        runner.model=SimpleNamespace(ready=lambda:None)
        return runner

    def test_recovery_preserves_interrupted_edits_and_abandons_pending_actions(self):
        runner=self.source_runner()
        (runner.project/"fixture.cs").write_text("interrupted actual edit")
        self.store.set(current_round="r0001-test",stage="building")
        self.store.begin_action("interrupted","blender",{"script":"Art/test.py"})
        runner.recover()
        self.assertEqual(git(runner.repo,"show","HEAD:game/fixture.cs"),"interrupted actual edit")
        self.assertEqual(self.store.get("stage"),"idle")
        self.assertEqual(self.store.get("recovery_count"),1)
        self.assertFalse(self.store.incomplete())
        runner.recover()
        self.assertEqual(self.store.get("recovery_count"),1)

    def test_repeated_failure_restores_only_owned_game_and_preserves_failed_candidate(self):
        runner=self.source_runner();accepted=git(runner.repo,"rev-parse","HEAD")
        self.store.set(accepted_checkpoint=accepted)
        (runner.project/"fixture.cs").write_text("broken candidate")
        candidate=runner.checkpoint_source("failed fixture")
        feedback={"failure":"input-driven-player-movement"}
        runner.reject(feedback,candidate);runner.reject(feedback,candidate)
        self.assertEqual((runner.project/"fixture.cs").read_text(),"accepted")
        self.assertEqual(git(runner.repo,"show",candidate+":game/fixture.cs"),"broken candidate")
        self.assertEqual((runner.repo/"outside.txt").read_text(),"preserve unrelated repository content")
        self.assertEqual(self.store.get("rollback_count"),1)
        runner.reject(feedback,candidate)
        with self.assertRaises(Halt):runner.reject(feedback,candidate)

    def test_context_rotation_preserves_progress_without_promoting_or_erasing_real_failure(self):
        runner=self.source_runner();before=git(runner.repo,"rev-parse","HEAD")
        self.store.set(accepted_checkpoint=before, failure_streak=1, feedback={"failure":"compile-build"}, bounded_no_progress_streak=1)
        p=runner.project/"Art/street.py";p.parent.mkdir();p.write_text("# actual local source fixture")
        candidate=runner.checkpoint_source("partial original art")
        runner.continue_bounded_role({"bounded_stop":"context"},before,candidate)
        self.assertEqual(self.store.get("source_checkpoint"),candidate)
        self.assertEqual(self.store.get("accepted_checkpoint"),before)
        self.assertEqual(self.store.get("failure_streak"),1)
        self.assertEqual(self.store.get("feedback")["failure"],"compile-build")
        self.assertEqual(self.store.get("bounded_no_progress_streak"),0)
        self.assertEqual(self.store.get("stage"),"partial")

    def test_context_rotations_without_source_progress_are_bounded(self):
        runner=self.source_runner();before=git(runner.repo,"rev-parse","HEAD")
        runner.continue_bounded_role({"bounded_stop":"context"},before,before)
        with self.assertRaises(Halt):runner.continue_bounded_role({"bounded_stop":"context"},before,before)
        self.assertIsNone(self.store.get("accepted_checkpoint"))

    def test_diagnosed_legacy_context_failure_migrates_once_on_resume(self):
        runner=self.source_runner()
        self.store.set(stage="rejected",feedback={"failure":"builder-context"},failure_streak=3,failure_key="old")
        runner.recover()
        self.assertEqual(self.store.get("failure_streak"),0)
        self.assertEqual(self.store.get("budget_rotation_version"),2)
        self.assertIsNone(self.store.get("accepted_checkpoint"))
        self.store.set(feedback={"failure":"compile-build"},failure_streak=2)
        runner.recover()
        self.assertEqual(self.store.get("failure_streak"),2)

    def test_ready_assets_focus_first_integration_on_runtime_code(self):
        runner=self.source_runner();runner.refs=self.root/"refs"
        for name in ("street","coupe","props","player"):
            p=runner.project/"Assets/Resources/Generated"/name/"scene.fbx"
            p.parent.mkdir(parents=True);p.write_bytes(b"fixture")
        def session(role,session_id,system,prompt,tools,dispatch,**kwargs):
            self.assertNotIn("run_blender",dispatch)
            self.assertNotIn("run_blender",[t["function"]["name"] for t in tools])
            with self.assertRaises(ValueError):dispatch["write_file"]("art",{"path":"Art/new.py","expected_sha256":sha(b""),"content":"bad"})
            with self.assertRaises(ValueError):dispatch["create_file"]("art-create",{"path":"Art/new.py","content":"bad"})
            result=dispatch["create_file"]("runtime",{"path":"Assets/Game/Bootstrap.cs","content":"// runtime fixture"})
            self.assertTrue(result["ok"])
            return {"ok":True}
        runner.model=SimpleNamespace(session=session)
        self.assertTrue(runner.builder({"phase":"foundation","outcome":"walking"},"fixture","brief")["ok"])

    def test_recovery_keeps_art_disabled_after_native_evidence(self):
        runner=self.source_runner();runner.refs=self.root/"refs"
        runner.c["csharp_only"]=True
        self.store.set(latest_evidence="evidence/prior-candidate")
        def session(role,session_id,system,prompt,tools,dispatch,**kwargs):
            self.assertNotIn("run_blender",dispatch)
            for name,fields in (("create_file",{"path":"Art/new.py","content":"bad"}),
                                ("replace_text",{"path":"Art/existing.py","expected_sha256":sha(b""),"old":"old","new":"new"})):
                with self.assertRaises(ValueError):dispatch[name]("forbidden",fields)
            self.assertFalse((runner.project/"Art").exists())
            return {"ok":True}
        runner.model=SimpleNamespace(session=session)
        self.assertTrue(runner.builder({"phase":"driving","outcome":"existing coupe controls"},"fixture","brief")["ok"])


if __name__=="__main__":unittest.main()
