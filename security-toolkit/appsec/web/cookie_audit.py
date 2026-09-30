#!/usr/bin/env python3
"""Audit cookies set by a target for security flags (authorized targets only).

Inspects Set-Cookie headers for:
  - Missing Secure flag (transmittable over HTTP)
  - Missing HttpOnly (readable by JavaScript / XSS exfil)
  - Missing or weak SameSite (CSRF exposure)
  - Session-like cookies without protections
  - Overly broad Domain / Path

Usage:
    python cookie_audit.py https://app.example.com
"""
from __future__ import annotations

import argparse
import sys
from http.cookies import SimpleCookie
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, confirm_authorized  # noqa: E402

try:
    import requests
except ImportError:
    print("Needs 'requests' (pip install requests).", file=sys.stderr)
    raise SystemExit(3)

SESSION_HINT = ("session", "sess", "sid", "auth", "token", "jwt")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cookie security auditor")
    ap.add_argument("url")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--insecure", action="store_true")
    args = ap.parse_args()

    confirm_authorized(args.url)
    rep = Report()
    try:
        r = requests.get(args.url, timeout=args.timeout, verify=not args.insecure,
                        allow_redirects=True)
    except requests.RequestException as exc:
        rep.fail(f"Request failed: {exc}")
        rep.summary()
        return rep.exit_code

    # requests collapses multiple Set-Cookie; use raw headers where possible.
    raw = r.raw.headers.getlist("Set-Cookie") if hasattr(r.raw.headers, "getlist") else []
    if not raw:
        sc = r.headers.get("Set-Cookie")
        raw = [sc] if sc else []

    if not raw:
        rep.info("No Set-Cookie headers on this response.")
        rep.summary()
        return rep.exit_code

    for line in raw:
        jar = SimpleCookie()
        try:
            jar.load(line)
        except Exception:  # noqa: BLE001
            continue
        for name, morsel in jar.items():
            attrs = {k.lower(): v for k, v in morsel.items()}
            flags = line.lower()
            is_session = any(h in name.lower() for h in SESSION_HINT)
            label = f"cookie '{name}'" + (" [session-like]" if is_session else "")

            secure = "secure" in flags
            httponly = "httponly" in flags
            samesite = attrs.get("samesite", "").lower()

            if not secure:
                (rep.fail if is_session else rep.warn)(f"{label}: missing Secure flag.")
            if not httponly:
                (rep.fail if is_session else rep.warn)(f"{label}: missing HttpOnly flag.")
            if not samesite:
                rep.warn(f"{label}: no SameSite attribute (CSRF exposure).")
            elif samesite == "none" and not secure:
                rep.fail(f"{label}: SameSite=None without Secure (rejected by browsers).")
            if attrs.get("domain", "").startswith("."):
                rep.info(f"{label}: broad Domain={attrs['domain']}.")

    if rep.exit_code == 0:
        rep.ok("All observed cookies carry appropriate security flags.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
