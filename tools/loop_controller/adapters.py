"""Fixed local engine adapters. Untrusted game/Blender code runs under macOS Sandbox."""
import contextlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import tempfile
import time
import uuid
import zlib

try:
    import psutil
except ImportError:
    psutil = None  # Pure acceptance/state tests need no machine dependency.

from .core import Halt, atomic, now, read_json, sha


def sandbox_profile(writable, readable, private_root, token_file, protected=()):
    def lit(p):
        return json.dumps(str(Path(p).resolve()))
    # Default OS reads/mach services remain available for installed signed tools;
    # writes are scoped and the run's private state/credentials are unreadable.
    write_except = " ".join("(require-not (subpath " + lit(p) + "))" for p in writable)
    write_except += ' (require-not (literal "/dev/null"))'
    read_except = " ".join("(require-not (subpath " + lit(p) + "))" for p in readable)
    return ("(version 1)\n(allow default)\n"
            "(deny file-write* (require-all " + write_except + "))\n"
            "(deny file-read-data (literal " + lit(token_file) + "))\n"
            "(deny file-read-data (require-all (subpath " + lit(private_root) + ") " + read_except + "))\n"
            "(deny network*)\n(allow network* (local unix-socket) (remote unix-socket))\n" +
            "".join("(deny file-write* (literal " + lit(p) + "))\n" for p in protected))


