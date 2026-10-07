#!/usr/bin/env python3
"""Bounded, explicitly authorized M5 Unity fixture; never opens existing projects.

Supply a new child workspace of the existing preparation directory, the original
Qwen Blender source and UnityFixture.cs. Run with the installed runtime Python.
The operator must first verify active licensing and resolve visible OS prompts.
"""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
try:
    import psutil
except ImportError:
    psutil=None  # Pure renderer classification tests need no machine dependency.


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def renderer_process(exe, name, argv):
    # The native player is a renderer too; its engine lease proves task ownership.
    if exe.endswith('/ChicagoLocalSlice.app/Contents/MacOS/Chicago Local Slice'):
        return True
    if exe.endswith("/Unity.app/Contents/MacOS/Unity"):
        # Observed Unity import workers explicitly use the Null graphics device.
        # Only exclude that documented worker shape, never a rendering editor.
        lower = [a.lower() for a in argv]
        worker = ("-nographics" in lower and "-parentpid" in lower and
                  any(lower[i] == "-name" and lower[i+1].startswith("assetimportworker")
                      for i in range(len(lower)-1)))
        return not worker
    return (exe.endswith("/Blender.app/Contents/MacOS/Blender") or
            "/UnrealEditor.app/Contents/MacOS/UnrealEditor" in exe or
            "/Godot.app/Contents/MacOS/" in exe or name in ("unrealeditor", "godot"))


