#!/usr/bin/env python3
"""AWS IAM hygiene audit (read-only) using your default credential chain.

Checks common IAM weaknesses:
  - Root account: recent usage, MFA, access keys
  - Users without MFA
  - Access keys older than --max-key-age days, or unused
  - Customer-managed policies granting Action "*" on Resource "*"
  - Password policy strength

Auth: uses the standard AWS credential chain (env, ~/.aws, SSO, instance role).
Requires read-only IAM permissions (iam:Get*, iam:List*, iam:GenerateCredentialReport).

Usage:
    python iam_audit.py
    python iam_audit.py --max-key-age 90 --profile prod --region us-east-1
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.common import Report, emit, Level  # noqa: E402

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
except ImportError:
    print("This script needs boto3 (pip install -r requirements-cloud.txt).",
          file=sys.stderr)
    raise SystemExit(3)

UTC = dt.timezone.utc


def _age_days(ts: dt.datetime | str | None) -> int | None:
    if not ts or ts in ("N/A", "no_information", "not_supported"):
        return None
    if isinstance(ts, str):
        try:
            ts = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return (dt.datetime.now(UTC) - ts).days


def get_credential_report(iam) -> list[dict]:
    # Trigger generation, then poll briefly.
    for _ in range(10):
        try:
            resp = iam.get_credential_report()
            data = resp["Content"].decode("utf-8")
            return list(csv.DictReader(io.StringIO(data)))
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("ReportNotPresent", "ReportInProgress", "ReportExpired"):
                iam.generate_credential_report()
                time.sleep(2)
                continue
            raise
    return []


def audit_report_rows(rep: Report, rows: list[dict], max_key_age: int) -> None:
    for row in rows:
        user = row["user"]
        if user == "<root_account>":
            if row.get("mfa_active") == "false":
                rep.fail("Root account has NO MFA enabled.")
            else:
                rep.ok("Root account MFA is enabled.")
            for k in ("access_key_1_active", "access_key_2_active"):
                if row.get(k) == "true":
                    rep.fail("Root account has active access keys — remove them.")
            used = _age_days(row.get("password_last_used"))
            if used is not None and used < 30:
                rep.warn(f"Root password used {used} days ago — avoid using root.")
            continue

        # MFA for console users
        if row.get("password_enabled") == "true" and row.get("mfa_active") == "false":
            rep.fail(f"User '{user}' has console access but no MFA.")

        # Access-key age / usage
        for idx in ("1", "2"):
            if row.get(f"access_key_{idx}_active") != "true":
                continue
            age = _age_days(row.get(f"access_key_{idx}_last_rotated"))
            if age is not None and age > max_key_age:
                rep.warn(f"User '{user}' access key {idx} is {age} days old "
                         f"(> {max_key_age}). Rotate it.")
            last_used = _age_days(row.get(f"access_key_{idx}_last_used_date"))
            if last_used is None and age is not None and age > 30:
                rep.warn(f"User '{user}' access key {idx} appears unused. Consider removing.")


def audit_wildcard_policies(rep: Report, iam) -> None:
    paginator = iam.get_paginator("list_policies")
    flagged = 0
    for page in paginator.paginate(Scope="Local", OnlyAttached=False):
        for pol in page["Policies"]:
            ver = iam.get_policy_version(
                PolicyArn=pol["Arn"], VersionId=pol["DefaultVersionId"]
            )["PolicyVersion"]["Document"]
            statements = ver.get("Statement", [])
            if isinstance(statements, dict):
                statements = [statements]
            for st in statements:
                if st.get("Effect") != "Allow":
                    continue
                actions = st.get("Action", [])
                resources = st.get("Resource", [])
                actions = [actions] if isinstance(actions, str) else actions
                resources = [resources] if isinstance(resources, str) else resources
                if "*" in actions and "*" in resources:
                    rep.fail(f"Policy '{pol['PolicyName']}' allows Action '*' on Resource '*'.")
                    flagged += 1
                    break
    if flagged == 0:
        rep.ok("No customer-managed policy grants '*' on '*'.")


def audit_password_policy(rep: Report, iam) -> None:
    try:
        pp = iam.get_account_password_policy()["PasswordPolicy"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchEntity":
            rep.fail("No account password policy is set.")
            return
        raise
    if pp.get("MinimumPasswordLength", 0) < 14:
        rep.warn(f"Password min length is {pp.get('MinimumPasswordLength')} (< 14).")
    else:
        rep.ok(f"Password min length is {pp.get('MinimumPasswordLength')}.")
    if not pp.get("RequireSymbols") or not pp.get("RequireNumbers"):
        rep.warn("Password policy does not require symbols and numbers.")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS IAM audit")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--max-key-age", type=int, default=90)
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        iam = session.client("iam")
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}. Run 'aws sts get-caller-identity'.")
        return 3

    emit(Level.INFO, f"Auditing AWS account {ident['Account']} as {ident['Arn']}")
    rep = Report()
    try:
        rows = get_credential_report(iam)
        if rows:
            audit_report_rows(rep, rows, args.max_key_age)
        else:
            rep.warn("Could not obtain IAM credential report.")
        audit_password_policy(rep, iam)
        audit_wildcard_policies(rep, iam)
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"API error during audit: {exc}")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
