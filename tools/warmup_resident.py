#!/usr/bin/env python3
"""Owned M5 BF16 warm-up and idle supervision; never starts a game or agent loop."""
import argparse
import contextlib
import datetime
import fcntl
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import stat
import subprocess
import threading
import time
import urllib.request
import psutil
from unity_smoke import renderer_process


def write_state(path, state):
    state["updated_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(path)


def session_token(path, resume=False, initial=None):
    if resume:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid():
                raise RuntimeError("Existing task token must be an owned regular mode-0600 file")
            token = stream.read(257).strip()
        if not 32 <= len(token) <= 256 or not all(c.isalnum() or c in "-_" for c in token):
            raise RuntimeError("Invalid existing task token format")
        return token
    token = initial or secrets.token_urlsafe(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token)
    return token


@contextlib.contextmanager
def gpu_admission(label, external_renderers=0):
    base = Path.home() / ".cache/gpu-slot"
    if (base / "PAUSED").exists():
        raise RuntimeError("Shared GPU admission paused")
    for name in ["locks", "holders", "queue"]:
        (base / name).mkdir(parents=True, exist_ok=True)
    if any((base / "queue").iterdir()):
        raise RuntimeError("Existing shared GPU waiters have priority")
    if any((base / "holders").glob("*.json")):
        raise RuntimeError("Existing GPU holder requires coordination")
    descriptors = []
    holder = base / "holders" / (str(os.getpid()) + ".json")
    try:
        perf = (base / "locks/perf.lock").open("a+")
        descriptors.append(perf)
        fcntl.flock(perf, fcntl.LOCK_SH | fcntl.LOCK_NB)
        slot = None
        reserved = []
        for index in range(2):
            fd = (base / "locks" / ("capture." + str(index) + ".lock")).open("a+")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fd.close()
                continue
            descriptors.append(fd)
            reserved.append(index)
            if slot is None:
                slot = index
            if not external_renderers:
                break
        if slot is None:
            raise RuntimeError("Shared GPU capture slots occupied")
        process_start = subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip()
        write_state(holder, {"pid": os.getpid(), "start": process_start,
                            "class": "capture", "label": label, "slot": str(slot),
                            "reserved_slots": reserved, "external_renderer_count": external_renderers,
                            "state": "warmup-and-resident-idle", "cmd": "tools/warmup_resident.py"})
        yield base
    finally:
        holder.unlink(missing_ok=True)
        for descriptor in reversed(descriptors):
            descriptor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-python", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--allow-warmup", action="store_true")
    parser.add_argument("--resume-stopped-session", action="store_true",
                        help="Explicit owner-requested restoration after a clean stop/reboot")
    parser.add_argument("--allow-one-existing-renderer", action="store_true",
                        help="Count and preserve one observed external renderer within shared admission")
    args = parser.parse_args()
    if not args.allow_warmup:
        parser.error("Warm-up needs current owner authorization and --allow-warmup")
    root = args.work_dir.resolve()
    receipt = root / "resident-state.json"
    if args.resume_stopped_session:
        previous = json.loads(receipt.read_text())
        if previous.get("status") != "stopped-by-request":
            raise RuntimeError("Resume requires a previously clean stopped-by-request receipt")
    model = root / "bf16/model"
    download = json.loads((root / "bf16/download-state.json").read_text())
    lock = json.loads((root / "QWEN-BF16-LOCK.json").read_text())
    if download["status"] != "complete" or download["revision"] != lock["revision"]:
        raise RuntimeError("Pinned download is not verified complete")
    if len(download["verified_files"]) != len(lock["files"]):
        raise RuntimeError("Incomplete artifact verification receipt")
    if set(download["dtype_counts"]) != {"BF16"}:
        raise RuntimeError("Verified weights are not all BF16")
    chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    hardware = subprocess.check_output(["sysctl", "-n", "hw.model"], text=True).strip()
    if chip != "Apple M5 Ultra" or hardware != "Mac17,15":
        raise RuntimeError("Refuse compute on a different machine")
    if psutil.virtual_memory().available < 100 * 1024 ** 3:
        raise RuntimeError("Insufficient pre-load memory headroom")
    external_renderers = 0
    for process in psutil.process_iter(["pid", "name", "cmdline", "exe"]):
        if process.pid == os.getpid():
            continue
        words = process.info["cmdline"] or []
        if any(word in ["mlx_vlm.server", "mlx_lm.server"] or Path(word).name == "llama-server" for word in words):
            raise RuntimeError("Existing inference process requires coordination")
        if renderer_process(process.info["exe"] or "", (process.info["name"] or "").lower(), words):
            external_renderers += 1
    if external_renderers > (1 if args.allow_one_existing_renderer else 0):
        raise RuntimeError("Existing renderer count exceeds explicitly admitted capacity")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 8027))
    stopped = threading.Event()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda *_: stopped.set())
    state = {"status": "starting", "supervisor_pid": os.getpid(), "host_role": "verified-M5-Ultra",
             "hardware": hardware, "chip": chip, "model_revision": lock["revision"],
             "precision": "BF16", "runtime": "mlx-vlm 0.7.4", "endpoint": "http://127.0.0.1:8027/v1",
             "game_loop": "held", "engine_launches": 0, "automatic_restarts": 0,
             "limits": {"minimum_available_GiB": 64, "maximum_swap_growth_MiB": 512,
                        "max_num_seqs": 1, "max_kv_size": 32768, "prefill_step_size": 2048}}
    child = None
    baseline_swap = psutil.swap_memory().used
    def memory_guard():
        available = psutil.virtual_memory().available
        swap = psutil.swap_memory().used
        state["memory"] = {"available_GiB": round(available / 1024 ** 3, 3),
                           "swap_used_GiB": round(swap / 1024 ** 3, 3),
                           "swap_growth_MiB": round(max(0, swap - baseline_swap) / 1024 ** 2, 3)}
        if available < 64 * 1024 ** 3 or swap - baseline_swap > 512 * 1024 ** 2:
            raise RuntimeError("New memory or swap guard triggered")
        console = subprocess.check_output(["stat", "-f", "%Su", "/dev/console"], text=True).strip()
        if console in ["root", "loginwindow", ""]:
            raise RuntimeError("Desktop session lost; pause compute")
        if child and child.poll() is not None:
            raise RuntimeError("Owned model server exited")
        live_renderers = sum(renderer_process(p.info["exe"] or "", (p.info["name"] or "").lower(),
                                             p.info["cmdline"] or [])
                             for p in psutil.process_iter(["exe", "name", "cmdline"]))
        if live_renderers > 1:
            raise RuntimeError("Additional renderer appeared; stop owned model to preserve capacity")
    with (root / "resident.lock").open("a+") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with gpu_admission("m5-qwen-gaming-bf16-warm-idle", external_renderers) as shared:
            try:
                env = os.environ.copy()
                # These are task-child settings only; no shared/system configuration changes.
                for key in list(env):
                    if key.startswith(("MLX_VLM_PRELOAD_", "MLX_VLM_DRAFT_", "KV_", "APC_")):
                        env.pop(key)
                env.update(PYTHONDONTWRITEBYTECODE="1", MLX_TRUST_REMOTE_CODE="false",
                           HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
                token_path = root / "server-access-token.txt"
                token = session_token(token_path, args.resume_stopped_session, env.get("MLX_VLM_SERVER_API_KEY"))
                env["MLX_VLM_SERVER_API_KEY"] = token
                def api(path, data=None, timeout=4):
                    request = urllib.request.Request("http://127.0.0.1:8027" + path,
                        data=json.dumps(data).encode() if data is not None else None,
                        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
                    with urllib.request.urlopen(request, timeout=timeout) as response:
                        return json.load(response)
                argv = [str(args.runtime_python.resolve()), "-B", "-m", "mlx_vlm.server",
                        "--host", "127.0.0.1", "--port", "8027", "--model", str(model),
                        "--model-dir", str(model), "--max-num-seqs", "1", "--max-kv-size", "32768",
                        "--prefill-step-size", "2048", "--enable-thinking", "--max-tokens", "8192",
                        "--vision-cache-size", "2", "--log-progress-interval", "32"]
                # Preserve the virtualenv interpreter path; resolving the executable would discard its packages.
                argv[0] = str(args.runtime_python.absolute())
                with (root / "model-server.log").open("ab") as log:
                    child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                             stdout=log, stderr=log, start_new_session=True)
                state["server_pid"] = child.pid
                write_state(receipt, state)
                deadline = time.monotonic() + 900
                healthy = None
                while not stopped.is_set() and time.monotonic() < deadline:
                    memory_guard()
                    try:
                        healthy = api("/health")
                    except (OSError, ValueError):
                        healthy = None
                    if healthy and healthy.get("loaded_model") == str(model):
                        break
                    write_state(receipt, state)
                    stopped.wait(2)
                else:
                    raise RuntimeError("Model preload did not finish within the warm-up window")
                loaded = [x for x in healthy.get("loaded_models", {}).values() if x.get("model")]
                if len(loaded) != 1 or healthy.get("loaded_tool_parser") != "qwen3_coder":
                    raise RuntimeError("Unexpected loaded model count or parser")
                state["status"] = "warming"
                state["health"] = {k: healthy.get(k) for k in ["status", "loaded_context_size",
                                  "configured_context_limit", "effective_context_limit", "loaded_tool_parser",
                                  "continuous_batching_enabled", "apc_enabled"]}
                write_state(receipt, state)
                result = {}
                payload = {"model": str(model), "messages": [{"role": "user",
                           "content": "Reply with exactly READY."}], "stream": False,
                           "enable_thinking": True, "reasoning_effort": "xhigh", "thinking_budget": 256,
                           "max_tokens": 512, "temperature": 1.0, "top_p": 0.95, "top_k": 20,
                           "min_p": 0.0, "presence_penalty": 0.0, "repetition_penalty": 1.0}
                def warm():
                    try:
                        result["response"] = api("/v1/chat/completions", payload, timeout=300)
                    except Exception as error:
                        result["error"] = type(error).__name__
                thread = threading.Thread(target=warm, daemon=True)
                thread.start()
                deadline = time.monotonic() + 315
                while thread.is_alive() and not stopped.is_set() and time.monotonic() < deadline:
                    memory_guard()
                    write_state(receipt, state)
                    stopped.wait(2)
                if thread.is_alive() or result.get("error"):
                    raise RuntimeError("Warm-up request failed or exceeded its deadline")
                response = result["response"]
                message = response["choices"][0]["message"]
                if (message.get("content") or "").strip().upper() != "READY":
                    raise RuntimeError("Warm-up final answer did not match the functional fixture")
                state["warmup"] = {"answer": message["content"], "thinking_enabled": True,
                    "reasoning_effort": "xhigh", "thinking_budget": 256, "max_tokens": 512,
                    "reasoning_content_returned": bool(message.get("reasoning_content")),
                    "finish_reason": response["choices"][0].get("finish_reason"),
                    "usage": response.get("usage"), "timings": response.get("timings")}
                state["status"] = "loaded-idle"
                while not stopped.is_set():
                    memory_guard()
                    if (shared / "PAUSED").exists():
                        raise RuntimeError("Shared GPU protocol paused")
                    healthy = api("/health")
                    loaded = [x for x in healthy.get("loaded_models", {}).values() if x.get("model")]
                    if len(loaded) != 1 or loaded[0]["model"] != str(model):
                        raise RuntimeError("Unexpected model replacement or additional model")
                    state["server_RSS_GiB"] = round(psutil.Process(child.pid).memory_info().rss / 1024 ** 3, 3)
                    write_state(receipt, state)
                    stopped.wait(10)
                state["status"] = "stopped-by-request"
            except Exception as error:
                state.update(status="stopped-on-fault", error=str(error), error_type=type(error).__name__)
            finally:
                # No relaunch path exists. Stop only the exact task-owned server.
                if child and child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=10)
                state["server_alive"] = bool(child and child.poll() is None)
                write_state(receipt, state)


if __name__ == "__main__":
    main()
