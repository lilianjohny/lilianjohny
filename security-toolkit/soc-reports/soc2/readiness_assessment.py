#!/usr/bin/env python3
"""SOC 2 readiness assessment — score control coverage vs Trust Services Criteria.

Compares your controls (mapped to TSC criteria, with an implementation status)
against the full TSC for the in-scope categories, and reports per-criterion
coverage, gaps, and an overall readiness score. Read-only. This estimates
audit readiness — only a licensed CPA firm issues a SOC 2 report.

Inputs:
  --tsc      trust_services_criteria.csv (shipped)
  --controls controls CSV with columns:
             control_id, tsc_criteria (";"-separated, e.g. CC6.1;CC6.2),
             status (implemented|partial|not_implemented|not_applicable),
             evidence
  --categories  which TSC categories are IN SCOPE (default: security only).
                Security (Common Criteria) is always required.

Usage:
  python readiness_assessment.py --tsc trust_services_criteria.csv \
      --controls controls_matrix.csv --categories security,availability,confidentiality
Exit: 0 ready (no gaps) · 1 partial gaps · 2 uncovered required criteria · 3 error
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

CATEGORY_KEYS = {
    "security": "Security (Common Criteria)",
    "availability": "Availability",
    "confidentiality": "Confidentiality",
    "processing_integrity": "Processing Integrity",
    "privacy": "Privacy",
}


def load_tsc(path: Path) -> dict[str, str]:
    crit: dict[str, str] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            crit[row["criterion"].strip()] = row["category"].strip()
    return crit


def load_controls(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser(description="SOC 2 readiness assessment")
    ap.add_argument("--tsc", type=Path, required=True)
    ap.add_argument("--controls", type=Path, required=True)
    ap.add_argument("--categories", default="security",
                    help="comma list: security,availability,confidentiality,processing_integrity,privacy")
    args = ap.parse_args()

    for p in (args.tsc, args.controls):
        if not p.exists():
            emit(Level.FAIL, f"File not found: {p}")
            return 3

    tsc = load_tsc(args.tsc)
    controls = load_controls(args.controls)

    scoped = {c.strip().lower() for c in args.categories.split(",")}
    scoped.add("security")  # Common Criteria always required
    scoped_cats = {CATEGORY_KEYS[c] for c in scoped if c in CATEGORY_KEYS}
    in_scope_criteria = {cid for cid, cat in tsc.items() if cat in scoped_cats}
    emit(Level.INFO, f"In-scope categories: {', '.join(sorted(scoped_cats))}")
    emit(Level.INFO, f"In-scope TSC criteria: {len(in_scope_criteria)}")

    # Map criterion -> best status among mapped controls.
    RANK = {"implemented": 3, "partial": 2, "not_applicable": 1, "not_implemented": 0}
    best: dict[str, int] = {c: -1 for c in in_scope_criteria}
    mapped_controls = 0
    for ctrl in controls:
        status = (ctrl.get("status") or "").strip().lower().replace(" ", "_")
        rank = RANK.get(status, 0)
        crits = [c.strip() for c in (ctrl.get("tsc_criteria") or "").replace(",", ";").split(";") if c.strip()]
        if crits:
            mapped_controls += 1
        for c in crits:
            if c in best:
                best[c] = max(best[c], rank)

    rep = Report()
    uncovered, partial, covered, na = [], [], [], []
    for c in sorted(in_scope_criteria):
        b = best[c]
        if b < 0 or b == 0:
            uncovered.append(c)
        elif b == 2:
            partial.append(c)
        elif b == 1:
            na.append(c)
        else:
            covered.append(c)

    for c in uncovered:
        rep.fail(f"NO implemented control mapped to {c} ({tsc[c]})")
    for c in partial:
        rep.warn(f"Only PARTIAL coverage for {c} ({tsc[c]})")

    total = len(in_scope_criteria)
    score = round(100 * (len(covered) + 0.5 * len(partial) + len(na)) / total) if total else 0
    emit(Level.INFO, f"Controls mapped: {mapped_controls}")
    emit(Level.INFO, f"Covered: {len(covered)}  Partial: {len(partial)}  "
                     f"N/A: {len(na)}  Uncovered: {len(uncovered)}")
    lvl = Level.OK if score >= 90 and not uncovered else (Level.WARN if score >= 70 else Level.FAIL)
    emit(lvl, f"Estimated SOC 2 readiness: {score}%")
    if uncovered:
        emit(Level.FAIL, f"{len(uncovered)} required criteria have no implemented control — not audit-ready.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
