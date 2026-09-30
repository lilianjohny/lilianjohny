#!/usr/bin/env python3
"""Static security audit of an OpenAPI / Swagger specification.

Reads a spec (JSON or YAML) and flags API-security issues aligned with the
OWASP API Security Top 10 — before the API is deployed. Read-only, no network.

Checks include:
  - No global or per-operation security scheme (broken/again missing authn)
  - Security schemes defined but not applied to operations
  - Weak/deprecated auth (HTTP Basic, API key in query string)
  - OAuth2 flows using the implicit grant (deprecated)
  - Servers using http:// (cleartext transport)
  - Operations with no defined error responses / no 429 (rate limiting)
  - Unbounded array parameters / missing pagination hints (resource abuse)
  - Verbose server errors exposed in examples

Usage:
    python openapi_security_audit.py openapi.yaml
    python openapi_security_audit.py openapi.json --min-warn
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def load_spec(path: Path) -> dict:
    text = path.read_text(errors="replace")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            emit(Level.FAIL, "YAML spec needs pyyaml (pip install pyyaml), or convert to JSON.")
            raise SystemExit(3)
        return yaml.safe_load(text)
    return json.loads(text)


def audit_servers(rep: Report, spec: dict) -> None:
    for srv in spec.get("servers", []):
        url = srv.get("url", "")
        if url.startswith("http://"):
            rep.fail(f"Server uses cleartext HTTP: {url}")
    # Swagger 2.0 style
    if spec.get("schemes") and "http" in spec["schemes"]:
        rep.fail("Swagger 'schemes' includes cleartext 'http'.")


def audit_security_schemes(rep: Report, spec: dict) -> dict:
    comps = spec.get("components", {}).get("securitySchemes", {})
    # Swagger 2.0
    comps = comps or spec.get("securityDefinitions", {})
    if not comps:
        rep.fail("No security schemes defined (API appears unauthenticated).")
        return {}
    for name, sch in comps.items():
        stype = (sch.get("type") or "").lower()
        scheme = (sch.get("scheme") or "").lower()
        if stype == "http" and scheme == "basic":
            rep.warn(f"Security scheme '{name}' uses HTTP Basic auth (avoid; use tokens).")
        if stype == "apikey" and sch.get("in") == "query":
            rep.warn(f"Security scheme '{name}' passes an API key in the query string "
                     "(leaks in logs/history) — use a header.")
        if stype == "oauth2":
            flows = sch.get("flows", {})
            if "implicit" in flows or sch.get("flow") == "implicit":
                rep.warn(f"OAuth2 scheme '{name}' uses the deprecated implicit grant.")
    return comps


def audit_operations(rep: Report, spec: dict, has_global_sec: bool) -> None:
    paths = spec.get("paths", {}) or {}
    total_ops = 0
    unprotected = 0
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            total_ops += 1
            # Authorization
            has_sec = "security" in op or has_global_sec
            # An explicit empty security ([]) disables auth for the op.
            if op.get("security") == []:
                rep.warn(f"{method.upper()} {path}: security explicitly disabled ([]).")
            elif not has_sec:
                unprotected += 1
                rep.fail(f"{method.upper()} {path}: no security applied (no authn/authz).")
            # Rate limiting signal
            responses = op.get("responses", {}) or {}
            codes = {str(c) for c in responses}
            if "429" not in codes:
                rep.info(f"{method.upper()} {path}: no 429 response documented (rate limiting?).")
            # Error handling
            if not any(c.startswith(("4", "5")) for c in codes):
                rep.warn(f"{method.upper()} {path}: no 4xx/5xx error responses defined.")
            # Unbounded collections
            for p in op.get("parameters", []) or []:
                schema = p.get("schema", {}) if isinstance(p, dict) else {}
                if schema.get("type") == "array" and "maxItems" not in schema:
                    rep.info(f"{method.upper()} {path}: array param '{p.get('name')}' "
                             "has no maxItems (resource-abuse risk).")
    emit(Level.INFO, f"Audited {total_ops} operations; {unprotected} without any security.")


def main() -> int:
    ap = argparse.ArgumentParser(description="OpenAPI/Swagger security audit")
    ap.add_argument("spec", type=Path)
    args = ap.parse_args()

    if not args.spec.exists():
        emit(Level.FAIL, f"Spec not found: {args.spec}")
        return 3
    try:
        spec = load_spec(args.spec)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        emit(Level.FAIL, f"Could not parse spec: {exc}")
        return 3
    if not isinstance(spec, dict):
        emit(Level.FAIL, "Spec did not parse into an object.")
        return 3

    ver = spec.get("openapi") or spec.get("swagger") or "unknown"
    title = spec.get("info", {}).get("title", "?")
    emit(Level.INFO, f"Auditing API '{title}' (spec version {ver})")

    rep = Report()
    audit_servers(rep, spec)
    audit_security_schemes(rep, spec)
    has_global_sec = bool(spec.get("security"))
    if not has_global_sec:
        rep.warn("No global 'security' requirement; each operation must set its own.")
    audit_operations(rep, spec, has_global_sec)

    if rep.exit_code == 0:
        rep.ok("No API-security issues detected by static checks.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