class Machine:
    def __init__(self, config, store):
        if psutil is None:
            raise Halt("Use the qualified M5 runtime Python with psutil installed")
        self.c, self.store = config, store
        self.baseline_swap = psutil.swap_memory().used
        self.started = time.time()
        self.child = None
        self.stage_deadline = None
        hardware = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()
        chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        if (hardware, chip) != ("Mac17,15", "Apple M5 Ultra"):
            raise Halt("Heavy work requires the verified M5 Ultra")

    def snapshot(self):
        from engine_admission import snapshot
        return snapshot(self.c['coordination_dir'])

    def guard(self):
        waiting=Path(self.c['coordination_dir'])/'capacity-wait.json'
        if self.child is not None and waiting.exists():
            self.store.set(runtime_snapshot=self.snapshot())
            raise Halt('Capacity wait: supervisor paused engine admission; preserve other jobs')
        if self.store.get('three_day_cap'):
            from .delivery_policy import deadline_guard
            deadline_guard(self.store)
        if (self.store.root / "STOP").exists():
            raise Halt("Requested stop")
        if (Path.home() / ".cache/gpu-slot/PAUSED").exists():
            raise Halt("Shared engine admission is paused")
        memory, swap = psutil.virtual_memory(), psutil.swap_memory()
        if memory.available < 64 * 1024**3 or swap.used - self.baseline_swap > 512 * 1024**2:
            raise Halt("Memory/swap bound exceeded")
        console = subprocess.check_output(["stat", "-f", "%Su", "/dev/console"], text=True).strip()
        if console in ("", "root", "loginwindow"):
            raise Halt("Desktop session unavailable")
        if time.time() - self.store.get("started_epoch", time.time()) > self.c["wall_hours"] * 3600:
            raise Halt("Run wall-clock budget exhausted")
        if shutil.disk_usage(self.store.root).free < self.c["minimum_disk_GiB"] * 1024**3:
            raise Halt("Disk headroom floor reached")
        self.store.set(memory={"available_GiB": round(memory.available / 1024**3, 2),
                               "swap_growth_MiB": round(max(0, swap.used-self.baseline_swap) / 1024**2, 2)},
                       heartbeat_utc=now())

    @contextlib.contextmanager
    def engine(self, label, timeout):
        from warmup_resident import gpu_admission
        from unity_smoke import renderer_process
        self.guard()
        coordination = Path(self.c["coordination_dir"])
        request, ack = coordination / "engine-request.json", coordination / "engine-ack.json"
        if request.exists():
            raise Halt("An engine handoff is already present; reconcile ownership before resume")
        lease = {"lease_id": uuid.uuid4().hex, "controller_pid": os.getpid(),
                 "controller_start": psutil.Process().create_time(), "expires_epoch": time.time()+timeout+90,
                 "label": label}
        atomic(request, lease)
        try:
            deadline = time.monotonic() + 60
            while (not ack.exists() or read_json(ack).get("lease_id") != lease["lease_id"] or
                   read_json(ack).get('status')!='granted'):
                self.guard()
                if time.monotonic() > deadline:
                    observed=self.snapshot();self.store.set(runtime_snapshot=observed)
                    raise Halt('Capacity wait: engine handoff not granted; process/lease snapshot preserved')
                time.sleep(0.5)
            existing = []
            for process in psutil.process_iter(["pid", "exe", "name", "cmdline"]):
                if renderer_process(process.info["exe"] or "", (process.info["name"] or "").lower(), process.info["cmdline"] or []):
                    existing.append(process.pid)
            if len(existing) > 1:
                raise Halt("No room for one owned engine beside the existing renderer")
            with gpu_admission("chicago-loop-" + label, len(existing)):
                yield
        finally:
            if request.exists() and read_json(request).get("lease_id") == lease["lease_id"]:
                request.unlink()
            # Model inference waits until the resident supervisor has reclaimed admission.
            deadline = time.monotonic()+20
            while ack.exists() and time.monotonic() < deadline:
                time.sleep(0.25)

    def execute(self, label, argv, cwd, output, timeout, env_extra=None, protected=(), writable_roots=None):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        # Darwin Unix-domain sockets allow only 104 bytes; Bee adds its own
        # nested directory and socket name. Keep owned IPC scratch deliberately short.
        temp = Path(tempfile.mkdtemp(prefix="ql-", dir="/private/tmp"))
        profile = output / "execution.sb"
        executable = Path(argv[0]).resolve()
        # CoreFoundation discovers the main bundle by enumerating the .app root,
        # not just Contents. Denying that read makes Unity's native startup dereference
        # a missing bundle path before it can emit a player log.
        bundle = next((p for p in executable.parents if p.suffix == ".app"), executable.parent)
        readable = [cwd, output, bundle]
        # Unity's native lock/IPC helpers use Darwin's per-user temporary path
        # even when TMPDIR is scoped. These are OS scratch roots, never projects.
        darwin_temp = subprocess.check_output(["getconf", "DARWIN_USER_TEMP_DIR"], text=True).strip()
        writable = [cwd] if writable_roots is None else list(writable_roots)
        profile.write_text(sandbox_profile([*writable, output, "/private/tmp", darwin_temp], readable, self.store.root,
                                          self.c["token_file"], protected))
        env = {k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))}
        preferences = output / "preferences-home"
        for child_dir in ("Library/Preferences", "Library/Caches", "Library/Logs", "dotnet", "upm"):
            (preferences / child_dir).mkdir(parents=True, exist_ok=True)
        env.update(TMPDIR=str(temp), PYTHONDONTWRITEBYTECODE="1",
                   CFFIXED_USER_HOME=str(preferences), DOTNET_CLI_HOME=str(preferences / "dotnet"),
                   UPM_CACHE_ROOT=str(preferences / "upm"))
        env.update(env_extra or {})
        with self.engine(label, timeout), (output / (label + ".log")).open("wb") as log:
            child = subprocess.Popen(["/usr/bin/sandbox-exec", "-f", str(profile), *argv], cwd=cwd,
                env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            self.child = child
            self.store.set(owned_process={"pid": child.pid, "start": psutil.Process(child.pid).create_time(),
                                          "label": label}, activity=label)
            self.store.report()
            deadline = time.monotonic()+timeout
            try:
                lease_path=Path(self.c['coordination_dir'])/'engine-request.json'
                lease=read_json(lease_path)
                lease.update(engine_pid=child.pid,engine_start=psutil.Process(child.pid).create_time(),engine_pgid=os.getpgid(child.pid))
                atomic(lease_path,lease)
                while child.poll() is None:
                    self.guard()
                    if time.monotonic() > deadline:
                        raise Halt("Owned engine deadline exceeded: " + label)
                    self.store.report()
                    time.sleep(2)
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=10)
                self.child = None
                self.store.set(owned_process=None)
                # Compilers and package helpers inherit this task's process group.
                # Do not leave their private IPC helpers alive after the editor exits.
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                # Keep the registered lease until its private group has drained.
                # Reparented helpers retain the group; unrelated groups are untouched.
                drain=time.monotonic()+10;remaining=[]
                while time.monotonic()<drain:
                    remaining=[]
                    for p in psutil.process_iter(['pid','status']):
                        try:
                            if p.pid!=child.pid and os.getpgid(p.pid)==child.pid and p.info['status']!=psutil.STATUS_ZOMBIE:
                                remaining.append(p.pid)
                        except (psutil.NoSuchProcess,ProcessLookupError):pass
                    if not remaining:break
                    time.sleep(.1)
                if remaining:self.store.set(engine_group_drain_pending=remaining,runtime_snapshot=self.snapshot())
                shutil.rmtree(temp)
                self.store.report()
            return child.returncode


