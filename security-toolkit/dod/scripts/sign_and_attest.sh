#!/usr/bin/env bash
# Control gate 8: Artifact signing + SBOM attestation (hard gate).
# Uses Sigstore cosign to sign a container image and attach an SBOM attestation.
# Supports keyless (Fulcio/OIDC, recommended in CI) or key-based signing.
#
# Usage:
#   # Keyless (CI with OIDC token), attach CycloneDX SBOM attestation:
#   sign_and_attest.sh <image@sha256:...> --sbom sbom/app.cdx.json
#   # Key-based:
#   sign_and_attest.sh <image@sha256:...> --key cosign.key --sbom sbom/app.cdx.json
#   # Verify an already-signed image:
#   sign_and_attest.sh <image@sha256:...> --verify --identity <oidc-id> --issuer <url>
set -uo pipefail
IMAGE="${1:-}"; shift || true
KEY=""; SBOM=""; VERIFY=0; IDENTITY=""; ISSUER=""
while [[ $# -gt 0 ]]; do case "$1" in
  --key) KEY="$2"; shift 2 ;;
  --sbom) SBOM="$2"; shift 2 ;;
  --verify) VERIFY=1; shift ;;
  --identity) IDENTITY="$2"; shift 2 ;;
  --issuer) ISSUER="$2"; shift 2 ;;
  *) shift ;; esac; done
[[ -z "$IMAGE" ]] && { echo "[FAIL] Provide an image reference (prefer image@sha256:digest)."; exit 3; }

command -v cosign >/dev/null 2>&1 || {
  echo "[FAIL] cosign not installed. Install: https://docs.sigstore.dev/cosign/installation/"
  exit 3; }

case "$IMAGE" in
  *@sha256:*) : ;;
  *) echo "[WARN] Sign by immutable digest (image@sha256:...) — tags are mutable." ;;
esac

if [[ $VERIFY -eq 1 ]]; then
  echo "[INFO] Verifying signature on $IMAGE"
  if [[ -n "$KEY" ]]; then
    cosign verify --key "${KEY%.key}.pub" "$IMAGE"; rc=$?
  else
    [[ -z "$IDENTITY" || -z "$ISSUER" ]] && { echo "[FAIL] Keyless verify needs --identity and --issuer."; exit 3; }
    cosign verify --certificate-identity "$IDENTITY" --certificate-oidc-issuer "$ISSUER" "$IMAGE"; rc=$?
  fi
  [[ $rc -eq 0 ]] && { echo "[OK] Signature verified."; exit 0; } || { echo "[FAIL] Verification failed."; exit 2; }
fi

# --- Sign ---
echo "[INFO] Signing $IMAGE"
if [[ -n "$KEY" ]]; then
  cosign sign --key "$KEY" --yes "$IMAGE" || { echo "[FAIL] Signing failed."; exit 2; }
else
  # Keyless: requires an OIDC token (CI: id-token: write). Records to Rekor.
  COSIGN_EXPERIMENTAL=1 cosign sign --yes "$IMAGE" || { echo "[FAIL] Keyless signing failed (OIDC token present?)."; exit 2; }
fi

# --- Attest SBOM ---
if [[ -n "$SBOM" && -f "$SBOM" ]]; then
  echo "[INFO] Attaching CycloneDX SBOM attestation"
  if [[ -n "$KEY" ]]; then
    cosign attest --key "$KEY" --predicate "$SBOM" --type cyclonedx --yes "$IMAGE" \
      || { echo "[FAIL] SBOM attestation failed."; exit 2; }
  else
    COSIGN_EXPERIMENTAL=1 cosign attest --predicate "$SBOM" --type cyclonedx --yes "$IMAGE" \
      || { echo "[FAIL] SBOM attestation failed."; exit 2; }
  fi
else
  echo "[WARN] No --sbom provided; signed image but did not attach an SBOM attestation."
fi

echo "[OK] Gate 8 (signing + attestation): PASS"
exit 0
