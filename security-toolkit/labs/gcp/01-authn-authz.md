# Lab 01 — Authentication & Authorization (GCP)

**Skills practiced:** IAM roles & bindings · service accounts done right ·
**Workload Identity Federation** (keyless) · **PAM** (JIT) · least privilege &
IAM Recommender · custom roles · app auth with **Identity Platform**.
**Proves (JD):** *"authentication / authorization."*

## Objective
Grant the minimum with well-scoped IAM, eliminate exported SA keys via workload
identity federation, elevate only just-in-time via PAM, and add real application
auth with proper token handling.

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Lab 00 done. gcloud CLI, `jq`, Python 3.

---

## Part A — Build: identities and a workload
1. A bucket `lab01-<project>-data` (public access prevention on).
2. A **service account** `app-sa`, given a **deliberately broad** role first:
   **`roles/editor` at the project** (a primitive role — the anti-pattern).
3. A **Workload Identity Federation** pool trusting GitHub OIDC (reuse
   `../../iam/terraform/gcp/main.tf`) — keyless CI.

## Part B — Attack / observe
1. Impersonate `app-sa` and show `roles/editor` lets it modify **any** resource
   in the project, far beyond the bucket:
   ```bash
   gcloud storage buckets list          # sees/edits everything
   gcloud projects get-iam-policy <p>
   ```
2. **Exported key risk:** create an SA key (if org policy allowed it) and note a
   long-lived JSON key is a credential that never expires — exactly what Lab 00's
   `disableServiceAccountKeyCreation` prevents.
3. Failures: **primitive role** (`editor`) + **project scope**. Run toolkit GCP
   IAM checks (`bash ../../cloud/gcp/*.sh`).

## Part C — Harden: least privilege + keyless + JIT
1. Replace `roles/editor` with the **minimum predefined role at bucket scope**:
   `roles/storage.objectViewer` on **that bucket only** (a resource-level binding).
2. If none fits, create a **custom role** with just the needed permissions — no
   `*` / primitive roles.
3. **Keyless workloads:** no SA keys anywhere — CI uses **Workload Identity
   Federation**; GKE uses **Workload Identity** (Lab 03). Org policy blocks key
   creation.
4. **PAM:** grant privileged roles **just-in-time** (request → approval →
   time-boxed) instead of standing grants.
5. **IAM Conditions:** add conditions (e.g., request time, resource tag) to
   bindings for context-bound access.

## Part D — Application auth with Identity Platform
1. Enable **Identity Platform**; configure sign-in with **MFA required**,
   password/passkey policy.
2. App uses OIDC (auth code + PKCE for SPA). Acquire a token and inspect:
   ```bash
   python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
   ```
   Confirm `iss`/`aud`, short `exp`, `alg` RS256 (not `none`), claims/roles.
3. Map a token claim → an IAM binding (via workforce/identity pool) so app users
   get least-privilege GCP access.

---

## Verify
```bash
gcloud projects get-iam-policy <p> --flatten="bindings[].members" \
  --filter="bindings.members:app-sa"      # scoped to the bucket only
gcloud storage ls gs://lab01-<project>-data     # works
gcloud storage ls                                # denied beyond scope
python3 ../../appsec/crypto/jwt_inspect.py <token>
```
Success = SA scoped to exactly its job, zero exported keys, PAM gates elevation,
Identity Platform issues short-lived correctly-scoped tokens.

## Cleanup
Delete the bucket, `app-sa`, the WIF pool, and the Identity Platform config.

## Portfolio artifact
- Before/after IAM (editor@project → objectViewer@bucket) with rationale.
- A note on **why exported SA keys are the #1 GCP identity risk** and how WIF
  removes them.
- Screenshot of a **PAM** JIT grant.

## Stretch goals
- ABAC via **IAM Conditions** on resource tags.
- Write the binding + custom role + WIF pool as Terraform; `checkov` it.
- Add a **VPC Service Controls** perimeter around the bucket (preview Lab 04).
