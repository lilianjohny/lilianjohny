# Lab 04 — Multi-Tenant Isolation (GCP)

**Skills practiced:** isolation models (silo/pool/bridge) · IAM Conditions tenant
boundaries · CMEK per tenant · VPC Service Controls · per-request scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use."*

## Objective
Model a pooled SaaS system and prove **Tenant A can never reach Tenant B's data**
at identity, data, key, and perimeter layers.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done. `jq`, Python 3.

---

## Part A — Build (pool)
```bash
BUCKET=lab04-$PROJECT
gcloud storage buckets create gs://$BUCKET --location=$REGION --uniform-bucket-level-access --public-access-prevention
echo "A" | gcloud storage cp - gs://$BUCKET/tenanta/secret.txt
echo "B" | gcloud storage cp - gs://$BUCKET/tenantb/secret.txt
for T in A B; do
  gcloud iam service-accounts create sa-tenant$T --display-name tenant$T
  SA=sa-tenant$T@$PROJECT.iam.gserviceaccount.com
  # Initially broad: storage.admin on the whole bucket
  gcloud storage buckets add-iam-policy-binding gs://$BUCKET --member="serviceAccount:$SA" --role="roles/storage.admin"
done
```

## Part B — Attack / observe
```bash
SAA=sa-tenantA@$PROJECT.iam.gserviceaccount.com
# As tenant A (impersonation), read tenant B — the bug:
gcloud storage cat gs://$BUCKET/tenantb/secret.txt --impersonate-service-account=$SAA   # ❌ succeeds
bash ../../cloud/prowler_scan.sh    # GCP — flags the broad grant
```

## Part C — Harden (isolation at every layer)
```bash
for T in A B; do
  low=$(echo $T | tr A-Z a-z)
  SA=sa-tenant$T@$PROJECT.iam.gserviceaccount.com
  gcloud storage buckets remove-iam-policy-binding gs://$BUCKET --member="serviceAccount:$SA" --role="roles/storage.admin"
  # Scope to its own prefix with an IAM Condition
  gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
    --member="serviceAccount:$SA" --role="roles/storage.objectViewer" \
    --condition="title=tenant$T-only,expression=resource.name.startsWith('projects/_/buckets/$BUCKET/objects/tenant$low/')"
done
# Per-tenant CMEK (a tenant can use only its own key)
gcloud kms keyrings create lab04 --location=$REGION 2>/dev/null || true
gcloud kms keys create tenantB --location=$REGION --keyring=lab04 --purpose=encryption
```
**Console:** add a **VPC Service Controls** perimeter around storage services so
stolen creds can't exfiltrate across the boundary (**Security → VPC Service
Controls → New perimeter**).

## Part D — Verify
```bash
SAA=sa-tenantA@$PROJECT.iam.gserviceaccount.com
gcloud storage ls gs://$BUCKET/tenanta/ --impersonate-service-account=$SAA         # works ✅
gcloud storage cat gs://$BUCKET/tenantb/secret.txt --impersonate-service-account=$SAA 2>&1 | grep -i denied  # denied ✅
bash ../../cloud/prowler_scan.sh    # GCP — re-scan clean on the broad-grant finding
```

## Cleanup
```bash
for T in A B; do gcloud iam service-accounts delete sa-tenant$T@$PROJECT.iam.gserviceaccount.com --quiet; done
gcloud kms keys versions destroy 1 --key=tenantB --keyring=lab04 --location=$REGION 2>/dev/null || true
gcloud storage rm --recursive gs://$BUCKET
```

## Portfolio artifact
- Tenant-isolation decision doc (silo/pool/bridge); where **VPC-SC** adds an
  exfil boundary IAM alone can't; before/after cross-tenant test output.

## Stretch goals
- Rebuild as **silo** (project-per-tenant under a folder).
- Per-tenant **log sink separation** (feeds Lab 06).
- Bridge two perimeters deliberately and show the controlled path.
