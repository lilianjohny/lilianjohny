# Lab 03 — Cross-Cloud Workload Identity (Multi-Cloud)

**Skills practiced:** workload identity federation *between* clouds · a service in
one cloud calling another with no stored keys · scoped short-lived cross-cloud
tokens.
**Proves (JD):** securing multi-cloud deployments + machine authN/authZ.

## Objective
A workload in **Cloud A** reaches a resource in **Cloud B** using federated,
short-lived credentials — never a stored key. Example here: a **GCP** workload
reads an **AWS** S3 object via OIDC token exchange.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Sandbox in ≥2 clouds; per-cloud Lab 01 done. Reference:
  `../../iam/architecture/multicloud.md`.

---

## Part A — Build the scenario
```bash
# Cloud B (AWS): the target bucket + object
aws s3api create-bucket --bucket xcloud-$ACCT_ID-data --region $AWS_REGION
echo "cross-cloud-ok" | aws s3 cp - s3://xcloud-$ACCT_ID-data/ok.txt
# Cloud A (GCP): a service account whose OIDC identity token we'll exchange
gcloud iam service-accounts create xcloud-caller
```

## Part B — Attack / observe: the stored-key anti-pattern
Putting a long-lived **AWS access key** in the GCP workload's config = a standing
credential in another cloud's environment, easy to leak, never expires. Note it,
don't do it.

## Part C — Harden: federate identity across clouds
```bash
# In AWS (Cloud B): an OIDC provider trusting Google's token issuer, and a role
# scoped to the GCP SA's subject (the SA's unique 'sub'/'oid').
GOOGLE_ISS=https://accounts.google.com
aws iam create-open-id-connect-provider --url $GOOGLE_ISS --client-id-list <gcp-sa-client-id> 2>/dev/null || true
cat > /tmp/xtrust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"Federated":"arn:aws:iam::$ACCT_ID:oidc-provider/accounts.google.com"},
 "Action":"sts:AssumeRoleWithWebIdentity",
 "Condition":{"StringEquals":{"accounts.google.com:sub":"<gcp-sa-unique-id>"}}}]}
EOF
aws iam create-role --role-name xcloud-reader --assume-role-policy-document file:///tmp/xtrust.json
aws iam put-role-policy --role-name xcloud-reader --policy-name read --policy-document \
  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::xcloud-$ACCT_ID-data/*\"}]}"
```
In the **GCP** workload: fetch its Google **identity token** (audience = the AWS
role/STS) and call `AssumeRoleWithWebIdentity`:
```bash
# On the GCP workload (metadata identity token → AWS STS), conceptually:
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
 "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=sts.amazonaws.com&format=full")
aws sts assume-role-with-web-identity --role-arn arn:aws:iam::$ACCT_ID:role/xcloud-reader \
  --role-session-name xc --web-identity-token "$TOKEN"   # → short-lived AWS creds, no stored key
```

## Part D — Verify
```bash
# With the exchanged short-lived creds:
aws s3 cp s3://xcloud-$ACCT_ID-data/ok.txt -    # works (scoped)
aws s3 ls                                        # denied beyond the bucket ✅
gitleaks detect --source <workload-config-dir>   # zero long-lived cross-cloud keys ✅
```

## Cleanup
```bash
aws iam delete-role-policy --role-name xcloud-reader --policy-name read
aws iam delete-role --role-name xcloud-reader
aws s3 rb s3://xcloud-$ACCT_ID-data --force
gcloud iam service-accounts delete xcloud-caller@$PROJECT.iam.gserviceaccount.com --quiet
```

## Portfolio artifact
- A **cross-cloud federation diagram** (Cloud A identity → token exchange → Cloud
  B role → resource).
- A writeup contrasting **stored key vs federated token**, with the scoped trust.

## Stretch goals
- Reverse the direction (AWS workload → GCP resource via Workload Identity Federation).
- Add **VPC-SC / RCP** on the target so even the federated identity is confined.
- Put the whole trust in Terraform; `checkov`.
