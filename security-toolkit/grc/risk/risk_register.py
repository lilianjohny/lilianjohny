#!/usr/bin/env python3
"""Risk register analysis — inherent/residual scoring, heat map, treatment status.

Reads a risk register CSV and computes, per risk:
  - inherent risk   = likelihood × impact (5×5 → 1..25)
  - residual risk   = inherent × (1 − control_effectiveness), rounded
  - risk level band (Low / Medium / High / Critical)
Then reports the heat-map distribution, risks that exceed the risk appetite,
overdue reviews, accepted risks past their expiry, and the top residual risks.

CSV columns (see risk_register.csv):
  risk_id, description, category, likelihood(1-5), impact(1-5),
  controls, control_effectiveness(0..1), treatment, owner, status,
  review_date, acceptance_expiry, kri

Usage:
  python risk_register.py risk_register.csv [--appetite 9]
Exit: 0 none over appetite/overdue · 2 risks over appetite or overdue · 3 error
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


def band(score: float) -> str:
    if score >= 15:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def pdate(s: str):
    for f in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            continue
    return None


def num(s, default=0.0):
    try:
        return float(str(s).strip())
    except (ValueError, AttributeError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser(description="Risk register analysis")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--appetite", type=float, default=9.0,
                    help="Residual risk above this exceeds appetite (default 9 = High+)")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    if not args.csv.exists():
        emit(Level.FAIL, f"not found: {args.csv}")
        return 3

    with args.csv.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        emit(Level.FAIL, "risk register is empty")
        return 3

    rep = Report()
    enriched = []
    bands = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    over_appetite = 0

    for r in rows:
        status = (r.get("status") or "open").strip().lower()
        L, I = num(r.get("likelihood")), num(r.get("impact"))
        inh = L * I
        eff = max(0.0, min(1.0, num(r.get("control_effectiveness"))))
        res = round(inh * (1 - eff))
        r["_inherent"], r["_residual"], r["_band"] = inh, res, band(res)
        enriched.append(r)
        if status in ("closed",):
            continue
        bands[band(res)] += 1
        if res > args.appetite and status != "accepted":
            over_appetite += 1
            rep.fail(f"OVER APPETITE — {r.get('risk_id')} [{r.get('_band')} {res}] "
                     f"{r.get('description','')[:50]} (owner {r.get('owner')})")

    # Overdue reviews + expired acceptances
    for r in enriched:
        status = (r.get("status") or "open").strip().lower()
        if status == "closed":
            continue
        rv = pdate(r.get("review_date", ""))
        if rv and rv < TODAY:
            rep.warn(f"Review overdue {(TODAY-rv).days}d — {r.get('risk_id')}")
        if status == "accepted":
            ax = pdate(r.get("acceptance_expiry", ""))
            if ax and ax < TODAY:
                rep.fail(f"Risk acceptance EXPIRED {(TODAY-ax).days}d — {r.get('risk_id')} "
                         "(re-assess or re-approve)")

    emit(Level.INFO, "Heat-map (residual, open risks): "
                     f"Critical {bands['Critical']}  High {bands['High']}  "
                     f"Medium {bands['Medium']}  Low {bands['Low']}")
    emit(Level.INFO, f"Risk appetite threshold: residual > {args.appetite}")

    emit(Level.INFO, f"Top {args.top} residual risks:")
    for r in sorted(enriched, key=lambda x: x["_residual"], reverse=True)[:args.top]:
        emit(Level.INFO, f"  {r.get('risk_id')} [{r['_band']} {r['_residual']}] "
                         f"(inherent {int(r['_inherent'])}) — {r.get('description','')[:55]}")

    if over_appetite == 0:
        rep.ok("No open risks exceed the risk appetite.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