def main():
    if psutil is None:raise RuntimeError('Use the qualified machine runtime with psutil installed')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--editor", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--allow-connector-test", action="store_true")
    p.add_argument("--allow-blender-with-unity-worker", action="store_true",
                   help="Owner-approved bounded check: one external Blender plus this Unity editor and its import worker")
    args = p.parse_args()
    if not args.allow_connector_test:
        p.error("Explicit current authorization required")
    if subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip() != "Mac17,15":
        raise RuntimeError("Refuse compute outside verified M5")
    root = args.workspace.absolute()
    if root.parent.resolve() != args.preparation.resolve() or root.exists():
        raise RuntimeError("Require a fresh direct child of task preparation")
    source = args.source.read_bytes()
    if hashlib.sha256(source).hexdigest() != "db4bb2305f5643f1fcaafa18fa22d04be1931d686b0b6ca75f3ee4e392d3aaa7":
        raise RuntimeError("Original local-Qwen source changed")
    root.mkdir(mode=0o700)
    project = root / "project"
    for rel in ["Assets/Editor", "Assets/Original", "Packages", "ProjectSettings", "Evidence"]:
        (project / rel).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.fixture, project / "Assets/Editor/UnityFixture.cs")
    (root / "asset_scene.py").write_bytes(source)
    (root / "export.py").write_text(
        "from pathlib import Path\nimport bpy\nroot=Path(__file__).parent\n"
        "exec(compile((root/'asset_scene.py').read_text(),'asset_scene.py','exec'))\n"
        "bpy.ops.export_scene.fbx(filepath=str(root/'project/Assets/Original/scene.fbx'),"
        "use_selection=False,object_types={'MESH'},add_leaf_bones=False)\n")
    save(project / "Packages/manifest.json", {"dependencies": {
        "com.unity.modules.imageconversion": "1.0.0",
        "com.unity.modules.jsonserialize": "1.0.0"}})
    (project / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.6.4f1\n")
    receipt = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "host": "Apple M5 Ultra / Mac17,15", "game_loop": "held",
               "asset_author": "prior unchanged local Qwen source",
               "fixture_author": "Codex cloud connector setup", "stages": {}}
    baseline_swap = psutil.swap_memory().used
    base = Path.home() / ".cache/gpu-slot"
    capacity = {"limit": 2, "editor_pid": None, "external_blender_pid": None}

    def renderers():
        found = []
        for proc in psutil.process_iter(["pid", "exe", "name", "status", "cmdline"]):
            try:
                exe = proc.info["exe"] or ""
                name = (proc.info["name"] or "").lower()
                if renderer_process(exe, name, proc.info["cmdline"] or []):
                    state = subprocess.check_output(["ps", "-o", "stat=", "-p", str(proc.pid)], text=True).strip()
                    if "E" in state or "Z" in state:
                        raise RuntimeError("Renderer is stuck exiting")
                    found.append(proc.pid)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        return found

    def guard():
        if (base / "PAUSED").exists():
            raise RuntimeError("Shared GPU admission paused")
        active = renderers()
        if len(active) > capacity["limit"]:
            raise RuntimeError("Explicit renderer-count bound exceeded")
        if capacity["limit"] == 3:
            for pid in active:
                if pid in (capacity["editor_pid"], capacity["external_blender_pid"]):
                    continue
                proc = psutil.Process(pid)
                words = proc.cmdline()
                low = [x.lower() for x in words]
                parent = words[low.index("-parentpid")+1] if "-parentpid" in low else None
                is_worker = (proc.exe() == str(args.editor) and parent == str(capacity["editor_pid"])
                             and any(low[i] == "-name" and low[i+1].startswith("assetimportworker")
                                     for i in range(len(low)-1)))
                if not is_worker:
                    raise RuntimeError("Unexpected renderer outside approved Blender/editor/worker shape")
        if psutil.virtual_memory().available < 64 * 1024**3:
            raise RuntimeError("Memory floor reached")
        if psutil.swap_memory().used - baseline_swap > 512 * 1024**2:
            raise RuntimeError("Swap growth bound reached")
        if subprocess.check_output(["stat", "-f", "%Su", "/dev/console"], text=True).strip() in ("", "root", "loginwindow"):
            raise RuntimeError("Desktop session unavailable")

    @contextlib.contextmanager
    def admission(required_slots):
        guard()
        if any((base / "queue").iterdir()):
            raise RuntimeError("Existing waiters have priority")
        # Hub, licensing helpers and the official CLI are not renderers.
        existing = renderers()
        if len(existing) + required_slots > capacity["limit"]:
            raise RuntimeError("Insufficient renderer capacity for editor and its observed Metal worker")
        handles = []
        holder = base / "holders" / (str(os.getpid()) + ".json")
        try:
            perf = (base / "locks/perf.lock").open("a+"); handles.append(perf)
            fcntl.flock(perf, fcntl.LOCK_SH | fcntl.LOCK_NB)
            slot = None
            reserved = []
            for i in range(2):
                fd = (base / ("locks/capture.%d.lock" % i)).open("a+")
                try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: fd.close(); continue
                handles.append(fd); reserved.append(i)
                if slot is None: slot = i
                # If an external GUI renderer has no slot lock, reserve the
                # otherwise-free second slot too, accounting for its capacity.
                if not existing and required_slots == 1: break
            if slot is None: raise RuntimeError("Both renderer slots occupied")
            if len(reserved) < required_slots:
                raise RuntimeError("Required shared renderer slots are occupied")
            save(holder, {"pid": os.getpid(), "start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(), "class": "capture", "slot": str(slot), "reserved_slots": reserved, "external_renderer_count": len(existing), "label": "m5-unity-disposable-check"})
            receipt["external_renderer_count"] = len(existing)
            yield
        finally:
            holder.unlink(missing_ok=True)
            for fd in reversed(handles): fd.close()

    def run(stage, argv, timeout):
        capacity.update(limit=2, editor_pid=None, external_blender_pid=None)
        if stage == "unity-render" and args.allow_blender_with_unity_worker:
            existing = renderers()
            if len(existing) == 1 and psutil.Process(existing[0]).exe().endswith("/Blender.app/Contents/MacOS/Blender"):
                capacity.update(limit=3, external_blender_pid=existing[0])
                receipt["owner_authorized_render_shape"] = "one external Blender, one task Unity editor, at most one owned Metal import worker"
                receipt["bounded_render_process_limit"] = 3
        guard()
        child = None
        required_slots = 2 if stage == "unity-render" else 1
        with admission(required_slots), (root / (stage + ".log")).open("wb") as log:
            try:
                child = subprocess.Popen(argv, cwd=project, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=log, start_new_session=True)
                capacity["editor_pid"] = child.pid
                deadline = time.monotonic() + timeout
                while child.poll() is None:
                    guard()
                    if time.monotonic() > deadline: raise TimeoutError(stage)
                    time.sleep(1)
                receipt["stages"][stage] = {"exit_code": child.returncode}
                save(root / "receipt.json", receipt)
                if child.returncode: raise RuntimeError(stage + " failed; inspect private log")
            finally:
                if child and child.poll() is None:
                    child.terminate()
                    try: child.wait(timeout=60)
                    except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=10)
                capacity.update(limit=2, editor_pid=None, external_blender_pid=None)

    try:
        run("blender-export", ["/Applications/Blender.app/Contents/MacOS/Blender", "--background", "--factory-startup", "--python", str(root / "export.py")], 120)
        # Request documented serial imports. Observed hardware import workers can
        # still initialize Metal, so the render stage reserves both slots.
        common = [str(args.editor), "-batchmode", "-projectPath", str(project),
                  "-refreshImportMode", "InProcess", "-quit", "-logFile", "-"]
        run("unity-import-compile", common + ["-nographics", "-executeMethod", "UnityFixture.ImportAndCheck"], 300)
        receipt["import_compile"] = json.loads((project / "Evidence/import-compile.json").read_text())
        run("unity-render", common + ["-force-metal", "-executeMethod", "UnityFixture.Render"], 240)
        receipt["render"] = json.loads((project / "Evidence/render.json").read_text())
        receipt["frame_sha256"] = hashlib.sha256((project / "Evidence/unity-frame.png").read_bytes()).hexdigest()
        receipt["status"] = "PASS"
    except Exception as error:
        receipt.update(status="STOPPED", error_type=type(error).__name__, error=str(error))
    finally:
        receipt["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt["available_GiB"] = round(psutil.virtual_memory().available / 1024**3, 3)
        receipt["swap_growth_MiB"] = round(max(0, psutil.swap_memory().used-baseline_swap) / 1024**2, 3)
        save(root / "receipt.json", receipt)
        print(json.dumps(receipt), flush=True)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
