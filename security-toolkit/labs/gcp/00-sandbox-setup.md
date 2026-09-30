# Lab 00 — GCP Sandbox Setup & Guardrails

**Skills practiced:** project/org hardening · Budgets · Organization Policy ·
Cloud Identity baseline · Cloud Audit Logs.
**Proves (JD):** securing a deployment "from construction" — the safe foundation.

## Objective
A safe, isolated GCP sandbox: a least-privilege day-to-day identity, org-policy
guardrails, budget alerts, and audit logging.

## Est. time / cost
45–60 min · **~$0**.

## Prerequisites
- A GCP **project you own** (ideally under an **organization**). FIDO2 key / authenticator.
- gcloud CLI:
  ```bash
  curl https://sdk.cloud.google.com | bash && exec -l $SHELL     # or your package manager
  gcloud version
  gcloud auth login                       # browser; no exported SA keys
  export PROJECT=$(gcloud config get-value project)
  export REGION=us-central1
  gcloud config set project "$PROJECT"
  ```

---

## Part A — Harden identity  *(console)*
1. **Admin console** (admin.google.com) → confirm **super-admin** accounts have
   **phishing-resistant MFA** (security keys). Create **2 break-glass**
   super-admins, sealed, alerted on use (see `../../iam/architecture/gcp.md`).
2. Your day-to-day user gets least privilege (Viewer at project):
   ```bash
   MY=$(gcloud config get-value account)
   gcloud projects add-iam-policy-binding "$PROJECT" --member="user:$MY" --role="roles/viewer"
   gcloud auth list      # your user, not a service-account key
   ```

## Part B — Org Policy guardrails (org/folder scope)
```bash
# Requires org-level permission; run at org or folder. Examples:
gcloud resource-manager org-policies enable-enforce iam.disableServiceAccountKeyCreation --project "$PROJECT"
gcloud resource-manager org-policies enable-enforce storage.publicAccessPrevention --project "$PROJECT"
gcloud resource-manager org-policies enable-enforce compute.requireOsLogin --project "$PROJECT"
# Restrict resource locations:
cat > /tmp/loc.yaml <<EOF
constraint: constraints/gcp.resourceLocations
listPolicy: {allowedValues: ["in:us-locations"]}
EOF
gcloud resource-manager org-policies set-policy /tmp/loc.yaml --project "$PROJECT"
```
**Console:** **IAM & Admin → Organization Policies** → search each constraint →
**Manage policy → Enforce**. Adapt `../../iam/policies/gcp-org-policy-baseline.md`.

## Part C — Cost guardrails
```bash
BILLING=$(gcloud billing projects describe "$PROJECT" --query billingAccountName 2>/dev/null || gcloud beta billing projects describe "$PROJECT" --format='value(billingAccountName)')
gcloud billing budgets create --billing-account="${BILLING##*/}" \
  --display-name="lab-monthly-5" --budget-amount=5USD \
  --threshold-rule=percent=0.8 --threshold-rule=percent=1.0 2>/dev/null \
  || echo "Console: Billing → Budgets & alerts → Create budget → \$5, alerts 80/100%"
```
Cost drivers to watch: **GKE control plane + nodes, LB, Cloud NAT, SCC Premium**.

## Part D — Logging
```bash
# Data Access logs on for tested services (Admin Activity is always on)
# Console: IAM & Admin → Audit Logs → enable Data Read/Write for the services you test.
# A log sink → a dedicated bucket (evidence trail; feeds Lab 06)
gcloud logging buckets create lab-logs --location=global --retention-days=365
gcloud logging sinks create lab-sink \
  logging.googleapis.com/projects/$PROJECT/locations/global/buckets/lab-logs \
  --log-filter='logName:"cloudaudit.googleapis.com"'
# Security Command Center (Standard is free)
gcloud scc settings services enable --service=SECURITY_CENTER --organization=<ORG_ID> 2>/dev/null || \
  echo "Console: Security → Security Command Center → enable (Standard)"
```

---

## Verify
```bash
gcloud auth list                                        # scoped user, not SA key
gcloud resource-manager org-policies list --project="$PROJECT"
bash ../../cloud/prowler_scan.sh                        # choose GCP — baseline posture
```
Success = super-admin MFA + break-glass, least-priv daily identity, org policies
enforced, budget alerts, audit logs sinking, SCC on.

## Cleanup
Keep this foundation. To remove the sink/bucket:
```bash
gcloud logging sinks delete lab-sink --quiet
gcloud logging buckets delete lab-logs --location=global --quiet
```

## Portfolio artifact
- "Secure GCP project baseline" writeup + screenshots of org policies, budget,
  and the log sink.

## Stretch goals
- Enable **Chronicle** / a SIEM sink now (Lab 06).
- Create a second project under a folder (preview Lab 04).
- Codify org policies + sink as Terraform; `checkov`.
