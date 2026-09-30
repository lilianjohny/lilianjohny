#!/usr/bin/env python3
"""Audit S3 buckets for public exposure and weak protections (read-only).

For each bucket in the account, checks:
  - Account-level & bucket-level Public Access Block
  - Bucket ACL granting AllUsers / AuthenticatedUsers
  - Bucket policy allowing Principal "*"
  - Default encryption
  - Versioning

Auth: standard AWS credential chain. Needs s3:GetBucket* / s3:ListAllMyBuckets.

Usage:
    python s3_public_check.py
    python s3_public_check.py --profile prod
"""
from __future__ import annotations

import argparse
import json
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

PUBLIC_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers": "AllUsers (public)",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers": "AnyAuthenticatedAWSUser",
}


def account_pab(session) -> bool:
    """True if account-level Public Access Block fully blocks public access."""
    try:
        ctrl = session.client("s3control")
        acct = session.client("sts").get_caller_identity()["Account"]
        cfg = ctrl.get_public_access_block(AccountId=acct)["PublicAccessBlockConfiguration"]
        return all(cfg.get(k) for k in
                   ("BlockPublicAcls", "IgnorePublicAcls",
                    "BlockPublicPolicy", "RestrictPublicBuckets"))
    except ClientError:
        return False


def check_bucket(rep: Report, s3, name: str) -> None:
    # Public Access Block
    try:
        cfg = s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
        if not all(cfg.get(k) for k in
                   ("BlockPublicAcls", "IgnorePublicAcls",
                    "BlockPublicPolicy", "RestrictPublicBuckets")):
            rep.warn(f"[{name}] Public Access Block not fully enabled.")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
            rep.warn(f"[{name}] No bucket-level Public Access Block set.")

    # ACL
    try:
        acl = s3.get_bucket_acl(Bucket=name)
        for grant in acl.get("Grants", []):
            uri = grant.get("Grantee", {}).get("URI", "")
            if uri in PUBLIC_URIS:
                rep.fail(f"[{name}] ACL grants {PUBLIC_URIS[uri]} "
                         f"({grant.get('Permission')}).")
    except ClientError as exc:
        rep.warn(f"[{name}] Could not read ACL: {exc.response['Error']['Code']}")

    # Policy with Principal "*"
    try:
        pol = json.loads(s3.get_bucket_policy(Bucket=name)["Policy"])
        for st in pol.get("Statement", []):
            principal = st.get("Principal")
            is_star = principal == "*" or (isinstance(principal, dict)
                                           and principal.get("AWS") == "*")
            if st.get("Effect") == "Allow" and is_star and "Condition" not in st:
                rep.fail(f"[{name}] Bucket policy allows Principal '*' without conditions.")
                break
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "NoSuchBucketPolicy":
            rep.warn(f"[{name}] Could not read policy: {exc.response['Error']['Code']}")

    # Encryption
    try:
        s3.get_bucket_encryption(Bucket=name)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            rep.warn(f"[{name}] No default encryption configured.")

    # Versioning
    try:
        ver = s3.get_bucket_versioning(Bucket=name)
        if ver.get("Status") != "Enabled":
            rep.info(f"[{name}] Versioning not enabled.")
    except ClientError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="S3 public-exposure audit")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--region", default=None)
    args = ap.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        s3 = session.client("s3")
        ident = session.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        emit(Level.FAIL, f"AWS auth failed: {exc}")
        return 3

    emit(Level.INFO, f"Auditing S3 in account {ident['Account']}")
    rep = Report()

    if account_pab(session):
        rep.ok("Account-level Public Access Block is fully enabled.")
    else:
        rep.warn("Account-level Public Access Block is NOT fully enabled.")

    try:
        buckets = s3.list_buckets().get("Buckets", [])
    except (BotoCoreError, ClientError) as exc:
        rep.fail(f"Could not list buckets: {exc}")
        rep.summary()
        return rep.exit_code

    emit(Level.INFO, f"Checking {len(buckets)} bucket(s)…")
    for b in buckets:
        try:
            check_bucket(rep, s3, b["Name"])
        except (BotoCoreError, ClientError) as exc:
            rep.warn(f"[{b['Name']}] error: {exc}")

    if rep.exit_code == 0:
        rep.ok("No public exposure or major misconfig found.")
    rep.summary()
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
