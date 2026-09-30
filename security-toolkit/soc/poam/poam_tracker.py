#!/usr/bin/env python3
"""Track POA&M (Plan of Action & Milestones) aging and overdue items.

Reads a POA&M CSV (see poam_template.csv) and reports open items, overdue
items, and items due within a window — the recurring RMF/FedRAMP ConMon task.

Usage:
  python poam_tracker.py poam.csv               # summary
  python poam_tracker.py poam.csv --due-days 30 # also list items due in 30 days
Exit: 0 none overdue · 2 overdue items present · 3 error.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

TODAY = dt.date.today()


def parse_date(s: str) -> dt.date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime((s or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def get(row: dict, *names: str) -> str:
    for n in names:
        if n in row and row[n]:
            return row[n]
        # case-insensitive
        for k in row:
            if k.lower() == n.lower() and row[k]:
                return row[k]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="POA&M aging tracker")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--due-days", type=int, default=0)
    args = ap.parse_args()

    if not args.csv.exists():
        emit(Level.FAIL, f"POA&M file not found: {args.csv}")
        return 3

    with args.csv.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    rep = Report()
    open_items = overdue = due_soon = 0
    for row in rows:
        status = get(row, "status", "Status").lower()
        if status in ("closed", "completed", "remediated", "risk accepted"):
            continue
        open_items += 1
        pid = get(row, "poam_id", "POA&M ID", "id") or "?"
        sev = get(row, "severity", "Severity") or "?"
        sched = parse_date(get(row, "scheduled_completion", "Scheduled Completion Date"))
        if sched and sched < TODAY:
            overdue += 1
            days = (TODAY - sched).days
            rep.fail(f"OVERDUE {days}d — {pid} [{sev}] (due {sched})")
        elif sched and args.due_days and (sched - TODAY).days <= args.due_days:
            due_soon += 1
            rep.warn(f"Due in {(sched - TODAY).days}d — {pid} [{sev}] (due {sched})")

    emit(Level.INFO, f"POA&M: {open_items} open, {overdue} overdue"
                     + (f", {due_soon} due within {args.due_days}d" if args.due_days else ""))
    if overdue == 0:
        rep.ok("No overdue POA&M items.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
