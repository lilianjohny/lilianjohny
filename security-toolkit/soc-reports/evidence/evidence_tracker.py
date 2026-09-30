#!/usr/bin/env python3
"""Track SOC audit evidence / PBC (Prepared-By-Client) request status.

For a SOC 2 Type II (and SOC 1 Type II), evidence must be collected across the
audit period. This tracks each request's status and flags outstanding/overdue
items and sample-collection shortfalls. Read-only.

Input CSV columns (see evidence_request_list.csv):
  request_id, description, control_id, owner, due_date,
  status (not_started|in_progress|provided|accepted|na),
  samples_required, samples_collected

Usage:
  python evidence_tracker.py evidence_request_list.csv [--due-days 14]
Exit: 0 all accepted/na · 1 outstanding remain · 2 overdue items · 3 error
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
DONE = {"accepted", "na", "n/a"}


def pdate(s: str) -> dt.date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime((s or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="SOC evidence / PBC tracker")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--due-days", type=int, default=14)
    args = ap.parse_args()
    if not args.csv.exists():
        emit(Level.FAIL, f"File not found: {args.csv}")
        return 3

    with args.csv.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        emit(Level.FAIL, "Evidence list is empty.")
        return 3

    rep = Report()
    total = len(rows)
    done = outstanding = overdue = sample_short = 0
    for r in rows:
        rid = (r.get("request_id") or "?").strip()
        status = (r.get("status") or "not_started").strip().lower()
        ctl = (r.get("control_id") or "").strip()
        if status in DONE:
            done += 1
        else:
            outstanding += 1
            due = pdate(r.get("due_date", ""))
            if due and due < TODAY:
                overdue += 1
                rep.fail(f"OVERDUE {(TODAY - due).days}d — {rid} [{ctl}] status={status}")
            elif due and (due - TODAY).days <= args.due_days:
                rep.warn(f"Due in {(due - TODAY).days}d — {rid} [{ctl}] status={status}")
        # Sample completeness (Type II)
        req = (r.get("samples_required") or "").strip()
        got = (r.get("samples_collected") or "").strip()
        if req.isdigit() and got.isdigit() and int(got) < int(req):
            sample_short += 1
            rep.warn(f"Sample shortfall — {rid}: {got}/{req} collected")

    pct = round(100 * done / total)
    emit(Level.INFO, f"Evidence: {done}/{total} accepted ({pct}%), "
                     f"{outstanding} outstanding, {overdue} overdue, {sample_short} sample-short")
    if overdue == 0 and outstanding == 0:
        rep.ok("All evidence requests accepted or N/A.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
