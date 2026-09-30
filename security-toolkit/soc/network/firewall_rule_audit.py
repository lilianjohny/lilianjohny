#!/usr/bin/env python3
"""Firewall rule-base audit (offline, vendor-neutral).

Reads a CSV export of firewall rules (Palo Alto, FortiGate, Cisco, SonicWall,
etc. — export/normalize to the columns below) and flags risky rules the way a
SOC / network-security engineer reviews a rule base:

  - **Any-any allow**: source=any AND destination=any AND action=allow (FAIL).
  - **Sensitive service exposed to the internet**: allow from any/0.0.0.0/0 to
    a management/database port (22, 3389, 3306, 1433, 5432, 6379, 9200, …) (FAIL).
  - **Cleartext protocol allowed** (telnet 23, ftp 21, http from any) (WARN/FAIL).
  - **Allow with logging disabled** (no audit trail) (WARN).
  - **Overly broad service 'any' on an allow** (WARN).
  - **Disabled rules** (cleanup / shadow risk) (INFO).

CSV columns (header required; case-insensitive; missing ones tolerated):
  name,action,source,destination,service,port,protocol,log,enabled

Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python firewall_rule_audit.py rules.csv
    python firewall_rule_audit.py rules.example.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

ANY_TOKENS = {"any", "all", "0.0.0.0/0", "0.0.0.0", "*", "::/0", ""}
SENSITIVE_PORTS = {
    "22": "SSH", "3389": "RDP", "3306": "MySQL", "1433": "MSSQL",
    "5432": "PostgreSQL", "6379": "Redis", "9200": "Elasticsearch",
    "27017": "MongoDB", "5984": "CouchDB", "2375": "Docker API",
    "445": "SMB", "135": "RPC", "389": "LDAP", "5985": "WinRM",
}
CLEARTEXT_PORTS = {"21": "FTP", "23": "Telnet", "80": "HTTP", "110": "POP3",
                   "143": "IMAP", "161": "SNMP"}


def _is_any(val: str) -> bool:
    return (val or "").strip().lower() in ANY_TOKENS


def _norm(row: dict) -> dict:
    return {k.strip().lower(): (v or "").strip() for k, v in row.items()}


def _is_allow(action: str) -> bool:
    return action.lower() in ("allow", "permit", "accept", "pass")


def _is_enabled(row: dict) -> bool:
    val = row.get("enabled", "yes").lower()
    return val not in ("no", "false", "0", "disabled")


def _logging_off(row: dict) -> bool:
    if "log" not in row:
        return False
    return row["log"].lower() in ("no", "false", "0", "off", "none", "disable")


def audit_rules(rep: Report, rows: list[dict]) -> None:
    if not rows:
        rep.warn("No rules found in the export.")
        return
    emit(Level.INFO, f"Auditing {len(rows)} firewall rule(s).")

    findings = 0
    for raw in rows:
        r = _norm(raw)
        name = r.get("name") or r.get("rule") or "(unnamed)"
        if not _is_enabled(r):
            rep.info(f"Rule '{name}' is disabled — remove if obsolete (shadow risk).")
            continue
        action = r.get("action", "")
        if not _is_allow(action):
            continue  # deny/drop rules are the safe default; skip

        src, dst = r.get("source", ""), r.get("destination", "")
        service = r.get("service", "")
        port = r.get("port", "")

        # Any-any allow
        if _is_any(src) and _is_any(dst):
            rep.fail(f"Rule '{name}': ALLOW any -> any (remove or tightly scope).")
            findings += 1
            continue

        # Sensitive service exposed from the internet
        if _is_any(src) and port in SENSITIVE_PORTS:
            rep.fail(f"Rule '{name}': {SENSITIVE_PORTS[port]} (port {port}) allowed "
                     f"from any source — exposes a management/data port.")
            findings += 1
        # Cleartext protocols
        elif port in CLEARTEXT_PORTS and _is_any(src):
            lvl = rep.fail if port in ("21", "23") else rep.warn
            lvl(f"Rule '{name}': cleartext {CLEARTEXT_PORTS[port]} (port {port}) "
                f"allowed from any source.")
            findings += 1
        # Overly broad service
        elif _is_any(service) and _is_any(port):
            rep.warn(f"Rule '{name}': allows ALL services/ports — scope to what's needed.")

        # Logging disabled on an allow rule
        if _logging_off(r):
            rep.warn(f"Rule '{name}': allow rule with logging DISABLED (no audit trail).")

    if findings == 0:
        rep.ok("No any-any or internet-exposed sensitive-service allow rules found.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Vendor-neutral firewall rule audit")
    ap.add_argument("csvfile", help="CSV export of firewall rules")
    args = ap.parse_args()

    path = Path(args.csvfile)
    if not path.exists():
        emit(Level.FAIL, f"File not found: {args.csvfile}")
        return 3
    try:
        rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    except (OSError, csv.Error) as exc:
        emit(Level.FAIL, f"Could not read CSV: {exc}")
        return 3

    rep = Report()
    audit_rules(rep, rows)
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
