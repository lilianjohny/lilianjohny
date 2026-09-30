#!/usr/bin/env python3
"""Unified multi-cloud security posture report.

Aggregates normalized cross-cloud findings (from normalize.py) into a single
view: totals by provider and severity, a provider × category matrix, the
issue classes that appear across multiple clouds, and (optionally) coverage
against the cross-cloud baseline. Read-only.

Usage:
  python report.py findings.jsonl --baseline baseline.csv --out report.md
Exit: 0 no critical/high · 2 critical/high findings present · 3 error
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROVIDERS = ["aws", "azure", "gcp"]
CATEGORIES = ["Identity", "Network", "Data", "Logging", "Config"]
SEVS = ["critical", "high", "medium", "low", "info"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Unified multi-cloud report")
    ap.add_argument("findings", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--out", default="multicloud_report.md")
    args = ap.parse_args()
    if not args.findings.exists():
        print(f"[FAIL] not found: {args.findings}", file=sys.stderr)
        return 3

    findings = []
    for line in args.findings.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("["):
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    by_prov = Counter(f["provider"] for f in findings)
    by_sev = Counter(f["severity"] for f in findings)
    prov_sev = defaultdict(Counter)
    prov_cat = defaultdict(Counter)
    cat_providers = defaultdict(set)      # category -> set of providers with it
    check_providers = defaultdict(set)    # normalized check-class -> providers
    for f in findings:
        prov_sev[f["provider"]][f["severity"]] += 1
        prov_cat[f["provider"]][f["category"]] += 1
        cat_providers[f["category"]].add(f["provider"])
        # class = category + a coarse check keyword, to spot cross-cloud repeats
        check_providers[f["category"]].add(f["provider"])

    crit_high = by_sev["critical"] + by_sev["high"]
    now = dt.datetime.now(dt.timezone.utc)
    L = ["# Multi-Cloud Security Posture", "",
         f"_Generated {now:%Y-%m-%dT%H:%M:%SZ}. Unified view across "
         f"{len(by_prov)} cloud(s)._", "",
         "## Summary", "",
         f"- **Total open findings:** {len(findings)}",
         f"- **Critical:** {by_sev['critical']}  **High:** {by_sev['high']}  "
         f"**Medium:** {by_sev['medium']}  **Low:** {by_sev['low']}",
         f"- **By provider:** " + (", ".join(f"{p}: {by_prov[p]}" for p in by_prov) or "none"),
         ""]

    # Provider × severity matrix
    L += ["## Findings by provider & severity", "",
          "| Provider | Critical | High | Medium | Low |",
          "|----------|:--------:|:----:|:------:|:---:|"]
    for p in [x for x in PROVIDERS if x in by_prov] + [x for x in by_prov if x not in PROVIDERS]:
        s = prov_sev[p]
        L.append(f"| {p} | {s['critical']} | {s['high']} | {s['medium']} | {s['low']} |")
    L.append("")

    # Provider × category matrix
    present = [p for p in PROVIDERS if p in by_prov] + [p for p in by_prov if p not in PROVIDERS]
    L += ["## Findings by category (cross-cloud)", "",
          "| Category | " + " | ".join(present) + " |",
          "|----------|" + "|".join(":--:" for _ in present) + "|"]
    for cat in CATEGORIES:
        L.append(f"| {cat} | " + " | ".join(str(prov_cat[p][cat]) for p in present) + " |")
    L.append("")

    # Systemic issues (a category failing on 2+ clouds)
    systemic = sorted(c for c, ps in cat_providers.items() if len(ps) >= 2)
    if systemic:
        L += ["## Systemic issues (present on 2+ clouds)", ""]
        for c in systemic:
            L.append(f"- **{c}** — findings on: {', '.join(sorted(cat_providers[c]))}")
        L.append("")

    # Baseline coverage (which baseline controls have failing findings)
    if args.baseline and args.baseline.exists():
        with args.baseline.open(newline="") as fh:
            base = list(csv.DictReader(fh))
        L += ["## Cross-cloud baseline — categories with open findings", "",
              "| Baseline control | Category | Clouds with findings |",
              "|------------------|----------|----------------------|"]
        for b in base:
            cat = b.get("category", "")
            hit = sorted(cat_providers.get(cat, set()))
            mark = ", ".join(hit) if hit else "—"
            L.append(f"| {b.get('control_id')} {b.get('control','')[:40]} | {cat} | {mark} |")
        L.append("")

    L += ["## Next steps",
          "Feed these findings into vulnerability management "
          "(`../../vulnmgmt/`) for risk-based prioritization, and into GRC "
          "(`../../grc/compliance/crosswalk.py`) for framework coverage. Fix "
          "systemic categories once as a cross-cloud guardrail (SCP / Azure "
          "Policy / GCP Org Policy).", ""]

    Path(args.out).write_text("\n".join(L) + "\n")
    print(f"[OK] Wrote {args.out} — {len(findings)} findings across "
          f"{len(by_prov)} cloud(s); {crit_high} critical/high.")
    return 2 if crit_high else 0


if __name__ == "__main__":
    raise SystemExit(main())
