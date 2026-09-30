#!/usr/bin/env bash
# Audit GCP project IAM for primitive roles, public bindings, and SA keys.
# Read-only (uses your 'gcloud auth' session).
#
# Usage:
#   gcloud auth login && gcloud config set project <PROJECT_ID>
#   bash iam_audit.sh [PROJECT_ID]
set -uo pipefail

command -v gcloud >/dev/null 2>&1 || { echo "[FAIL] 'gcloud' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
[[ -z "$PROJECT" || "$PROJECT" == "(unset)" ]] && { echo "[FAIL] No project set. Pass one or run 'gcloud config set project'."; exit 3; }
echo "[INFO] Auditing IAM for project: $PROJECT"

policy="$(gcloud projects get-iam-policy "$PROJECT" --format=json 2>/dev/null)" \
  || { echo "[FAIL] Could not read IAM policy (auth/permissions?)."; exit 3; }

# 1. Primitive roles (owner/editor/viewer) — prefer predefined/custom least-priv.
echo "$policy" | jq -r '.bindings[] | select(.role|test("^roles/(owner|editor|viewer)$")) | "\(.role) \(.members|length) member(s)"' \
  | while read -r line; do echo "[WARN] Primitive role in use: $line"; done

# 2. Public bindings (allUsers / allAuthenticatedUsers)
public="$(echo "$policy" | jq -r '.bindings[] | select(.members[]? | test("^(allUsers|allAuthenticatedUsers)$")) | .role' | sort -u)"
if [[ -n "$public" ]]; then
  echo "[FAIL] IAM bindings granted to allUsers/allAuthenticatedUsers on roles:"
  echo "$public" | sed 's/^/  /'
else
  echo "[OK]   No public (allUsers/allAuthenticatedUsers) IAM bindings."
fi

# 3. User-managed service-account keys (rotation/leak risk)
echo "[INFO] Checking service-account user-managed keys…"
sa_list="$(gcloud iam service-accounts list --project "$PROJECT" --format='value(email)' 2>/dev/null || true)"
if [[ -n "$sa_list" ]]; then
  while read -r sa; do
    [[ -z "$sa" ]] && continue
    keys="$(gcloud iam service-accounts keys list --iam-account "$sa" \
      --managed-by=user --format='value(name)' 2>/dev/null | wc -l | tr -d ' ')"
    [[ "$keys" -gt 0 ]] && echo "[WARN] SA $sa has $keys user-managed key(s) — prefer workload identity."
  done <<< "$sa_list"
else
  echo "[INFO] No service accounts (or no permission to list)."
fi

echo "[OK] GCP IAM audit complete. Review [FAIL]/[WARN] lines above."
exit 0
