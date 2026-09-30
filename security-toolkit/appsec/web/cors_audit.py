#!/usr/bin/env python3
"""Detect CORS misconfigurations on a target you are authorized to test.

Sends requests with crafted Origin headers and inspects the
Access-Control-Allow-* response headers for unsafe patterns:
  - Reflected arbitrary Origin + credentials (account-takeover class)
  - Access-Control-Allow-Origin: * combined with credentials
  - Trust of 'null' origin
  - Overly broad trusted-origin reflection

Usage:
    python cors_audit.py https://api.example.com/endpoint
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, confirm_authorized  # noqa: E402

try:
    import requests
except ImportError:
    print("Needs 'requests' (pip install requests).", file=sys.stderr)
    raise SystemExit(3)

EVIL = "https://evil.example.org"


def probe(url: str, origin: str, timeout: float, verify: bool) -> dict:
    try:
        r = requests.get(url, headers={"Origin": origin}, timeout=timeout,
                        verify=verify, allow_redirects=True)
        return {k.lower(): v for k, v in r.headers.items()}
    except requests.RequestException as exc:
        return {"__error__": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser(description="CORS misconfiguration auditor")
    ap.add_argument("url")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--insecure", action="store_true")
    args = ap.parse_args()

    confirm_authorized(args.url)
    rep = Report()
    verify = not args.insecure

    # 1. Reflected arbitrary origin
    h = probe(args.url, EVIL, args.timeout, verify)
    if "__error__" in h:
        rep.fail(f"Request failed: {h['__error__']}")
        rep.summary()
        return rep.exit_code
    acao = h.get("access-control-allow-origin")
    acac = h.get("access-control-allow-credentials", "").lower()

    if acao == EVIL:
        if acac == "true":
            rep.fail("Reflects arbitrary Origin AND allows credentials — "
                     "critical CORS misconfig (cross-origin data theft).")
        else:
            rep.warn("Reflects arbitrary Origin (credentials not allowed, lower risk).")
    if acao == "*" and acac == "true":
        rep.fail("ACAO '*' with Allow-Credentials true (invalid + unsafe).")

    # 2. null origin trust
    h2 = probe(args.url, "null", args.timeout, verify)
    if h2.get("access-control-allow-origin") == "null":
        rep.warn("Trusts the 'null' origin (reachable from sandboxed iframes/data URIs).")

    # 3. Report the observed baseline
    if acao and acao not in (EVIL, "null"):
        rep.info(f"Access-Control-Allow-Origin: {acao}")
    if not acao:
        rep.ok("No Access-Control-Allow-Origin reflected for foreign origins.")

    if rep.exit_code == 0:
        rep.ok("No unsafe CORS behavior detected.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
