#!/usr/bin/env python3
"""Lightweight secret scanner for source trees and CI (read-only).

Regex-based detection of common credential patterns. Meant as a dependency-free
fallback / pre-commit gate; for production use, pair with gitleaks or trufflehog.

Skips binary files, common vendor/build dirs, and respects a simple allowlist
of substrings via --ignore.

Usage:
    python secrets_scan.py .
    python secrets_scan.py src/ --ignore EXAMPLE_KEY --ignore dummy
Exit: 0 clean, 2 potential secrets found, 3 error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.common import Report, emit, Level  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__",
             ".venv", "venv", ".terraform", ".mypy_cache"}
MAX_BYTES = 2 * 1024 * 1024  # skip files >2MB

# (name, compiled regex). Patterns favor precision to limit false positives.
PATTERNS = [
    ("AWS Access Key ID", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("AWS Secret Access Key", re.compile(r"(?i)aws.{0,20}?['\"][0-9a-zA-Z/+]{40}['\"]")),
    ("GCP Service Account key", re.compile(r'"type"\s*:\s*"service_account"')),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("Azure client secret (assignment)", re.compile(r"(?i)(client_secret|clientsecret)\s*[=:]\s*['\"][^'\"]{16,}['\"]")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("Generic secret assignment", re.compile(
        r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[=:]\s*['\"][^'\"\s]{8,}['\"]")),
]

# Reduce noise: obvious placeholders.
PLACEHOLDER = re.compile(r"(?i)(example|dummy|changeme|placeholder|xxxx|<[^>]+>|\$\{)")


def is_probably_text(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(1024)
        return b"\x00" not in chunk
    except OSError:
        return False


def scan_file(path: Path, ignores: list[str]) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        if any(ig in line for ig in ignores):
            continue
        for name, rx in PATTERNS:
            if rx.search(line):
                if PLACEHOLDER.search(line) and name == "Generic secret assignment":
                    continue
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:117] + "…"
                hits.append((lineno, name, snippet))
                break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="Lightweight secret scanner")
    ap.add_argument("root", type=Path)
    ap.add_argument("--ignore", action="append", default=[],
                    help="Substring; lines containing it are skipped (repeatable)")
    args = ap.parse_args()

    if not args.root.exists():
        emit(Level.FAIL, f"Path not found: {args.root}")
        return 3

    rep = Report()
    scanned = 0
    files = [args.root] if args.root.is_file() else args.root.rglob("*")
    for path in files:
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES or not is_probably_text(path):
                continue
        except OSError:
            continue
        scanned += 1
        for lineno, name, snippet in scan_file(path, args.ignore):
            rep.fail(f"{path}:{lineno} — {name}: {snippet}")

    emit(Level.INFO, f"Scanned {scanned} text file(s).")
    if rep.exit_code == 0:
        rep.ok("No secrets detected by built-in patterns.")
    else:
        emit(Level.INFO, "Review hits; add --ignore for confirmed false positives.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
