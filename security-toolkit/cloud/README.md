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
| `prowler_scan.sh`      | **Production CSPM** via Prowler (AWS/Azure/GCP/K8s), severity-gated | `prowler` or `docker` |
| `iac/iac_scan.sh`      | Runs checkov / tfsec / trivy over Terraform/IaC if installed | any of those |
| `cicd/pipeline_gate.sh`| DevSecOps gate: secrets + SCA + IaC + image + CSPM, SARIF output | trivy/checkov/gitleaks |

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

## Production usage

The recommended, production-grade path uses the standard scanners end-to-end:

```bash
# One reproducible gate (secrets + SCA + IaC + image + optional CSPM),
# emitting SARIF into ./security-reports for the GitHub Security tab.
bash cloud/cicd/pipeline_gate.sh \
  --path . --report-dir security-reports \
  --severity CRITICAL,HIGH --image myregistry/app:1.2.3 --cloud aws

# Cloud posture only (Prowler), machine-readable + HTML reports:
bash cloud/prowler_scan.sh aws --severity critical,high --output-dir out/aws
```

- **CI pipeline:** `.github/workflows/devsecops.yml` runs the gate on every PR
  and push, uploads SARIF to Code scanning, and includes an opt-in Prowler job
  that authenticates via **OIDC** (no long-lived cloud keys).
- **Reproducible image:** `../Dockerfile` bundles the toolkit with pinned
  Trivy / Gitleaks / Checkov / Prowler / boto3 versions, so the gate behaves
  identically locally and in CI.
- **Least privilege:** cloud CSPM should assume a read-only role
  (e.g. AWS `SecurityAudit` + Prowler's extra read policy, Azure `Reader` +
  `Security Reader`, GCP `roles/viewer` + `roles/iam.securityReviewer`).

The lightweight per-provider scripts remain as a **zero-dependency fallback**
for environments where you can't install the full scanner set.
