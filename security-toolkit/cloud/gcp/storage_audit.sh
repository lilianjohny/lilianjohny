#!/usr/bin/env bash
# Audit GCS buckets for public access and weak access controls.
# Read-only (uses your 'gcloud auth' session).
#
# Usage:
#   gcloud config set project <PROJECT_ID>
#   bash storage_audit.sh [PROJECT_ID]
set -uo pipefail

command -v gcloud >/dev/null 2>&1 || { echo "[FAIL] 'gcloud' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
[[ -z "$PROJECT" || "$PROJECT" == "(unset)" ]] && { echo "[FAIL] No project set."; exit 3; }
echo "[INFO] Auditing GCS buckets for project: $PROJECT"

buckets="$(gcloud storage buckets list --project "$PROJECT" --format='value(name)' 2>/dev/null)" \
  || { echo "[FAIL] Could not list buckets (need storage.buckets.list)."; exit 3; }
[[ -z "$buckets" ]] && { echo "[OK] No buckets found."; exit 0; }

while read -r b; do
  [[ -z "$b" ]] && continue
  desc="$(gcloud storage buckets describe "gs://$b" --format=json 2>/dev/null)" || {
    echo "[WARN] $b: cannot describe."; continue; }

  ubla="$(echo "$desc" | jq -r '.uniform_bucket_level_access.enabled // .iamConfiguration.uniformBucketLevelAccess.enabled // false')"
  ppa="$(echo "$desc" | jq -r '.iamConfiguration.publicAccessPrevention // .public_access_prevention // "unspecified"')"

  [[ "$ubla" != "true" ]] && echo "[WARN] $b: uniform bucket-level access disabled (ACLs in play)."
  [[ "$ppa" != "enforced" ]] && echo "[WARN] $b: public access prevention is '$ppa' (want 'enforced')."

  # Check IAM policy for public members
  pub="$(gcloud storage buckets get-iam-policy "gs://$b" --format=json 2>/dev/null \
    | jq -r '.bindings[]?.members[]? | select(test("^(allUsers|allAuthenticatedUsers)$"))' | sort -u)"
  if [[ -n "$pub" ]]; then
    echo "[FAIL] $b: bucket IAM grants PUBLIC access ($(echo "$pub" | tr '\n' ' '))."
  else
    [[ "$ubla" == "true" && "$ppa" == "enforced" ]] && echo "[OK]   $b: not public; UBLA + PAP enforced."
  fi
done <<< "$buckets"

echo "[INFO] GCS audit complete. Review [FAIL]/[WARN] lines above."
exit 0