class Engines:
    def __init__(self, config, store, machine, source_root):
        self.c, self.store, self.machine = config, store, machine
        self.source_root = Path(source_root)

    def blender(self, project, script, action_id):
        from .core import Files
        path = Files(project, self.store).path(script)
        if not script.startswith("Art/") or path.suffix != ".py":
            raise ValueError("Choose an original Art/*.py authoring script")
        status, saved = self.store.begin_action(action_id, "blender", {"script": script, "sha256": sha(path.read_bytes())})
        if status == "complete":
            return saved
        if status == "pending":
            raise Halt("Interrupted Blender output requires reconciliation; no blind replay")
        output = self.store.root / "artifacts" / action_id
        output.mkdir(parents=True)
        shutil.copyfile(path, output / "original-authoring-source.py")
        generated = Path(project) / "Assets/Resources/Generated" / path.stem
        generated.mkdir(parents=True, exist_ok=True)
        originals = Path(project) / "ArtSources" / path.stem
        originals.mkdir(parents=True, exist_ok=True)
        wrapper = output / "author.py"
        wrapper.write_text("import os,runpy,bpy\nfrom pathlib import Path\n"
            "out=Path(os.environ['LOOP_ASSET_OUTPUT'])\n"
            "runpy.run_path(os.environ['LOOP_ART_SCRIPT'],run_name='__main__')\n"
            "bpy.context.preferences.filepaths.save_version=0\n"
            "bpy.ops.wm.save_as_mainfile(filepath=str(Path(os.environ['LOOP_BLEND_SOURCE'])/'source.blend'))\n"
            "bpy.ops.export_scene.fbx(filepath=str(out/'scene.fbx'),use_selection=False,add_leaf_bones=False,"
            "path_mode='COPY',embed_textures=True)\n")
        code = self.machine.execute("blender", [self.c["blender"], "--background", "--factory-startup",
            "--python-exit-code", "7", "--python", str(wrapper)], project, output, 240,
            {"LOOP_ASSET_OUTPUT": str(generated), "LOOP_ART_SCRIPT": str(path), "LOOP_BLEND_SOURCE": str(originals)},
            protected=[path, wrapper], writable_roots=[generated, originals])
        result = {"ok": code == 0, "exit_code": code, "script": script, "files": []}
        for p in sorted([*generated.rglob("*"), *originals.rglob("*")]):
            if p.is_file():
                if p.is_symlink() or p.stat().st_size > 50*1024**2:
                    raise Halt("Generated asset violates the bounded local artifact contract")
                if p.suffix.lower() not in (".fbx", ".blend", ".png", ".jpg", ".jpeg", ".tga", ".json"):
                    raise Halt("Blender output must contain art data only, never executable Unity code")
                result["files"].append({"path": str(p.relative_to(project)), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size})
        if not (originals/"source.blend").exists() or not (generated/"scene.fbx").exists():
            result["ok"] = False
        if result["ok"]:
            shutil.copytree(generated, output / "original-assets")
            shutil.copytree(originals, output / "editable-originals")
        result["diagnostic"] = (output / "blender.log").read_text(errors="replace")[-6000:]
        atomic(originals / "provenance.json", {"author": "local-Qwen", "script": script,
               "script_sha256": sha(path.read_bytes()), "action_id": action_id, "files": result["files"]})
        self.store.finish_action(action_id, result)
        self.store.event("local-art", action_id=action_id, ok=result["ok"], files=result["files"])
        return result

    def unity(self, project, bundle, scenario, candidate_commit):
        bundle = Path(bundle)
        bundle.mkdir(parents=True, exist_ok=False)
        build_project = bundle / "project"
        shutil.copytree(project, build_project)
        harness = build_project / "Assets/LoopHarness"
        shutil.copytree(self.source_root / "controller/unity", harness)
        protected = [p for p in build_project.rglob("*") if p.is_file() and p.suffix in (".cs", ".py", ".blend", ".fbx")]
        expected = {str(p): sha(p.read_bytes()) for p in protected}
        build = bundle / "build"
        build.mkdir()
        app = build / "ChicagoLocalSlice.app"
        build_code = self.machine.execute("unity-build", [self.c["unity"], "-batchmode", "-nographics",
            "-projectPath", str(build_project), "-refreshImportMode", "InProcess",
            "-executeMethod", "LoopBuild.Build", "-logFile", "-"],
            build_project, build, 900, {"LOOP_BUILD_OUTPUT": str(app)}, protected)
        errors = (build / "unity-build.log").read_text(errors="replace")
        failure_lines = [line for line in errors.splitlines() if re.search(r"error CS\d+|Compilation failed|BuildFailedException|Scripts have compiler errors", line)]
        for p, expected_hash in expected.items():
            if sha(Path(p).read_bytes()) != expected_hash:
                raise Halt("Protected Unity harness changed")
        receipt = {"candidate_commit": candidate_commit, "build_exit": build_code,
                   "compile_errors": failure_lines[-30:], "harness_sha256": sha(json.dumps(expected, sort_keys=True).encode()),
                   "acceptance_fixture": scenario.get('fixture')}
        if build_code or failure_lines or not (build / "build-result.json").exists():
            receipt.update(passed=False, failure="compile-build", diagnostic=errors[-7000:])
            atomic(bundle / "gate.json", receipt)
            return receipt
        executable = app / "Contents/MacOS/Chicago Local Slice"
        if not executable.exists():
            choices = list((app / "Contents/MacOS").glob("*"))
            if len(choices) != 1:
                raise Halt("Cannot resolve exact owned native player")
            executable = choices[0]
        captures = bundle / "captures"
        captures.mkdir()
        scenario_path = captures / "scenario.json"
        atomic(scenario_path, scenario)
        player_code = self.machine.execute("unity-play", [str(executable), "-batchmode", "-force-metal",
            "-screen-width", "960", "-screen-height", "540", "-logFile", "-",
            "--loop-output", str(captures), "--loop-scenario", str(scenario_path), "--loop-capture-id", bundle.name],
            build_project, captures, int(scenario["duration"])+90, protected=[*protected, scenario_path])
        receipt.update(evaluate_runtime(captures, scenario, player_code, bundle.name))
        receipt["build_id"] = sha(encode_directory(app))
        receipt["capture_id"] = bundle.name
        atomic(bundle / "gate.json", receipt)
        return receipt


