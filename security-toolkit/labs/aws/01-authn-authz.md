# Lab 01 — Authentication & Authorization

**Skills practiced:** IAM policy authoring · roles vs users · assume-role &
short-lived creds · MFA & conditions · permission boundaries · least-privilege
iteration · app auth with Amazon Cognito.
**Proves (JD):** *"authentication / authorization."*

## Objective
Master AWS authN/authZ end-to-end: prove who you are with short-lived,
MFA-gated credentials; grant the *minimum* needed with well-scoped policies;
contain blast radius with boundaries and conditions; and add real
**application** auth (Cognito) with proper token handling.

## Est. time / cost
2–3 h · **~$0** (Cognito free tier; no paid resources needed).

## Prerequisites
- Lab 00 done (SSO admin + a ReadOnlyTester identity).
- AWS CLI v2, `jq`, Python 3.

---

## Part A — Build: identities and a workload role
1. Create an S3 bucket `lab01-<youracct>-data` (Block Public Access ON).
2. Create an IAM **role** `app-reader` with a trust policy your test principal can
   assume, and a **deliberately broad** policy first: `s3:*` on `*`.
3. Create a second role `ci-oidc` trusting **GitHub OIDC** (no static keys) —
   reuse the pattern in `../../iam/terraform/aws/main.tf`.

## Part B — Attack / observe: why broad grants hurt
1. Assume `app-reader` (broad) and show you can read/**write/delete** *any*
   bucket in the account, not just `lab01-…`:
   ```bash
   aws sts assume-role --role-arn <app-reader-arn> --role-session-name t | ...
   aws s3 ls                       # sees everything
   aws s3 rb s3://<some-other-bucket> --force   # (don't actually — just note you COULD)
   ```
2. Note the two failures: **over-broad action** (`s3:*`) and **over-broad
   resource** (`*`). That's privilege escalation waiting to happen.
3. Run `python3 ../../cloud/ciem/aws_least_privilege.py` and see the role flagged.

## Part C — Harden: least privilege, conditions, boundaries
1. Rewrite `app-reader` to the minimum:
   ```json
   {
     "Effect": "Allow",
     "Action": ["s3:GetObject", "s3:ListBucket"],
     "Resource": [
       "arn:aws:s3:::lab01-<youracct>-data",
       "arn:aws:s3:::lab01-<youracct>-data/*"
     ]
   }
   ```
2. Add **conditions**: require MFA (`aws:MultiFactorAuthPresent`), TLS
   (`aws:SecureTransport`), and (optionally) a source VPC/IP.
3. Attach a **permission boundary** so even an admin-ish role can't exceed a cap.
4. Make credentials **short-lived**: set a small `MaxSessionDuration`; use
   assume-role, never long-lived keys.
5. Enforce **MFA to assume** privileged roles.

## Part D — Application auth with Cognito
1. Create a **Cognito User Pool**: strong password policy, **MFA required**,
   advanced security (risk-based) on, hosted UI.
2. Create an app client (no client secret for SPA; **PKCE** for the auth-code flow).
3. Get tokens and inspect them:
   ```bash
   python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
   ```
   Confirm: correct `iss`/`aud`, short `exp`, `alg` is RS256 (not `none`),
   scopes/groups present.
4. Map a Cognito **group** → an IAM role (identity pool) so app users get
   least-privilege AWS access by group — the app-layer version of Lab 01's IAM work.

---

## Verify
```bash
# Least privilege now holds: broad access is gone
python3 ../../cloud/ciem/aws_least_privilege.py
python3 ../../cloud/aws/iam_audit.py

# Prove the hardened role CAN read lab01 data and CANNOT touch other buckets
aws s3 ls s3://lab01-<youracct>-data      # works
aws s3 ls                                  # denied / empty beyond scope

# Token hygiene
python3 ../../appsec/crypto/jwt_inspect.py <token>
```
Success = the role does exactly its job and nothing more; MFA/TLS conditions
enforced; Cognito requires MFA and issues short-lived, correctly-scoped tokens.

## Cleanup
Delete the roles, the bucket, and the Cognito user pool/app client.

## Portfolio artifact
- **Before/after IAM policy** (broad → least-privilege) with a paragraph on each
  change (action scope, resource scope, conditions, boundary).
- A short note on **authN vs authZ**: Cognito proved *who*, IAM decided *what*.
- Screenshot of `aws_least_privilege.py` flagging then clearing the role.

## Stretch goals
- Add an **attribute-based access control (ABAC)** policy using tags
  (`aws:PrincipalTag` / `aws:ResourceTag`) — one policy, many teams.
- Write the hardened role + boundary as Terraform; run `checkov` on it.
- Add an **SCP/RCP data-perimeter** (`../../iam/policies/aws-rcp-data-perimeter.json`)
  so only your identities/networks can reach the bucket — then re-test the attack.
