# Lab 00 — Sandbox Setup & Guardrails

**Skills practiced:** account hardening · budget/cost guardrails · IAM Identity
Center · secure CLI access (no long-lived keys) · baseline logging.
**Proves (JD):** "securing … deployments from construction" — you secure the
foundation *before* building on it.

## Objective
Stand up a **safe, isolated AWS sandbox** you can attack and break in later labs
without risking real assets or a surprise bill. When you finish, you have: an
admin identity that isn't root, a low-privilege identity to test with, budget
alarms, org-level guardrails, and audit logging on.

## Est. time / cost
45–60 min · **~$0** (all free-tier / no-cost services).

## Prerequisites
- A **dedicated AWS account** you own (ideally a fresh one, not shared).
- AWS CLI v2 installed (`aws --version`).
- A FIDO2 security key or an authenticator app for MFA.

---

## Part A — Lock down the root user
1. Sign in as **root** (email + password) — this is the *only* time you should.
2. Enable **MFA on root** (hardware key preferred).
3. Confirm there are **no root access keys** (IAM console → root → delete any).
4. Set account **contact + alternate security contact**.

> Why: root is unrestricted. From here on you never use it; everything else is
> least-privilege identities.

## Part B — Set up IAM Identity Center (your day-to-day access)
1. Enable **IAM Identity Center** (in your home Region).
2. Create a user for yourself; create two **permission sets**:
   - `AdminForLabs` → `AdministratorAccess` (for building labs).
   - `ReadOnlyTester` → `ReadOnlyAccess` (to test least-privilege from the
     attacker's side).
3. Assign both to your account.
4. Configure the CLI with SSO (no static keys):
   ```bash
   aws configure sso           # follow prompts; pick the AdminForLabs role
   aws sts get-caller-identity # confirm you're the SSO admin role, not root
   ```

## Part C — Cost guardrails (so a lab never surprises you)
1. **AWS Budgets** → create a **$5/month** cost budget with alerts at 50/80/100%.
2. (Optional) A **zero-spend budget** to catch anything leaving free tier.
3. Note the cost drivers you'll meet later: **EKS control plane, NAT Gateway,
   ALB/NLB, GuardDuty** — labs flag these; tear them down same-session.

## Part D — Baseline logging & guardrails
1. Enable a **CloudTrail** org/all-Region trail → a dedicated S3 bucket
   (Block Public Access on, SSE-KMS). This is your evidence trail for every lab.
2. Enable **AWS Config** (at least in your home Region).
3. Turn on **IAM Access Analyzer**.
4. (If using AWS Organizations) attach a minimal **SCP** denying
   `iam:CreateAccessKey` for humans and blocking Regions you won't use — see
   `../../iam/policies/aws-scp-baseline.json` for a baseline to adapt.

---

## Verify
```bash
# You are NOT root and have a session, not static keys:
aws sts get-caller-identity

# Toolkit: baseline IAM hygiene (expect clean or documented exceptions)
python3 ../../cloud/aws/iam_audit.py

# Toolkit: is logging/detection coverage on?
python3 ../../cloud/detection/aws_detection_coverage.py
```
Success = root has MFA + no keys, you operate via SSO, budgets alert, CloudTrail
+ Config + Access Analyzer are on.

## Cleanup
Keep this foundation — later labs reuse it. (Only tear down per-lab resources.)
If you're abandoning the account entirely, disable services and close the
account.

## Portfolio artifact
- A one-page "secure account baseline" writeup + a screenshot of your budget,
  CloudTrail, and Identity Center config.
- Note the **order** you did things (root → identities → guardrails → logging) —
  sequencing *is* the security lesson.

## Stretch goals
- Add a **break-glass** IAM user (hardware MFA, alerted on use) per
  `../../iam/architecture/aws.md`; test that alerting fires.
- Stand up a **second member account** and manage both from Organizations —
  preview of multi-tenant (Lab 04).
- Codify this whole baseline as Terraform and diff it against the console.
