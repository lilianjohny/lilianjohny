#!/usr/bin/env python3
"""Multi-framework compliance crosswalk — "implement once, comply with many".

Given a master control catalog (each control mapped to its equivalents across
frameworks) and your control implementation status, this reports coverage per
framework and which framework requirements are unmet — so one control set can
be measured against NIST 800-53, CSF 2.0, ISO 27001, SOC 2, PCI-DSS, CIS, and
CMMC at the same time.

Inputs:
  --catalog  control_catalog.csv (control_id + per-framework refs)
  --status   CSV with columns control_id, status
             (implemented|partial|not_implemented|not_applicable)
             — e.g. the SOC-2 controls_evidence.csv or soc/frameworks mapping.

Usage:
  python crosswalk.py --catalog control_catalog.csv --status my_status.csv
  python crosswalk.py --catalog control_catalog.csv --status my_status.csv --framework iso_27001
Exit: 0 all frameworks fully covered · 1 gaps · 3 error
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

FRAMEWORKS = {
    "nist_800_53": "NIST SP 800-53",
    "nist_csf_2": "NIST CSF 2.0",
    "iso_27001": "ISO/IEC 27001",
    "soc2_tsc": "SOC 2 (TSC)",
    "pci_dss_4": "PCI-DSS v4",
    "cis_v8": "CIS v8",
    "cmmc_l2": "CMMC L2",
}
IMPLEMENTED = {"implemented", "not_applicable", "na", "n/a"}


def load_status(path: Path) -> dict[str, str]:
    st: dict[str, str] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            cid = (row.get("control_id") or "").strip()
            status = (row.get("status") or "").strip().lower().replace(" ", "_")
            if cid:
                st[cid] = status
    return st


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-framework crosswalk coverage")
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--framework", choices=list(FRAMEWORKS), default=None,
                    help="Limit output to one framework")
    args = ap.parse_args()
    for p in (args.catalog, args.status):
        if not p.exists():
            emit(Level.FAIL, f"not found: {p}")
            return 3

    with args.catalog.open(newline="") as fh:
        catalog = list(csv.DictReader(fh))
    status = load_status(args.status)

    frameworks = [args.framework] if args.framework else list(FRAMEWORKS)
    rep = Report()
    any_gap = False

    for fw in frameworks:
        # Requirements this framework has (via mapped controls in the catalog),
        # and whether the control satisfying each is implemented.
        reqs: dict[str, bool] = {}  # framework-ref -> covered?
        for ctrl in catalog:
            refs = [x.strip() for x in (ctrl.get(fw) or "").replace(",", ";").split(";") if x.strip()]
            if not refs:
                continue
            impl = status.get(ctrl["control_id"], "not_implemented") in IMPLEMENTED
            for ref in refs:
                reqs[ref] = reqs.get(ref, False) or impl
        if not reqs:
            continue
        covered = sum(1 for v in reqs.values() if v)
        total = len(reqs)
        pct = round(100 * covered / total)
        lvl = Level.OK if pct == 100 else (Level.WARN if pct >= 60 else Level.FAIL)
        emit(lvl, f"{FRAMEWORKS[fw]:16} {pct:3}% covered  ({covered}/{total} mapped requirements)")
        unmet = sorted(r for r, v in reqs.items() if not v)
        if unmet:
            any_gap = True
            emit(Level.INFO, f"    unmet: {', '.join(unmet[:12])}"
                             + (" …" if len(unmet) > 12 else ""))

    # Which controls are the highest-leverage to fix (map to most frameworks)?
    if not args.framework:
        emit(Level.INFO, "Highest-leverage unimplemented controls (map to most frameworks):")
        leverage = []
        for ctrl in catalog:
            if status.get(ctrl["control_id"], "not_implemented") in IMPLEMENTED:
                continue
            n = sum(1 for fw in FRAMEWORKS if (ctrl.get(fw) or "").strip())
            leverage.append((n, ctrl["control_id"], ctrl.get("control_name", "")))
        for n, cid, name in sorted(leverage, reverse=True)[:5]:
            emit(Level.INFO, f"  {cid} — {name} (covers {n} frameworks)")

    if any_gap:
        rep.warn("One or more frameworks have unmet requirements (see above).")
    else:
        rep.ok("All mapped framework requirements are covered.")
    rep.summary()
    return 0 if not any_gap else 1


if __name__ == "__main__":
    raise SystemExit(main())
