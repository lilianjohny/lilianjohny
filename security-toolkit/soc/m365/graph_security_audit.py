#!/usr/bin/env python3
"""Microsoft 365 / Entra ID security-posture audit.

Evaluates a tenant's identity security posture against common baselines
(the M365/Entra hardening a SOC / cybersecurity engineer owns). Works two ways:

  - **Offline (default):** reads a posture JSON you exported (from the Graph
    Security API, Secure Score, or your own collection). Fully testable, no
    creds. This is the recommended CI/portfolio mode.
  - **Live (--graph):** if `msal` + `requests` are installed and app-only
    credentials are provided, fetches the same fields from Microsoft Graph.
    Degrades cleanly to an explanatory message when unavailable.

Posture JSON fields (all optional):
  users_total, users_without_mfa, global_admins, legacy_auth_enabled (bool),
  security_defaults_enabled (bool), ca_policies (list of {name,state}),
  guest_users, stale_users_90d, shared_mailboxes_signin_enabled (bool)

Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python graph_security_audit.py --input posture.example.json
    python graph_security_audit.py --graph --tenant <id> --client-id <id>
        (set GRAPH_CLIENT_SECRET in the environment)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

MIN_ADMINS, MAX_ADMINS = 2, 5


def evaluate(rep: Report, p: dict) -> None:
    total = p.get("users_total")
    no_mfa = p.get("users_without_mfa")
    if no_mfa is not None:
        if no_mfa > 0:
            rep.fail(f"{no_mfa} user(s) without MFA registered — require "
                     f"phishing-resistant MFA for all.")
        else:
            rep.ok("All users have MFA registered.")
    if total:
        emit(Level.INFO, f"Tenant has {total} users.")

    if p.get("legacy_auth_enabled") is True:
        rep.fail("Legacy/basic authentication is ENABLED — it bypasses MFA. Block it.")
    elif p.get("legacy_auth_enabled") is False:
        rep.ok("Legacy authentication is blocked.")

    admins = p.get("global_admins")
    if admins is not None:
        if admins > MAX_ADMINS:
            rep.warn(f"{admins} Global Administrators (> {MAX_ADMINS}) — reduce and "
                     f"use PIM/eligible roles.")
        elif admins < MIN_ADMINS:
            rep.warn(f"Only {admins} Global Administrator — keep 2+ (with break-glass).")
        else:
            rep.ok(f"{admins} Global Administrators (within {MIN_ADMINS}-{MAX_ADMINS}).")

    # Conditional Access vs security defaults
    ca = p.get("ca_policies") or []
    enabled_ca = [c for c in ca if str(c.get("state", "")).lower() == "enabled"]
    mfa_ca = [c for c in enabled_ca
              if "mfa" in str(c.get("name", "")).lower()
              or "multi" in str(c.get("name", "")).lower()]
    if p.get("security_defaults_enabled") is True:
        rep.info("Security defaults enabled (baseline MFA). Move to Conditional "
                 "Access for granular control.")
    elif enabled_ca:
        rep.ok(f"{len(enabled_ca)} Conditional Access policy(ies) enabled.")
        if not mfa_ca:
            rep.warn("No enabled CA policy appears to require MFA — verify coverage.")
    else:
        rep.fail("No enabled Conditional Access policies and security defaults off "
                 "— no baseline access control.")

    guests = p.get("guest_users")
    if guests:
        rep.warn(f"{guests} guest user(s) — review external access and restrict "
                 f"guest permissions.")

    stale = p.get("stale_users_90d")
    if stale:
        rep.warn(f"{stale} user(s) with no sign-in in 90 days — disable/deprovision.")

    if p.get("shared_mailboxes_signin_enabled") is True:
        rep.warn("Shared mailboxes have sign-in enabled — block interactive sign-in.")


def fetch_from_graph(tenant: str, client_id: str) -> dict:
    """Best-effort live fetch. Returns a posture dict or raises RuntimeError."""
    try:
        import msal  # noqa: F401
        import requests  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(f"live mode needs msal + requests ({exc})")
    secret = os.environ.get("GRAPH_CLIENT_SECRET")
    if not secret:
        raise RuntimeError("set GRAPH_CLIENT_SECRET for app-only Graph auth")
    # Intentionally minimal: acquire a token and confirm connectivity. Extend
    # with specific Graph queries (identity/conditionalAccess, reports, etc.)
    # for your tenant's permissions.
    import msal
    app = msal.ConfidentialClientApplication(
        client_id, authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=secret)
    token = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in token:
        raise RuntimeError(f"Graph token error: {token.get('error_description')}")
    raise RuntimeError("live Graph collection is a stub — export posture JSON and "
                       "use --input (see the module docstring for fields).")


def main() -> int:
    ap = argparse.ArgumentParser(description="M365 / Entra security posture audit")
    ap.add_argument("--input", help="posture JSON file (offline mode)")
    ap.add_argument("--graph", action="store_true", help="fetch live from Graph")
    ap.add_argument("--tenant", help="Entra tenant id (live mode)")
    ap.add_argument("--client-id", help="app registration client id (live mode)")
    args = ap.parse_args()

    if args.graph:
        try:
            posture = fetch_from_graph(args.tenant or "", args.client_id or "")
        except RuntimeError as exc:
            emit(Level.FAIL, f"Live Graph mode unavailable: {exc}")
            return 3
    elif args.input:
        try:
            posture = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            emit(Level.FAIL, f"Could not read posture JSON: {exc}")
            return 3
    else:
        emit(Level.FAIL, "Provide --input <posture.json> or --graph.")
        return 3

    emit(Level.INFO, "Evaluating M365/Entra posture.")
    rep = Report()
    evaluate(rep, posture)
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
