# Lab 01 — Keyless CI/CD Federation (Multi-Cloud)

**Skills practiced:** OIDC workload identity federation · one pipeline → three
keyless cloud trusts · scoped trust conditions (repo/branch/environment) ·
eliminating long-lived cloud secrets from CI.
**Proves (JD):** authN/authZ for machines + supply-chain security — no static keys
anywhere.

## Objective
Make a single GitHub Actions pipeline authenticate to **AWS, Azure, and GCP** with
**no stored credentials** — every token short-lived and OIDC-exchanged, scoped to
this repo (and branch/environment).

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Sandbox AWS + Azure + GCP; a GitHub repo you control.
- Reference IaC: `../../iam/terraform/aws/main.tf`, `azure/main.tf`, `gcp/main.tf`,
  and `../../iam/terraform/multicloud/README.md`.

---

## Part A — Build the three trusts (as code)
1. **AWS:** GitHub OIDC provider + a role with a trust policy scoped to
   `repo:<org>/<repo>:environment:production` — outputs `github_ci_role_arn`.
2. **Azure:** an Entra app + **federated credential** for the same subject —
   outputs `github_ci_client_id`.
3. **GCP:** a **Workload Identity Pool + Provider** + a least-privilege SA —
   outputs `workload_identity_provider`, `ci_service_account_email`.
   > Note the pinned subject condition in `../../iam/terraform/gcp/main.tf`.

## Part B — Attack / observe: why static keys are the risk
1. Show the anti-pattern: putting `AWS_SECRET_ACCESS_KEY` / an Azure client secret
   / a GCP SA JSON in GitHub **secrets**. A leaked long-lived key = standing
   access with no expiry.
2. Run `../../devsecops/` secret scanning / `gitleaks` to show how such keys get
   caught (and why you never want them in the first place).

## Part C — Harden: one workflow, three keyless logins
Create `.github/workflows/deploy.yml` (excerpt from
`../../iam/terraform/multicloud/README.md`):
```yaml
permissions:
  id-token: write        # required for OIDC in all three
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ vars.AWS_CI_ROLE_ARN }}, aws-region: us-east-1 }
      - uses: azure/login@v2
        with: { client-id: ${{ vars.AZURE_CLIENT_ID }}, tenant-id: ${{ vars.AZURE_TENANT_ID }}, subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }} }
      - uses: google-github-actions/auth@v2
        with: { workload_identity_provider: ${{ vars.GCP_WIF_PROVIDER }}, service_account: ${{ vars.GCP_CI_SA_EMAIL }} }
```
Store the outputs as GitHub **variables** (identifiers, not secrets).

## Part D — Verify
```bash
# In the workflow, after each login step, prove identity with no stored keys:
aws sts get-caller-identity
az account show
gcloud auth list
# And prove NO long-lived cloud secrets exist in the repo/settings:
gitleaks detect --source .        # clean
```
Success = all three logins succeed via OIDC, tokens are short-lived, the trust is
scoped to this repo/branch/env, and there are zero long-lived cloud keys in CI.

## Part E — Least privilege the CI identities
Scope each CI role/SP/SA to only what the pipeline needs (deploy targets), not
broad admin. Re-check with `../../cloud/ciem/aws_least_privilege.py` (AWS side).

## Cleanup
Delete the OIDC providers/pools, CI roles/apps/SAs, and the workflow if not kept.

## Portfolio artifact
- The **deploy.yml** + a diagram: one pipeline → three keyless trusts.
- A short writeup: "how OIDC federation removes standing cloud credentials," with
  the scoped trust conditions you used.

## Stretch goals
- Add **environment protection rules** so only `production` deploys get the trust.
- Add supply-chain steps (SBOM + image signing from the per-cloud Lab 02) so the
  same keyless pipeline also proves artifact integrity.
- Break the trust condition (wrong branch) and show the login is **denied**.
