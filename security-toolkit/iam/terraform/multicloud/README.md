# Multi-Cloud IAM — federation wiring

The per-cloud modules (`../aws`, `../azure`, `../gcp`) each establish a **keyless
OIDC trust** for the *same* CI identity and equivalent guardrails. Applied
together, one pipeline authenticates to all three clouds with **no stored keys**.

## One pipeline, three keyless trusts

```yaml
# .github/workflows/deploy.yml (excerpt)
permissions:
  id-token: write        # required for OIDC in all three
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # AWS — assume role via OIDC (output github_ci_role_arn)
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_CI_ROLE_ARN }}
          aws-region: us-east-1

      # Azure — login via workload identity federation (output github_ci_client_id)
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      # GCP — auth via workload identity federation (output workload_identity_provider)
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.GCP_WIF_PROVIDER }}
          service_account: ${{ vars.GCP_CI_SA_EMAIL }}
```

No `AWS_SECRET_ACCESS_KEY`, no Azure client secret, no GCP service-account JSON
— every credential is a short-lived OIDC-exchanged token, scoped to this repo
(and branch/environment) by the trust conditions in each module.

## Apply order
1. `../aws` → outputs `github_ci_role_arn`
2. `../azure` → outputs `github_ci_client_id` (+ your tenant/subscription ids)
3. `../gcp` → outputs `workload_identity_provider`, `ci_service_account_email`
4. Put those into GitHub repo/environment **variables** (not secrets — they're
   identifiers, not credentials), and use the workflow above.

## Human identity (out of band)
Human SSO federates each cloud to your central IdP (see
`../../architecture/multicloud.md`): AWS IAM Identity Center (SAML+SCIM), Entra
(native/federated), GCP Workforce Identity Federation. Those are configured in
the IdP + cloud consoles / dedicated providers, not in these workload modules.

## State & secrets
- Store Terraform state in an encrypted, access-controlled backend per cloud
  (S3+DynamoDB lock / Azure Storage / GCS) — never local for real orgs.
- These modules store **no** long-lived credentials; the only sensitive inputs
  are org/tenant identifiers.
