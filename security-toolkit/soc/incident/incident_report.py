#!/usr/bin/env python3
"""Generate a compliance-aligned cyber incident report and reporting deadline.

Given the regime (dod / federal / critical_infrastructure / fedramp), the
incident category/type, and the discovery time, this:
  - resolves the reporting authority and channel,
  - computes the reporting DEADLINE from the discovery timestamp, and
  - emits a structured report (Markdown + JSON) with the required fields.

The timelines below reflect commonly documented requirements. THEY MUST BE
VERIFIED against the current issuance (CJCSM 6510.01B, FISMA/CISA guidance,
CIRCIA final rule, your CSSP/AO SOP) — they are configurable here on purpose.

Usage:
  python incident_report.py --regime dod --category 1 \
     --discovered 2026-02-01T14:30:00Z --summary "root-level intrusion host X"
  python incident_report.py --regime federal --discovered 2026-02-01T14:30:00Z \
     --summary "confirmed data breach"
  python incident_report.py --regime critical_infrastructure --ransom-paid \
     --discovered 2026-02-01T14:30:00Z --summary "ransomware, payment made"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import emit, Level  # noqa: E402

# CJCSM 6510.01B incident categories (classic set — verify current edition).
DOD_CATEGORIES = {
    "1": ("Root/Admin-Level Intrusion", 1),
    "2": ("User-Level Intrusion", 1),
    "3": ("Unsuccessful Activity Attempt", 24),
    "4": ("Denial of Service", 1),
    "5": ("Non-Compliance Activity", 72),
    "6": ("Reconnaissance", 72),
    "7": ("Malicious Logic", 1),
    "8": ("Investigating", 24),
    "9": ("Explained Anomaly", 168),
}

# Regime -> reporting authority/channel + default deadline (hours) resolver.
REGIMES = {
    "dod": {
        "authority": "JFHQ-DODIN via JIMS (Joint Incident Management System); "
                     "CAT 1/2/4 also to DoD LE/CI",
        "basis": "DoDI 8530.03 / CJCSM 6510.01B / DTM-24-001",
    },
    "federal": {
        "authority": "CISA (report to CISA within 1 hour of discovery)",
        "basis": "FISMA (44 U.S.C. 3554) / OMB M-21-31",
        "deadline_hours": 1,
    },
    "fedramp": {
        "authority": "Agency AO + FedRAMP PMO (and CISA within 1 hour)",
        "basis": "FedRAMP Continuous Monitoring / FISMA",
        "deadline_hours": 1,
    },
    "critical_infrastructure": {
        "authority": "CISA (CIRCIA covered-incident report)",
        "basis": "CIRCIA — 72 hrs incident / 24 hrs ransom payment",
        "deadline_hours": 72,
        "ransom_hours": 24,
    },
}

REQUIRED_FIELDS = [
    "Incident ID / tracking number",
    "Reporting organization & POC (name, phone, email)",
    "Discovery date/time (UTC) and detection method",
    "Affected systems / IP / hostname / enclave / data impacted",
    "Incident category & description",
    "Attack vector / TTPs (map to MITRE ATT&CK)",
    "Current status & containment actions taken",
    "Classification of the report itself (e.g., CUI)",
]


def parse_ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def resolve_deadline(regime: str, category: str | None, ransom: bool):
    r = REGIMES[regime]
    if regime == "dod":
        if not category or category not in DOD_CATEGORIES:
            return None, "Select a CJCSM category (--category 1..9) to compute the deadline."
        name, hours = DOD_CATEGORIES[category]
        return hours, f"CAT {category} — {name}"
    if regime == "critical_infrastructure" and ransom:
        return r["ransom_hours"], "Ransom payment made (CIRCIA 24-hr clock)"
    return r.get("deadline_hours"), r["basis"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Cyber incident report + deadline")
    ap.add_argument("--regime", required=True, choices=list(REGIMES))
    ap.add_argument("--category", default=None, help="DoD CJCSM category 1..9")
    ap.add_argument("--discovered", required=True, help="ISO8601 discovery time (UTC)")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--ransom-paid", action="store_true",
                    help="critical_infrastructure: a ransom payment was made")
    ap.add_argument("--org", default="<reporting org>")
    ap.add_argument("--poc", default="<name / phone / email>")
    ap.add_argument("--out", default=None, help="Output basename (default: incident_<ts>)")
    args = ap.parse_args()

    try:
        discovered = parse_ts(args.discovered)
    except ValueError as exc:
        emit(Level.FAIL, f"Bad --discovered time: {exc}")
        return 3

    r = REGIMES[args.regime]
    hours, basis = resolve_deadline(args.regime, args.category, args.ransom_paid)

    emit(Level.INFO, f"Regime   : {args.regime} — {r['basis']}")
    emit(Level.INFO, f"Authority: {r['authority']}")
    emit(Level.INFO, f"Basis    : {basis}")

    deadline = None
    if hours is not None:
        deadline = discovered + dt.timedelta(hours=hours)
        now = dt.datetime.now(dt.timezone.utc)
        remaining = (deadline - now).total_seconds() / 3600
        lvl = Level.OK if remaining > 2 else (Level.WARN if remaining > 0 else Level.FAIL)
        emit(lvl, f"Report by: {deadline:%Y-%m-%dT%H:%M:%SZ} "
                  f"({hours}h after discovery; {remaining:+.1f}h from now)")
        if remaining <= 0:
            emit(Level.FAIL, "DEADLINE PASSED — report immediately and note the delay.")
    else:
        emit(Level.WARN, basis)

    # Build the report artifacts.
    base = args.out or f"incident_{discovered:%Y%m%dT%H%M%SZ}"
    report = {
        "regime": args.regime,
        "authority": r["authority"],
        "basis": r["basis"],
        "category": (f"CAT {args.category} — {DOD_CATEGORIES.get(args.category, ('',))[0]}"
                     if args.regime == "dod" and args.category else None),
        "discovered_utc": f"{discovered:%Y-%m-%dT%H:%M:%SZ}",
        "report_deadline_utc": f"{deadline:%Y-%m-%dT%H:%M:%SZ}" if deadline else None,
        "summary": args.summary,
        "org": args.org,
        "poc": args.poc,
        "required_fields": REQUIRED_FIELDS,
    }
    Path(f"{base}.json").write_text(json.dumps(report, indent=2))

    md = [f"# Cyber Incident Report — {args.regime.upper()}", "",
          f"- **Reporting basis:** {r['basis']}",
          f"- **Report to:** {r['authority']}",
          f"- **Category:** {report['category'] or 'n/a'}",
          f"- **Discovered (UTC):** {report['discovered_utc']}",
          f"- **Report by (UTC):** {report['report_deadline_utc'] or 'per SOP — verify'}",
          f"- **Reporting org:** {args.org}",
          f"- **POC:** {args.poc}", "",
          "## Summary", args.summary, "",
          "## Required fields (complete before submission)"]
    md += [f"- [ ] {f}" for f in REQUIRED_FIELDS]
    md += ["", "> Verify the deadline and channel against the current issuance and "
               "your CSSP/AO SOP before submitting. Mark the report's classification (e.g., CUI)."]
    Path(f"{base}.md").write_text("\n".join(md) + "\n")

    emit(Level.OK, f"Wrote {base}.md and {base}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
