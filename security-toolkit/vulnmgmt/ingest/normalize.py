#!/usr/bin/env python3
"""Normalize scanner outputs into one common finding schema (JSONL).

Ingests the JSON output of common scanners and emits a unified findings stream
that the rest of the vulnerability-management pipeline (enrich → dedupe → track
→ report) consumes. Read-only.

Supported inputs (auto-detected):
  - Trivy      (trivy ... -f json)
  - Grype      (grype ... -o json)
  - nuclei     (nuclei ... -jsonl)
  - pip-audit  (pip-audit -f json)
  - Prowler    (json-ocsf, config findings)

Common finding fields:
  id, source, vuln_id, title, severity, cvss, component, version, fixed_version,
  asset, status, first_seen, fix

Usage:
  python normalize.py --asset web01 trivy.json grype.json > findings.jsonl
  python normalize.py --asset img:tag --source trivy trivy.json >> findings.jsonl
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

TODAY = dt.date.today().isoformat()
SEV_NORM = {"critical": "critical", "high": "high", "medium": "medium",
            "moderate": "medium", "low": "low", "info": "info",
            "informational": "info", "negligible": "low", "unknown": "low"}


def norm_sev(s: str) -> str:
    return SEV_NORM.get(str(s or "").strip().lower(), "low")


def fid(source: str, vuln: str, asset: str, comp: str) -> str:
    return hashlib.sha1(f"{source}|{vuln}|{asset}|{comp}".encode()).hexdigest()[:16]


def mk(source, vuln_id, title, severity, cvss, component, version, fixed, asset):
    return {
        "id": fid(source, vuln_id, asset, f"{component}:{version}"),
        "source": source, "vuln_id": vuln_id, "title": title,
        "severity": norm_sev(severity), "cvss": cvss,
        "component": component, "version": version, "fixed_version": fixed,
        "asset": asset, "status": "open", "first_seen": TODAY, "fix": fixed or "",
    }


def cvss_of(obj) -> float | None:
    # Trivy: CVSS dict; Grype: cvss list. Best-effort base score.
    try:
        if isinstance(obj, dict):
            for v in obj.values():
                for k in ("V3Score", "V4Score", "V2Score"):
                    if isinstance(v, dict) and v.get(k):
                        return float(v[k])
        if isinstance(obj, list):
            for c in obj:
                m = (c.get("metrics") or {})
                if m.get("baseScore"):
                    return float(m["baseScore"])
    except (ValueError, TypeError, AttributeError):
        return None
    return None


def parse_trivy(data, asset):
    out = []
    for res in data.get("Results", []) or []:
        tgt = res.get("Target", "")
        for v in res.get("Vulnerabilities", []) or []:
            out.append(mk("trivy", v.get("VulnerabilityID", "?"), v.get("Title", ""),
                          v.get("Severity", "low"), cvss_of(v.get("CVSS")),
                          v.get("PkgName", tgt), v.get("InstalledVersion", ""),
                          v.get("FixedVersion", ""), asset))
    return out


def parse_grype(data, asset):
    out = []
    for m in data.get("matches", []) or []:
        vuln = m.get("vulnerability", {}) or {}
        art = m.get("artifact", {}) or {}
        fixed = ""
        fx = vuln.get("fix", {}) or {}
        if fx.get("versions"):
            fixed = ", ".join(fx["versions"])
        out.append(mk("grype", vuln.get("id", "?"), vuln.get("description", ""),
                      vuln.get("severity", "low"), cvss_of(vuln.get("cvss")),
                      art.get("name", ""), art.get("version", ""), fixed, asset))
    return out


def parse_nuclei(lines, asset):
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        info = o.get("info", {}) or {}
        host = o.get("host") or o.get("matched-at") or asset
        out.append(mk("nuclei", o.get("template-id", "?"), info.get("name", ""),
                      info.get("severity", "info"), None, o.get("matched-at", ""),
                      "", "", host))
    return out


def parse_pip_audit(data, asset):
    out = []
    deps = data.get("dependencies", data if isinstance(data, list) else [])
    for d in deps:
        name = d.get("name", "")
        ver = d.get("version", "")
        for v in d.get("vulns", []) or []:
            fixed = ", ".join(v.get("fix_versions", []) or [])
            out.append(mk("pip-audit", v.get("id", "?"), v.get("description", ""),
                          "high", None, name, ver, fixed, asset))
    return out


def parse_prowler(data, asset):
    out = []
    items = data if isinstance(data, list) else data.get("findings", [])
    for f in items:
        status = (f.get("status_code") or f.get("status") or "").upper()
        if status not in ("FAIL", "FAILED"):
            continue
        sev = (f.get("severity") or (f.get("finding_info", {}) or {}).get("severity") or "medium")
        title = f.get("check_title") or f.get("message") or (f.get("finding_info", {}) or {}).get("title", "")
        res = f.get("resource_uid") or (f.get("resources", [{}])[0].get("uid") if f.get("resources") else asset)
        out.append(mk("prowler", f.get("check_id", "config"), title, sev, None,
                      res or asset, "", "", res or asset))
    return out


def detect_and_parse(path: Path, asset: str, forced: str | None):
    text = path.read_text(errors="replace")
    # nuclei is JSONL; others are JSON.
    stripped = text.lstrip()
    if forced == "nuclei" or (not stripped.startswith(("{", "[")) is False and "\n{" in text and '"template-id"' in text):
        if forced in (None, "nuclei") and '"template-id"' in text:
            return parse_nuclei(text.splitlines(), asset)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # assume nuclei jsonl
        return parse_nuclei(text.splitlines(), asset)

    if forced:
        return {"trivy": parse_trivy, "grype": parse_grype,
                "pip-audit": parse_pip_audit, "prowler": parse_prowler}[forced](data, asset)
    # auto-detect by shape
    if isinstance(data, dict) and "Results" in data:
        return parse_trivy(data, asset)
    if isinstance(data, dict) and "matches" in data:
        return parse_grype(data, asset)
    if isinstance(data, dict) and "dependencies" in data:
        return parse_pip_audit(data, asset)
    if isinstance(data, list) or "findings" in data:
        return parse_prowler(data, asset)
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize scanner outputs to common findings JSONL")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--asset", default="unknown", help="Asset id if the file lacks one")
    ap.add_argument("--source", choices=["trivy", "grype", "nuclei", "pip-audit", "prowler"],
                    default=None, help="Force the parser instead of auto-detect")
    args = ap.parse_args()

    total = 0
    for p in args.files:
        if not p.exists():
            print(f"[WARN] not found: {p}", file=sys.stderr)
            continue
        try:
            findings = detect_and_parse(p, args.asset, args.source)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] {p}: could not parse ({exc})", file=sys.stderr)
            continue
        for f in findings:
            print(json.dumps(f))
            total += 1
        print(f"[INFO] {p.name}: {len(findings)} findings", file=sys.stderr)
    print(f"[INFO] Total normalized findings: {total}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
