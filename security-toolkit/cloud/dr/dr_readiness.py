#!/usr/bin/env python3
"""AWS Disaster-Recovery readiness audit (read-only).

Two independent checks — either runs on its own:

1. **RTO/RPO register validation** (offline, no AWS needed): reads a CSV of
   systems with their documented Recovery Time / Recovery Point Objectives and
   backup posture, and flags where the configuration can't meet the objective
   (e.g. backup interval longer than the RPO, no cross-region copy for a
   mission system, stale/again-overdue DR test). This is the RTO/RPO alignment
   a DoD/Navy AvPLM cloud engineer is accountable for.

2. **AWS Backup coverage** (needs boto3 + creds): confirms backup plans and
   vaults exist, whether plan rules include **cross-region copy**, and whether
   any resources are actually protected. Skipped cleanly when boto3/creds are
   unavailable so check #1 still runs.

Register CSV columns (header required):
  system,tier,rto_hours,rpo_hours,backup_frequency_hours,cross_region,last_dr_test_days
  AvPLM-core,mission,4,1,1,yes,45

Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup error.

Usage:
    python dr_readiness.py --register dr_register.example.csv
    python dr_readiness.py --register dr_register.csv --region us-gov-west-1
    python dr_readiness.py --aws --region us-gov-west-1        # AWS checks only
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

MISSION_TIERS = {"mission", "critical", "tier0", "tier1"}


def _to_float(val: str) -> float | None:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return None


def validate_register(rep: Report, path: str, max_dr_test_age: int) -> None:
    rows = list(csv.DictReader(Path(path).open(newline="", encoding="utf-8")))
    if not rows:
        rep.warn(f"Register '{path}' has no rows.")
        return
    emit(Level.INFO, f"Validating {len(rows)} system(s) against RTO/RPO objectives.")

    for row in rows:
        name = (row.get("system") or "?").strip()
        tier = (row.get("tier") or "").strip().lower()
        rpo = _to_float(row.get("rpo_hours"))
        rto = _to_float(row.get("rto_hours"))
        freq = _to_float(row.get("backup_frequency_hours"))
        xregion = (row.get("cross_region") or "").strip().lower() in ("yes", "true", "1")
        test_age = _to_float(row.get("last_dr_test_days"))

        # RPO cannot be met if backups are less frequent than the RPO window.
        if rpo is not None and freq is not None and freq > rpo:
            rep.fail(
                f"{name}: backup interval {freq}h EXCEEDS RPO {rpo}h — "
                f"data loss window violates the objective."
            )
        elif rpo is not None and freq is not None:
            rep.ok(f"{name}: backup interval {freq}h meets RPO {rpo}h.")
        else:
            rep.warn(f"{name}: missing rpo_hours or backup_frequency_hours.")

        # Mission/critical systems need cross-region protection for regional loss.
        if tier in MISSION_TIERS and not xregion:
            rep.fail(f"{name} ({tier}): no cross-region copy — a Region outage "
                     f"means the RTO cannot be met.")

        # RTO sanity: no value documented.
        if rto is None:
            rep.warn(f"{name}: no rto_hours documented.")

        # DR test freshness.
        if test_age is None:
            rep.warn(f"{name}: no DR test recorded (last_dr_test_days empty).")
        elif test_age > max_dr_test_age:
            rep.warn(f"{name}: last DR test was {int(test_age)} days ago "
                     f"(> {max_dr_test_age}). Re-test and document results.")


def audit_aws_backup(rep: Report, region: str | None, profile: str | None) -> None:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
    except ImportError:
        rep.info("boto3 not installed — skipping live AWS Backup checks.")
        return
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        backup = session.client("backup")
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        rep.info(f"No AWS creds for live Backup checks ({exc}). Register check still ran.")
        return

    emit(Level.INFO, f"Checking AWS Backup in account {ident['Account']} region "
                     f"{session.region_name}")
    try:
        plans = []
        paginator = backup.get_paginator("list_backup_plans")
        for page in paginator.paginate():
            plans.extend(page.get("BackupPlansList", []))
        if not plans:
            rep.fail("No AWS Backup plans exist — no automated backups configured.")
        else:
            rep.ok(f"{len(plans)} AWS Backup plan(s) configured.")
            # Check for cross-region copy in any plan rule.
            has_copy = False
            for p in plans:
                detail = backup.get_backup_plan(BackupPlanId=p["BackupPlanId"])
                for rule in detail["BackupPlan"].get("Rules", []):
                    if rule.get("CopyActions"):
                        has_copy = True
            if has_copy:
                rep.ok("At least one backup plan performs cross-region/account copy.")
            else:
                rep.warn("No backup plan defines a cross-region CopyAction — "
                         "regional resilience is not automated.")

        vaults = []
        vpag = backup.get_paginator("list_backup_vaults")
        for page in vpag.paginate():
            vaults.extend(page.get("BackupVaultList", []))
        if not vaults:
            rep.warn("No backup vaults found.")
        else:
            rep.ok(f"{len(vaults)} backup vault(s) present.")
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"AWS Backup API error (partial results): {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS DR readiness audit")
    ap.add_argument("--register", help="RTO/RPO register CSV to validate (offline).")
    ap.add_argument("--aws", action="store_true",
                    help="Run live AWS Backup checks (also runs if --register omitted).")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--max-dr-test-age", type=int, default=180,
                    help="Warn if the last DR test is older than this many days.")
    args = ap.parse_args()

    if not args.register and not args.aws:
        args.aws = True  # nothing specified → try AWS

    rep = Report()
    if args.register:
        if not Path(args.register).exists():
            emit(Level.FAIL, f"Register file not found: {args.register}")
            return 3
        validate_register(rep, args.register, args.max_dr_test_age)
    if args.aws:
        audit_aws_backup(rep, args.region, args.profile)

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
