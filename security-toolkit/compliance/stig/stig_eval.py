#!/usr/bin/env python3
"""DISA STIG checklist (.ckl) evaluator & CI gate.

Parses a DISA STIG Viewer checklist (.ckl XML) and scores findings by
severity category, so you can (a) see where a system stands against its STIG
and (b) gate a pipeline on open findings — the STIG-compliance evidence an
AWS/Windows/Linux admin on a DoD RMF system is responsible for.

Severity map (DISA):  high = CAT I · medium = CAT II · low = CAT III
Statuses:  Open · NotAFinding · Not_Applicable · Not_Reviewed

Gate (--fail-on):
  cat1  -> exit 2 if any open CAT I            (default)
  cat2  -> exit 2 if any open CAT I or CAT II
  any   -> exit 2 if any open finding at all
Open items below the gate, and any Not_Reviewed items, produce warnings (exit 1).

Exit codes: 0 clean · 1 warnings · 2 gate failure · 3 setup error.

Usage:
    python stig_eval.py system.ckl
    python stig_eval.py system.ckl --fail-on cat2
    python stig_eval.py *.ckl --fail-on any
"""
from __future__ import annotations

import argparse
import glob
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

SEV_TO_CAT = {"high": "CAT I", "medium": "CAT II", "low": "CAT III"}
OPEN = "Open"
NOT_REVIEWED = "Not_Reviewed"


def _attr(vuln: ET.Element, name: str) -> str:
    """Return the ATTRIBUTE_DATA for a given VULN_ATTRIBUTE name."""
    for sd in vuln.findall("STIG_DATA"):
        va = sd.findtext("VULN_ATTRIBUTE")
        if va == name:
            return (sd.findtext("ATTRIBUTE_DATA") or "").strip()
    return ""


def parse_ckl(path: str) -> list[dict]:
    """Parse a .ckl file into a list of finding dicts."""
    tree = ET.parse(path)
    root = tree.getroot()
    findings = []
    for istig in root.iter("iSTIG"):
        for vuln in istig.findall("VULN"):
            findings.append({
                "vuln_num": _attr(vuln, "Vuln_Num"),
                "severity": _attr(vuln, "Severity").lower(),
                "cat": SEV_TO_CAT.get(_attr(vuln, "Severity").lower(), "?"),
                "rule_title": _attr(vuln, "Rule_Title"),
                "status": (vuln.findtext("STATUS") or "").strip(),
            })
    return findings


def evaluate(rep: Report, findings: list[dict], fail_on: str, source: str) -> None:
    by_status: dict[str, int] = {}
    open_by_cat = {"CAT I": [], "CAT II": [], "CAT III": []}
    not_reviewed = 0

    for f in findings:
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1
        if f["status"] == OPEN and f["cat"] in open_by_cat:
            open_by_cat[f["cat"]].append(f["vuln_num"])
        if f["status"] == NOT_REVIEWED:
            not_reviewed += 1

    emit(Level.INFO, f"{source}: {len(findings)} checks — " +
         ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))

    gate_cats = {"cat1": {"CAT I"},
                 "cat2": {"CAT I", "CAT II"},
                 "any": {"CAT I", "CAT II", "CAT III"}}[fail_on]

    for cat in ("CAT I", "CAT II", "CAT III"):
        ids = open_by_cat[cat]
        if not ids:
            continue
        msg = f"{source}: {len(ids)} open {cat} finding(s): {', '.join(ids[:8])}"
        if cat in gate_cats:
            rep.fail(msg)
        else:
            rep.warn(msg)

    if not any(open_by_cat.values()):
        rep.ok(f"{source}: no open findings.")

    if not_reviewed:
        rep.warn(f"{source}: {not_reviewed} check(s) Not_Reviewed — review them "
                 f"(an unreviewed control is not a passed control).")


def main() -> int:
    ap = argparse.ArgumentParser(description="DISA STIG .ckl evaluator / gate")
    ap.add_argument("files", nargs="+", help=".ckl file(s) or globs")
    ap.add_argument("--fail-on", choices=["cat1", "cat2", "any"], default="cat1",
                    help="Severity level that fails the gate (default cat1).")
    args = ap.parse_args()

    paths: list[str] = []
    for pattern in args.files:
        paths.extend(glob.glob(pattern))
    if not paths:
        emit(Level.FAIL, "No .ckl files matched.")
        return 3

    rep = Report()
    for path in paths:
        try:
            findings = parse_ckl(path)
        except (ET.ParseError, OSError) as exc:
            rep.fail(f"{path}: could not parse .ckl ({exc}).")
            continue
        evaluate(rep, findings, args.fail_on, Path(path).name)

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
