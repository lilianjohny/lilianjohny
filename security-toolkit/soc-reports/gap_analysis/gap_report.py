#!/usr/bin/env python3
"""Produce a SOC 2 gap-analysis report from a controls matrix.

Lists controls that are not_implemented or partial, groups by TSC category,
and writes a remediation-oriented Markdown report. Read-only.

Usage:
  python gap_report.py --controls ../soc2/controls_matrix.csv \
      --tsc ../soc2/trust_services_criteria.csv --out gap_report.md
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import emit, Level  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="SOC 2 gap-analysis report")
    ap.add_argument("--controls", type=Path, required=True)
    ap.add_argument("--tsc", type=Path, required=True)
    ap.add_argument("--out", default="gap_report.md")
    args = ap.parse_args()
    for p in (args.controls, args.tsc):
        if not p.exists():
            emit(Level.FAIL, f"File not found: {p}")
            return 3

    with args.tsc.open(newline="") as fh:
        tsc = {r["criterion"].strip(): (r["category"].strip(), r["title"].strip())
               for r in csv.DictReader(fh)}
    with args.controls.open(newline="") as fh:
        controls = list(csv.DictReader(fh))

    gaps = []  # (severity, control)
    for c in controls:
        status = (c.get("status") or "").strip().lower().replace(" ", "_")
        if status in ("not_implemented", "partial"):
            gaps.append((status, c))

    now = dt.datetime.now(dt.timezone.utc)
    lines = ["# SOC 2 Gap Analysis", "",
             f"_Generated {now:%Y-%m-%dT%H:%M:%SZ}. Readiness estimate — a licensed "
             "CPA firm issues the SOC 2 report._", "",
             f"**Open gaps:** {len(gaps)} "
             f"(not implemented: {sum(1 for s,_ in gaps if s=='not_implemented')}, "
             f"partial: {sum(1 for s,_ in gaps if s=='partial')})", ""]

    if not gaps:
        lines += ["No gaps found in the controls matrix. Proceed to evidence collection."]
    else:
        lines += ["| Control | Description | TSC | Status | Owner | Remediation |",
                  "|---|---|---|---|---|---|"]
        order = {"not_implemented": 0, "partial": 1}
        for status, c in sorted(gaps, key=lambda x: order.get(x[0], 9)):
            crits = (c.get("tsc_criteria") or "").replace(";", ", ")
            lines.append(f"| {c.get('control_id','')} | {c.get('control_description','')} "
                         f"| {crits} | {status} | {c.get('owner','')} | _fill remediation + target date_ |")

    lines += ["", "## Affected TSC criteria",
              "Criteria touched by the gaps above (confirm none are left without an "
              "implemented control using `soc2/readiness_assessment.py`):", ""]
    touched = set()
    for _, c in gaps:
        for cr in (c.get("tsc_criteria") or "").replace(",", ";").split(";"):
            cr = cr.strip()
            if cr in tsc:
                touched.add(cr)
    for cr in sorted(touched):
        cat, title = tsc[cr]
        lines.append(f"- **{cr}** ({cat}): {title}")

    Path(args.out).write_text("\n".join(lines) + "\n")
    emit(Level.OK, f"Wrote {args.out} — {len(gaps)} gap(s), {len(touched)} TSC criteria affected.")
    return 0 if not gaps else 2


if __name__ == "__main__":
    raise SystemExit(main())
