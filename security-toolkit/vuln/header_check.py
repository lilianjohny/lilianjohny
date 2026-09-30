#!/usr/bin/env python3
"""Audit HTTP security headers for a URL you own or are authorized to test.

Read-only single GET request. Reports on the common defensive headers.

Usage:
    python header_check.py https://example.com
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.common import Report  # noqa: E402

try:
    import requests
except ImportError:
    print("This script needs 'requests' (pip install requests).", file=sys.stderr)
    raise SystemExit(4)

# header -> (advice when missing)
EXPECTED = {
    "strict-transport-security": "Enable HSTS to force HTTPS.",
    "content-security-policy": "Add a CSP to mitigate XSS/injection.",
    "x-content-type-options": "Set to 'nosniff' to stop MIME sniffing.",
    "x-frame-options": "Set DENY/SAMEORIGIN (or use CSP frame-ancestors) vs clickjacking.",
    "referrer-policy": "Set a Referrer-Policy to limit referrer leakage.",
    "permissions-policy": "Restrict powerful browser features.",
}
# Headers that leak stack info — presence is a (soft) finding.
DISCOURAGED = ["server", "x-powered-by", "x-aspnet-version"]


def main() -> int:
    ap = argparse.ArgumentParser(description="HTTP security header auditor")
    ap.add_argument("url")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--insecure", action="store_true",
                    help="Skip TLS verification (debugging only)")
    args = ap.parse_args()

    rep = Report()
    try:
        resp = requests.get(args.url, timeout=args.timeout,
                            verify=not args.insecure, allow_redirects=True)
    except requests.RequestException as exc:
        rep.fail(f"Request failed: {exc}")
        return rep.exit_code

    rep.info(f"{args.url} -> HTTP {resp.status_code} ({resp.url})")
    headers = {k.lower(): v for k, v in resp.headers.items()}

    for name, advice in EXPECTED.items():
        if name in headers:
            rep.ok(f"{name}: {headers[name][:80]}")
        else:
            rep.warn(f"Missing {name}. {advice}")

    for name in DISCOURAGED:
        if name in headers:
            rep.warn(f"Info-leak header {name}: {headers[name]}")

    if args.url.startswith("http://"):
        rep.fail("URL is plain HTTP — traffic is unencrypted.")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
