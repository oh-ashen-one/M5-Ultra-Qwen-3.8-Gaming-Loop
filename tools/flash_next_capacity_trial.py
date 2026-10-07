#!/usr/bin/env python3
"""Opt-in capacity qualification on the unchanged official0.7.0 runtime/model."""
import argparse
import contextlib
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time
import urllib.request

import psutil

from unity_smoke import renderer_process
from warmup_resident import gpu_admission, session_token, write_state
from engine_admission import snapshot, complete_process_scan, hardware_pressure, resource_reasons
from qwen_capacity import Budget, POLICY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-python", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--coordination-dir", type=Path,
                        help="Owned controller handoff directory; loaded idle model yields engine slots")
    parser.add_argument("--allow-load", action="store_true")
    parser.add_argument('--capacity-trial',action='store_true',help='Explicit owner-authorized dynamic capacity qualification')
    parser.add_argument("--allow-one-existing-renderer", action="store_true")
    parser.add_argument('--authorized-shared-coexistence',action='store_true',
        help='Simultaneous operation: observe actual load and preserve shared slots, resource and owned-lease guards')
    args = parser.parse_args()
    if not args.allow_load or not args.capacity_trial:
        parser.error('Current owner authorization, --allow-load and --capacity-trial are required')
    hardware = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()
    chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    if (hardware, chip) != ("Mac17,15", "Apple M5 Ultra"):
        raise RuntimeError("Refuse compute outside the verified M5")
    manifest = json.loads(args.manifest.read_text())
    if (manifest["repository"], manifest["revision"]) != (
        "mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp",
        "e171af86f499f1855b0fb71d781105e8dd609610",
    ):
        raise RuntimeError("Unexpected model revision")
    model = Path(manifest["model_path"])
    for entry in manifest["files"]:
        p = model / entry["path"]
        if not p.is_file() or p.is_symlink() or p.stat().st_size != entry["size"]:
            raise RuntimeError("Verified model file changed: " + entry["path"])
    if importlib.metadata.version("omlx") != "0.7.0":
        raise RuntimeError("Re-audit changed runtime before loading")
    root = args.work_dir.absolute()
    os.umask(0o077)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if (root / "resident-state.json").exists():
        raise RuntimeError("Use a fresh task directory; no automatic relaunch")
    token = session_token(args.token_file, resume=True)
    with socket.socket() as probe:
        # A clean server shutdown can leave accepted TCP connections in TIME_WAIT.
        # SO_REUSEADDR permits that reuse but still rejects an active listener.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", 8027))

    def renderers():
        found = []
        for p in complete_process_scan(["pid", "name", "exe", "cmdline"], psutil):
            if p.pid == os.getpid():
                continue
            words = p.info["cmdline"] or []
            if ((p.info["name"] or "") == "omlx-server" or
                any(w in ("mlx_vlm.server", "mlx_lm.server") or Path(w).name in ("llama-server", "omlx") for w in words)):
                if child is None or p.pid != child.pid:
                    raise RuntimeError("Another inference process needs coordination")
            if renderer_process(p.info["exe"] or "", (p.info["name"] or "").lower(), words):
                found.append(p.pid)
        return found

    child = None
    engine_lease = None
    resident_admitted = False
    existing = renderers()
    baseline=snapshot(args.coordination_dir)['processes']
    baseline=[p for p in baseline if p.get('renderer')]
    if not args.authorized_shared_coexistence and len(existing) > (1 if args.allow_one_existing_renderer else 0):
        raise RuntimeError("Renderer count exceeds admitted capacity")
    trial=Budget(root/'capacity-budget.jsonl')
    capacity_phase='load'
    preflight=trial.observe('load')
    if not preflight['passed']:
        write_state(root/'load-refused.json',preflight)
        raise RuntimeError('Capacity trial load budget: '+','.join(preflight['failure']))
    baseline_swap = psutil.swap_memory().used
    stopped = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())
    state = {
        "status": "starting", "supervisor_pid": os.getpid(),
        "hardware": hardware, "chip": chip,
        "repository": manifest["repository"], "model_revision": manifest["revision"],
        "model_path": str(model), "runtime": "omlx 0.7.0",
        "runtime_commit": "4d4f5a280bc1739ba2cf39c1cee44fd5cc89cb40",
        "endpoint": "http://127.0.0.1:8027/v1", "game_loop": "held",
        "automatic_restarts": 0,
        "settings": {"max_num_seqs": 1, "max_kv_size": 262144,
                     "server_max_tokens": 8192,
                     "enable_thinking": True, "template_default_effort": "xhigh",
                     "template_default_preserve_thinking": True,
                     "kv_bits": None, "apc_enabled": False,
                     "mtp_enabled": False, "qwen4_ple_ssd_offload": False},
        'limits': {'memory_policy':POLICY,'omlx_memory_guard':'safe',
                   'maximum_qwen_footprint_GiB':192,'maximum_swap_growth_MiB':512,
                   'maximum_compressor_growth_GiB':2,'workload_priority':'simultaneous-no-default-priority'},
        "preserved_external_renderer_pids": existing,
        "authorized_shared_coexistence":args.authorized_shared_coexistence,
    }

    def api(path, timeout=5):
        req = urllib.request.Request("http://127.0.0.1:8027" + path,
                                     headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.load(response)

    def guard():
        nonlocal resident_admitted
        memory, swap = psutil.virtual_memory(), psutil.swap_memory()
        state["memory"] = {
            "available_GiB": round(memory.available / 1024**3, 3),
            "swap_used_GiB": round(swap.used / 1024**3, 3),
            "swap_growth_MiB": round(max(0, swap.used - baseline_swap) / 1024**2, 3),
        }
        metrics=hardware_pressure();state['hardware_pressure']=metrics
        if child is not None and trial.pid is None:trial.set_owned_pid(child.pid)
        budget=trial.observe(capacity_phase,metrics['thermal_warning'])
        state['capacity_budget']=budget
        pressure=budget['failure']
        if pressure:raise RuntimeError('Resource guard: '+','.join(pressure))
        if subprocess.check_output(["stat", "-f", "%Su", "/dev/console"], text=True).strip() in ("root", "loginwindow", ""):
            raise RuntimeError("Desktop session lost")
        if child is not None and child.poll() is not None:
            raise RuntimeError("Owned model server exited")
        renderers()  # Preserve detection of a competing inference service.
        observed=snapshot(args.coordination_dir,baseline,engine_lease,coexistence=args.authorized_shared_coexistence)
        state['admission_snapshot']=observed
        # Neither workload has automatic priority. Actual shared lock ownership
        # and resource/graphics guards still govern admission and continuation.
        decision=observed['decision']
        waiting=args.coordination_dir/'capacity-wait.json' if args.coordination_dir else None
        if decision['status']=='capacity-wait':
            status=api('/api/status') if child else {}
            if status.get('active_requests',0) or status.get('waiting_requests',0):
                raise RuntimeError('Renderer conflict during active inference; snapshot preserved')
            state['status']='capacity-wait'
            if waiting:write_state(waiting,{'supervisor_pid':os.getpid(),'status':'capacity-wait',
                'reason':decision['reasons'],'snapshot':observed})
            # An idle loaded model needs no renderer slot. Preserve other jobs.
            admission.close()
            resident_admitted=False
            return False
        if engine_lease:
            if time.time() > engine_lease["expires_epoch"]:
                raise RuntimeError("Engine handoff expired")
            status = api("/api/status")
            if status.get("active_requests", 0) or status.get("waiting_requests", 0):
                raise RuntimeError("Inference overlapped an engine handoff")
        return True

    with (root / "resident.lock").open("a+") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with contextlib.ExitStack() as admission:
            shared = admission.enter_context(gpu_admission("m5-flash-next-resident", len(existing),
                authorized_shared_coexistence=args.authorized_shared_coexistence,guard=guard))
            resident_admitted=True
            try:
                env = os.environ.copy()
                for key in list(env):
                    if key.startswith(("MLX_VLM_PRELOAD_", "MLX_VLM_DRAFT_", "KV_", "APC_")):
                        env.pop(key)
                env.update(PYTHONDONTWRITEBYTECODE="1", MLX_TRUST_REMOTE_CODE="false",
                           HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                           APC_ENABLED="0", OMLX_API_KEY=token)
                base = root / "omlx-data"
                base.mkdir(mode=0o700)
                model_settings = {
                    "max_context_window": 262144, "max_tokens": 8192,
                    "temperature": 1.0, "top_p": 0.95, "top_k": 20,
                    "min_p": 0.0, "presence_penalty": 0.0, "repetition_penalty": 1.0,
                    "enable_thinking": True, "preserve_thinking": True,
                    "chat_template_kwargs": {"reasoning_effort": "xhigh"},
                    "is_pinned": True, "is_default": True, "ttl_seconds": None,
                    "trust_remote_code": False, "mtp_enabled": False,
                    "turboquant_kv_enabled": False, "qwen4_ple_ssd_offload": False,
                    "dflash_enabled": False, "vlm_mtp_enabled": False,
                }
                write_state(base / "model_settings.json", {"version": 1, "models": {model.name: model_settings}})
                write_state(base / "settings.json", {
                    "server": {"host": "127.0.0.1", "port": 8027, "log_level": "info",
                               "distributed_inference_enabled": False},
                    "model": {"model_dirs": [str(model.parent)]},
                    "scheduler": {"max_concurrent_requests": 1},
                    "sampling": {"max_context_window": 262144, "max_tokens": 8192,
                                 "temperature": 1.0, "top_p": 0.95, "top_k": 20},
                    "cache": {"enabled": False},
                    "huggingface": {"cache_enabled": False},
                })
                argv = [str(args.runtime_python.parent / "omlx"), "serve",
                        "--base-path", str(base), "--model-dir", str(model.parent),
                        "--host", "127.0.0.1", "--port", "8027",
                        "--max-concurrent-requests", "1", "--memory-guard", "safe",
                        "--no-cache", "--no-hf-cache", "--log-level", "info"]
                if not guard():raise RuntimeError('Capacity changed before model load; snapshot preserved')
                with (root / "model-server.log").open("ab") as log:
                    child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                             stdout=log, stderr=log, start_new_session=True)
                state["server_pid"] = child.pid
                deadline = time.monotonic() + 900
                while not stopped.is_set() and time.monotonic() < deadline:
                    guard()
                    try:
                        healthy = api("/health")
                    except (OSError, ValueError):
                        healthy = {}
                    if healthy.get("status") == "healthy":
                        models = api("/v1/models/status").get("models", [])
                        loaded = [m for m in models if m.get("is_loaded") or m.get("loaded") or m.get("status") == "loaded"]
                        if len(loaded) == 1 and loaded[0].get("id") == model.name:
                            state["loaded_model_status"] = loaded[0]
                            break
                    write_state(root / "resident-state.json", state)
                    stopped.wait(2)
                else:
                    raise RuntimeError("Model load interrupted or timed out")
                capacity_phase='decode'
                state["status"] = "loaded-idle"
                while not stopped.is_set():
                    if args.coordination_dir:
                        args.coordination_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                        request = args.coordination_dir / "engine-request.json"
                        ack = args.coordination_dir / "engine-ack.json"
                        if request.exists() and engine_lease is not None:
                            refreshed=json.loads(request.read_text())
                            if refreshed['lease_id']==engine_lease['lease_id']:
                                engine_lease=refreshed
                        if request.exists() and engine_lease is None:
                            proposal = json.loads(request.read_text())
                            if proposal["expires_epoch"] > time.time() + 1500:
                                raise RuntimeError("Engine handoff deadline is not bounded")
                            owner = psutil.Process(proposal["controller_pid"])
                            if abs(owner.create_time() - proposal["controller_start"]) > 0.01:
                                raise RuntimeError("Invalid engine handoff owner")
                            status = api("/api/status")
                            if guard() and not status.get("active_requests", 0) and not status.get("waiting_requests", 0):
                                admission.close()
                                resident_admitted=False
                                engine_lease = proposal
                                write_state(ack, {"lease_id": proposal["lease_id"], "status": "granted"})
                        elif not request.exists() and engine_lease is not None:
                            # The controller closes its slot locks before withdrawing the request.
                            engine_lease = None
                        state["engine_handoff"] = engine_lease["lease_id"] if engine_lease else None
                    available=guard()
                    if not available:
                        if args.coordination_dir and engine_lease:
                            write_state(ack,{'lease_id':engine_lease['lease_id'],'status':'capacity-wait',
                                'reason':state['admission_snapshot']['decision']['reasons']})
                        write_state(root/'resident-state.json',state);stopped.wait(2);continue
                    if args.coordination_dir and engine_lease:
                        write_state(ack,{'lease_id':engine_lease['lease_id'],'status':'granted'})
                    elif not resident_admitted:
                        # Acquisition is nonblocking. Competing holders/queue mean wait,
                        # not a model fault. Never remove their records.
                        admission.close()
                        try:
                            shared=admission.enter_context(gpu_admission('m5-flash-next-resident',len(existing),
                                authorized_shared_coexistence=args.authorized_shared_coexistence,guard=guard))
                            resident_admitted=True
                        except (RuntimeError,BlockingIOError) as error:
                            state['status']='capacity-wait';state['admission_wait_reason']=str(error)
                            write_state(args.coordination_dir/'capacity-wait.json',{'supervisor_pid':os.getpid(),
                                'status':'capacity-wait','reason':str(error),'snapshot':snapshot(args.coordination_dir,baseline,
                                    coexistence=args.authorized_shared_coexistence)})
                            write_state(root/'resident-state.json',state);stopped.wait(2);continue
                    state['status']='engine-handoff' if engine_lease else 'loaded-idle'
                    if args.coordination_dir:(args.coordination_dir/'capacity-wait.json').unlink(missing_ok=True)
                    if args.coordination_dir and not engine_lease and not request.exists():ack.unlink(missing_ok=True)
                    if (shared / "PAUSED").exists():
                        raise RuntimeError("Shared GPU protocol paused")
                    healthy = api("/health")
                    if healthy.get("status") != "healthy":
                        raise RuntimeError("Model health failed")
                    models = api("/v1/models/status").get("models", [])
                    loaded = [m for m in models if m.get("is_loaded") or m.get("loaded") or m.get("status") == "loaded"]
                    if len(loaded) != 1 or loaded[0].get("id") != model.name:
                        raise RuntimeError("Unexpected model replacement")
                    state["health"] = healthy
                    state["loaded_model_status"] = loaded[0]
                    state["server_RSS_GiB"] = round(psutil.Process(child.pid).memory_info().rss / 1024**3, 3)
                    write_state(root / "resident-state.json", state)
                    stopped.wait(2 if args.coordination_dir else 10)
                state["status"] = "stopped-by-request"
            except Exception as exc:
                state.update(status="stopped-on-fault", error=str(exc), error_type=type(exc).__name__)
                try:state['stop_snapshot']=snapshot(args.coordination_dir,baseline,engine_lease)
                except Exception as capture_error:state['stop_snapshot_error']=type(capture_error).__name__+': '+str(capture_error)
            finally:
                if child is not None and child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=10)
                state["server_alive"] = bool(child is not None and child.poll() is None)
                write_state(root / "resident-state.json", state)


if __name__ == "__main__":
    main()
