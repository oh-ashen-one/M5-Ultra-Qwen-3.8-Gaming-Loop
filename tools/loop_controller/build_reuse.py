"""In-owner compiled artifact reuse; every scenario still launches a fresh player."""
import json
import os
from pathlib import Path
import shutil
import stat
from .core import Halt, atomic, sha


def tree_digest(root):
    root = Path(root)
    records = []
    for p in sorted(root.rglob('*')):
        mode = stat.S_IMODE(p.lstat().st_mode)
        if p.is_symlink():
            if not p.resolve().is_relative_to(root.resolve()):
                raise Halt('Build reuse refuses links outside the artifact')
            record = dict(link=os.readlink(p))
        elif p.is_file():
            record = dict(sha256=sha(p.read_bytes()))
        elif p.is_dir():
            record = dict(directory=True)
        else:
            raise Halt('Build reuse requires regular files and directories')
        records.append(dict(path=str(p.relative_to(root)), mode=mode, **record))
    return sha(json.dumps(records, sort_keys=True).encode())


def build_key(project, editor, candidate):
    editor = Path(editor)
    return sha(json.dumps(dict(source=tree_digest(project), candidate=candidate,
        editor=str(editor.resolve()), editor_sha256=sha(editor.read_bytes())), sort_keys=True).encode())


class BuildReuse:
    def __init__(self):
        self.records = {}

    def remember(self, key, build):
        build = Path(build)
        app = build / 'ChicagoLocalSlice.app'
        self.records[key] = dict(build=build, app_hash=tree_digest(app),
            result_hash=sha((build / 'build-result.json').read_bytes()),
            log_hash=sha((build / 'unity-build.log').read_bytes()))

    def restore(self, key, build):
        record = self.records.get(key)
        if record is None:
            return False
        source = record['build']; build = Path(build)
        if (tree_digest(source / 'ChicagoLocalSlice.app') != record['app_hash']
            or sha((source / 'build-result.json').read_bytes()) != record['result_hash']
            or sha((source / 'unity-build.log').read_bytes()) != record['log_hash']):
            raise Halt('Previously qualified compiled artifact changed')
        shutil.copytree(source / 'ChicagoLocalSlice.app', build / 'ChicagoLocalSlice.app', symlinks=True)
        for name in ('build-result.json', 'unity-build.log'):
            shutil.copy2(source / name, build / name)
        if tree_digest(build / 'ChicagoLocalSlice.app') != record['app_hash']:
            raise Halt('Reused compiled artifact copy differs')
        atomic(build / 'build-reuse.json', dict(key=key, source_bundle=source.parent.name,
            artifact_sha256=record['app_hash'], compile_reused=True, runtime_evidence_reused=False))
        return True
