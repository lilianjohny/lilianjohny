# Lab 00 — Azure Sandbox Setup & Guardrails

**Skills practiced:** subscription hardening · Cost Management budgets · Entra ID
baseline · Conditional Access · PIM · activity/diagnostic logging.
**Proves (JD):** securing a deployment "from construction" — the safe foundation.

## Objective
A safe, isolated Azure sandbox: a non-privileged day-to-day identity, PIM for
elevation, budget alarms, management-group guardrails, and audit logging — before
you build anything to attack.

## Est. time / cost
45–60 min · **~$0**.

## Prerequisites
- An Azure **subscription you own** (ideally a fresh one, or a dedicated tenant).
- Azure CLI (`az version`). FIDO2 key / authenticator for MFA.

---

## Part A — Harden the tenant/global admin
1. Ensure **Global Administrator** accounts have **phishing-resistant MFA**.
2. Create **2 break-glass** cloud-only Global Admin accounts, FIDO2, **excluded
   from Conditional Access**, alerted on sign-in (see `../../iam/architecture/azure.md`).
3. You will **not** operate day-to-day as Global Admin.

## Part B — Identity & elevation (Entra + PIM)
1. Create your day-to-day user with a **least-privilege** role (e.g. Reader at
   subscription).
2. Enable **PIM**: make privileged roles (Owner, Contributor, Global Admin)
   **eligible, not active**; require approval + MFA + justification to activate.
3. **Conditional Access** baseline (start in **report-only**):
   - Require MFA for all users; **block legacy authentication**.
   - Require compliant device for admin (if you have Intune) — else note it.
4. CLI without secrets: `az login` (interactive/device code); confirm identity:
   ```bash
   az account show
   ```

## Part C — Cost guardrails
1. **Cost Management → Budgets:** a **$5/month** budget with 50/80/100% alerts.
2. Note cost drivers you'll meet: **AKS load balancers/nodes, Azure Firewall,
   Bastion, Defender plans** — labs flag them; tear down same-session.

## Part D — Guardrails & logging
1. **Azure Policy** at **management-group** scope — assign a baseline (region
   lock, deny public network, require diagnostics). Adapt
   `../../iam/policies/azure-policy-baseline.md`; assign the **Microsoft cloud
   security benchmark** initiative for broad coverage.
2. **Diagnostic settings:** send Entra sign-in/audit + Activity Log to a **Log
   Analytics workspace** (your evidence trail).
3. Turn on **Defender for Cloud** (free tier / Foundational CSPM) for posture.

---

## Verify
```bash
az account show                       # you're a scoped user, not break-glass GA
az policy assignment list --query "[].displayName"   # guardrails assigned
# Toolkit posture (Azure)
bash ../../cloud/prowler_scan.sh      # (choose Azure) — baseline findings
```
Success = GA has MFA + break-glass exists, you operate least-privilege with PIM,
budget alerts set, Azure Policy assigned, logs flowing, Defender on.

## Cleanup
Keep this foundation for later labs.

## Portfolio artifact
- A "secure Azure landing zone (lite)" writeup + screenshots of PIM config,
  Conditional Access (report-only), budget, and the policy assignment.

## Stretch goals
- Enable **Microsoft Sentinel** on the workspace now (used in Lab 06).
- Stand up a second subscription under the management group — preview Lab 04.
- Codify the policy assignment + diagnostic settings as **Bicep/Terraform**.
