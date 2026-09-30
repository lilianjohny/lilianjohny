# Lab 02 — Container Image Security (Azure)

**Skills practiced:** Dockerfile hardening · ACR + Defender for Containers · SBOM ·
Trivy/Grype · image signing (cosign) · distroless · registry access control · CI gate.
**Proves (JD):** *"container security."*

## Objective
Expose a weak image's flaws, rebuild secure-by-design, and prove the supply chain
in a locked-down ACR — gated in CI.

## Est. time / cost
2–3 h · **~$0–1** (ACR Basic).

## Prerequisites
- Lab 00 done. Docker. `trivy`, `grype`, `syft`, `cosign` (see `../aws/02` for
  install one-liners; `bash ../../setup.sh --doctor`).

---

## Part A — Build a weak image → ACR
```bash
az group create -n rg-lab02 -l "$LOCATION"
ACR=lab02acr$RANDOM
az acr create -g rg-lab02 -n "$ACR" --sku Basic --admin-enabled false
mkdir -p /tmp/lab02az && cd /tmp/lab02az
cat > server.js <<'EOF'
require('http').createServer((_,r)=>r.end('ok')).listen(3000);
EOF
printf '{"name":"l","version":"1.0.0","dependencies":{}}' > package.json
cat > Dockerfile.weak <<'EOF'
FROM node:18
WORKDIR /app
COPY . .
RUN npm install
ENV API_KEY=supersecret123
USER root
CMD ["node","server.js"]
EOF
az acr build -r "$ACR" -t lab02-app:weak -f Dockerfile.weak .   # builds in ACR
```

## Part B — Attack / observe
```bash
az acr login -n "$ACR"
IMG=$ACR.azurecr.io/lab02-app:weak
trivy image "$IMG"                       # CVEs
trivy image --scanners secret "$IMG"     # baked-in API_KEY
docker pull "$IMG" && docker run --rm "$IMG" id   # uid=0 root ❌
bash ../../dod/scripts/generate_sbom.sh "$IMG"
```
**Portal — Defender for Containers:** Defender for Cloud → **Environment
settings → your sub → Defender plans → Containers = On**; ACR image scan findings
appear under **Recommendations**.

## Part C — Harden
```bash
cat > .dockerignore <<'EOF'
.git
.env
node_modules
EOF
cat > Dockerfile.secure <<'EOF'
FROM node:18.20.4-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev || npm install --omit=dev
COPY . .
FROM gcr.io/distroless/nodejs18-debian12
WORKDIR /app
COPY --from=build /app /app
USER 1000
CMD ["server.js"]
EOF
az acr build -r "$ACR" -t lab02-app:secure -f Dockerfile.secure .
# Secret → Key Vault (read via managed identity)
az keyvault create -n kv-lab02$RANDOM -g rg-lab02 -l "$LOCATION"
# Lock ACR: admin off (already), AAD-only pulls, immutable/retention
az acr config retention update -r "$ACR" --status enabled --days 7 --type UntaggedManifests 2>/dev/null || true
```
**Portal:** ACR → **Access keys** → confirm **Admin user = Disabled**; assign
**AcrPull** only to your workload's managed identity; enable **Private endpoint**.

## Part D — Prove the supply chain
```bash
SEC=$ACR.azurecr.io/lab02-app:secure
trivy image --severity HIGH,CRITICAL --exit-code 1 "$SEC"   # gate passes
syft "$SEC" -o spdx-json > sbom.spdx.json
cosign generate-key-pair
cosign sign --key cosign.key "$SEC" && cosign verify --key cosign.pub "$SEC"
docker run --rm "$SEC" id                                   # non-root ✅
trivy image --scanners secret "$SEC"                        # clean ✅
```

## Part E — CI gate
Reuse `../../cloud/cicd/pipeline_gate.sh`; fail on HIGH/CRITICAL, missing SBOM, or
unsigned image. (Feeds Lab 03: only signed images admitted to AKS via Ratify.)

## Cleanup
```bash
az group delete -n rg-lab02 --yes --no-wait
docker image rm "$IMG" "$SEC" 2>/dev/null
```

## Portfolio artifact
- Weak vs secure Dockerfile + scan deltas; SBOM + `cosign verify`; ACR hardening
  (admin disabled, AAD-only, private endpoint).

## Stretch goals
- Enforce signature/attestation at deploy with **Ratify + Gatekeeper** on AKS.
- Compare distroless vs alpine vs fat base (size + CVEs).
- Add a custom Semgrep rule (`../../appsec/sast/rules/`) in CI.
