# SSO Implementation Process (2026)

A repeatable, change-controlled rollout. Do it **once in a non-production
tenant/org**, validate, then promote. Each phase has an owner and an exit check.

> Order matters: get the IdP right first, federate one cloud, prove the login +
> deprovisioning loop, then repeat. Never big-bang all three clouds at once.

---

## Phase 0 — Prerequisites & design (before touching anything)
- [ ] Choose the **single IdP** (Entra ID or Okta) and confirm it is HR-fed
      (joiners/movers/leavers).
- [ ] Enable **phishing-resistant MFA** (FIDO2 / passkeys) in the IdP; plan to
      block legacy/basic auth.
- [ ] Define the **group taxonomy** (`role-<function>-<scope>-<privilege>`) — see
      `../architecture/multicloud.md`.
- [ ] Inventory targets: AWS Organization + accounts, Azure tenant + subscriptions,
      GCP org + projects, SaaS apps.
- [ ] Decide protocol per target (SAML vs OIDC) and whether SCIM is supported.
- [ ] **Exit check:** design doc approved; break-glass plan written.

---

## Phase 1 — Harden the IdP (the hub)
- [ ] Enforce phishing-resistant MFA for all users; require it for admins.
- [ ] Configure baseline sign-in policy / **Conditional Access**: block legacy
      auth, require MFA, set session lifetime, restrict risky sign-ins.
- [ ] Create the group taxonomy; connect the HR feed for lifecycle.
- [ ] Protect IdP admin roles with **JIT/PIM** + hardware MFA (Tier-0).
- [ ] **Exit check:** a test user authenticates with FIDO2; legacy auth is blocked.

---

## Phase 2 — AWS (IAM Identity Center)
1. Enable **IAM Identity Center** in the Org (delegate admin to a dedicated account).
2. Set identity source = **external IdP**: configure **SAML** trust + **SCIM**
   provisioning from the IdP (bootstrap in console; token/metadata exchanged once).
3. Verify users/groups sync via SCIM.
4. Define **permission sets** and **group→permission-set→account** assignments as
   code — see `../terraform/aws/main.tf`.
5. Test: a user in `role-…-readonly` logs in via the access portal, assumes a
   short-lived role in the right account, and **cannot** exceed it.
- [ ] **Exit check:** SSO login works; SCIM sync works; SCP/RCP guardrails
      (`../../iam/policies/`) still cap the SSO roles.

---

## Phase 3 — Azure (Entra ID)
1. Confirm Entra is authoritative (or federated upstream from Okta).
2. Configure **Conditional Access**: MFA, device compliance, block legacy auth,
   sign-in frequency.
3. Register **enterprise applications** for SaaS (SAML/OIDC), assign **groups** —
   see `../terraform/azure/main.tf`.
4. Set privileged roles to **PIM-eligible** (JIT); configure approvals + access
   reviews.
5. Configure **SCIM provisioning** to downstream apps.
- [ ] **Exit check:** CA blocks a non-compliant sign-in; PIM activation requires
      approval + MFA; legacy auth is off.

---

## Phase 4 — GCP (Workforce Identity Federation)
1. Create a **Workforce Identity Pool + Provider** (OIDC or SAML) trusting the IdP;
   map attributes incl. **`google.groups`** — see `../terraform/gcp/main.tf`.
2. Grant IAM roles by **`principalSet://…/group/<group>`** binding (never per user).
3. (Optional but recommended) Configure **Context-Aware Access** access levels for
   the ZT gate — `../../zero-trust/architecture/gcp.md`.
4. Enforce **Org Policies** (disable SA keys, resource locations, public access
   prevention) — `../../iam/terraform/gcp/main.tf`.
5. Test: a federated user assumes short-lived Google creds and gets exactly their
   group's roles.
- [ ] **Exit check:** federated login works; IAM follows groups; no SA keys exist.

---

## Phase 5 — Provisioning & lifecycle (prove offboarding)
- [ ] SCIM/provisioning live on every target that supports it.
- [ ] **Test a joiner:** add to a group → correct access appears in each cloud.
- [ ] **Test a mover:** change groups → entitlements shift.
- [ ] **Test a leaver:** disable in IdP → access removed **everywhere** within the
      provisioning SLA. This is the single most important test.
- [ ] **Exit check:** leaver test passes in all clouds; screenshot/log kept as
      evidence (`../../soc-reports/evidence/`).

---

## Phase 6 — Zero standing privilege
- [ ] Privileged access is JIT everywhere: Identity Center JIT / Entra PIM / GCP PAM.
- [ ] Activation requires approval + MFA + justification, time-boxed.
- [ ] Access reviews / recertification scheduled on privileged groups.
- [ ] **Exit check:** no standing admins; elevation is logged and expires.

---

## Phase 7 — Detection, review & operate
- [ ] All auth + admin logs → SIEM (`../../soc/`, `../../cloud/detection/`).
- [ ] Alerts: new admin, root/Global-Admin use, MFA disabled, CA/policy change,
      federation/permission-set change, impossible-travel.
- [ ] Access reviews on a cadence (`../../iam/validation/iam_posture_check.md`).
- [ ] Break-glass tested quarterly; usage alerts verified.
- [ ] Map controls to frameworks (`../../grc/compliance/crosswalk.py`).
- [ ] **Exit check:** `../validation/sso_posture_check.md` fully green.

---

## Rollback / safety
- Keep **break-glass** (cloud-native, outside federation) working at every phase.
- Roll out CA / policy in **report-only** first, then enforce.
- Federate **one cloud at a time**; keep the previous access path until the new one
  is proven.
- All federation trusts and assignments in `../terraform/` under version control —
  revert = revoke.

---

## How to run the Terraform references
```bash
cd terraform/aws     # or azure / gcp
terraform init
terraform plan        # review — never apply blind to a real tenant
# terraform apply     # only after review, in a non-prod tenant first
```
The Terraform here is **reference/starting point**: fill in your IdP metadata,
org/tenant ids, and account/project ids. SAML/SCIM connection bootstrapping and
Conditional Access/PIM tuning are done in the IdP + cloud consoles/Graph as noted
per phase, then captured as code where the providers support it.
