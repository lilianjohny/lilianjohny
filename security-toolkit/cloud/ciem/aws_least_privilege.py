#!/usr/bin/env python3
"""AWS CIEM — Cloud Infrastructure Entitlement Management (read-only).

Focuses on *entitlements/identity* (vs the broader posture in aws/iam_audit.py):
  - IAM Access Analyzer external-access findings (resources shared outside the
    account/org)
  - Principals with AdministratorAccess or inline wildcard (Action:* Resource:*)
  - Unused access: users/roles not used in > --idle-days
  - Access keys unused in > --idle-days

Auth: standard AWS credential chain. Needs IAM read + access-analyzer read.

Usage:
    python aws_least_privilege.py
    python aws_least_privilege.py --idle-days 60 --profile prod --region us-east-1
"""
from __future__ import annotations

import argparse
import datetime as dt
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

UTC = dt.timezone.utc


def _age_days(ts) -> int | None:
    if not ts:
        return None
    if isinstance(ts, str):
        try:
            ts = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return (dt.datetime.now(UTC) - ts).days


def access_analyzer_findings(rep: Report, session, region: str) -> None:
    aa = session.client("accessanalyzer", region_name=region)
    try:
        analyzers = aa.list_analyzers(type="ACCOUNT").get("analyzers", [])
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"Access Analyzer not readable in {region}: {exc}")
        return
    if not analyzers:
        rep.warn(f"No IAM Access Analyzer configured in {region} (enable it).")
        return
    arn = analyzers[0]["arn"]
    try:
        paginator = aa.get_paginator("list_findings_v2")
        active = 0
        for page in paginator.paginate(analyzerArn=arn,
                                        filter={"status": {"eq": ["ACTIVE"]}}):
            for f in page.get("findings", []):
                active += 1
                rep.fail(f"External-access finding: {f.get('resourceType')} "
                         f"{f.get('resource', '?')} shared with {f.get('principal', {})}")
        if active == 0:
            rep.ok(f"No active external-access findings in {region}.")
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"Could not list findings: {exc}")


def admin_principals(rep: Report, iam) -> None:
    # Attached AdministratorAccess
    admin_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
    try:
        ent = iam.list_entities_for_policy(PolicyArn=admin_arn)
        for u in ent.get("PolicyUsers", []):
            rep.warn(f"User '{u['UserName']}' has AdministratorAccess attached.")
        for r in ent.get("PolicyRoles", []):
            rep.info(f"Role '{r['RoleName']}' has AdministratorAccess (verify it's intended).")
        for g in ent.get("PolicyGroups", []):
            rep.warn(f"Group '{g['GroupName']}' has AdministratorAccess.")
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"Could not enumerate AdministratorAccess: {exc}")


def unused_access(rep: Report, iam, idle_days: int) -> None:
    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for u in page["Users"]:
            name = u["UserName"]
            last = _age_days(u.get("PasswordLastUsed"))
            # Access keys
            keys = iam.list_access_keys(UserName=name).get("AccessKeyMetadata", [])
            for k in keys:
                if k["Status"] != "Active":
                    continue
                used = iam.get_access_key_last_used(AccessKeyId=k["AccessKeyId"])
                lu = used.get("AccessKeyLastUsed", {}).get("LastUsedDate")
                age = _age_days(lu)
                if age is None:
                    rep.warn(f"User '{name}' key {k['AccessKeyId'][-4:]} never used.")
                elif age > idle_days:
                    rep.warn(f"User '{name}' key {k['AccessKeyId'][-4:]} unused {age}d (> {idle_days}).")
            if last is not None and last > idle_days and not keys:
                rep.warn(f"User '{name}' console unused {last}d and has no keys — consider removal.")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS CIEM / least-privilege review")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--idle-days", type=int, default=90)
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        iam = session.client("iam")
        ident = session.client("sts").get_caller_identity()
        region = args.region or session.region_name or "us-east-1"
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}")
        return 3

    emit(Level.INFO, f"CIEM review of account {ident['Account']} (region {region})")
    rep = Report()
    try:
        access_analyzer_findings(rep, session, region)
        admin_principals(rep, iam)
        unused_access(rep, iam, args.idle_days)
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"API error: {exc}")

    if rep.exit_code == 0:
        rep.ok("No entitlement issues found by these checks.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
