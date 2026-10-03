"""Read-only source/license manifest check. No vendor execution or network calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    vendor = root / "reference" / "vendor"
    manifest = json.loads((root / "reference" / "IMPORT-MANIFEST.json").read_text())
    components = manifest.get("components", [])
    errors: list[str] = []
    expected: set[str] = set()
    if manifest.get("schema_version") != 1 or not components:
        errors.append("Invalid or empty import manifest")
    for component in components:
        if not re.fullmatch(r"[0-9a-f]{40}", component.get("commit", "")):
            errors.append(f"{component.get('id')}: missing exact upstream commit")
        if component.get("status") != "unintegrated-untested-reference":
            errors.append(f"{component.get('id')}: qualification status requires review")
        entries = [component.get("license_file", {})] + component.get("files", [])
        for entry in entries:
            relative = entry.get("path", "")
            path = root / relative
            if not relative or not path.resolve().is_relative_to(vendor.resolve()):
                errors.append(f"Unsafe or missing manifest path: {relative}")
                continue
            expected.add(relative)
            if path.is_symlink() or not path.is_file():
                errors.append(f"Missing file or symlink: {relative}")
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != entry.get("sha256"):
                errors.append(f"Hash mismatch: {relative}")
        license_path = root / component.get("license_file", {}).get("path", "")
        if license_path.is_file() and "Permission is hereby granted" not in license_path.read_text():
            errors.append(f"{component.get('id')}: full MIT permission notice missing")
    actual = {str(path.relative_to(root)) for path in vendor.rglob("*") if path.is_file()}
    for relative in sorted(actual - expected):
        errors.append(f"Unregistered vendor file: {relative}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(components)} pinned components; {len(expected)} source/notice hashes match.")
    print("This is a source-integrity check, not engine or gameplay qualification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
