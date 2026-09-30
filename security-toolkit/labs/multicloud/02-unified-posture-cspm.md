# Lab 02 — Unified Posture / CSPM (Multi-Cloud)

**Skills practiced:** cross-cloud posture assessment · normalizing findings to one
schema · a single risk view over AWS+Azure+GCP · prioritizing across providers.
**Proves (JD):** securing multi-cloud deployments — see the whole estate.

## Objective
Scan all three clouds, **normalize** findings into one schema, and produce one
prioritized report.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Sandbox AWS + Azure + GCP with read/security-audit access; auth set for each
  (`aws configure sso` / `az login` / `gcloud auth login`).
- Toolkit: `../../cloud/multicloud/` (`scan_all.sh`, `normalize.py`, `report.py`,
  `baseline.csv`).

---

## Part A — Build: one misconfig per cloud (your sandbox)
```bash
# AWS: a public-ish bucket setting (then you'll lock it)
aws s3api create-bucket --bucket cspm-demo-$ACCT_ID --region $AWS_REGION
aws s3api delete-public-access-block --bucket cspm-demo-$ACCT_ID   # (the misconfig)
# Azure: a storage account allowing public blob access
az storage account create -n cspm$RANDOM -g rg-cspm -l $LOCATION --allow-blob-public-access true 2>/dev/null || az group create -n rg-cspm -l $LOCATION
# GCP: a firewall open to the world
gcloud compute firewall-rules create cspm-open --allow=tcp:22 --source-ranges=0.0.0.0/0 2>/dev/null || true
```

## Part B — Attack / observe: the three-consoles problem
Each cloud names/severity-rates these differently — cross-cloud triage by hand
doesn't scale.

## Part C — Harden the *process*: one pane
```bash
bash ../../cloud/multicloud/scan_all.sh                    # runs per-cloud scanners
python3 ../../cloud/multicloud/normalize.py <scan-output>  # → one schema (category, severity, resource)
python3 ../../cloud/multicloud/report.py <normalized>      # single prioritized report
```
Confirm all three "public exposure" findings land in the **Data** category with
consistent severity (that's what `normalize.py`'s category rules do). Diff
against `../../cloud/multicloud/baseline.csv` to track drift.

## Part D — Remediate + verify
```bash
aws s3api put-public-access-block --bucket cspm-demo-$ACCT_ID \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
az storage account update -n <acct> -g rg-cspm --allow-blob-public-access false
gcloud compute firewall-rules delete cspm-open --quiet
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py   # findings clear
python3 ../../cloud/aws/s3_public_check.py                                            # AWS confirm
```

## Cleanup
```bash
aws s3 rb s3://cspm-demo-$ACCT_ID --force
az group delete -n rg-cspm --yes --no-wait
```

## Portfolio artifact
- The **before/after unified report** (three clouds, one schema).
- A note on **why normalization matters** for cross-cloud prioritization.

## Stretch goals
- Extend `normalize.py`'s mapping to a new finding type; add a test case.
- Feed the normalized output into `../../vulnmgmt/` for SLA + KEV/EPSS enrichment.
- Schedule the scan (cron/CI) and alert on drift vs `baseline.csv`.
