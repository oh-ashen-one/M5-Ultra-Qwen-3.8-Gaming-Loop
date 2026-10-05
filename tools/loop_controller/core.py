"""Durable state, mediated source edits, immutable evidence and progress views."""
import contextlib
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
import re
from pathlib import Path, PurePosixPath
import sqlite3
import time
import uuid


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode()


def atomic(path, value, raw=False, exclusive_target=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("xb") as out:
        out.write(value if raw else encode(value) + b"\n")
        out.flush()
        os.fsync(out.fileno())
    if exclusive_target:
        try:
            # Same-filesystem hard-link publication is atomic and fails if the
            # target exists, including an empty file or a concurrent creator.
            os.link(temp, path)
        finally:
            temp.unlink(missing_ok=True)
    else:
        temp.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_json(path):
    return json.loads(Path(path).read_text())


class Halt(RuntimeError):
    """A persisted, readable stop; never interpreted as successful completion."""


@contextlib.contextmanager
def exclusive(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a+") as fd:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise Halt("Another controller already owns this run") from error
        yield


class Store:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "state.sqlite3", timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, at TEXT, kind TEXT, data TEXT);
          CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, kind TEXT, status TEXT,
                                            request TEXT, result TEXT, updated TEXT);
        """)

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, **values):
        with self.db:
            for key, value in values.items():
                self.db.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (key, json.dumps(value)))

    def event(self, kind, **data):
        with self.db:
            self.db.execute("INSERT INTO events(at,kind,data) VALUES (?,?,?)", (now(), kind, json.dumps(data)))

    def begin_action(self, action_id, kind, request):
        row = self.db.execute("SELECT status,request,result FROM actions WHERE id=?", (action_id,)).fetchone()
        if row:
            if json.loads(row[1]) != request:
                raise Halt("Action identity collision")
            return row[0], json.loads(row[2]) if row[2] else None
        with self.db:
            self.db.execute("INSERT INTO actions VALUES (?,?, 'pending',?,NULL,?)",
                            (action_id, kind, json.dumps(request), now()))
        return "new", None

    def finish_action(self, action_id, result):
        with self.db:
            self.db.execute("UPDATE actions SET status='complete',result=?,updated=? WHERE id=?",
                            (json.dumps(result), now(), action_id))

    def incomplete(self):
        return [{"id": a, "kind": k, "request": json.loads(r)} for a, k, r in self.db.execute(
            "SELECT id,kind,request FROM actions WHERE status='pending'")]

    def status(self):
        return {key: json.loads(value) for key, value in self.db.execute("SELECT key,value FROM state")}

    def report(self):
        data = self.status()
        if (self.root / "publish-receipt.json").exists():
            data["publication"] = read_json(self.root / "publish-receipt.json")
        data["reported_utc"] = now()
        data["elapsed_seconds"] = round(time.time() - data.get("started_epoch", time.time()))
        last_progress = data.get("last_accepted_epoch", data.get("started_epoch", time.time()))
        data["seconds_since_accepted_progress"] = round(time.time() - last_progress)
        data["seconds_since_verified_subfeature"] = round(time.time() - data.get("last_verified_progress_epoch",data.get("started_epoch",time.time())))
        # Private role histories, tokens, responses and absolute paths never enter this view.
        atomic(self.root / "status.json", data)
        lines = ["# Chicago local game loop", "", "Status: " + str(data.get("status", "prepared")),
                 "Updated: " + data["reported_utc"], "Phase: " + str(data.get("phase", "preparation")),
                 "Current task: " + str(data.get("current_task", "none")),
                 "Accepted checkpoint: " + str(data.get("accepted_checkpoint", "none")),
                 "Verified limited subfeatures: " + ", ".join(data.get("accepted_subfeatures", {})),
                 "Playable coverage: " + str(data.get("playable_coverage", "unverified")),
                 "Next: " + str(data.get("next_task", "none")),
                 "Blocker: " + str(data.get("blocker", "none")), "",
                 "Actual evidence: " + str(data.get("latest_evidence", "none")),
                 "Reference images are aspirational targets, not game output.", "",
                 "Cloud manager: parent dot; existing ten-minute oversight. No duplicate schedule."]
        atomic(self.root / "PROGRESS.md", ("\n".join(lines) + "\n").encode(), raw=True)
        pictures = "".join('<figure><img width="640" src="' + html.escape(p, quote=True) +
                           '"><figcaption>Actual Unity capture</figcaption></figure>'
                           for p in data.get("latest_captures", []))
        page = ("<!doctype html><meta charset=utf-8><title>Chicago loop progress</title>"
                "<style>body{font:16px system-ui;max-width:1000px;margin:3em auto;background:#10151c;color:#eee}"
                "pre{white-space:pre-wrap}img{max-width:100%}a{color:#97cdfd}</style>"
                "<h1>Chicago local game loop</h1><pre>" + html.escape("\n".join(lines[2:])) +
                "</pre>" + pictures + "<p>Open status.json for machine-readable state. No web server is required.</p>")
        atomic(self.root / "progress.html", page.encode(), raw=True)
        return data


class Files:
    """Only original runtime C#, Blender scripts and brief notes are model-writable."""
    def __init__(self, root, store):
        self.root = Path(root).resolve()
        self.store = store

    def path(self, relative, write=False):
        p = PurePosixPath(relative)
        if not relative or p.is_absolute() or any(v in ("", ".", "..") for v in relative.split("/")):
            raise ValueError("Use a canonical project-relative path")
        if any(v.startswith(".") or v == "Editor" for v in p.parts):
            raise ValueError("Hidden files and Editor code are outside builder access")
        path = self.root.joinpath(*p.parts)
        if any(v.is_symlink() for v in [path, *path.parents] if v != self.root.parent):
            raise ValueError("Symlinks are outside builder access")
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("Path escape")
        if write and not ((relative.startswith("Assets/Game/") and p.suffix == ".cs") or
                          (relative.startswith("Art/") and p.suffix in (".py", ".json")) or
                          (relative.startswith("Notes/") and p.suffix == ".md")):
            raise ValueError("Only Assets/Game/*.cs, Art/*.py|json and Notes/*.md are writable")
        return path

    def tree(self):
        return [{"path": str(p.relative_to(self.root)), "bytes": p.stat().st_size}
                for p in sorted(self.root.rglob("*")) if p.is_file() and not p.is_symlink()
                and p.parts[len(self.root.parts)] in ("Assets", "Art", "ArtSources", "Notes", "Packages", "ProjectSettings")
                and p.suffix != ".meta"][:1500]

    def read(self, path, start_line=1, line_count=140):
        p = self.path(path)
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        if not 1 <= start_line or not 1 <= line_count <= 300:
            raise ValueError("Invalid source range")
        lines = text.splitlines(keepends=True)
        selected = "".join(lines[start_line-1:start_line-1+line_count])
        if len(selected.encode()) > 24000:
            raise ValueError("Range too large; request a narrower exact range")
        return {"path": path, "sha256": sha(raw), "total_lines": len(lines),
                "start_line": start_line, "content": selected, "complete": start_line == 1 and line_count >= len(lines)}

    def create(self, action_id, path, content):
        p = self.path(path, write=True)
        if not isinstance(content, str) or len(content.encode()) > 100000:
            raise ValueError("Source must be text at most 100 KB; split large modules")
        desired = content.encode()
        request = {"path": path, "before": "absent", "after": sha(desired)}
        status, saved = self.store.begin_action(action_id, "source-create", request)
        if status == "complete":
            if saved.get("ok") and (not p.is_file() or sha(p.read_bytes()) != request["after"]):
                raise Halt("Completed creation no longer matches its recorded output")
            return saved
        if p.exists():
            if status == "pending" and p.is_file() and sha(p.read_bytes()) == request["after"]:
                result = {"ok": True, "path": path, "sha256": request["after"], "reconciled": True}
            else:
                self.store.finish_action(action_id, {"ok": False, "error": "Path already exists; use hash-checked editing"})
                raise ValueError("Path already exists; read its exact hash and use write_file or replace_text")
        else:
            try: atomic(p, desired, raw=True, exclusive_target=True)
            except FileExistsError as error:
                self.store.finish_action(action_id, {"ok": False, "error": "Concurrent creation; no overwrite"})
                raise ValueError("Path was created concurrently; no overwrite occurred") from error
            result = {"ok": True, "path": path, "sha256": request["after"]}
        self.store.finish_action(action_id, result)
        self.store.event("local-source-edit", **request)
        return result

    def edit(self, action_id, path, expected_sha256, content=None, old=None, new=None):
        p = self.path(path, write=True)
        before = p.read_bytes() if p.exists() else b""
        if content is None:
            text = before.decode()
            if not old or text.count(old) != 1:
                raise ValueError("Targeted replacement requires one exact nonempty match")
            content = text.replace(old, new, 1)
        if not isinstance(content, str) or len(content.encode()) > 100000:
            raise ValueError("Source must be text at most 100 KB; split large modules")
        desired = content.encode()
        request = {"path": path, "before": expected_sha256, "after": sha(desired)}
        status, saved = self.store.begin_action(action_id, "source-edit", request)
        if status == "complete":
            if sha(before) != request["after"]:
                raise Halt("Completed edit no longer matches its recorded output")
            return saved
        if sha(before) == request["after"] and status == "pending":
            result = {"ok": True, "path": path, "sha256": request["after"], "reconciled": True}
        else:
            if sha(before) != expected_sha256:
                raise ValueError("Stale hash; re-read exact current source before editing")
            atomic(p, desired, raw=True)
            result = {"ok": True, "path": path, "sha256": sha(desired)}
        self.store.finish_action(action_id, result)
        self.store.event("local-source-edit", **request)
        return result


