#!/usr/bin/env python3
"""SCIM 2.0 resource / ServiceProviderConfig validator (offline).

Validates SCIM 2.0 JSON against the core spec (RFC 7643/7644) so you can design
and troubleshoot provisioning/deprovisioning integrations. Auto-detects the
resource type from `schemas` and checks:

  - **User**: schemas, `id`, `userName`, `meta.resourceType`, and an **`active`**
    flag (needed for deprovisioning — disabling a leaver sets active=false).
  - **Group**: schemas, `id`, `displayName`, members.
  - **ListResponse**: schemas, `totalResults`, `Resources`.
  - **ServiceProviderConfig**: whether **PATCH** (incremental sync), **filter**,
    and **bulk** are supported — a provider without PATCH forces full re-syncs.

Input: a JSON file containing a SCIM resource, list response, or SP config.
Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python scim_probe.py sample.scim-user.json
    python scim_probe.py serviceproviderconfig.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

USER = "urn:ietf:params:scim:schemas:core:2.0:User"
GROUP = "urn:ietf:params:scim:schemas:core:2.0:Group"
LIST = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SPCONFIG = "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"
ENTERPRISE = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"


def check_user(rep: Report, r: dict) -> None:
    for field in ("id", "userName"):
        if not r.get(field):
            rep.fail(f"User missing required '{field}'.")
        else:
            emit(Level.INFO, f"{field}: {r[field]}")
    meta = r.get("meta", {})
    if meta.get("resourceType") != "User":
        rep.warn("meta.resourceType is not 'User'.")
    if "active" not in r:
        rep.warn("No 'active' attribute — deprovisioning (active=false on a "
                 "leaver) can't be represented. Critical for offboarding.")
    else:
        rep.ok(f"'active' present ({r['active']}) — supports enable/disable lifecycle.")
    if not r.get("emails"):
        rep.warn("No 'emails' — the app may not get a usable email claim.")
    if ENTERPRISE in r.get("schemas", []):
        emit(Level.INFO, "Enterprise User extension present (manager/department/etc.).")


def check_group(rep: Report, r: dict) -> None:
    for field in ("id", "displayName"):
        if not r.get(field):
            rep.fail(f"Group missing required '{field}'.")
    members = r.get("members", [])
    emit(Level.INFO, f"Group '{r.get('displayName','?')}' has {len(members)} member(s).")


def check_list(rep: Report, r: dict) -> None:
    if "totalResults" not in r:
        rep.fail("ListResponse missing 'totalResults'.")
    res = r.get("Resources", [])
    emit(Level.INFO, f"ListResponse: totalResults={r.get('totalResults','?')}, "
                     f"{len(res)} resource(s) in this page.")
    for sub in res[:50]:
        if USER in sub.get("schemas", []):
            check_user(rep, sub)


def check_spconfig(rep: Report, r: dict) -> None:
    patch = (r.get("patch") or {}).get("supported")
    filt = (r.get("filter") or {}).get("supported")
    bulk = (r.get("bulk") or {}).get("supported")
    if patch:
        rep.ok("PATCH supported — incremental sync (add/remove one member) works.")
    else:
        rep.warn("PATCH NOT supported — the IdP must full-replace resources; "
                 "slower and riskier sync.")
    if filt:
        rep.ok("filter supported — the IdP can look users up by userName/externalId.")
    else:
        rep.warn("filter NOT supported — reconciliation is harder.")
    emit(Level.INFO, f"bulk supported: {bool(bulk)}")


def validate(rep: Report, r: dict) -> None:
    schemas = r.get("schemas", [])
    if not schemas:
        rep.fail("No 'schemas' attribute — not a valid SCIM resource.")
        return
    if SPCONFIG in schemas:
        check_spconfig(rep, r)
    elif LIST in schemas:
        check_list(rep, r)
    elif USER in schemas:
        check_user(rep, r)
    elif GROUP in schemas:
        check_group(rep, r)
    else:
        rep.warn(f"Unrecognized SCIM schema(s): {schemas}")


def main() -> int:
    ap = argparse.ArgumentParser(description="SCIM 2.0 resource validator")
    ap.add_argument("input", help="SCIM JSON file (User/Group/ListResponse/SPConfig)")
    args = ap.parse_args()

    if not Path(args.input).exists():
        emit(Level.FAIL, f"File not found: {args.input}")
        return 3
    try:
        r = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        emit(Level.FAIL, f"Invalid JSON: {exc}")
        return 3

    emit(Level.INFO, "Validating SCIM 2.0 resource.")
    rep = Report()
    validate(rep, r)
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
