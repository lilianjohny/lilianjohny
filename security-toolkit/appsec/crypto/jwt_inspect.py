#!/usr/bin/env python3
"""Inspect a JWT for common security weaknesses (read-only, no network).

Decodes the header and payload (does NOT verify the signature — you need the
key for that) and flags issues:
  - alg = "none"  (unsigned token accepted)
  - Weak/symmetric alg where asymmetric expected (HS256 vs RS256 confusion risk)
  - Missing or past 'exp' (no/So expired expiry)
  - Missing 'iat' / 'nbf'
  - Overly long lifetime (exp - iat)
  - Sensitive-looking claims in the payload (password, secret, ssn, card)

Usage:
    python jwt_inspect.py <token>
    echo "$JWT" | python jwt_inspect.py --stdin
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

SENSITIVE = re.compile(r"(?i)(password|passwd|secret|ssn|social|card|cvv|pan|private_key)")
MAX_LIFETIME_HOURS = 24


def b64url_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def main() -> int:
    ap = argparse.ArgumentParser(description="JWT security inspector")
    ap.add_argument("token", nargs="?")
    ap.add_argument("--stdin", action="store_true")
    args = ap.parse_args()

    token = (sys.stdin.readline().strip() if args.stdin else args.token) or ""
    token = token.strip().strip('"').replace("Bearer ", "")
    parts = token.split(".")
    if len(parts) not in (2, 3):
        emit(Level.FAIL, "Not a JWT (expected header.payload[.signature]).")
        return 3

    rep = Report()
    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError) as exc:
        emit(Level.FAIL, f"Could not decode token: {exc}")
        return 3

    alg = str(header.get("alg", "")).lower()
    emit(Level.INFO, f"Header: alg={header.get('alg')} typ={header.get('typ')} kid={header.get('kid', '-')}")

    if alg == "none":
        rep.fail("alg=none — token is unsigned; reject these server-side.")
    elif alg.startswith("hs"):
        rep.warn(f"Symmetric alg ({header.get('alg')}). Ensure the server does not accept "
                 "HS* when it expects RS*/ES* (algorithm-confusion attack).")
    elif alg == "":
        rep.warn("No 'alg' in header.")

    if len(parts) == 2 or not parts[2]:
        rep.fail("Token has no signature segment.")

    now = dt.datetime.now(dt.timezone.utc).timestamp()
    exp = payload.get("exp")
    iat = payload.get("iat")
    if exp is None:
        rep.fail("No 'exp' claim — token never expires.")
    elif exp < now:
        rep.info(f"Token is expired (exp {int(now - exp)}s ago).")
    if iat is None:
        rep.warn("No 'iat' claim.")
    if "nbf" not in payload:
        rep.info("No 'nbf' (not-before) claim.")
    if exp and iat and (exp - iat) > MAX_LIFETIME_HOURS * 3600:
        rep.warn(f"Long token lifetime ({(exp - iat) / 3600:.1f}h > {MAX_LIFETIME_HOURS}h).")

    for k in payload:
        if SENSITIVE.search(str(k)):
            rep.fail(f"Sensitive-looking claim in payload: '{k}' (JWT payload is not encrypted).")

    emit(Level.INFO, f"Claims: {', '.join(sorted(map(str, payload)))[:200]}")
    if rep.exit_code == 0:
        rep.ok("No obvious JWT weaknesses (signature NOT verified — validate with the key).")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
