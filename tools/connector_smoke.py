#!/usr/bin/env python3
"""Explicitly authorized, bounded M5 connector diagnostics; never a game loop.

Run on the verified M5 with its existing resident server and existing Blender.
The caller supplies a new disposable workspace. Private model replies stay there;
only the selected receipt, original scene source and rendered frame are public.
This small AST/allowlist mediator is a diagnostic boundary, not an OS sandbox.
"""
import argparse
import ast
import base64
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request

import psutil


def digest(data):
    return hashlib.sha256(data).hexdigest()


def store_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def schema(name, description, properties, required):
    return {"type": "function", "function": {"name": name,
        "description": description, "parameters": {"type": "object",
        "properties": properties, "required": required,
        "additionalProperties": False}}}


def validate_source(name, source):
    if len(source.encode()) > 24000:
        raise ValueError("Diagnostic source too large")
    tree = ast.parse(source)
    denied = {"eval", "exec", "open", "compile", "getattr", "setattr", "delattr",
              "globals", "locals", "input", "exit", "quit", "breakpoint"}
    operators = {"bpy.ops.mesh.primitive_cube_add", "bpy.ops.mesh.primitive_uv_sphere_add",
                 "bpy.ops.mesh.primitive_plane_add", "bpy.ops.object.select_all",
                 "bpy.ops.object.delete", "bpy.ops.object.camera_add",
                 "bpy.ops.object.light_add", "bpy.ops.object.transform_apply",
                 "bpy.ops.object.shade_smooth"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = ([x.name for x in node.names] if isinstance(node, ast.Import)
                       else [node.module])
            allowed = {"bpy", "math", "mathutils"} if name == "asset_scene.py" else set()
            if not set(modules) <= allowed:
                raise ValueError("Import outside diagnostic allowlist")
        if isinstance(node, ast.Name) and (node.id in denied or node.id.startswith("__")):
            raise ValueError("Forbidden diagnostic name")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("Private attribute access forbidden")
        if isinstance(node, ast.Call):
            rendered = ast.unparse(node.func)
            if rendered.startswith("bpy.ops.") and rendered not in operators:
                raise ValueError("Blender operator outside mesh/scene allowlist")
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "load", "write", "read", "write_text", "read_text", "save",
                "save_as_mainfile", "render", "unlink", "system", "popen"}:
                raise ValueError("File/process operation outside trusted wrapper")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "remove" and rendered not in {
                "nodes.remove", "w_nodes.remove"}:
                raise ValueError("Only named shader-node removal is permitted")
    if name == "diagnostic.py":
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise ValueError("Expected one diagnostic function")
        fn = tree.body[0]
        if fn.name != "doubled" or fn.decorator_list or fn.args.defaults or len(fn.body) != 1:
            raise ValueError("Expected a simple doubled function")
        if not isinstance(fn.body[0], ast.Return):
            raise ValueError("Expected return expression")


