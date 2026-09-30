# Cloud DevSecOps

Security-posture audits and pipeline guardrails for **AWS**, **Azure**, and
**Google Cloud**, plus provider-agnostic **IaC scanning** and a **CI/CD
security gate**.

> ⚠️ **Authorized use only.** Every audit here reads from cloud accounts using
> **your own authenticated credentials/CLI session**. It only inspects
> configuration you already have access to — nothing here changes cloud
> resources. Run against accounts you own or are contracted to assess.

## Layout

| Path | What it does | Needs |
|------|--------------|-------|
| `aws/iam_audit.py`     | IAM hygiene: root usage, MFA, stale keys, wildcard policies | `boto3`, AWS creds |
| `aws/s3_public_check.py` | Public buckets, encryption, versioning, public-access block | `boto3`, AWS creds |
| `aws/sg_audit.py`      | Security groups exposing sensitive ports to `0.0.0.0/0` | `boto3`, AWS creds |
| `azure/nsg_audit.sh`   | NSG rules open to the internet on sensitive ports | `az` CLI |
| `azure/storage_audit.sh` | Storage accounts: HTTPS-only, public blob access, TLS version | `az` CLI |
| `azure/rbac_audit.sh`  | Subscription Owner/role-assignment sprawl, classic admins | `az` CLI |
| `gcp/iam_audit.sh`     | Primitive roles, user-managed SA keys, public IAM bindings | `gcloud` CLI |
| `gcp/storage_audit.sh` | Public GCS buckets, uniform bucket-level access | `gcloud`/`gsutil` |
| `gcp/firewall_audit.sh`| Firewall rules allowing `0.0.0.0/0` to sensitive ports | `gcloud` CLI |
| `iac/iac_scan.sh`      | Runs checkov / tfsec / trivy over Terraform/IaC if installed | any of those |
| `cicd/pipeline_gate.sh`| DevSecOps gate: secrets + SCA + IaC in one pass/fail | see script |

## Authentication (bring your own session)

These scripts never take credentials as arguments. Authenticate first with the
provider's own tooling:

```bash
# AWS  – uses default credential chain (env vars, ~/.aws, SSO, role)
aws sts get-caller-identity

# Azure
az login            # or: az login --identity  (managed identity in pipelines)

# GCP
gcloud auth login   # or: gcloud auth activate-service-account ... (CI)
gcloud config set project <PROJECT_ID>
```

## Install

```bash
pip install -r ../requirements-cloud.txt   # boto3 for the AWS scripts
```

CLI tools (`az`, `gcloud`) and scanners (`checkov`, `tfsec`, `trivy`,
`gitleaks`) are used **if present** — each script degrades gracefully and tells
you what to install.

## Exit codes (CI-friendly)

`0` clean · `1` warnings · `2` failing findings · `3` setup/auth error.

Wire `cicd/pipeline_gate.sh` into a pipeline stage to block merges on
high-severity findings.
