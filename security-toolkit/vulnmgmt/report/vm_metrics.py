#!/usr/bin/env python3
"""Vulnerability-management program metrics + Markdown report.

Summarizes the enriched findings into the KPIs a VM program reports: open by
severity/priority, KEV exposure, risk distribution, top assets, SLA posture,
and (if closed findings carry closed_date) mean time to remediate (MTTR).

Usage:
  python vm_metrics.py enriched.jsonl --out vm_report.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

TODAY = dt.date.today()


def main() -> int:
    ap = argparse.ArgumentParser(description="VM program metrics")
    ap.add_argument("findings", type=Path)
    ap.add_argument("--out", default="vm_report.md")
    args = ap.parse_args()
    if not args.findings.exists():
        print(f"[FAIL] not found: {args.findings}", file=sys.stderr)
        return 3

    sev = Counter(); pri = Counter(); asset = Counter()
    total = kev = overdue = 0
    mttrs = []
    risk_buckets = {"9-10": 0, "7-8.9": 0, "4-6.9": 0, "0-3.9": 0}
    for line in args.findings.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        f = json.loads(line)
        status = f.get("status", "open")
        if status == "open":
            total += 1
            sev[f.get("severity", "low")] += 1
            pri[f.get("priority", "P4")] += 1
            asset[f.get("asset", "?")] += 1
            if f.get("kev"):
                kev += 1
            rs = f.get("risk_score") or 0
            b = ("9-10" if rs >= 9 else "7-8.9" if rs >= 7 else "4-6.9" if rs >= 4 else "0-3.9")
            risk_buckets[b] += 1
            due = f.get("due_date")
            try:
                if due and dt.date.fromisoformat(due) < TODAY:
                    overdue += 1
            except ValueError:
                pass
        else:
            fs, cd = f.get("first_seen"), f.get("closed_date")
            try:
                mttrs.append((dt.date.fromisoformat(cd) - dt.date.fromisoformat(fs)).days)
            except (ValueError, TypeError):
                pass

    mttr = round(sum(mttrs) / len(mttrs), 1) if mttrs else None
    lines = ["# Vulnerability Management — Program Metrics", "",
             f"_Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}._", "",
             "## Open findings", "",
             f"- **Total open:** {total}",
             f"- **KEV (known-exploited) open:** {kev}",
             f"- **Overdue (past SLA):** {overdue}",
             f"- **MTTR (closed):** {mttr if mttr is not None else 'n/a'} days", "",
             "### By priority",
             *(f"- {p}: {pri.get(p,0)}" for p in ("P1", "P2", "P3", "P4")), "",
             "### By severity",
             *(f"- {s}: {sev.get(s,0)}" for s in ("critical", "high", "medium", "low", "info")), "",
             "### Risk-score distribution",
             *(f"- {b}: {c}" for b, c in risk_buckets.items()), "",
             "### Top assets by open findings"]
    for a, c in asset.most_common(10):
        lines.append(f"- {a}: {c}")
    lines += ["", "## Notes",
              "P1 = KEV or risk ≥ 9. Prioritize KEV and high-EPSS items first; "
              "SLAs are dated from first_seen per `track/sla_policy.csv`."]

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"[OK] Wrote {args.out} — {total} open, {kev} KEV, {overdue} overdue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