def seal(directory, metadata):
    directory = Path(directory)
    entries = []
    for base, dirs, names in os.walk(directory):
        # Engine caches/builds have their own build digest and source commit;
        # only durable observation records belong in this evidence manifest.
        dirs[:] = sorted(d for d in dirs if d not in ("project", "build", "tmp"))
        for name in sorted(names):
            p = Path(base) / name
            if p.is_symlink():
                raise Halt("Evidence contains a symlink")
            if p.is_file() and p != directory / "manifest.json":
                entries.append({"path": str(p.relative_to(directory)), "bytes": p.stat().st_size,
                                "sha256": sha(p.read_bytes())})
    value = {**metadata, "sealed_utc": now(), "excluded_regenerable_dirs": ["project", "build", "tmp"], "files": entries}
    atomic(directory / "manifest.json", value)
    return sha((directory / "manifest.json").read_bytes())


def verify_seal(directory, expected):
    directory = Path(directory)
    if sha((directory / "manifest.json").read_bytes()) != expected:
        raise Halt("Evidence manifest changed")
    manifest = read_json(directory / "manifest.json")
    for item in manifest["files"]:
        path = directory / item["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()) or not path.is_file():
            raise Halt("Evidence path invalid or missing")
        if sha(path.read_bytes()) != item["sha256"]:
            raise Halt("Evidence bytes changed: " + item["path"])
    return manifest


def failure_key(error):
    # Callers supply stable failure classes/metrics, not per-run paths or timestamps.
    text = encode(error).decode()
    text = re.sub(r'r\d{4}-[a-f0-9]{8}', '<round>', text)
    text = re.sub(r'/[^\s"\\]*/Assets/', 'Assets/', text)
    return sha(text.encode())
