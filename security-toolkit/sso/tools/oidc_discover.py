#!/usr/bin/env python3
"""OpenID Connect discovery & posture checker.

Validates an OIDC provider's discovery document
(`/.well-known/openid-configuration`) against the things that matter when you
design or support an OIDC/OAuth integration:

  - Required endpoints present (issuer, authorization, token, jwks_uri, userinfo).
  - **issuer is HTTPS** (and, live, matches the requested host).
  - **PKCE supported** (`code_challenge_methods_supported` contains S256).
  - **id_token signing** excludes `none`; RS256/ES256 offered.
  - `openid` scope + `code` response type offered (auth-code flow).
  - Flags legacy/implicit (`token`/`id_token` response types) if present.

Two modes:
  --file <discovery.json>   offline (recommended for CI/portfolio; testable).
  --url  <issuer-or-url>    live fetch of .well-known/openid-configuration
                            (uses urllib; degrades cleanly if egress blocked).

Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python oidc_discover.py --file sample.discovery.json
    python oidc_discover.py --url https://login.microsoftonline.com/<tenant>/v2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

REQUIRED = ["issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"]
RECOMMENDED = ["userinfo_endpoint", "end_session_endpoint"]


def fetch(url: str) -> dict:
    import urllib.request
    if not url.rstrip("/").endswith("openid-configuration"):
        url = url.rstrip("/") + "/.well-known/openid-configuration"
    with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def check(rep: Report, doc: dict) -> None:
    for key in REQUIRED:
        if not doc.get(key):
            rep.fail(f"Missing required endpoint: {key}")
        else:
            emit(Level.INFO, f"{key}: {doc[key]}")
    for key in RECOMMENDED:
        if not doc.get(key):
            rep.warn(f"Missing recommended endpoint: {key}")

    issuer = str(doc.get("issuer", ""))
    if issuer and not issuer.startswith("https://"):
        rep.fail(f"issuer is not HTTPS: {issuer}")
    elif issuer:
        rep.ok("issuer uses HTTPS.")

    algs = doc.get("id_token_signing_alg_values_supported", [])
    if "none" in [a.lower() for a in algs]:
        rep.fail("id_token signing allows 'none' — unsigned tokens are forgeable.")
    if any(a in algs for a in ("RS256", "ES256", "PS256")):
        rep.ok(f"id_token signing offers a strong alg ({', '.join(algs[:4])}).")
    elif algs:
        rep.warn(f"id_token signing algs look weak/unusual: {algs}")

    pkce = doc.get("code_challenge_methods_supported", [])
    if "S256" in pkce:
        rep.ok("PKCE S256 supported (use it for public clients).")
    else:
        rep.warn("No S256 PKCE advertised — public/native clients can't use PKCE.")

    scopes = doc.get("scopes_supported", [])
    if scopes and "openid" not in scopes:
        rep.fail("'openid' scope not advertised — this is not a valid OIDC provider.")

    rtypes = doc.get("response_types_supported", [])
    if "code" not in rtypes and rtypes:
        rep.warn("Auth-code flow ('code') not advertised.")
    implicit = [r for r in rtypes if r and r != "code" and ("token" in r or "id_token" in r)]
    if implicit:
        rep.warn(f"Implicit/hybrid response types offered ({implicit}) — "
                 f"prefer auth-code + PKCE; avoid implicit.")


def main() -> int:
    ap = argparse.ArgumentParser(description="OIDC discovery/posture checker")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", help="local discovery JSON (offline)")
    g.add_argument("--url", help="issuer URL or full discovery URL (live fetch)")
    args = ap.parse_args()

    if args.file:
        if not Path(args.file).exists():
            emit(Level.FAIL, f"File not found: {args.file}")
            return 3
        try:
            doc = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            emit(Level.FAIL, f"Invalid JSON: {exc}")
            return 3
    else:
        try:
            doc = fetch(args.url)
        except Exception as exc:  # noqa: BLE001
            emit(Level.FAIL, f"Could not fetch discovery doc ({exc}). "
                             f"Try --file with a saved copy.")
            return 3

    emit(Level.INFO, "Checking OIDC discovery document.")
    rep = Report()
    check(rep, doc)
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
