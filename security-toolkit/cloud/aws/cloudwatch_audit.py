#!/usr/bin/env python3
"""AWS CloudWatch observability-coverage audit (read-only).

Checks whether an account's monitoring is actually wired up — the day-to-day
concern of an AWS SysOps / CloudWatch specialist (e.g. DoD AvPLM GovCloud):

  - Log groups with **no retention** set (never expire: cost + log-retention
    compliance risk under DoD/Navy retention requirements).
  - Log groups with **no metric filter** (no way to alarm on log patterns).
  - CloudWatch **alarms**: total, any in INSUFFICIENT_DATA, and alarms with
    **no actions** (fire silently — nobody is paged).
  - **Dashboards** present (operational visibility / DR-readiness view).
  - **SNS** topics available for alarm notification.
  - **EventBridge** rules present (event-driven remediation wiring).

Auth: standard AWS credential chain (env, ~/.aws, SSO, instance role).
Needs read-only perms: logs:Describe*, cloudwatch:Describe*/List*,
events:ListRules, sns:ListTopics.

Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup/auth error.

Usage:
    python cloudwatch_audit.py
    python cloudwatch_audit.py --region us-gov-west-1 --profile govcloud
    python cloudwatch_audit.py --min-retention-days 365   # DoD-style retention
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
    print("This script needs boto3 (pip install -r requirements-cloud.txt).",
          file=sys.stderr)
    raise SystemExit(3)


def audit_log_groups(rep: Report, logs, min_retention_days: int) -> None:
    groups = []
    paginator = logs.get_paginator("describe_log_groups")
    for page in paginator.paginate():
        groups.extend(page.get("logGroups", []))

    if not groups:
        rep.warn("No CloudWatch log groups found — is anything logging?")
        return

    no_retention = [g["logGroupName"] for g in groups if not g.get("retentionInDays")]
    short = [
        g["logGroupName"]
        for g in groups
        if g.get("retentionInDays") and g["retentionInDays"] < min_retention_days
    ]
    if no_retention:
        rep.fail(
            f"{len(no_retention)} log group(s) have NO retention set (never expire). "
            f"e.g. {', '.join(no_retention[:3])}"
        )
    if short:
        rep.warn(
            f"{len(short)} log group(s) retain < {min_retention_days} days "
            f"(below DoD-style retention). e.g. {', '.join(short[:3])}"
        )
    if not no_retention and not short:
        rep.ok(f"All {len(groups)} log groups have retention >= {min_retention_days} days.")

    # Metric filters: how many groups have at least one?
    with_filters = 0
    mf_paginator = logs.get_paginator("describe_metric_filters")
    covered = {mf["logGroupName"] for page in mf_paginator.paginate()
               for mf in page.get("metricFilters", [])}
    with_filters = len(covered)
    if with_filters == 0:
        rep.warn("No metric filters exist — no log-pattern alarms are possible.")
    else:
        rep.ok(f"{with_filters} log group(s) have metric filters for alarming.")


def audit_alarms(rep: Report, cw) -> None:
    alarms = []
    paginator = cw.get_paginator("describe_alarms")
    for page in paginator.paginate():
        alarms.extend(page.get("MetricAlarms", []))
        alarms.extend(page.get("CompositeAlarms", []))

    if not alarms:
        rep.fail("No CloudWatch alarms defined — nothing is being alerted on.")
        return
    rep.ok(f"{len(alarms)} CloudWatch alarm(s) defined.")

    no_action = [a["AlarmName"] for a in alarms if not a.get("AlarmActions")]
    if no_action:
        rep.warn(
            f"{len(no_action)} alarm(s) have NO alarm actions (fire silently). "
            f"e.g. {', '.join(no_action[:3])}"
        )
    insufficient = [a["AlarmName"] for a in alarms
                    if a.get("StateValue") == "INSUFFICIENT_DATA"]
    if insufficient:
        rep.warn(
            f"{len(insufficient)} alarm(s) in INSUFFICIENT_DATA "
            f"(no metric data — check the source). e.g. {', '.join(insufficient[:3])}"
        )
    in_alarm = [a["AlarmName"] for a in alarms if a.get("StateValue") == "ALARM"]
    if in_alarm:
        rep.warn(f"{len(in_alarm)} alarm(s) currently in ALARM state: "
                 f"{', '.join(in_alarm[:5])}")


def audit_dashboards(rep: Report, cw) -> None:
    names = []
    paginator = cw.get_paginator("list_dashboards")
    for page in paginator.paginate():
        names.extend(d["DashboardName"] for d in page.get("DashboardEntries", []))
    if not names:
        rep.warn("No CloudWatch dashboards — no at-a-glance operational/DR view.")
    else:
        rep.ok(f"{len(names)} CloudWatch dashboard(s) present.")


def audit_notification_wiring(rep: Report, sns, events) -> None:
    topics = []
    paginator = sns.get_paginator("list_topics")
    for page in paginator.paginate():
        topics.extend(page.get("Topics", []))
    if not topics:
        rep.warn("No SNS topics — alarm notifications have nowhere to go.")
    else:
        rep.ok(f"{len(topics)} SNS topic(s) available for alarm notifications.")

    rules = []
    try:
        paginator = events.get_paginator("list_rules")
        for page in paginator.paginate():
            rules.extend(page.get("Rules", []))
    except (BotoCoreError, ClientError):
        pass
    if not rules:
        rep.warn("No EventBridge rules — no event-driven remediation is wired.")
    else:
        rep.ok(f"{len(rules)} EventBridge rule(s) for event-driven workflows.")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS CloudWatch observability audit (read-only)")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--min-retention-days", type=int, default=365,
                    help="Minimum acceptable log retention (default 365; DoD-style).")
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        logs = session.client("logs")
        cw = session.client("cloudwatch")
        sns = session.client("sns")
        events = session.client("events")
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}. Run 'aws sts get-caller-identity'.")
        return 3

    region = session.region_name or "default"
    emit(Level.INFO, f"Auditing CloudWatch in account {ident['Account']} region {region}")
    rep = Report()
    try:
        audit_log_groups(rep, logs, args.min_retention_days)
        audit_alarms(rep, cw)
        audit_dashboards(rep, cw)
        audit_notification_wiring(rep, sns, events)
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"API error during audit: {exc}")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
