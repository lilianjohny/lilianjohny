#!/usr/bin/env python3
"""GRC executive dashboard — aggregate governance, risk, and compliance.

Rolls up the GRC tools (and, when provided, the toolkit's POA&M and vuln
metrics) into one Markdown report for a risk committee / leadership review.

Usage:
  python grc_dashboard.py \
     --risk ../risk/risk_register.csv \
     --catalog ../compliance/control_catalog.csv --status status.csv \
     --policies ../governance/policy_register.csv \
     [--poam poam.csv] [--vulns enriched.jsonl] \
     --out grc_dashboard.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRC = HERE.parent
TOOLKIT = GRC.parent


def run(argv: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run([sys.executable, *argv], capture_output=True, text=True, timeout=120)
        return p.returncode, (p.stdout + p.stderr).rstrip()
    except Exception as exc:  # noqa: BLE001
        return 3, f"(could not run {argv}: {exc})"


def section(lines, title, argv):
    lines += [f"## {title}", "", "```"]
    rc, out = run(argv)
    lines += [out, "```", ""]
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="GRC executive dashboard")
    ap.add_argument("--risk", type=Path)
    ap.add_argument("--catalog", type=Path)
    ap.add_argument("--status", type=Path)
    ap.add_argument("--policies", type=Path)
    ap.add_argument("--poam", type=Path)
    ap.add_argument("--vulns", type=Path)
    ap.add_argument("--appetite", type=float, default=9.0)
    ap.add_argument("--out", default="grc_dashboard.md")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    lines = ["# GRC Executive Dashboard", "",
             f"_Generated {now:%Y-%m-%dT%H:%M:%SZ}. Governance, Risk & Compliance "
             "roll-up. Decision support — verify against your registers and assessors._", ""]
    worst = 0

    if args.risk and args.risk.exists():
        rc = section(lines, "Risk — register & appetite",
                     [str(GRC / "risk" / "risk_register.py"), str(args.risk),
                      "--appetite", str(args.appetite)])
        worst = max(worst, rc)

    if args.catalog and args.status and args.catalog.exists() and args.status.exists():
        rc = section(lines, "Compliance — multi-framework coverage",
                     [str(GRC / "compliance" / "crosswalk.py"),
                      "--catalog", str(args.catalog), "--status", str(args.status)])
        worst = max(worst, rc)

    if args.policies and args.policies.exists():
        rc = section(lines, "Governance — policy review status",
                     [str(GRC / "governance" / "policy_review_tracker.py"), str(args.policies)])
        worst = max(worst, rc)

    if args.poam and args.poam.exists():
        rc = section(lines, "POA&M — remediation plan status",
                     [str(TOOLKIT / "soc" / "poam" / "poam_tracker.py"), str(args.poam),
                      "--due-days", "30"])
        worst = max(worst, rc)

    if args.vulns and args.vulns.exists():
        rc = section(lines, "Vulnerabilities — SLA & KEV exposure",
                     [str(TOOLKIT / "vulnmgmt" / "track" / "sla_tracker.py"), str(args.vulns)])
        worst = max(worst, rc)

    lines += ["## How this ties together",
              "Governance sets appetite & policy; Risk tracks residual exposure vs "
              "appetite; Compliance proves controls across frameworks. The same "
              "controls feed SOC 2 (`../soc-reports/`), DoD/public-sector ConMon "
              "(`../soc/`), and vulnerability management (`../vulnmgmt/`).", ""]

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"[OK] Wrote {args.out} (aggregate status rc={worst})")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
