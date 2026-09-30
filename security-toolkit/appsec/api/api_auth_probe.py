#!/usr/bin/env python3
"""Probe API endpoints for broken authorization (BOLA/BFLA) — authorized only.

Given a list of endpoints and (optionally) two tokens for two different users,
this checks the OWASP API Security Top 10 "Broken Object/Function Level
Authorization" classes:

  - Unauthenticated access: does the endpoint respond 2xx with NO token?
  - Cross-user access (BOLA): can user A's token read a resource owned by B?
    (You supply paths that reference B's object ids.)

This is a lightweight assist, not a full DAST. It only sends the requests you
define. Run ONLY against systems you are authorized to test.

Endpoints file (JSON):
  [
    {"method":"GET","path":"/api/users/{OTHER_ID}/profile","expect_denied":true},
    {"method":"GET","path":"/api/admin/metrics","expect_denied":true}
  ]

Usage:
  python api_auth_probe.py --base https://api.example.com --endpoints eps.json \
      --token-a "$TOKEN_A"  [--token-b "$TOKEN_B"]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, confirm_authorized, emit, Level  # noqa: E402

try:
    import requests
except ImportError:
    print("Needs 'requests' (pip install requests).", file=sys.stderr)
    raise SystemExit(3)


def call(base: str, ep: dict, token: str | None, timeout: float, verify: bool):
    url = base.rstrip("/") + "/" + ep["path"].lstrip("/")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return requests.request(ep.get("method", "GET"), url, headers=headers,
                                timeout=timeout, verify=verify, allow_redirects=False)
    except requests.RequestException as exc:
        return exc


def main() -> int:
    ap = argparse.ArgumentParser(description="API broken-authorization probe")
    ap.add_argument("--base", required=True)
    ap.add_argument("--endpoints", type=Path, required=True)
    ap.add_argument("--token-a", default=None)
    ap.add_argument("--token-b", default=None)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--insecure", action="store_true")
    args = ap.parse_args()

    if not args.endpoints.exists():
        emit(Level.FAIL, f"Endpoints file not found: {args.endpoints}")
        return 3
    confirm_authorized(args.base)
    endpoints = json.loads(args.endpoints.read_text())
    verify = not args.insecure
    rep = Report()

    for ep in endpoints:
        label = f"{ep.get('method','GET')} {ep['path']}"
        # 1. Unauthenticated access
        r = call(args.base, ep, None, args.timeout, verify)
        if isinstance(r, Exception):
            rep.warn(f"{label}: request error ({r}).")
            continue
        if r.status_code < 400 and ep.get("expect_denied", True):
            rep.fail(f"{label}: reachable WITHOUT authentication (HTTP {r.status_code}).")
        else:
            rep.ok(f"{label}: unauthenticated request denied (HTTP {r.status_code}).")

        # 2. Cross-user (BOLA) with token A against B's resources
        if args.token_a and ep.get("expect_denied", True):
            ra = call(args.base, ep, args.token_a, args.timeout, verify)
            if not isinstance(ra, Exception) and ra.status_code < 400:
                rep.fail(f"{label}: user A's token accessed a resource expected to be denied "
                         f"(HTTP {ra.status_code}) — possible BOLA/BFLA.")

    if rep.exit_code == 0:
        rep.ok("No broken-authorization behavior observed for the defined endpoints.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
