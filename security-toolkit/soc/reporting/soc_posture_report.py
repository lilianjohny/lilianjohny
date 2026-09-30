#!/usr/bin/env python3
"""Roll ConMon, POA&M, and logging inputs into one SOC compliance posture report.

Aggregates the other soc/ tools' inputs into a single Markdown report suitable
for a monthly compliance review (RMF ConMon / FedRAMP / CSSP readiness).

Usage:
  python soc_posture_report.py --regime federal \
      --vulns scans.json --poam poam.csv --sources log_sources.json \
      --out soc_posture.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent


def run_tool(argv: list[str]) -> tuple[int, str]:
    """Run a soc tool as a subprocess, capture its output + exit code."""
    try:
        p = subprocess.run([sys.executable, *argv], capture_output=True, text=True, timeout=120)
        return p.returncode, (p.stdout + p.stderr)
    except Exception as exc:  # noqa: BLE001
        return 3, f"(could not run {argv}: {exc})"


def main() -> int:
    ap = argparse.ArgumentParser(description="SOC compliance posture report")
    ap.add_argument("--regime", default="federal",
                    choices=["dod", "federal", "fedramp", "critical_infrastructure"])
    ap.add_argument("--vulns", type=Path)
    ap.add_argument("--poam", type=Path)
    ap.add_argument("--sources", type=Path)
    ap.add_argument("--out", default="soc_posture.md")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    lines = [f"# SOC Compliance Posture — {args.regime.upper()}", "",
             f"_Generated {now:%Y-%m-%dT%H:%M:%SZ}._", "",
             "> Decision support aligned to the publicly documented frameworks; "
             "verify against current issuances and your AO/ISSM/CSSP.", ""]
    overall_rc = 0

    if args.vulns or args.poam:
        lines += ["## Continuous Monitoring (vulns + POA&M)", "", "```"]
        argv = [str(SOC / "continuous_monitoring" / "conmon_metrics.py")]
        if args.vulns: argv += ["--vulns", str(args.vulns)]
        if args.poam: argv += ["--poam", str(args.poam)]
        rc, out = run_tool(argv); overall_rc = max(overall_rc, rc)
        lines += [out.rstrip(), "```", ""]

    if args.poam:
        lines += ["## POA&M aging", "", "```"]
        rc, out = run_tool([str(SOC / "poam" / "poam_tracker.py"), str(args.poam), "--due-days", "30"])
        overall_rc = max(overall_rc, rc)
        lines += [out.rstrip(), "```", ""]

    if args.sources:
        lines += ["## Event-logging maturity (OMB M-21-31)", "", "```"]
        rc, out = run_tool([str(SOC / "logging" / "log_coverage_check.py"), "--sources", str(args.sources)])
        overall_rc = max(overall_rc, rc)
        lines += [out.rstrip(), "```", ""]

    lines += ["## Control coverage",
              "See `frameworks/control_mapping.csv` for SOC capability → NIST "
              "SP 800-53 → regime mapping and the toolkit support for each.", "",
              "## Reporting readiness",
              f"Incident reporting for **{args.regime}** — see "
              "`incident/reporting_timelines.md`; generate reports with "
              "`incident/incident_report.py`.", ""]

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"[OK] Wrote {args.out} (aggregate status rc={overall_rc})")
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