@contextlib.contextmanager
def engine_slot():
    """Existing shared protocol; the resident model conservatively holds slot 0."""
    base = Path.home() / ".cache/gpu-slot"
    if (base / "PAUSED").exists() or any((base / "queue").iterdir()):
        raise RuntimeError("Shared admission paused or prior waiter present")
    engines = [p for p in psutil.process_iter(["name", "status"])
               if any(k in (p.info["name"] or "").lower()
                      for k in ["blender", "unity", "godot", "unreal"])]
    if engines:
        raise RuntimeError("Existing engine requires ownership coordination")
    handles = []
    holder = base / "holders" / (str(os.getpid()) + ".json")
    try:
        perf = (base / "locks/perf.lock").open("a+"); handles.append(perf)
        fcntl.flock(perf, fcntl.LOCK_SH | fcntl.LOCK_NB)
        slot = None
        for i in range(2):
            fd = (base / "locks" / ("capture." + str(i) + ".lock")).open("a+")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fd.close(); continue
            handles.append(fd); slot = i; break
        if slot is None:
            raise RuntimeError("Both existing capture slots occupied")
        store_json(holder, {"pid": os.getpid(), "start": subprocess.check_output(
            ["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
            "class": "capture", "slot": str(slot), "label": "m5-qwen-connector-smoke",
            "cmd": "tools/connector_smoke.py"})
        yield slot
    finally:
        holder.unlink(missing_ok=True)
        for fd in reversed(handles):
            fd.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--allow-connector-test", action="store_true")
    parser.add_argument("--resume-rejected-source", action="store_true",
                        help="Reconcile and retry only a previously rejected Blender source submission")
    args = parser.parse_args()
    if not args.allow_connector_test:
        parser.error("Current owner authorization and explicit flag required")
    chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    hardware = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()
    if chip != "Apple M5 Ultra" or hardware != "Mac17,15":
        raise RuntimeError("Refuse diagnostic compute on a different host")
    root = args.workspace.absolute()
    if root.resolve().parent != args.preparation.resolve():
        raise RuntimeError("Diagnostic workspace must belong to this preparation directory")
    if not args.resume_rejected_source:
        root.mkdir(mode=0o700, exist_ok=False)
    if root.is_symlink() or root.resolve() != root:
        raise RuntimeError("Workspace must be new, absolute and not a symlink")
    root.chmod(0o700)
    token = (args.preparation / "server-access-token.txt").read_text().strip()
    model = str(args.preparation / "bf16/model")
    baseline_swap = psutil.swap_memory().used
    receipt = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": {"chip": chip, "model": hardware, "memory_GiB": 256, "GPU_cores": 80},
        "runtime": "MLX-VLM 0.7.4", "model": "Qwen3.8-27B BF16",
        "model_revision": "6f265714824f3c38d4452baa1628aef3d9b9aae9",
        "request_settings": {"enable_thinking": True, "reasoning_effort": "xhigh",
            "thinking_budget": 1024, "max_tokens": 4096, "temperature": 1.0,
            "top_p": 0.95, "top_k": 20, "min_p": 0.0,
            "presence_penalty": 0.0, "repetition_penalty": 1.0},
        "game_loop": "held", "stages": {}, "requests": [], "tool_actions": []}
    replay = None
    if args.resume_rejected_source:
        previous = json.loads((root/"receipt.json").read_text())
        if previous.get("error", {}).get("message") != "Blender operator outside mesh/scene allowlist":
            raise RuntimeError("Resume requires this exact diagnosed pre-execution rejection")
        if previous["stages"].get("qwen_tool_file_shell", {}).get("status") != "PASS":
            raise RuntimeError("Previous file/shell stage not verified")
        if any((root/x).exists() for x in ["scene.blend", "scene.glb", "scene.fbx", "frame.png"]):
            raise RuntimeError("Reconcile existing Blender outputs before retry; no automatic replay")
        responses = sorted(root.glob("private-response-*.json"))
        replay = json.loads(responses[-1].read_text())["choices"][0]["message"]
        if [c["function"]["name"] for c in replay.get("tool_calls") or []] != ["write_file"]:
            raise RuntimeError("Expected the unexecuted source submission only")
        prior_error = previous.pop("error")
        previous["setup_recovery"] = {"prior_error": prior_error,
            "change": "Allow normal shade_smooth and named shader-node removal; preserve local Qwen source",
            "resumed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        previous.pop("finished_utc", None)
        receipt = previous

    def guard():
        s = json.loads((args.preparation / "resident-state.json").read_text())
        if s["status"] != "loaded-idle":
            raise RuntimeError("Resident supervisor no longer healthy")
        available = psutil.virtual_memory().available / 1024**3
        growth = max(0, psutil.swap_memory().used-baseline_swap) / 1024**2
        receipt["resource_snapshot"] = {"available_GiB": round(available, 3),
                                        "swap_growth_MiB": round(growth, 3)}
        if available < 64 or growth > 512:
            raise RuntimeError("Resource guard exceeded")
        if (Path.home()/".cache/gpu-slot/PAUSED").exists():
            raise RuntimeError("Shared GPU admission paused")
        console = subprocess.check_output(["stat", "-f", "%Su", "/dev/console"], text=True).strip()
        if console in ["", "root", "loginwindow"]:
            raise RuntimeError("Desktop session unavailable")

    def api(path, data=None, timeout=300):
        guard()
        req = urllib.request.Request("http://127.0.0.1:8027"+path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Authorization": "Bearer "+token, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            value = json.load(res)
        guard()
        return value

    def request(stage, messages, tools=None):
        payload = dict(receipt["request_settings"], model=model, messages=messages, stream=False)
        if tools: payload.update(tools=tools, tool_choice="auto")
        value = api("/v1/chat/completions", payload)
        # Full responses contain private reasoning; never include them in publication.
        store_json(root/("private-response-%02d.json" % len(receipt["requests"])), value)
        msg = value["choices"][0]["message"]
        receipt["requests"].append({"stage": stage, "usage": value.get("usage"),
            "finish_reason": value["choices"][0].get("finish_reason"),
            "reasoning_content_returned": bool(msg.get("reasoning_content")),
            "tool_names": [t["function"]["name"] for t in msg.get("tool_calls") or []]})
        return msg

    write_tool = schema("write_file", "Replace one allowed diagnostic source with an exact hash precondition.",
        {"path": {"type": "string"}, "expected_sha256": {"type": "string"},
         "content": {"type": "string"}}, ["path", "expected_sha256", "content"])
    test_tool = schema("run_test", "Run the immutable Python diagnostic test through a fixed shell command.", {}, [])
    blender_tool = schema("run_blender", "Run the guarded scene source in owned headless Blender; save, export and render.", {}, [])
    allowed = {"diagnostic.py", "asset_scene.py"}

    def write_file(fields):
        if set(fields) != {"path", "expected_sha256", "content"} or fields["path"] not in allowed:
            raise ValueError("Path/argument allowlist rejected")
        path = root/fields["path"]
        if path.is_symlink() or path.resolve().parent != root:
            raise ValueError("Path boundary rejected")
        if digest(path.read_bytes()) != fields["expected_sha256"]:
            raise ValueError("Hash precondition rejected")
        validate_source(fields["path"], fields["content"])
        path.write_text(fields["content"])
        return {"ok": True, "path": fields["path"], "sha256": digest(path.read_bytes())}

    checker = ("import runpy; f=runpy.run_path('diagnostic.py')['doubled']; "
               "pairs=[(-3,-6),(0,0),(7,14),(1.25,2.5)]; "
               "assert all(f(x)==y for x,y in pairs), 'doubled fixture failed'; "
               "print('PASS: 4 numeric cases')")

    def run_test(fields):
        if fields: raise ValueError("Unexpected test arguments")
        result = subprocess.run(["/bin/zsh", "-f", "-c", "exec "+
            __import__("shlex").quote(os.sys.executable)+" -I -c "+__import__("shlex").quote(checker)],
            cwd=root, capture_output=True, text=True, timeout=15)
        return {"ok": result.returncode == 0, "exit_code": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()[-1000:]}

    def run_blender(fields):
        if fields: raise ValueError("Unexpected Blender arguments")
        validate_source("asset_scene.py", (root/"asset_scene.py").read_text())
        wrapper = '''import bpy, pathlib, json
root = pathlib.Path(__file__).parent
exec(compile((root/"asset_scene.py").read_text(), "asset_scene.py", "exec"))
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=8
scene.render.threads_mode="FIXED"
scene.render.threads=8
scene.render.resolution_x=512
scene.render.resolution_y=512
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.filepath=str(root/"frame.png")
bpy.ops.wm.save_as_mainfile(filepath=str(root/"scene.blend"))
bpy.ops.export_scene.gltf(filepath=str(root/"scene.glb"),export_format="GLB")
bpy.ops.export_scene.fbx(filepath=str(root/"scene.fbx"),use_selection=False,object_types={"MESH"},add_leaf_bones=False)
bpy.ops.render.render(write_still=True)
receipt={"version":bpy.app.version_string,"renderer":"Cycles CPU","resolution":[512,512],"samples":8,
 "objects":[{"name":o.name,"type":o.type,"vertices":len(o.data.vertices) if o.type=="MESH" else None,
 "materials":[m.name for m in o.data.materials] if o.type=="MESH" else []} for o in scene.objects]}
(root/"blender-evidence.json").write_text(json.dumps(receipt,indent=2))
'''
        (root/"blender_wrapper.py").write_text(wrapper)
        log_path = root/"private-blender.log"
        with engine_slot() as slot, log_path.open("w") as log:
            guard()
            child = subprocess.Popen(["/Applications/Blender.app/Contents/MacOS/Blender",
                "--background", "--factory-startup", "--python-exit-code", "7", "--python",
                str(root/"blender_wrapper.py")], cwd=root, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic()+240
            try:
                while child.poll() is None:
                    guard()
                    if time.monotonic()>deadline: raise RuntimeError("Blender diagnostic deadline exceeded")
                    time.sleep(2)
            finally:
                if child.poll() is None:
                    child.terminate()
                    try: child.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.wait(timeout=10)
            if child.returncode:
                return {"ok": False, "exit_code": child.returncode, "error": "Owned Blender failed; inspect private log"}
        paths = [root/x for x in ["scene.blend", "scene.glb", "scene.fbx", "frame.png"]]
        info = json.loads((root/"blender-evidence.json").read_text())
        info.update(ok=all(p.is_file() and p.stat().st_size>0 for p in paths),
            artifacts=[{"name":p.name,"bytes":p.stat().st_size,"sha256":digest(p.read_bytes())} for p in paths],
            GPU_slot=slot, control="Blender CLI --background --factory-startup --python")
        return info

    def session(stage, prompt, tools, dispatch, success, turns, replay_message=None):
        messages=[{"role":"system","content":"You are the local Qwen diagnostic worker. Use the provided tools only. This is a disposable setup check, not a game. Never write outside the given allowlisted filenames."},
                  {"role":"user","content":prompt}]
        for _ in range(turns):
            msg = replay_message if replay_message is not None else request(stage,messages,tools)
            replay_message = None
            messages.append(msg)
            calls=msg.get("tool_calls") or []
            if not calls: return False
            for call in calls:
                fn=call["function"]; fields=fn["arguments"]
                if isinstance(fields,str): fields=json.loads(fields)
                if fn["name"] not in dispatch: raise ValueError("Unexpected function")
                outcome=dispatch[fn["name"]](fields)
                receipt["tool_actions"].append({"stage":stage,"tool":fn["name"],"result":outcome})
                store_json(root/"receipt.json",receipt)
                messages.append({"role":"tool","tool_call_id":call["id"],"content":json.dumps(outcome)})
                if fn["name"]==success and outcome.get("ok"): return True
        return False

    try:
        healthy=api("/health",timeout=5)
        loaded=[v for v in healthy.get("loaded_models",{}).values() if v.get("model")]
        if len(loaded)!=1 or loaded[0]["model"]!=model or healthy.get("loaded_tool_parser")!="qwen3_coder":
            raise RuntimeError("Unexpected resident model/parser")
        if not args.resume_rejected_source:
            (root/"diagnostic.py").write_text("def doubled(value):\n    return value\n")
            red=run_test({})
            assert not red["ok"], "Broken fixture must fail before model edit"
            try:
                write_file({"path":"../outside.py","expected_sha256":"0"*64,"content":""})
                raise AssertionError("Outside path accepted")
            except ValueError: pass
            receipt["boundary_fixtures"]={"broken_test_exit":red["exit_code"],"outside_path_rejected":True}
            initial=digest((root/"diagnostic.py").read_bytes())
            passed=session("file_shell", "Fix diagnostic.py so doubled(value) returns twice its input. Current source:\n"+
                (root/"diagnostic.py").read_text()+"\nCurrent SHA256: "+initial+
                ". Use write_file with this exact hash, then run_test. One simple function, no imports.",
                [write_tool,test_tool],{"write_file":write_file,"run_test":run_test},"run_test",3)
            receipt["stages"]["qwen_tool_file_shell"]={"status":"PASS" if passed else "FAIL",
                "host":"M5 Ultra","tool":"qwen3_coder -> allowlist/hash edit -> zsh/Python immutable test",
                "source_sha256":digest((root/"diagnostic.py").read_bytes())}
            print("FILE_SHELL",receipt["stages"]["qwen_tool_file_shell"]["status"],flush=True)
            (root/"asset_scene.py").write_text("# Original diagnostic scene to be authored by local Qwen.\n")
        initial=digest((root/"asset_scene.py").read_bytes())
        passed=session("blender", "Author asset_scene.py from scratch using bpy and mathutils only. Create an original red cube centered (-1.3,0,1), an original blue UV sphere centered (1.3,0,1), and gray ground plane at z=0. Make new node-based materials, roughness about .4. Camera at (4,-7,5) looks at (0,0,1), orthographic scale 7. Use a large area light and subdued world light. Ensure both shapes fully visible, red cube on image left, blue sphere on image right. Use direct Python statements; no file/process operations or save/export/render calls (trusted wrapper does these). Do not use bpy.data removal; clear scene using object.select_all and object.delete. Current file SHA256: "+initial+
            ". Write allowed file through write_file, then call run_blender. This tests original geometry/materials, not final game art.",
            [write_tool,blender_tool],{"write_file":write_file,"run_blender":run_blender},"run_blender",3,replay)
        receipt["stages"]["blender_cli"]={"status":"PASS" if passed else "FAIL","host":"M5 Ultra",
            "tool":"existing Blender CLI","author":"local Qwen from scratch",
            "source_sha256":digest((root/"asset_scene.py").read_bytes())}
        receipt["stages"]["blender_mcp"]={"status":"NOT RUN","reason":"No installed MCP addon/server found; no installation authorized"}
        receipt["stages"]["unity_import_compile_render"]={"status":"NOT RUN",
            "reason":"M5 Unity editor/Hub and license directory absent in live inventory",
            "required_action":"Owner selects/installs a Unity release and activates appropriate license on M5, then authorizes rerun"}
        receipt["stages"]["qwen_vision_unity_frame"]={"status":"NOT RUN",
            "reason":"No Unity rendered frame exists; the independent Blender-image check is recorded separately"}
        print("BLENDER",receipt["stages"]["blender_cli"]["status"],flush=True)
        if passed:
            from PIL import Image
            image_path=root/"frame.png"
            before=digest(image_path.read_bytes())
            pixels=Image.open(image_path).convert("RGB")
            red=[]; blue=[]
            for y in range(pixels.height):
                for x in range(pixels.width):
                    r,g,b=pixels.getpixel((x,y))
                    if r>g*1.5 and r>b*1.5 and r>70: red.append(x)
                    if b>r*1.5 and b>g*1.5 and b>70: blue.append(x)
            pixel_check=len(red)>500 and len(blue)>500 and sum(red)/len(red)<sum(blue)/len(blue)
            receipt["pixel_fixture"]={"red_pixels":len(red),"blue_pixels":len(blue),
                "red_centroid_x":round(sum(red)/len(red),2) if red else None,
                "blue_centroid_x":round(sum(blue)/len(blue),2) if blue else None,"pass":pixel_check}
            msg=request("vision",[{"role":"user","content":[
                {"type":"text","text":"Inspect this image only. Return JSON with left_object and right_object, each containing shape and color. Describe the two main foreground solids, not the floor. Do not infer from filenames."},
                {"type":"image_url","image_url":{"url":"data:image/png;base64,"+base64.b64encode(image_path.read_bytes()).decode()}}]}])
            answer=(msg.get("content") or "").strip()
            start=answer.find("{"); end=answer.rfind("}")
            observed=json.loads(answer[start:end+1])
            left=observed.get("left_object",{}); right=observed.get("right_object",{})
            vision=("red" in str(left.get("color","")).lower() and
                    any(s in str(left.get("shape","")).lower() for s in ["cube","box"]) and
                    "blue" in str(right.get("color","")).lower() and
                    any(s in str(right.get("shape","")).lower() for s in ["sphere","ball"]))
            unchanged=before==digest(image_path.read_bytes())
            receipt["stages"]["qwen_vision_blender_frame"]={"status":"PASS" if vision and pixel_check and unchanged else "FAIL",
                "host":"M5 Ultra","image_sha256":before,"image_unchanged":unchanged,
                "observed":observed,"source":"actual Blender render; Unity frame unavailable"}
            print("VISION",receipt["stages"]["qwen_vision_blender_frame"]["status"],flush=True)
        else:
            receipt["stages"]["qwen_vision_blender_frame"]={"status":"NOT RUN","reason":"Blender did not produce verified frame"}
        guard()
    except Exception as error:
        receipt["error"]={"type":type(error).__name__,"message":str(error).replace(str(root),"<diagnostic-workspace>")}
        print("DIAGNOSTIC_ERROR",type(error).__name__,flush=True)
    finally:
        receipt["finished_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
        store_json(root/"receipt.json",receipt)


if __name__=="__main__":
    main()
