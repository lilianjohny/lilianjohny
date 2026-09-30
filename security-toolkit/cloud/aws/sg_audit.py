#!/usr/bin/env python3
"""Audit EC2 security groups for sensitive ports open to the internet.

Flags inbound rules allowing 0.0.0.0/0 or ::/0 to sensitive ports
(SSH, RDP, databases, etc.). Read-only. Scans all regions by default.

Auth: standard AWS credential chain. Needs ec2:DescribeSecurityGroups,
ec2:DescribeRegions.

Usage:
    python sg_audit.py
    python sg_audit.py --region us-east-1 --profile prod
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

SENSITIVE = {
    22: "SSH", 23: "Telnet", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL",
    1433: "MSSQL", 6379: "Redis", 27017: "MongoDB", 9200: "Elasticsearch",
    5601: "Kibana", 11211: "Memcached", 2375: "Docker", 445: "SMB",
}
OPEN_CIDRS = {"0.0.0.0/0", "::/0"}


def port_in_range(from_p, to_p) -> list[int]:
    # -1 means all ports
    if from_p in (None, -1) or to_p in (None, -1):
        return list(SENSITIVE)  # "all ports" exposes every sensitive port
    return [p for p in SENSITIVE if from_p <= p <= to_p]


def regions(session) -> list[str]:
    ec2 = session.client("ec2")
    return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]


def audit_region(rep: Report, session, region: str) -> None:
    ec2 = session.client("ec2", region_name=region)
    try:
        groups = ec2.describe_security_groups()["SecurityGroups"]
    except ClientError as exc:
        rep.warn(f"[{region}] cannot describe SGs: {exc.response['Error']['Code']}")
        return
    for sg in groups:
        for perm in sg.get("IpPermissions", []):
            open_v4 = any(r.get("CidrIp") in OPEN_CIDRS for r in perm.get("IpRanges", []))
            open_v6 = any(r.get("CidrIpv6") in OPEN_CIDRS for r in perm.get("Ipv6Ranges", []))
            if not (open_v4 or open_v6):
                continue
            hit = port_in_range(perm.get("FromPort"), perm.get("ToPort"))
            for p in hit:
                rep.fail(f"[{region}] SG {sg['GroupId']} ({sg['GroupName']}): "
                         f"{SENSITIVE[p]}/{p} open to the internet.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Security-group exposure audit")
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
    target_regions = [args.region] if args.region else regions(session)
    emit(Level.INFO,
         f"Account {ident['Account']} — auditing {len(target_regions)} region(s)")

    for region in target_regions:
        try:
            audit_region(rep, session, region)
        except (BotoCoreError, ClientError) as exc:
            rep.warn(f"[{region}] error: {exc}")

    if rep.exit_code == 0:
        rep.ok("No sensitive ports exposed to 0.0.0.0/0 or ::/0.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