def encode_directory(root):
    return json.dumps([{ "path": str(p.relative_to(root)), "sha256": sha(p.read_bytes()) }
                       for p in sorted(Path(root).rglob("*")) if p.is_file() and not p.is_symlink()], sort_keys=True).encode()


def evaluate_runtime(captures, scenario, player_exit, capture_id):
    captures = Path(captures)
    failed = []
    try:
        final = read_json(captures / "runtime-result.json")
        trace = [json.loads(line) for line in (captures / "trace.jsonl").read_text().splitlines()]
    except (FileNotFoundError, ValueError):
        return {"passed": False, "failure": "missing-runtime-evidence", "player_exit": player_exit}
    if player_exit != 0 or not final.get("completed") or final.get("errors") or final.get("capture_id") != capture_id:
        failed.append("runtime-exit-or-identity")
    if final.get("graphics") != "Metal" or final.get("duration", 0) < scenario["duration"] - 0.5:
        failed.append("renderer-or-duration")
    if len(trace) < scenario["duration"] * 3 or not all(t.get("camera") for t in trace):
        failed.append("missing-camera-or-trace")
    if any(not isinstance(t.get("time"), (int, float)) or not math.isfinite(t["time"]) for t in trace):
        failed.append("invalid-time")
    if any(b["time"] <= a["time"] for a,b in zip(trace, trace[1:])):
        failed.append("nonmonotonic-trace")
    frames = sorted(captures.glob("frame-*.png"))
    if len(frames) != len(scenario["captures"]) or any(not valid_capture_png(p.read_bytes()) for p in frames):
        failed.append("missing-captures")
    def distance(key):
        values = [t.get(key) for t in trace if t.get(key) and len(t[key]) == 3]
        if not values:
            return 0
        if any(not math.isfinite(v) for row in values for v in row):
            failed.append("nonfinite-"+key)
            return 0
        # Grounded input motion is horizontal; falling must never count as walking.
        return max(math.hypot(v[0]-values[0][0], v[2]-values[0][2]) for v in values)
    movement, driving = distance("player"), distance("vehicle")
    coverage = scenario["coverage"]
    if not any("W" in t.get("keys", []) for t in trace) or movement < 1.5:
        failed.append("input-driven-player-movement")
    player_positions = [t["player"] for t in trace if t.get("player") and len(t["player"]) == 3
                        and all(math.isfinite(v) for v in t["player"])]
    vertical_drop = max(0, player_positions[0][1]-min(v[1] for v in player_positions)) if player_positions else 0
    if coverage == "foundation" and vertical_drop > 5:
        failed.append("foundation-fall-below-start")
    if len({sha(p.read_bytes()) for p in frames}) < 2:
        failed.append("unchanging-captures")
    if coverage in ("driving", "combat", "mission", "polish", "whole-route"):
        if driving < 3 or not any(t.get("mode") == "vehicle" for t in trace):
            failed.append("vehicle-entry-and-motion")
        if not any(t.get("mode") == "foot" and t["time"] > 15 for t in trace):
            failed.append("vehicle-exit")
    if coverage in ("combat", "mission", "polish", "whole-route"):
        if max(t.get("shots", 0) for t in trace) < 1 or max(t.get("hits", 0) for t in trace) < 1:
            failed.append("combat-input-and-hit")
        if max(t.get("pursuit", 0) for t in trace) < 1:
            failed.append("pursuit-response")
        if not any("Mouse0" in t.get("keys", []) for t in trace):
            failed.append("combat-input-missing")
    if coverage in ("mission", "polish", "whole-route"):
        if not any(t.get("mission") == "complete" for t in trace):
            failed.append("mission-ending")
        if max(t.get("restarts", 0) for t in trace) < 1:
            failed.append("restart")
        if not any(t.get("mission") == "failed" or t.get("health", 100) <= 0 for t in trace):
            failed.append("failure-or-death-path")
    return {"passed": not failed, "failure": failed or None, "player_exit": player_exit,
            "coverage": coverage, "samples": len(trace), "duration": final["duration"],
            "player_displacement": round(movement, 3), "vehicle_displacement": round(driving, 3),
            "displacement_axes": "horizontal XZ", "player_vertical_drop": round(vertical_drop, 3),
            "frame_count": len(frames), "capture_scope": "native runtime camera frames plus input/state trace; HUD/audio not established by camera frames",
            "performance_claim": "unqualified; shared renderer and capture overhead"}


def valid_capture_png(raw):
    """Validate complete RGB/RGBA PNG bytes, not a success filename or header."""
    try:
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"): return False
        offset=8; payload=b""; dimensions=None; ended=False
        while offset<len(raw):
            length=struct.unpack(">I",raw[offset:offset+4])[0]
            kind=raw[offset+4:offset+8];data=raw[offset+8:offset+8+length]
            crc=struct.unpack(">I",raw[offset+8+length:offset+12+length])[0]
            if zlib.crc32(kind+data)&0xffffffff!=crc:return False
            if kind==b"IHDR":
                width,height,depth,color,compression,filtering,interlace=struct.unpack(">IIBBBBB",data)
                if not (320<=width<=4096 and 180<=height<=4096 and depth==8 and color in (2,6) and compression==filtering==interlace==0):return False
                dimensions=(width,height,3 if color==2 else 4)
            elif kind==b"IDAT":payload+=data
            elif kind==b"IEND":ended=True
            offset+=12+length
        if not ended or dimensions is None:return False
        width,height,channels=dimensions
        return len(zlib.decompress(payload))==height*(1+width*channels)
    except (ValueError,struct.error,zlib.error):return False
