#!/usr/bin/env python3
"""Enrich + prioritize normalized findings (risk-based, KEV/EPSS aware).

For each finding, adds:
  - kev            (CISA Known Exploited — actively exploited in the wild)
  - epss           (FIRST exploit-probability 0..1)
  - asset_criticality (from the asset inventory)
  - risk_score     (0..10) combining CVSS/severity + EPSS + criticality, KEV override
  - priority       (P1..P4)
  - sla_days, due_date  (from the SLA policy, dated off first_seen)

Prioritization rationale: severity alone over-counts. KEV (known-exploited) and
EPSS (likely-to-be-exploited) plus how much the asset matters give a defensible,
CISA-SSVC-aligned order to remediate in.

Usage:
  python prioritize.py findings.jsonl \
     --kev-file kev.json --epss-file epss.csv \
     --assets ../assets/asset_inventory.example.csv \
     --sla ../track/sla_policy.csv > enriched.jsonl
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kev_epss import load_intel  # noqa: E402

SEV_SCORE = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 3.0, "info": 1.0}
CRIT_ADJ = {"critical": 2.0, "high": 1.0, "medium": 0.0, "low": -1.0, "unknown": 0.0}
DEFAULT_SLA = {"P1": 15, "P2": 30, "P3": 90, "P4": 180}


def load_assets(path: str | None) -> dict[str, str]:
    inv: dict[str, str] = {}
    if not path or not Path(path).exists():
        return inv
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            aid = (row.get("asset") or row.get("Asset") or "").strip()
            crit = (row.get("criticality") or row.get("Criticality") or "").strip().lower()
            if aid:
                inv[aid] = crit or "medium"
    return inv


def load_sla(path: str | None) -> dict[str, int]:
    sla = dict(DEFAULT_SLA)
    if path and Path(path).exists():
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                pr = (row.get("priority") or "").strip().upper()
                days = row.get("sla_days") or ""
                if pr in sla and str(days).strip().isdigit():
                    sla[pr] = int(days)
    return sla


def base_score(f: dict) -> float:
    if isinstance(f.get("cvss"), (int, float)) and f["cvss"]:
        return float(f["cvss"])
    return SEV_SCORE.get(f.get("severity", "low"), 3.0)


def prioritize(f: dict, kev: set, epss: dict, assets: dict) -> dict:
    cve = str(f.get("vuln_id", "")).upper()
    is_kev = cve in kev
    ep = epss.get(cve)
    crit = assets.get(f.get("asset", ""), "unknown")

    score = base_score(f)
    score += (ep or 0.0) * 2.0            # exploit-likelihood boost (0..+2)
    score += CRIT_ADJ.get(crit, 0.0)      # asset importance (-1..+2)
    if is_kev:
        score = max(score, 9.5)           # known-exploited floor
    score = round(max(0.0, min(10.0, score)), 1)

    if is_kev or score >= 9.0:
        pr = "P1"
    elif score >= 7.0:
        pr = "P2"
    elif score >= 4.0:
        pr = "P3"
    else:
        pr = "P4"

    f.update({"kev": is_kev, "epss": ep, "asset_criticality": crit,
              "risk_score": score, "priority": pr})
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="Prioritize findings (KEV/EPSS/criticality)")
    ap.add_argument("findings", type=Path)
    ap.add_argument("--kev-file")
    ap.add_argument("--epss-file")
    ap.add_argument("--assets")
    ap.add_argument("--sla")
    ap.add_argument("--allow-fetch", action="store_true")
    args = ap.parse_args()
    if not args.findings.exists():
        print(f"[FAIL] not found: {args.findings}", file=sys.stderr)
        return 3

    kev, epss = load_intel(args.kev_file, args.epss_file, args.allow_fetch)
    assets = load_assets(args.assets)
    sla = load_sla(args.sla)
    print(f"[INFO] intel: KEV={len(kev)} EPSS={len(epss)} assets={len(assets)}", file=sys.stderr)

    counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    kev_hits = 0
    for line in args.findings.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        f = json.loads(line)
        f = prioritize(f, kev, epss, assets)
        days = sla.get(f["priority"], 180)
        try:
            fs = dt.date.fromisoformat(f.get("first_seen"))
        except (ValueError, TypeError):
            fs = dt.date.today()
        f["sla_days"] = days
        f["due_date"] = (fs + dt.timedelta(days=days)).isoformat()
        counts[f["priority"]] += 1
        if f["kev"]:
            kev_hits += 1
        print(json.dumps(f))

    print(f"[INFO] Prioritized — P1:{counts['P1']} P2:{counts['P2']} "
          f"P3:{counts['P3']} P4:{counts['P4']} (KEV: {kev_hits})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
