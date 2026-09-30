#!/usr/bin/env python3
"""Track remediation SLA status on enriched findings.

Reports open findings by priority, overdue items (past due_date), items due
soon, and SLA compliance %. Feed it the output of prioritize.py.

Usage:
  python sla_tracker.py enriched.jsonl [--due-days 7]
Exit: 0 none overdue · 2 overdue items present · 3 error
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

TODAY = dt.date.today()


def main() -> int:
    ap = argparse.ArgumentParser(description="Remediation SLA tracker")
    ap.add_argument("findings", type=Path)
    ap.add_argument("--due-days", type=int, default=7)
    args = ap.parse_args()
    if not args.findings.exists():
        emit(Level.FAIL, f"not found: {args.findings}")
        return 3

    by_pri = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    overdue = due_soon = total_open = kev_open = 0
    overdue_items = []
    for line in args.findings.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        f = json.loads(line)
        if f.get("status", "open") != "open":
            continue
        total_open += 1
        by_pri[f.get("priority", "P4")] = by_pri.get(f.get("priority", "P4"), 0) + 1
        if f.get("kev"):
            kev_open += 1
        due = f.get("due_date")
        try:
            dd = dt.date.fromisoformat(due) if due else None
        except ValueError:
            dd = None
        if dd and dd < TODAY:
            overdue += 1
            overdue_items.append((dd, f))
        elif dd and (dd - TODAY).days <= args.due_days:
            due_soon += 1

    rep = Report()
    emit(Level.INFO, f"Open findings: {total_open} "
                     f"(P1:{by_pri['P1']} P2:{by_pri['P2']} P3:{by_pri['P3']} P4:{by_pri['P4']})")
    if kev_open:
        rep.fail(f"{kev_open} open finding(s) are on the CISA KEV list (known-exploited) — expedite.")
    for dd, f in sorted(overdue_items)[:25]:
        rep.fail(f"OVERDUE {(TODAY - dd).days}d — {f.get('vuln_id')} on {f.get('asset')} "
                 f"[{f.get('priority')} risk {f.get('risk_score')}]")
    if due_soon:
        rep.warn(f"{due_soon} finding(s) due within {args.due_days} days.")

    compliance = round(100 * (total_open - overdue) / total_open) if total_open else 100
    lvl = Level.OK if overdue == 0 else Level.FAIL
    emit(lvl, f"SLA compliance (open, not overdue): {compliance}%")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
