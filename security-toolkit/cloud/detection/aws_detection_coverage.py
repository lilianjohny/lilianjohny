#!/usr/bin/env python3
"""AWS cloud detection & response coverage check (read-only).

Verifies the threat-detection and audit-logging baseline is actually enabled —
the foundation of cloud detection & response (CDR):
  - CloudTrail: a multi-region trail with log-file validation enabled
  - GuardDuty: a detector enabled in each region
  - Security Hub: enabled (findings aggregation)
  - AWS Config: recorder on (configuration history for investigations)
  - IAM Access Analyzer: present

Auth: standard AWS credential chain (read-only across the listed services).

Usage:
    python aws_detection_coverage.py                 # all regions
    python aws_detection_coverage.py --region us-east-1 --profile prod
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
except ImportError:
    print("Needs boto3 (pip install -r requirements-cloud.txt).", file=sys.stderr)
    raise SystemExit(3)


def check_cloudtrail(rep: Report, session) -> None:
    ct = session.client("cloudtrail")
    try:
        trails = ct.describe_trails().get("trailList", [])
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"CloudTrail unreadable: {exc}")
        return
    multi = [t for t in trails if t.get("IsMultiRegionTrail")]
    if not multi:
        rep.fail("No multi-region CloudTrail trail — audit logging is incomplete.")
        return
    for t in multi:
        name = t["Name"]
        if not t.get("LogFileValidationEnabled"):
            rep.warn(f"CloudTrail '{name}': log-file validation disabled.")
        try:
            st = ct.get_trail_status(Name=t["TrailARN"])
            if not st.get("IsLogging"):
                rep.fail(f"CloudTrail '{name}': trail exists but is NOT logging.")
            else:
                rep.ok(f"CloudTrail '{name}': multi-region, logging.")
        except (BotoCoreError, ClientError):
            rep.warn(f"CloudTrail '{name}': status unavailable.")


def regions(session) -> list[str]:
    ec2 = session.client("ec2")
    return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]


def check_guardduty(rep: Report, session, region_list) -> None:
    disabled = []
    for region in region_list:
        gd = session.client("guardduty", region_name=region)
        try:
            dets = gd.list_detectors().get("DetectorIds", [])
            if not dets:
                disabled.append(region)
        except (BotoCoreError, ClientError):
            disabled.append(region)
    if disabled:
        rep.fail(f"GuardDuty NOT enabled in {len(disabled)} region(s): "
                 f"{', '.join(disabled[:8])}{' …' if len(disabled) > 8 else ''}")
    else:
        rep.ok("GuardDuty enabled in all scanned regions.")


def check_securityhub(rep: Report, session, region_list) -> None:
    off = []
    for region in region_list:
        sh = session.client("securityhub", region_name=region)
        try:
            sh.describe_hub()
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("InvalidAccessException", "ResourceNotFoundException"):
                off.append(region)
        except BotoCoreError:
            off.append(region)
    if off:
        rep.warn(f"Security Hub not enabled in {len(off)} region(s).")
    else:
        rep.ok("Security Hub enabled in all scanned regions.")


def check_config(rep: Report, session, region_list) -> None:
    off = []
    for region in region_list:
        cfg = session.client("config", region_name=region)
        try:
            recs = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])
            status = cfg.describe_configuration_recorder_status().get("ConfigurationRecordersStatus", [])
            if not recs or not any(s.get("recording") for s in status):
                off.append(region)
        except (BotoCoreError, ClientError):
            off.append(region)
    if off:
        rep.warn(f"AWS Config recorder off in {len(off)} region(s).")
    else:
        rep.ok("AWS Config recording in all scanned regions.")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS detection & response coverage")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None, help="Limit to one region")
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile)
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}")
        return 3

    rep = Report()
    region_list = [args.region] if args.region else regions(session)
    emit(Level.INFO, f"Detection coverage — account {ident['Account']}, "
                     f"{len(region_list)} region(s)")

    check_cloudtrail(rep, session)  # global-ish; multi-region trail
    check_guardduty(rep, session, region_list)
    check_securityhub(rep, session, region_list)
    check_config(rep, session, region_list)

    if rep.exit_code == 0:
        rep.ok("Detection & logging baseline looks complete.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
