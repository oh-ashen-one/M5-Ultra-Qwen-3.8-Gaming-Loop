#!/usr/bin/env python3
"""Download and hash a pinned data-only artifact; never import MLX or load weights."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import time


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def digest_file(path, algorithm, prefix=b""):
    digest = hashlib.new(algorithm)
    digest.update(prefix)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text())
    root = args.work_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    model = root / "model"
    state = {"status": "preparing", "pid": os.getpid(), "repository": lock["repository"],
             "revision": lock["revision"], "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "verified_files": [], "inference": False}
    receipt = root / "download-state.json"
    with (root / "download.lock").open("a+") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
        atomic_json(receipt, state)
        try:
            paths = [item["path"] for item in lock["files"]]
            for name in paths:
                if Path(name).name != name or not name.endswith((".json", ".txt", ".jinja", ".md", ".safetensors")):
                    raise ValueError("Only flat model data files may be downloaded")
            if len(lock["revision"]) != 40:
                raise ValueError("A full immutable revision is required")
            # Retain 100 GiB beyond a full fresh artifact; never delete existing data.
            if shutil.disk_usage(root).free < lock["download_bytes"] + 100 * 1024 ** 3:
                raise RuntimeError("Insufficient disk headroom")
            os.environ["HF_HOME"] = str(root / "hf-cache")
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            from huggingface_hub import snapshot_download
            state["status"] = "downloading"
            atomic_json(receipt, state)
            for attempt in range(1, 4):
                state["attempt"] = attempt
                atomic_json(receipt, state)
                try:
                    snapshot_download(repo_id=lock["repository"], revision=lock["revision"],
                                      local_dir=model, allow_patterns=paths, token=False, max_workers=2)
                    break
                except Exception as error:
                    state["last_error"] = type(error).__name__  # Never log credential-bearing URLs.
                    atomic_json(receipt, state)
                    if attempt == 3:
                        raise RuntimeError("Download failed after three bounded attempts") from None
                    time.sleep(20)
            state["status"] = "verifying"
            atomic_json(receipt, state)
            dtype_counts = {}
            for item in lock["files"]:
                path = model / item["path"]
                if path.stat().st_size != item["size"]:
                    raise ValueError("File size mismatch: " + item["path"])
                if "sha256" in item:
                    actual = digest_file(path, "sha256")
                    if actual != item["sha256"]:
                        raise ValueError("SHA256 mismatch: " + item["path"])
                else:
                    prefix = ("blob " + str(item["size"]) + "\0").encode()
                    if digest_file(path, "sha1", prefix) != item["git_blob_sha1"]:
                        raise ValueError("Git blob mismatch: " + item["path"])
                    actual = digest_file(path, "sha256")
                if path.suffix == ".safetensors":
                    with path.open("rb") as stream:
                        length = struct.unpack("<Q", stream.read(8))[0]
                        if not 0 < length <= 16 * 1024 * 1024:
                            raise ValueError("Invalid safetensors header length")
                        header = json.loads(stream.read(length))
                    for name, tensor in header.items():
                        if name == "__metadata__":
                            continue
                        dtype = tensor["dtype"]
                        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
                    if any(tensor.get("dtype") != "BF16" for name, tensor in header.items() if name != "__metadata__"):
                        raise ValueError("A weight tensor is not BF16")
                state["verified_files"].append({"path": item["path"], "size": item["size"], "sha256": actual})
                atomic_json(receipt, state)
            config = json.loads((model / "config.json").read_text())
            if config.get("quantization") or config.get("quantization_config"):
                raise ValueError("Unexpected quantization metadata")
            if config.get("language_model_only") is not False or not config.get("vision_config"):
                raise ValueError("Vision component missing")
            state.update(status="complete", dtype_counts=dtype_counts,
                         finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            atomic_json(receipt, state)
            print("Pinned BF16 artifact verified; no model loaded.", flush=True)
        except Exception as error:
            state.update(status="failed", error_type=type(error).__name__,
                         finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            atomic_json(receipt, state)
            print("Download or verification failed: " + type(error).__name__, flush=True)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
