# Lab 01 — Authentication & Authorization

**Skills practiced:** IAM policy authoring · roles vs users · assume-role &
short-lived creds · MFA & conditions · permission boundaries · least-privilege
iteration · app auth with Amazon Cognito.
**Proves (JD):** *"authentication / authorization."*

## Objective
Prove who you are with short-lived, MFA-gated credentials; grant the *minimum*
with well-scoped policies; contain blast radius with boundaries/conditions; and
add real application auth (Cognito) with proper token handling.

## Est. time / cost
2–3 h · **~$0** (Cognito free tier).

## Prerequisites
- Lab 00 done (`export AWS_PROFILE=admin-labs`, `AWS_REGION`, `ACCT_ID`).
- `jq` installed. Python 3.

---

## Part A — Build: identities and a workload role
```bash
# 1. A bucket this lab's role should be allowed to read (and nothing else)
BUCKET=lab01-$ACCT_ID-data
aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
  $( [ "$AWS_REGION" != us-east-1 ] && echo --create-bucket-configuration LocationConstraint=$AWS_REGION )
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
echo "hello" | aws s3 cp - "s3://$BUCKET/ok.txt"

# 2. A role your own identity can assume, with a DELIBERATELY BROAD policy first
MYARN=$(aws sts get-caller-identity --query Arn --output text)
cat > /tmp/trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
  "Principal":{"AWS":"arn:aws:iam::$ACCT_ID:root"},"Action":"sts:AssumeRole"}]}
EOF
aws iam create-role --role-name app-reader --assume-role-policy-document file:///tmp/trust.json
cat > /tmp/broad.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"}]}
EOF
aws iam put-role-policy --role-name app-reader --policy-name broad --policy-document file:///tmp/broad.json
```
**GUI equivalent:** Console → **IAM → Roles → Create role → Custom trust policy**
(paste trust.json) → skip permissions → name `app-reader` → then **Add
permissions → Create inline policy → JSON** (paste broad.json).

## Part B — Attack / observe: why broad grants hurt
```bash
# Assume the broad role and get short-lived creds
CREDS=$(aws sts assume-role --role-arn arn:aws:iam::$ACCT_ID:role/app-reader \
  --role-session-name test --query Credentials --output json)
export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r .AccessKeyId)
export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r .SecretAccessKey)
export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r .SessionToken)

aws s3 ls                       # BUG: sees EVERY bucket, not just lab01
aws sts get-caller-identity     # you're now app-reader
# (Don't actually delete anything — just note s3:* on * means you COULD.)

# Reset back to your admin identity:
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```
Two failures: **over-broad action** (`s3:*`) and **over-broad resource** (`*`).
```bash
python3 ../../cloud/ciem/aws_least_privilege.py    # flags the role
```

## Part C — Harden: least privilege, conditions, boundaries
```bash
# 1. Replace the broad policy with least privilege + TLS + MFA conditions
cat > /tmp/least.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["s3:GetObject","s3:ListBucket"],
  "Resource":["arn:aws:s3:::$BUCKET","arn:aws:s3:::$BUCKET/*"],
  "Condition":{"Bool":{"aws:SecureTransport":"true"}}}]}
EOF
aws iam put-role-policy --role-name app-reader --policy-name least --policy-document file:///tmp/least.json
aws iam delete-role-policy --role-name app-reader --policy-name broad

# 2. A permission boundary capping the role to S3-read only, ever
cat > /tmp/boundary.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:Get*","s3:List*"],"Resource":"*"}]}
EOF
aws iam create-policy --policy-name lab01-boundary --policy-document file:///tmp/boundary.json
aws iam put-role-permissions-boundary --role-name app-reader \
  --permissions-boundary arn:aws:iam::$ACCT_ID:policy/lab01-boundary

# 3. Short sessions
aws iam update-role --role-name app-reader --max-session-duration 3600
```
**GUI:** IAM → Roles → `app-reader` → **Permissions** tab (edit inline policy),
**Permissions boundary** section → **Set boundary**.

## Part D — Application auth with Cognito
```bash
# User pool with MFA required + strong password policy
POOL_ID=$(aws cognito-idp create-user-pool --pool-name lab01-pool \
  --mfa-configuration ON \
  --auto-verified-attributes email \
  --policies '{"PasswordPolicy":{"MinimumLength":12,"RequireUppercase":true,"RequireNumbers":true,"RequireSymbols":true}}' \
  --query 'UserPool.Id' --output text)
# App client for a SPA: no secret, SRP + refresh
CLIENT_ID=$(aws cognito-idp create-user-pool-client --user-pool-id "$POOL_ID" \
  --client-name spa --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient.ClientId' --output text)
echo "Pool=$POOL_ID Client=$CLIENT_ID"
```
**GUI:** Console → **Cognito → Create user pool** → Cognito user pool →
sign-in = email → **MFA = Required** → password policy → app client = **Public
client** (no secret) with **ALLOW_USER_SRP_AUTH** → create.

Inspect a token you obtain from the hosted UI / SRP sign-in:
```bash
python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
# Confirm: iss/aud correct, short exp, alg=RS256 (not "none"), groups/scopes present
```

---

## Verify
```bash
python3 ../../cloud/ciem/aws_least_privilege.py     # broad access gone
# Prove scope: assume the role again and confirm it can read lab01 but not list all
CREDS=$(aws sts assume-role --role-arn arn:aws:iam::$ACCT_ID:role/app-reader --role-session-name v --query Credentials --output json)
AWS_ACCESS_KEY_ID=$(echo $CREDS|jq -r .AccessKeyId) AWS_SECRET_ACCESS_KEY=$(echo $CREDS|jq -r .SecretAccessKey) AWS_SESSION_TOKEN=$(echo $CREDS|jq -r .SessionToken) aws s3 ls "s3://$BUCKET"    # works
AWS_ACCESS_KEY_ID=$(echo $CREDS|jq -r .AccessKeyId) AWS_SECRET_ACCESS_KEY=$(echo $CREDS|jq -r .SecretAccessKey) AWS_SESSION_TOKEN=$(echo $CREDS|jq -r .SessionToken) aws s3 ls    # AccessDenied ✅
```

## Cleanup
```bash
aws iam delete-role-policy --role-name app-reader --policy-name least
aws iam delete-role-permissions-boundary --role-name app-reader
aws iam delete-role --role-name app-reader
aws iam delete-policy --policy-arn arn:aws:iam::$ACCT_ID:policy/lab01-boundary
aws cognito-idp delete-user-pool --user-pool-id "$POOL_ID"
aws s3 rb "s3://$BUCKET" --force
```

## Portfolio artifact
- **Before/after IAM policy** (broad → least-privilege) with a note on each change
  (action scope, resource scope, conditions, boundary).
- A short **authN vs authZ** note: Cognito proved *who*, IAM decided *what*.
- Screenshot of `aws_least_privilege.py` flagging then clearing the role.

## Stretch goals
- Add **ABAC** with `aws:PrincipalTag`/`aws:ResourceTag`.
- Write the hardened role + boundary as Terraform; run `checkov`.
- Add an **RCP data perimeter** (`../../iam/policies/aws-rcp-data-perimeter.json`)
  and re-test the attack.
