#!/usr/bin/env python3
"""Assess event-logging coverage against OMB M-21-31 expectations.

M-21-31 defines event-logging maturity tiers (EL0 not effective → EL3 advanced)
and required log categories with retention (commonly cited: 12 months active +
18 months cold storage). This tool checks which required categories your
declared log sources cover and estimates the maturity tier.

Input (--sources JSON):
  {
    "retention_active_months": 12,
    "retention_cold_months": 18,
    "centralized": true,
    "categories": {
      "authentication": true, "network": true, "dns": false, ...
    }
  }

Usage:
  python log_coverage_check.py --sources log_sources.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

# Required event categories (aligned to M-21-31 logging criteria / NIST AU family).
REQUIRED_CATEGORIES = [
    "authentication", "authorization", "account_management", "process_execution",
    "network", "dns", "http_web", "file_access", "cloud_control_plane",
    "endpoint_edr", "email", "database",
]
REQ_ACTIVE_MONTHS = 12
REQ_COLD_MONTHS = 18


def main() -> int:
    ap = argparse.ArgumentParser(description="OMB M-21-31 log-coverage assessment")
    ap.add_argument("--sources", type=Path, required=True)
    args = ap.parse_args()
    if not args.sources.exists():
        emit(Level.FAIL, f"Sources file not found: {args.sources}")
        return 3

    cfg = json.loads(args.sources.read_text())
    rep = Report()
    cats = cfg.get("categories", {}) or {}

    covered = [c for c in REQUIRED_CATEGORIES if cats.get(c)]
    missing = [c for c in REQUIRED_CATEGORIES if not cats.get(c)]
    pct = round(100 * len(covered) / len(REQUIRED_CATEGORIES))

    emit(Level.INFO, f"Log-category coverage: {len(covered)}/{len(REQUIRED_CATEGORIES)} ({pct}%)")
    for c in missing:
        rep.warn(f"Missing required log category: {c}")

    # Retention
    ra = cfg.get("retention_active_months", 0)
    rc = cfg.get("retention_cold_months", 0)
    if ra < REQ_ACTIVE_MONTHS:
        rep.fail(f"Active retention {ra}mo < required {REQ_ACTIVE_MONTHS}mo.")
    else:
        rep.ok(f"Active retention {ra}mo meets {REQ_ACTIVE_MONTHS}mo.")
    if rc < REQ_COLD_MONTHS:
        rep.warn(f"Cold retention {rc}mo < recommended {REQ_COLD_MONTHS}mo (total 30mo).")

    centralized = bool(cfg.get("centralized"))
    if not centralized:
        rep.warn("Logs are not centralized — required for correlation/EL maturity.")

    # Estimate maturity tier (EL0..EL3), indicative.
    if pct >= 90 and centralized and ra >= REQ_ACTIVE_MONTHS and rc >= REQ_COLD_MONTHS:
        tier = "EL3 (Advanced)"
    elif pct >= 75 and centralized and ra >= REQ_ACTIVE_MONTHS:
        tier = "EL2 (Intermediate)"
    elif pct >= 40:
        tier = "EL1 (Basic)"
    else:
        tier = "EL0 (Not effective)"
    lvl = Level.OK if tier.startswith(("EL2", "EL3")) else Level.WARN
    emit(lvl, f"Estimated M-21-31 maturity tier: {tier}")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
