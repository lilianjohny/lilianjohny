#!/usr/bin/env python3
"""Auto-link live toolkit output to SOC 2 controls (evidence collector).

Bridges the gap between "the toolkit produces the evidence" and the SOC 2
readiness assessment: it scans a directory of collected artifacts, matches them
to controls via an evidence-source mapping, and emits an evidence-backed
controls file that drops straight into readiness_assessment.py / gap_report.py.

A control's status is set from what is actually found:
  - implemented        → matching evidence artifact(s) present
  - not_implemented    → no evidence found (and a toolkit command is suggested)

Inputs:
  --sources   evidence_sources.csv (control_id, tsc_criteria, owner,
              evidence_glob (";"-separated globs), toolkit_command)
  --evidence-dir  directory holding collected artifacts (searched recursively)

Usage:
  python collect_evidence.py --sources ../soc2/evidence_sources.csv \
      --evidence-dir ./evidence_artifacts --out controls_evidence.csv
Then:
  python ../soc2/readiness_assessment.py --tsc ../soc2/trust_services_criteria.csv \
      --controls controls_evidence.csv --categories security,availability,confidentiality
Exit: 0 all controls have evidence · 1 some missing · 3 error
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402


def find_matches(evidence_dir: Path, globs: str) -> list[str]:
    hits: list[str] = []
    for g in (globs or "").split(";"):
        g = g.strip()
        if not g:
            continue
        for p in evidence_dir.rglob(g):
            if p.is_file():
                hits.append(str(p.relative_to(evidence_dir)))
    return sorted(set(hits))


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-link toolkit evidence to SOC 2 controls")
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--evidence-dir", type=Path, required=True)
    ap.add_argument("--out", default="controls_evidence.csv")
    args = ap.parse_args()

    if not args.sources.exists():
        emit(Level.FAIL, f"sources not found: {args.sources}")
        return 3
    if not args.evidence_dir.exists():
        emit(Level.WARN, f"evidence dir not found (treating all as missing): {args.evidence_dir}")

    with args.sources.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    rep = Report()
    out_rows = []
    have = 0
    for r in rows:
        cid = r["control_id"]
        matches = find_matches(args.evidence_dir, r.get("evidence_glob", "")) \
            if args.evidence_dir.exists() else []
        if matches:
            have += 1
            status = "implemented"
            evidence = "; ".join(matches[:5]) + (f" (+{len(matches)-5} more)" if len(matches) > 5 else "")
            rep.ok(f"{cid}: evidence found ({len(matches)}) — {matches[0]}")
        else:
            status = "not_implemented"
            evidence = f"MISSING — generate via: {r.get('toolkit_command', 'n/a')}"
            rep.warn(f"{cid}: no evidence — run: {r.get('toolkit_command', 'n/a')}")
        out_rows.append({
            "control_id": cid,
            "control_description": r.get("control_description", ""),
            "tsc_criteria": r.get("tsc_criteria", ""),
            "status": status,
            "owner": r.get("owner", ""),
            "evidence": evidence,
        })

    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["control_id", "control_description",
                                           "tsc_criteria", "status", "owner", "evidence"])
        w.writeheader()
        w.writerows(out_rows)

    emit(Level.INFO, f"{have}/{len(rows)} controls have live evidence. Wrote {args.out}")
    emit(Level.INFO, "Feed it to readiness_assessment.py / gap_report.py --controls "
                     f"{args.out}")
    rep.summary()
    return 0 if have == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
