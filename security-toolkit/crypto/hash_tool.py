#!/usr/bin/env python3
"""Compute and verify file hashes (integrity / evidence handling).

Usage:
    python hash_tool.py hash file1 file2 ...            # print hashes
    python hash_tool.py hash file1 --algo sha1
    python hash_tool.py verify file1 --expected <hexdigest>
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import emit, Level  # noqa: E402

ALGOS = ("md5", "sha1", "sha256", "sha512")


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="File hashing utility")
    sub = ap.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("hash")
    h.add_argument("files", nargs="+", type=Path)
    h.add_argument("--algo", choices=ALGOS, default="sha256")

    v = sub.add_parser("verify")
    v.add_argument("file", type=Path)
    v.add_argument("--expected", required=True)
    v.add_argument("--algo", choices=ALGOS, default="sha256")

    args = ap.parse_args()

    if args.cmd == "hash":
        rc = 0
        for f in args.files:
            if not f.exists():
                emit(Level.FAIL, f"Not found: {f}")
                rc = 3
                continue
            print(f"{digest(f, args.algo)}  {f}")
        return rc

    # verify
    if not args.file.exists():
        emit(Level.FAIL, f"Not found: {args.file}")
        return 3
    actual = digest(args.file, args.algo)
    if actual.lower() == args.expected.strip().lower():
        emit(Level.OK, f"MATCH ({args.algo}): {args.file}")
        return 0
    emit(Level.FAIL, f"MISMATCH ({args.algo}): {args.file}")
    emit(Level.INFO, f"expected {args.expected.lower()}")
    emit(Level.INFO, f"actual   {actual}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
