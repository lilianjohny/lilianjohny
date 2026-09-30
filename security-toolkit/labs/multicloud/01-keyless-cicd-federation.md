# Lab 01 — Keyless CI/CD Federation (Multi-Cloud)

**Skills practiced:** OIDC workload identity federation · one pipeline → three
keyless cloud trusts · scoped trust conditions · eliminating static cloud secrets.
**Proves (JD):** machine authN/authZ + supply-chain security.

## Objective
One GitHub Actions pipeline authenticates to AWS, Azure, and GCP with **no stored
credentials** — every token short-lived and OIDC-exchanged, scoped to this repo.

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Sandbox AWS + Azure + GCP; a GitHub repo you control. Reference IaC:
  `../../iam/terraform/{aws,azure,gcp}/main.tf`, `../../iam/terraform/multicloud/README.md`.

---

## Part A — Build the three trusts
**AWS (OIDC provider + role):**
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
cat > /tmp/trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"Federated":"arn:aws:iam::$ACCT_ID:oidc-provider/token.actions.githubusercontent.com"},
 "Action":"sts:AssumeRoleWithWebIdentity",
 "Condition":{"StringEquals":{"token.actions.githubusercontent.com:sub":"repo:<org>/<repo>:environment:production"}}}]}
EOF
aws iam create-role --role-name github-ci --assume-role-policy-document file:///tmp/trust.json
```
**Azure (app + federated credential):**
```bash
APPID=$(az ad app create --display-name github-ci --query appId -o tsv)
az ad sp create --id "$APPID"
az ad app federated-credential create --id "$APPID" --parameters '{
 "name":"gh-prod","issuer":"https://token.actions.githubusercontent.com",
 "subject":"repo:<org>/<repo>:environment:production","audiences":["api://AzureADTokenExchange"]}'
```
**GCP (workload identity pool + provider):**
```bash
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='<org>/<repo>'"
```

## Part B — Attack / observe: why static keys are the risk
```bash
# Anti-pattern: a long-lived key in GitHub secrets. Show how it gets caught:
bash ../../devsecops/secret_scan.sh .    # or gitleaks — flags committed cloud keys
```

## Part C — Harden: one workflow, three keyless logins
```yaml
# .github/workflows/deploy.yml
permissions: { id-token: write, contents: read }
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
      - run: aws sts get-caller-identity && az account show && gcloud auth list
```
Store the trust identifiers as GitHub **variables** (not secrets — they're not
credentials).

## Part D — Verify
```bash
# In the Actions run log: all three identity commands succeed, tokens short-lived.
gitleaks detect --source .        # zero long-lived cloud keys in the repo ✅
```

## Cleanup
```bash
aws iam delete-role --role-name github-ci
aws iam delete-open-id-connect-provider --open-id-connect-provider-arn arn:aws:iam::$ACCT_ID:oidc-provider/token.actions.githubusercontent.com
az ad app delete --id "$APPID"
gcloud iam workload-identity-pools delete github --location=global --quiet
```

## Portfolio artifact
- The **deploy.yml** + a diagram: one pipeline → three keyless trusts.
- A writeup: "how OIDC federation removes standing cloud credentials," with the
  scoped trust conditions.

## Stretch goals
- Add **environment protection rules** so only `production` gets the trust.
- Add SBOM + signing (per-cloud Lab 02) so the same keyless pipeline proves
  artifact integrity.
- Break the trust condition (wrong branch) and show the login is **denied**.
