#!/usr/bin/env python3
"""SOC alert triage & incident-response helper (offline).

Ingests security alerts (JSON), scores and prioritizes them, maps each to the
NIST SP 800-61 incident-response lifecycle, and emits a normalized triage
record + a suggested first-response action. Built for a SOC / cybersecurity
engineer who lives in the escalation queue and has to decide fast, consistently,
and with an audit trail.

Input: a JSON file that is either a single alert object or a list of alerts.
Recognized fields (all optional; unknowns are ignored):
  id, source, title, severity (critical/high/medium/low/info),
  asset, asset_criticality (crown_jewel/high/medium/low),
  category (e.g. malware, phishing, c2, exfiltration, recon, policy),
  indicators (list), user, count, confidence (0-1)

Priority = f(alert severity, asset criticality, category weight, confidence),
bucketed P1..P4 with a target response SLA. Output is JSON (for a ticketing
system) or a human summary.

Exit codes: 0 no P1/P2 · 1 P2 present · 2 P1 present · 3 setup error.

Usage:
    python triage.py alerts.json
    python triage.py alerts.json --format json > triage.json
    echo '{"severity":"high","category":"c2","asset_criticality":"crown_jewel"}' \
        | python triage.py -
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

SEV_SCORE = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
ASSET_SCORE = {"crown_jewel": 5, "high": 4, "medium": 3, "low": 2, "": 2}
# Category weights: active-compromise categories escalate hardest.
CATEGORY_WEIGHT = {
    "exfiltration": 5, "c2": 5, "ransomware": 5, "malware": 4,
    "lateral_movement": 4, "privilege_escalation": 4, "credential_access": 4,
    "phishing": 3, "recon": 2, "policy": 2, "": 2,
}
# NIST SP 800-61 lifecycle hint by category.
NIST_PHASE = {
    "recon": "Detection & Analysis",
    "phishing": "Detection & Analysis",
    "policy": "Detection & Analysis",
    "malware": "Containment, Eradication & Recovery",
    "c2": "Containment, Eradication & Recovery",
    "lateral_movement": "Containment, Eradication & Recovery",
    "privilege_escalation": "Containment, Eradication & Recovery",
    "credential_access": "Containment, Eradication & Recovery",
    "exfiltration": "Containment, Eradication & Recovery",
    "ransomware": "Containment, Eradication & Recovery",
}
FIRST_ACTION = {
    "c2": "Isolate the host from the network; block the C2 indicator at egress.",
    "exfiltration": "Block egress to the destination; preserve logs; engage IR lead.",
    "ransomware": "Isolate affected hosts immediately; do NOT power off; invoke IR plan.",
    "malware": "Isolate the endpoint; submit sample; scan for lateral spread.",
    "credential_access": "Force-reset the affected credentials; revoke sessions/tokens.",
    "privilege_escalation": "Revoke elevated access; review recent IAM/role changes.",
    "lateral_movement": "Isolate involved hosts; check for reused credentials.",
    "phishing": "Quarantine the message org-wide; reset clickers; block sender/URL.",
    "recon": "Monitor and correlate; tighten exposed surface if external.",
    "policy": "Document; route to the owning team for remediation.",
}
# Priority -> response SLA (minutes) for the summary.
SLA_MINUTES = {"P1": 15, "P2": 60, "P3": 240, "P4": 1440}


def score_alert(alert: dict) -> dict:
    sev = str(alert.get("severity", "")).lower()
    asset = str(alert.get("asset_criticality", "")).lower()
    cat = str(alert.get("category", "")).lower()
    conf = alert.get("confidence")
    try:
        conf = float(conf) if conf is not None else 0.8
    except (TypeError, ValueError):
        conf = 0.8
    conf = min(max(conf, 0.0), 1.0)

    raw = (SEV_SCORE.get(sev, 2)
           + ASSET_SCORE.get(asset, 2)
           + CATEGORY_WEIGHT.get(cat, 2))
    score = round(raw * (0.5 + 0.5 * conf), 2)  # confidence scales 50-100%

    if score >= 12:
        prio = "P1"
    elif score >= 9:
        prio = "P2"
    elif score >= 6:
        prio = "P3"
    else:
        prio = "P4"

    return {
        "id": alert.get("id"),
        "source": alert.get("source"),
        "title": alert.get("title"),
        "asset": alert.get("asset"),
        "user": alert.get("user"),
        "severity": sev or None,
        "category": cat or None,
        "score": score,
        "priority": prio,
        "sla_minutes": SLA_MINUTES[prio],
        "nist_phase": NIST_PHASE.get(cat, "Detection & Analysis"),
        "first_action": FIRST_ACTION.get(cat, "Investigate, enrich indicators, "
                                              "and confirm scope before acting."),
        "indicators": alert.get("indicators", []),
    }


def load_alerts(path: str) -> list[dict]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [a for a in data if isinstance(a, dict)]
    raise ValueError("JSON must be an alert object or a list of alert objects.")


def main() -> int:
    ap = argparse.ArgumentParser(description="SOC alert triage / IR helper")
    ap.add_argument("input", help="alerts JSON file, or '-' for stdin")
    ap.add_argument("--format", choices=["summary", "json"], default="summary")
    args = ap.parse_args()

    try:
        alerts = load_alerts(args.input)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        emit(Level.FAIL, f"Could not load alerts: {exc}")
        return 3
    if not alerts:
        emit(Level.WARN, "No alerts to triage.")
        return 1

    triaged = sorted((score_alert(a) for a in alerts),
                     key=lambda t: t["score"], reverse=True)

    if args.format == "json":
        print(json.dumps(triaged, indent=2))
    else:
        rep = Report()
        for t in triaged:
            label = (f"[{t['priority']}] score {t['score']} "
                     f"(SLA {t['sla_minutes']}m) — {t.get('title') or t.get('category') or 'alert'}"
                     f" on {t.get('asset') or 'unknown asset'} "
                     f"| phase: {t['nist_phase']} | action: {t['first_action']}")
            if t["priority"] == "P1":
                rep.fail(label)
            elif t["priority"] == "P2":
                rep.warn(label)
            else:
                rep.info(label)
        rep.summary()
        return rep.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
