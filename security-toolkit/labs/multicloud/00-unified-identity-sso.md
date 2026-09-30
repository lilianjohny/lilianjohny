# Lab 00 — Unified Identity & SSO (Multi-Cloud)

**Skills practiced:** single IdP federation · SSO to AWS + Azure + GCP ·
phishing-resistant MFA · group-driven entitlements · SCIM · the leaver test.
**Proves (JD):** authN/authZ at scale.

## Objective
One identity, one login + MFA, works in every cloud; disable once → access gone
everywhere.

## Est. time / cost
3–4 h · **~$0**.

## Prerequisites
- A central IdP (Entra ID or Okta) you control; sandbox AWS + Azure + GCP (each
  Lab 00 done). Reference: `../../sso/`.

---

## Part A — Harden the IdP (hub)  *(IdP portal)*
1. Enforce **phishing-resistant MFA** (FIDO2/passkeys); block legacy auth.
2. Create the group taxonomy, e.g.:
   ```
   role-platform-all-readonly
   role-payments-prod-dba
   role-breakglass-<cloud>
   ```
3. Connect an HR/lifecycle source (or simulate joiners/movers/leavers).

## Part B — Federate each cloud
**AWS (Identity Center — console + CLI):**
```bash
# In IAM Identity Center: set identity source = External IdP (SAML), upload the
# IdP metadata, enable SCIM. Then assign the IdP group to a permission set:
aws sso-admin list-instances
# (permission sets + group assignments as code: ../../sso/terraform/aws/main.tf)
```
**Azure (Entra — native/federated):** Entra admin center → **Enterprise
applications** or native users; assign the group → RBAC (`../../sso/terraform/azure/main.tf`).
**GCP (Workforce Identity Federation — CLI):**
```bash
gcloud iam workforce-pools create external-idp --organization=<ORG_ID> --location=global
gcloud iam workforce-pools providers create-oidc oidc-provider \
  --workforce-pool=external-idp --location=global \
  --issuer-uri="https://login.microsoftonline.com/<tenant>/v2.0" \
  --client-id="<client-id>" --attribute-mapping="google.subject=assertion.sub,google.groups=assertion.groups"
# Bind IAM by group:
gcloud projects add-iam-policy-binding "$PROJECT" \
  --role=roles/viewer \
  --member="principalSet://iam.googleapis.com/locations/global/workforcePools/external-idp/group/role-platform-all-readonly"
```
(Full Terraform: `../../sso/terraform/gcp/main.tf`.)

## Part C — Prove the loop (the leaver test — the key artifact)
1. **Joiner:** add a test user to `role-platform-all-readonly` in the IdP →
   confirm read access appears in AWS, Azure, GCP.
2. **Mover:** change the user's groups → entitlements shift in each cloud.
3. **Leaver:** disable the user in the IdP → SCIM/federation removes access
   **everywhere** within the provisioning SLA. Capture evidence.

## Verify
```bash
aws sts get-caller-identity        # SSO role, short-lived
az account show                    # Entra user
gcloud auth list                   # workforce identity
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py   # identity posture across clouds
```

## Cleanup
Remove the test user/groups; keep federation if you'll continue the track.

## Portfolio artifact
- A **federation diagram** (one IdP → three clouds) + group→entitlement mapping.
- The **leaver-test evidence** (present → disabled → gone in each cloud).

## Stretch goals
- Add per-cloud **break-glass** (cloud-native, outside federation); test alerts.
- Enforce **JIT everywhere** (Identity Center JIT / Entra PIM / GCP PAM).
- Access reviews from IdP groups + per-cloud CIEM (`../../cloud/ciem/`).
