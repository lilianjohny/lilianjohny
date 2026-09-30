# Lab 04 — Multi-Tenant Isolation

**Skills practiced:** tenant isolation models (silo/pool/bridge) · IAM-based
tenant boundaries · per-tenant KMS keys · data isolation (prefix/partition
scoping) · dynamic per-request scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use."*

## Objective
Model a pooled SaaS system and prove **Tenant A can never reach Tenant B's data**,
at identity, data, and key layers — even when a tenant is malicious.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done. `jq`, Python 3. (`AWS_PROFILE`, `AWS_REGION`, `ACCT_ID` set.)

---

## Part A — Build: a shared (pool) setup with two tenants
```bash
BUCKET=lab04-$ACCT_ID
aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
  $( [ "$AWS_REGION" != us-east-1 ] && echo --create-bucket-configuration LocationConstraint=$AWS_REGION )
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
echo "A-secret" | aws s3 cp - "s3://$BUCKET/tenantA/secret.txt"
echo "B-secret" | aws s3 cp - "s3://$BUCKET/tenantB/secret.txt"

aws dynamodb create-table --table-name lab04-data \
  --attribute-definitions AttributeName=tenant_id,AttributeType=S AttributeName=item,AttributeType=S \
  --key-schema AttributeName=tenant_id,KeyType=HASH AttributeName=item,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name lab04-data
aws dynamodb put-item --table-name lab04-data --item '{"tenant_id":{"S":"tenantB"},"item":{"S":"x"},"data":{"S":"B-only"}}'

# Two roles, initially OVER-BROAD (full bucket + full table)
MYARN=arn:aws:iam::$ACCT_ID:root
cat > /tmp/trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"$MYARN"},"Action":"sts:AssumeRole"}]}
EOF
for T in A B; do
  aws iam create-role --role-name tenant-$T-role --assume-role-policy-document file:///tmp/trust.json
  cat > /tmp/broad.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"s3:*","Resource":["arn:aws:s3:::$BUCKET","arn:aws:s3:::$BUCKET/*"]},
 {"Effect":"Allow","Action":"dynamodb:*","Resource":"arn:aws:dynamodb:$AWS_REGION:$ACCT_ID:table/lab04-data"}]}
EOF
  aws iam put-role-policy --role-name tenant-$T-role --policy-name broad --policy-document file:///tmp/broad.json
done
```

## Part B — Attack / observe: cross-tenant access
```bash
assume(){ aws sts assume-role --role-arn arn:aws:iam::$ACCT_ID:role/$1 --role-session-name x --query Credentials --output json; }
CA=$(assume tenant-A-role)
run_as(){ AWS_ACCESS_KEY_ID=$(echo $CA|jq -r .AccessKeyId) AWS_SECRET_ACCESS_KEY=$(echo $CA|jq -r .SecretAccessKey) AWS_SESSION_TOKEN=$(echo $CA|jq -r .SessionToken) "$@"; }
run_as aws s3 cp "s3://$BUCKET/tenantB/secret.txt" -           # BUG: Tenant A reads Tenant B ❌
run_as aws dynamodb get-item --table-name lab04-data --key '{"tenant_id":{"S":"tenantB"},"item":{"S":"x"}}'  # reads B ❌
python3 ../../cloud/ciem/aws_least_privilege.py
```

## Part C — Harden: isolation at every layer
```bash
# 1. Scope each role to its own prefix + partition via IAM conditions
for T in A B; do
  low=$(echo $T | tr A-Z a-z)
  cat > /tmp/scoped-$T.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject"],
  "Resource":"arn:aws:s3:::$BUCKET/tenant$T/*"},
 {"Effect":"Allow","Action":"s3:ListBucket","Resource":"arn:aws:s3:::$BUCKET",
  "Condition":{"StringLike":{"s3:prefix":"tenant$T/*"}}},
 {"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:Query"],
  "Resource":"arn:aws:dynamodb:$AWS_REGION:$ACCT_ID:table/lab04-data",
  "Condition":{"ForAllValues:StringEquals":{"dynamodb:LeadingKeys":["tenant$T"]}}}]}
EOF
  aws iam put-role-policy --role-name tenant-$T-role --policy-name scoped --policy-document file:///tmp/scoped-$T.json
  aws iam delete-role-policy --role-name tenant-$T-role --policy-name broad
done

# 2. Per-tenant KMS key (a tenant can use only its own key)
KMS_B=$(aws kms create-key --description tenantB --query KeyMetadata.KeyId --output text)
aws kms create-alias --alias-name alias/tenantB --target-key-id "$KMS_B"
# (grant only tenant-B-role kms:Decrypt on KMS_B via its key policy or a role policy)
```
**GUI:** IAM → Roles → `tenant-A-role` → edit the inline policy; **KMS → Customer
managed keys → Create key** → key policy grants only `tenant-B-role`.

## Part D — Verify
```bash
CA=$(assume tenant-A-role)
run_as aws s3 ls "s3://$BUCKET/tenantA/"                        # works ✅
run_as aws s3 cp "s3://$BUCKET/tenantB/secret.txt" - 2>&1 | grep -i denied   # AccessDenied ✅
run_as aws dynamodb get-item --table-name lab04-data --key '{"tenant_id":{"S":"tenantB"},"item":{"S":"x"}}' 2>&1 | grep -i denied  # denied ✅
python3 ../../cloud/ciem/aws_least_privilege.py
python3 ../../cloud/aws/s3_public_check.py
```

## Cleanup
```bash
for T in A B; do aws iam delete-role-policy --role-name tenant-$T-role --policy-name scoped 2>/dev/null; aws iam delete-role --role-name tenant-$T-role; done
aws dynamodb delete-table --table-name lab04-data
aws kms schedule-key-deletion --key-id "$KMS_B" --pending-window-in-days 7
aws s3 rb "s3://$BUCKET" --force
```

## Portfolio artifact
- A **tenant-isolation decision doc** (silo/pool/bridge, when each) + the controls
  used at identity/data/key layers.
- The **before/after** cross-tenant test output (crossover → denied).
- An isolation-boundary diagram.

## Stretch goals
- Rebuild as **silo** (account-per-tenant via Organizations) and compare.
- Add **session tags + scoped session policy** for one app role downscoped per
  request (pool-at-scale ABAC).
- Enforce the perimeter with an **RCP** (`../../iam/policies/aws-rcp-data-perimeter.json`).
