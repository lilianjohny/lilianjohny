#!/usr/bin/env python3
"""Normalize multi-cloud posture findings into one common schema.

Reads Prowler JSON-OCSF output (from AWS, Azure, and/or GCP) and merges every
finding into a single cross-cloud stream, so AWS + Azure + GCP posture can be
viewed and compared together. Read-only.

Also assigns each finding a cross-cloud CATEGORY (Identity / Network / Data /
Logging / Config) so the same class of issue lines up across providers.

Common finding fields:
  provider, check_id, title, severity, status, service, resource, region, category

Usage:
  python normalize.py aws.ocsf.json azure.ocsf.json gcp.ocsf.json > findings.jsonl
  python normalize.py multicloud-out/**/*.ocsf.json > findings.jsonl
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

SEV_NORM = {"critical": "critical", "high": "high", "medium": "medium",
            "moderate": "medium", "low": "low", "informational": "info",
            "info": "info", "unknown": "low"}

# Keyword → cross-cloud category (checked against title + service).
CATEGORY_RULES = [
    # Note: avoid the bare word "user" — it matches "allUsers" (a Data/public
    # issue). Use specific identity signals instead.
    ("Data", ("s3", "bucket", "blob", "storage", "encryption", "kms", "cmek",
              "encrypt", "public access", "publicly", "allusers", "object")),
    ("Identity", ("iam", "mfa", "policy", "role", "principal", "access key",
                  "service account", "privilege", "rbac", "identity", "user without",
                  "user has", "credential")),
    ("Network", ("security group", "firewall", "nsg", "0.0.0.0", "public ip",
                 "ingress", "port", "network", "exposed", "internet")),
    ("Logging", ("cloudtrail", "log", "guardduty", "securityhub", "defender",
                 "audit", "monitor", "command center", "diagnostic")),
    ("Config", ("config", "secret", "key vault", "compliance", "inventory",
                "posture", "policy assignment")),
]


def categorize(text: str) -> str:
    t = (text or "").lower()
    for cat, kws in CATEGORY_RULES:
        if any(k in t for k in kws):
            return cat
    return "Config"


def norm_sev(s: str) -> str:
    return SEV_NORM.get(str(s or "").strip().lower(), "low")


def provider_of(f: dict) -> str:
    # OCSF: cloud.provider; Prowler variants: cloud.provider or finding_info
    cloud = f.get("cloud", {}) or {}
    p = (cloud.get("provider") or f.get("provider") or "").lower()
    if p in ("aws", "amazon"):
        return "aws"
    if p in ("azure", "microsoft"):
        return "azure"
    if p in ("gcp", "google", "gcloud"):
        return "gcp"
    return p or "unknown"


def status_of(f: dict) -> str:
    return str(f.get("status_code") or f.get("status") or
               (f.get("status_detail") or "")).upper()


def resource_of(f: dict) -> tuple[str, str, str]:
    res = f.get("resources") or []
    if res and isinstance(res, list):
        r = res[0]
        return (r.get("uid") or r.get("name") or "", r.get("type") or "",
                (r.get("region") or (r.get("cloud", {}) or {}).get("region") or ""))
    return (f.get("resource_uid", ""), f.get("resource_type", ""), f.get("region", ""))


def normalize_file(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[WARN] {path}: {exc}", file=sys.stderr)
        return []
    items = data if isinstance(data, list) else data.get("findings", [])
    out = []
    for f in items:
        if not isinstance(f, dict):
            continue
        st = status_of(f)
        if st not in ("FAIL", "FAILED", "FAILURE"):
            continue  # only failing/open findings
        meta = f.get("metadata", {}) or {}
        fi = f.get("finding_info", {}) or {}
        check = (f.get("check_id") or meta.get("event_code")
                 or fi.get("uid") or f.get("event_code") or "?")
        title = (f.get("check_title") or fi.get("title") or f.get("message")
                 or f.get("title") or "")
        sev = (f.get("severity") or (f.get("severity_id") and "")
               or fi.get("severity") or "medium")
        uid, rtype, region = resource_of(f)
        svc = (f.get("service_name") or (f.get("resources", [{}])[0].get("type") if f.get("resources") else "")
               or rtype)
        out.append({
            "provider": provider_of(f),
            "check_id": check,
            "title": title,
            "severity": norm_sev(sev),
            "status": "FAIL",
            "service": svc,
            "resource": uid,
            "region": region,
            "category": categorize(f"{title} {svc} {check}"),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize multi-cloud findings")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    # Expand globs (in case the shell didn't).
    paths: list[Path] = []
    for pat in args.files:
        matched = [Path(p) for p in glob.glob(pat, recursive=True)]
        paths.extend(matched or [Path(pat)])

    total = 0
    by_provider: dict[str, int] = {}
    for p in paths:
        if not p.exists():
            print(f"[WARN] not found: {p}", file=sys.stderr)
            continue
        findings = normalize_file(p)
        for f in findings:
            print(json.dumps(f))
            total += 1
            by_provider[f["provider"]] = by_provider.get(f["provider"], 0) + 1
    summary = ", ".join(f"{k}:{v}" for k, v in sorted(by_provider.items()))
    print(f"[INFO] {total} findings ({summary or 'none'})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
