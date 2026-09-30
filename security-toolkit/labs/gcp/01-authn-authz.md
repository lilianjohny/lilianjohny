# Lab 01 — Authentication & Authorization (GCP)

**Skills practiced:** IAM roles & bindings · service accounts done right ·
Workload Identity Federation (keyless) · PAM (JIT) · IAM Recommender · custom
roles · app auth with Identity Platform.
**Proves (JD):** *"authentication / authorization."*

## Objective
Grant the minimum with well-scoped IAM, eliminate exported SA keys via workload
identity federation, elevate only JIT via PAM, and add real app auth.

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Lab 00 done (`gcloud auth login`, `PROJECT`, `REGION`). `jq`, Python 3.

---

## Part A — Build: identities and a workload
```bash
BUCKET=lab01-$PROJECT-data
gcloud storage buckets create gs://$BUCKET --location=$REGION --uniform-bucket-level-access --public-access-prevention
echo "ok" | gcloud storage cp - gs://$BUCKET/ok.txt
# A service account, given a DELIBERATELY BROAD primitive role first (anti-pattern)
gcloud iam service-accounts create app-sa --display-name "lab01 app"
SA=app-sa@$PROJECT.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role="roles/editor"
```

## Part B — Attack / observe
```bash
# Editor lets app-sa modify anything in the project, far beyond the bucket
gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
  --filter="bindings.members:$SA" --format="table(bindings.role)"
# Exported-key risk (org policy from Lab 00 should BLOCK this):
gcloud iam service-accounts keys create /tmp/key.json --iam-account=$SA 2>&1 | head -2
```
Failures: primitive role (`editor`) + project scope. Exported keys never expire.

## Part C — Harden: least privilege + keyless + JIT
```bash
# 1. Minimum predefined role at bucket scope
gcloud projects remove-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role="roles/editor"
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --member="serviceAccount:$SA" --role="roles/storage.objectViewer"

# 2. (If none fits) a custom role with just the needed permissions
gcloud iam roles create lab01BlobViewer --project="$PROJECT" \
  --title="lab01 blob viewer" --permissions=storage.objects.get,storage.objects.list

# 3. Keyless CI via Workload Identity Federation (reuse the module)
#    See ../../iam/terraform/gcp/main.tf — pool + provider pinned to your repo.

# 4. PAM (JIT) for privileged roles instead of standing grants
gcloud pam entitlements create lab01-admin-jit --location=global \
  --entitlement-file=/dev/stdin <<'EOF' 2>/dev/null || echo "Console: IAM & Admin → Privileged Access Manager → Create entitlement"
{"maxRequestDuration":"3600s","privilegedAccess":{"gcpIamAccess":{"roleBindings":[{"role":"roles/storage.admin"}]}},"requesterJustificationConfig":{"unstructured":{}}}
EOF
```
**Console:** IAM & Admin → **Roles → Create role** (custom); **Privileged Access
Manager → Create entitlement** (approval + time-box).

## Part D — Application auth with Identity Platform
**Console:** **Identity Platform → Enable** → add a provider (email/OIDC) → set
**MFA required** + password/passkey policy. App uses OIDC (auth code + PKCE).
```bash
python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
# Confirm iss/aud, short exp, alg=RS256 (not "none"), claims/roles.
```

---

## Verify
```bash
gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
  --filter="bindings.members:$SA" --format="table(bindings.role)"     # bucket-scoped only
gcloud storage ls gs://$BUCKET                                        # works (as app-sa)
python3 ../../appsec/crypto/jwt_inspect.py <token>
```

## Cleanup
```bash
gcloud iam roles delete lab01BlobViewer --project="$PROJECT" 2>/dev/null
gcloud iam service-accounts delete "$SA" --quiet
gcloud storage rm --recursive gs://$BUCKET
```

## Portfolio artifact
- Before/after IAM (editor@project → objectViewer@bucket) with rationale.
- A note on **why exported SA keys are the #1 GCP identity risk** and how WIF
  removes them.
- Screenshot of a **PAM** JIT grant.

## Stretch goals
- ABAC via **IAM Conditions** on resource tags.
- Write the binding + custom role + WIF pool as Terraform; `checkov`.
- Add a **VPC Service Controls** perimeter around the bucket (preview Lab 04).
