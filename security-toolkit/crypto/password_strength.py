#!/usr/bin/env python3
"""Estimate password strength via entropy and common-weakness checks.

Educational / policy-testing tool. Reads a password interactively (never
echoed) or from --stdin. Does NOT transmit the password anywhere.

Usage:
    python password_strength.py            # prompt (hidden)
    echo 'p@ss' | python password_strength.py --stdin
"""
from __future__ import annotations

import argparse
import getpass
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import emit, Level  # noqa: E402

COMMON = {
    "password", "123456", "123456789", "qwerty", "abc123", "password1",
    "111111", "letmein", "admin", "welcome", "monkey", "iloveyou", "dragon",
}


def charset_size(pw: str) -> int:
    size = 0
    if re.search(r"[a-z]", pw): size += 26
    if re.search(r"[A-Z]", pw): size += 26
    if re.search(r"\d", pw): size += 10
    if re.search(r"[^A-Za-z0-9]", pw): size += 32
    return size or 1


def entropy_bits(pw: str) -> float:
    return len(pw) * math.log2(charset_size(pw))


def assess(pw: str) -> int:
    if not pw:
        emit(Level.FAIL, "Empty password.")
        return 2

    bits = entropy_bits(pw)
    emit(Level.INFO, f"Length: {len(pw)}  Estimated entropy: {bits:.1f} bits")

    issues = []
    if pw.lower() in COMMON:
        issues.append("appears in a common-password list")
    if len(pw) < 12:
        issues.append("shorter than 12 characters")
    if pw.isalpha():
        issues.append("letters only")
    if pw.isdigit():
        issues.append("digits only")
    if re.search(r"(.)\1\1", pw):
        issues.append("contains a run of 3+ repeated characters")
    if re.search(r"(0123|1234|2345|abcd|qwer)", pw.lower()):
        issues.append("contains a common sequence")

    for i in issues:
        emit(Level.WARN, f"Weakness: {i}")

    if bits >= 80 and not issues:
        emit(Level.OK, "Strong.")
        return 0
    if bits >= 60 and len(issues) <= 1:
        emit(Level.WARN, "Moderate — could be stronger (aim for 80+ bits, 16+ chars).")
        return 1
    emit(Level.FAIL, "Weak. Use a longer passphrase or a password manager.")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Password strength estimator")
    ap.add_argument("--stdin", action="store_true",
                    help="Read password from stdin instead of prompting")
    args = ap.parse_args()

    if args.stdin:
        pw = sys.stdin.readline().rstrip("\n")
    else:
        pw = getpass.getpass("Password (hidden): ")
    return assess(pw)


if __name__ == "__main__":
    raise SystemExit(main())
