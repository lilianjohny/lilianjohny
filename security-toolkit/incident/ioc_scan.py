#!/usr/bin/env python3
"""Hunt for Indicators of Compromise (IOCs) across a directory tree.

Given an IOC list (hashes, IPs, domains, or literal strings), scan files and
report matches. Read-only. Useful during incident response and threat hunting.

IOC file format: one indicator per line. Blank lines and '#' comments ignored.
Indicators are auto-classified:
    - 64 hex chars      -> SHA-256 (matched against file hashes)
    - 32 hex chars      -> MD5     (matched against file hashes)
    - looks like IP     -> substring match in file contents
    - otherwise         -> substring match (domain / string)

Usage:
    python ioc_scan.py /path/to/scan --iocs iocs.txt
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report, emit, Level  # noqa: E402

IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")
MAX_CONTENT_BYTES = 5 * 1024 * 1024  # skip content match on files >5MB


def load_iocs(path: Path) -> tuple[set[str], set[str], list[str]]:
    sha, md5, strings = set(), set(), []
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if HEX64.match(line):
            sha.add(line.lower())
        elif HEX32.match(line):
            md5.add(line.lower())
        else:
            strings.append(line.lower())
    return sha, md5, strings


def hash_file(path: Path) -> tuple[str, str]:
    s, m = hashlib.sha256(), hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            s.update(chunk)
            m.update(chunk)
    return s.hexdigest(), m.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="IOC scanner")
    ap.add_argument("root", type=Path)
    ap.add_argument("--iocs", type=Path, required=True)
    args = ap.parse_args()

    if not args.iocs.exists():
        emit(Level.FAIL, f"IOC file not found: {args.iocs}")
        return 3

    sha_iocs, md5_iocs, str_iocs = load_iocs(args.iocs)
    emit(Level.INFO,
         f"Loaded {len(sha_iocs)} SHA256, {len(md5_iocs)} MD5, "
         f"{len(str_iocs)} string indicators.")

    rep = Report()
    scanned = 0
    for path in args.root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        scanned += 1
        try:
            if sha_iocs or md5_iocs:
                sd, md = hash_file(path)
                if sd in sha_iocs:
                    rep.fail(f"SHA256 IOC match: {path} ({sd})")
                if md in md5_iocs:
                    rep.fail(f"MD5 IOC match: {path} ({md})")
            if str_iocs and path.stat().st_size <= MAX_CONTENT_BYTES:
                data = path.read_bytes().lower()
                for needle in str_iocs:
                    if needle.encode() in data:
                        rep.fail(f"String IOC '{needle}' found in {path}")
        except (OSError, PermissionError):
            rep.warn(f"Could not read {path}")

    emit(Level.INFO, f"Scanned {scanned} files.")
    if rep.exit_code == 0:
        rep.ok("No IOC matches found.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
