#!/usr/bin/env python3
"""File Integrity Monitoring (FIM): baseline files, then detect changes.

Stores SHA-256 hashes of files under one or more directories in a JSON
manifest. On later runs, compares current state to the manifest and reports
added / modified / removed files.

Usage:
    # Create baseline
    python integrity_check.py baseline /etc --out etc.fim.json

    # Later, check for drift
    python integrity_check.py check /etc --manifest etc.fim.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report, emit, Level  # noqa: E402


def sha256(path: Path) -> str | None:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()


def walk(roots: list[Path]) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for root in roots:
        if root.is_file():
            digest = sha256(root)
            if digest:
                manifest[str(root.resolve())] = digest
            continue
        for p in root.rglob("*"):
            if p.is_file() and not p.is_symlink():
                digest = sha256(p)
                if digest:
                    manifest[str(p.resolve())] = digest
    return manifest


def cmd_baseline(args) -> int:
    roots = [Path(p) for p in args.paths]
    manifest = walk(roots)
    out = Path(args.out)
    out.write_text(json.dumps({"files": manifest}, indent=2, sort_keys=True))
    emit(Level.OK, f"Baseline written: {out} ({len(manifest)} files)")
    return 0


def cmd_check(args) -> int:
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        emit(Level.FAIL, f"Manifest not found: {manifest_path}")
        return 3
    baseline = json.loads(manifest_path.read_text()).get("files", {})
    current = walk([Path(p) for p in args.paths])

    rep = Report()
    base_keys, cur_keys = set(baseline), set(current)

    for path in sorted(cur_keys - base_keys):
        rep.warn(f"ADDED    {path}")
    for path in sorted(base_keys - cur_keys):
        rep.fail(f"REMOVED  {path}")
    for path in sorted(base_keys & cur_keys):
        if baseline[path] != current[path]:
            rep.fail(f"MODIFIED {path}")

    if rep.exit_code == 0:
        rep.ok("No integrity drift detected.")
    rep.summary()
    return rep.exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description="File integrity monitoring")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baseline", help="Create a baseline manifest")
    b.add_argument("paths", nargs="+")
    b.add_argument("--out", default="fim.json")
    b.set_defaults(func=cmd_baseline)

    c = sub.add_parser("check", help="Check current state against a manifest")
    c.add_argument("paths", nargs="+")
    c.add_argument("--manifest", default="fim.json")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
