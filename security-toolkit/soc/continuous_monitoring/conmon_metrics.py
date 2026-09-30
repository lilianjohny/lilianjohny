#!/usr/bin/env python3
"""Continuous Monitoring (ConMon) KPIs for RMF/FedRAMP-style reporting.

Computes the metrics a SOC reports monthly: open vulnerabilities by severity,
remediation SLA compliance (vuln aging), and POA&M status. Read-only.

Inputs:
  --vulns  JSON list of findings:
     [{"id":"CVE-...","severity":"critical|high|medium|low",
       "first_seen":"2026-01-01","status":"open|closed"}]
  --poam   CSV with columns incl. severity,status,scheduled_completion (see poam_template.csv)

FedRAMP-style remediation SLAs (days) are the defaults; override with --sla.

Usage:
  python conmon_metrics.py --vulns scans.json --poam poam.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

DEFAULT_SLA = {"critical": 15, "high": 30, "medium": 90, "low": 180}
TODAY = dt.date.today()


def parse_date(s: str) -> dt.date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(s.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def analyze_vulns(rep: Report, path: Path, sla: dict) -> None:
    data = json.loads(path.read_text())
    open_by_sev = {k: 0 for k in DEFAULT_SLA}
    breaches = {k: 0 for k in DEFAULT_SLA}
    for v in data:
        if str(v.get("status", "open")).lower() != "open":
            continue
        sev = str(v.get("severity", "")).lower()
        if sev not in open_by_sev:
            continue
        open_by_sev[sev] += 1
        fs = parse_date(str(v.get("first_seen", "")))
        if fs:
            age = (TODAY - fs).days
            if age > sla.get(sev, 99999):
                breaches[sev] += 1
    emit(Level.INFO, "Open vulnerabilities by severity:")
    for sev in ("critical", "high", "medium", "low"):
        emit(Level.INFO, f"  {sev:8}: {open_by_sev[sev]} open, {breaches[sev]} past {sla[sev]}d SLA")
        if breaches[sev] > 0:
            lvl = rep.fail if sev in ("critical", "high") else rep.warn
            lvl(f"{breaches[sev]} {sev} finding(s) breach the {sla[sev]}-day remediation SLA.")
    if all(b == 0 for b in breaches.values()):
        rep.ok("All open findings are within remediation SLA.")


def analyze_poam(rep: Report, path: Path) -> None:
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        emit(Level.INFO, "POA&M file empty.")
        return
    open_items = overdue = 0
    for row in rows:
        status = (row.get("status") or row.get("Status") or "").strip().lower()
        if status in ("closed", "completed", "remediated", "risk accepted"):
            continue
        open_items += 1
        sched = parse_date(row.get("scheduled_completion") or row.get("Scheduled Completion Date") or "")
        if sched and sched < TODAY:
            overdue += 1
    emit(Level.INFO, f"POA&M: {open_items} open item(s), {overdue} overdue.")
    if overdue:
        rep.fail(f"{overdue} POA&M item(s) past scheduled completion.")
    else:
        rep.ok("No overdue POA&M items.")


def main() -> int:
    ap = argparse.ArgumentParser(description="ConMon KPIs")
    ap.add_argument("--vulns", type=Path)
    ap.add_argument("--poam", type=Path)
    ap.add_argument("--sla", help="Override SLAs, e.g. critical=15,high=30,medium=90,low=180")
    args = ap.parse_args()

    sla = dict(DEFAULT_SLA)
    if args.sla:
        for pair in args.sla.split(","):
            k, _, v = pair.partition("=")
            if k.strip() in sla and v.strip().isdigit():
                sla[k.strip()] = int(v)

    if not args.vulns and not args.poam:
        emit(Level.FAIL, "Provide --vulns and/or --poam.")
        return 3

    rep = Report()
    if args.vulns and args.vulns.exists():
        analyze_vulns(rep, args.vulns, sla)
    elif args.vulns:
        rep.warn(f"Vulns file not found: {args.vulns}")
    if args.poam and args.poam.exists():
        analyze_poam(rep, args.poam)
    elif args.poam:
        rep.warn(f"POA&M file not found: {args.poam}")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
