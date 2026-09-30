#!/usr/bin/env python3
"""AWS Systems Manager patch & managed-instance audit (read-only).

The patch-compliance and fleet-visibility view an AWS SysOps admin owns:

  - **Managed instances**: how many EC2 instances are SSM-managed vs. not
    (unmanaged instances can't be patched or inventoried via SSM).
  - **Ping status**: agents that are ConnectionLost (can't be managed).
  - **Patch compliance**: instances reporting NON_COMPLIANT patch state, and
    counts of missing/failed patches.
  - **Patch baselines**: at least one baseline exists.

Auth: standard AWS credential chain. Needs read-only ssm:Describe*/List*.
Exit codes: 0 clean · 1 warnings · 2 findings · 3 setup/auth error.

Usage:
    python ssm_patch_audit.py --region us-gov-west-1 --profile govcloud
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


def audit_managed_instances(rep: Report, ssm) -> None:
    infos = []
    paginator = ssm.get_paginator("describe_instance_information")
    for page in paginator.paginate():
        infos.extend(page.get("InstanceInformationList", []))

    if not infos:
        rep.warn("No SSM-managed instances found — nothing is centrally patchable.")
        return
    rep.ok(f"{len(infos)} SSM-managed instance(s).")

    lost = [i for i in infos if i.get("PingStatus") != "Online"]
    if lost:
        names = [i.get("InstanceId", "?") for i in lost]
        rep.warn(f"{len(lost)} managed instance(s) not Online (ConnectionLost/Inactive): "
                 f"{', '.join(names[:5])}")

    # Agents far behind can miss patch features (informational).
    stale_agent = [i["InstanceId"] for i in infos if i.get("IsLatestVersion") is False]
    if stale_agent:
        rep.info(f"{len(stale_agent)} instance(s) not running the latest SSM agent.")


def audit_patch_compliance(rep: Report, ssm) -> None:
    states = []
    try:
        paginator = ssm.get_paginator("describe_instance_patch_states")
        for page in paginator.paginate():
            states.extend(page.get("InstancePatchStates", []))
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"Could not read patch states: {exc}")
        return

    if not states:
        rep.warn("No patch state reported — is a patch baseline scan running?")
        return

    non_compliant = []
    total_missing = 0
    total_failed = 0
    for s in states:
        missing = s.get("MissingCount", 0)
        failed = s.get("FailedCount", 0)
        total_missing += missing
        total_failed += failed
        if missing or failed or s.get("ComplianceLevel") == "NON_COMPLIANT":
            non_compliant.append(s.get("InstanceId", "?"))

    if non_compliant:
        rep.fail(
            f"{len(non_compliant)} instance(s) NON_COMPLIANT on patching "
            f"({total_missing} missing, {total_failed} failed patches). "
            f"e.g. {', '.join(non_compliant[:5])}"
        )
    else:
        rep.ok(f"All {len(states)} scanned instance(s) are patch-compliant.")


def audit_baselines(rep: Report, ssm) -> None:
    baselines = []
    try:
        paginator = ssm.get_paginator("describe_patch_baselines")
        for page in paginator.paginate():
            baselines.extend(page.get("BaselineIdentities", []))
    except (BotoCoreError, ClientError) as exc:
        rep.warn(f"Could not list patch baselines: {exc}")
        return
    # AWS provides default baselines; look for at least one custom (non-default owner).
    custom = [b for b in baselines if b.get("BaselineName", "").lower().find("aws-") != 0]
    if not baselines:
        rep.warn("No patch baselines available.")
    elif not custom:
        rep.info(f"{len(baselines)} baseline(s), all AWS-default — consider a "
                 f"custom baseline aligned to your patch policy.")
    else:
        rep.ok(f"{len(custom)} custom patch baseline(s) defined.")


def main() -> int:
    ap = argparse.ArgumentParser(description="AWS SSM patch & managed-instance audit")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        ssm = session.client("ssm")
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}. Run 'aws sts get-caller-identity'.")
        return 3

    emit(Level.INFO, f"Auditing SSM in account {ident['Account']} region "
                     f"{session.region_name or 'default'}")
    rep = Report()
    try:
        audit_managed_instances(rep, ssm)
        audit_patch_compliance(rep, ssm)
        audit_baselines(rep, ssm)
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"API error during audit: {exc}")

    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
