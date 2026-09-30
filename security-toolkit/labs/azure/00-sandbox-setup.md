# Lab 00 — Azure Sandbox Setup & Guardrails

**Skills practiced:** subscription hardening · Cost Management budgets · Entra ID
baseline · Conditional Access · PIM · activity/diagnostic logging.
**Proves (JD):** securing a deployment "from construction" — the safe foundation.

## Objective
A safe, isolated Azure sandbox: a non-privileged day-to-day identity, PIM for
elevation, budget alarms, management-group guardrails, and audit logging.

## Est. time / cost
45–60 min · **~$0**.

## Prerequisites
- An Azure **subscription you own**. FIDO2 key / authenticator for MFA.
- Azure CLI:
  ```bash
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash    # Linux (Debian/Ubuntu)
  # macOS: brew install azure-cli
  az version
  az login                      # device-code / browser; no static secrets
  export SUB=$(az account show --query id -o tsv)
  export LOCATION=eastus
  az account set --subscription "$SUB"
  ```

---

## Part A — Harden the tenant/global admin  *(portal)*
1. **Entra admin center** (https://entra.microsoft.com) → **Users** → confirm
   **Global Administrator** accounts have **phishing-resistant MFA** registered.
2. Create **2 break-glass** cloud-only Global Admins, FIDO2, **excluded from
   Conditional Access** (see `../../iam/architecture/azure.md`); add a sign-in
   alert. You will not operate day-to-day as Global Admin.

## Part B — Identity & elevation (Entra + PIM)
```bash
# Day-to-day user gets least privilege (Reader at subscription)
MYID=$(az ad signed-in-user show --query id -o tsv)   # or a dedicated lab user's objectId
az role assignment create --assignee "$MYID" --role "Reader" --scope "/subscriptions/$SUB"
```
**Portal — PIM:** Entra admin center → **Identity Governance → Privileged
Identity Management → Azure resources / Microsoft Entra roles** → make **Owner /
Contributor / Global Admin** *Eligible* (not active); require **approval + MFA +
justification** to activate.
**Portal — Conditional Access (start report-only):** Entra → **Protection →
Conditional Access → Create policy**: require MFA for all users; a second policy
to **Block legacy authentication**; set state = **Report-only** first.

## Part C — Cost guardrails
```bash
az consumption budget create --budget-name lab-monthly-5 --amount 5 \
  --category cost --time-grain Monthly \
  --start-date $(date +%Y-%m-01) --end-date 2030-12-31 \
  --scope "/subscriptions/$SUB" 2>/dev/null || \
  echo "If the CLI extension errors, set the budget in Portal → Cost Management → Budgets → Add"
```
**Portal:** **Cost Management + Billing → Budgets → Add** → $5 monthly, alert at
80/100%. Cost drivers to watch: **AKS LBs/nodes, Azure Firewall, Bastion,
Defender plans**.

## Part D — Guardrails & logging
```bash
# Log Analytics workspace = your evidence trail
az monitor log-analytics workspace create -g rg-security -n lab-law -l "$LOCATION" \
  2>/dev/null || { az group create -n rg-security -l "$LOCATION"; \
  az monitor log-analytics workspace create -g rg-security -n lab-law -l "$LOCATION"; }
WSID=$(az monitor log-analytics workspace show -g rg-security -n lab-law --query id -o tsv)

# Send subscription Activity Log to the workspace
az monitor diagnostic-settings subscription create --name to-law \
  --location "$LOCATION" --workspace "$WSID" \
  --logs '[{"category":"Administrative","enabled":true},{"category":"Security","enabled":true}]'

# Assign a baseline Azure Policy initiative (region lock example) at the subscription
az policy assignment create --name allowed-locations \
  --policy "e56962a6-4747-49cd-b67b-bf8b01975c4c" \
  --params "{\"listOfAllowedLocations\":{\"value\":[\"$LOCATION\"]}}" \
  --scope "/subscriptions/$SUB"
```
**Portal:** **Microsoft Defender for Cloud → Environment settings** → turn on
foundational CSPM. **Policy → Assignments → Assign initiative** → *Microsoft
cloud security benchmark* at the management group. Adapt
`../../iam/policies/azure-policy-baseline.md`.

---

## Verify
```bash
az account show                                   # scoped user, not break-glass GA
az policy assignment list --query "[].displayName" -o tsv
bash ../../cloud/prowler_scan.sh                  # choose Azure — baseline findings
```
Success = GA has MFA + break-glass exists, PIM gates elevation, budget alerts,
Azure Policy assigned, logs flowing to the workspace, Defender on.

## Cleanup
Keep this foundation for later labs. To remove just this lab's guardrail:
```bash
az policy assignment delete --name allowed-locations --scope "/subscriptions/$SUB"
```

## Portfolio artifact
- A "secure Azure landing zone (lite)" writeup + screenshots of PIM, Conditional
  Access (report-only), the budget, and the policy assignment.

## Stretch goals
- Enable **Microsoft Sentinel** on `lab-law` now (used in Lab 06).
- Add a second subscription under a management group (preview Lab 04).
- Codify the policy + diagnostic settings as **Bicep/Terraform**.
