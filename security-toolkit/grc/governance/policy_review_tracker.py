#!/usr/bin/env python3
"""Policy governance — flag policies overdue (or soon due) for review.

Computes each policy's next-review date from last_reviewed + review_cadence and
reports overdue and upcoming reviews. Governance hygiene for the "G" in GRC.

CSV columns (see policy_register.csv):
  policy_id, title, owner, approved_date, review_cadence_months,
  last_reviewed, status, related_controls

Usage:
  python policy_review_tracker.py policy_register.csv [--due-days 60]
Exit: 0 none overdue · 2 overdue policies · 3 error
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


def pdate(s: str):
    for f in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            continue
    return None


def add_months(d: dt.date, months: int) -> dt.date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return dt.date(y, m, day)


def main() -> int:
    ap = argparse.ArgumentParser(description="Policy review tracker")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--due-days", type=int, default=60)
    args = ap.parse_args()
    if not args.csv.exists():
        emit(Level.FAIL, f"not found: {args.csv}")
        return 3

    with args.csv.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    rep = Report()
    overdue = due_soon = 0
    for r in rows:
        last = pdate(r.get("last_reviewed") or r.get("approved_date", ""))
        cad = r.get("review_cadence_months", "12")
        cad = int(cad) if str(cad).strip().isdigit() else 12
        if not last:
            rep.warn(f"{r.get('policy_id')}: no last_reviewed/approved date.")
            continue
        nxt = add_months(last, cad)
        if nxt < TODAY:
            overdue += 1
            rep.fail(f"OVERDUE {(TODAY-nxt).days}d — {r.get('policy_id')} "
                     f"'{r.get('title')}' (owner {r.get('owner')}, due {nxt})")
        elif (nxt - TODAY).days <= args.due_days:
            due_soon += 1
            rep.warn(f"Due in {(nxt-TODAY).days}d — {r.get('policy_id')} '{r.get('title')}' ({nxt})")

    emit(Level.INFO, f"Policies: {len(rows)} total, {overdue} overdue, "
                     f"{due_soon} due within {args.due_days}d")
    if overdue == 0:
        rep.ok("No policies overdue for review.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
