#!/usr/bin/env python3
"""Bridge real scanner output into the ConMon --vulns format.

conmon_metrics.py expects a JSON list of findings; this produces it from the
tools a SOC actually runs, so ACAS/Nessus and the toolkit's own scanners are
wired in rather than only referenced.

Supported inputs (auto-detected):
  - Nessus / ACAS  export (.nessus XML)
  - vulnmgmt normalized findings (JSONL from vulnmgmt/ingest/normalize.py or
    the enrich/dedupe stages)

Output: JSON list of {id, severity, first_seen, status, asset, ...} on stdout.

Usage:
  python ingest_scans.py scan.nessus > vulns.json
  python ingest_scans.py deduped.jsonl --first-seen 2026-09-01 > vulns.json
  python ingest_scans.py scan.nessus more_findings.jsonl > vulns.json
Then:
  python conmon_metrics.py --vulns vulns.json --poam poam.csv
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TODAY = dt.date.today().isoformat()
NESSUS_SEV = {"0": "low", "1": "low", "2": "medium", "3": "high", "4": "critical"}


def from_nessus(path: Path, first_seen: str) -> list[dict]:
    out: list[dict] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"[WARN] {path}: not valid XML ({exc})", file=sys.stderr)
        return out
    for host in root.iter("ReportHost"):
        asset = host.get("name", "unknown")
        for item in host.iter("ReportItem"):
            sev = item.get("severity", "0")
            if sev == "0":
                continue  # skip informational
            cve_el = item.find("cve")
            vid = cve_el.text.strip() if cve_el is not None and cve_el.text else \
                f"plugin-{item.get('pluginID', '?')}"
            score = None
            for tag in ("cvss3_base_score", "cvss_base_score"):
                el = item.find(tag)
                if el is not None and el.text:
                    try:
                        score = float(el.text)
                    except ValueError:
                        pass
            out.append({
                "id": vid, "severity": NESSUS_SEV.get(sev, "low"),
                "cvss": score, "first_seen": first_seen, "status": "open",
                "asset": asset, "title": item.get("pluginName", ""),
                "source": "nessus",
            })
    return out


def from_jsonl(path: Path, first_seen: str) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            f = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.append({
            "id": f.get("vuln_id") or f.get("id"),
            "severity": f.get("severity", "low"),
            "cvss": f.get("cvss"),
            "first_seen": f.get("first_seen") or first_seen,
            "status": f.get("status", "open"),
            "asset": f.get("asset", ""),
            "title": f.get("title", ""),
            "source": f.get("source", "vulnmgmt"),
        })
    return out


def detect(path: Path, first_seen: str) -> list[dict]:
    head = path.read_text(errors="replace").lstrip()[:200]
    if head.startswith("<"):
        return from_nessus(path, first_seen)
    return from_jsonl(path, first_seen)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest scanner output -> ConMon vulns JSON")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--first-seen", default=TODAY,
                    help="first_seen date for findings lacking one (default: today)")
    args = ap.parse_args()

    all_findings: list[dict] = []
    for p in args.files:
        if not p.exists():
            print(f"[WARN] not found: {p}", file=sys.stderr)
            continue
        f = detect(p, args.first_seen)
        print(f"[INFO] {p.name}: {len(f)} findings", file=sys.stderr)
        all_findings.extend(f)

    print(json.dumps(all_findings, indent=2))
    print(f"[INFO] Total: {len(all_findings)} findings -> feed to conmon_metrics.py --vulns",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
