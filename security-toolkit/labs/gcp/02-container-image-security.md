# Lab 02 — Container Image Security (GCP)

**Skills practiced:** Dockerfile hardening · Artifact Registry + Artifact
Analysis · SBOM · Trivy/Grype · Binary Authorization + cosign · distroless ·
registry access control · CI gate.
**Proves (JD):** *"container security."*

## Objective
Expose a weak image's flaws, rebuild secure-by-design, and enforce **Binary
Authorization** so only verified images can deploy.

## Est. time / cost
2–3 h · **~$0–1** (Artifact Registry + Analysis pennies).

## Prerequisites
- Lab 00 done. Docker. `trivy`, `grype`, `syft`, `cosign` (see `../aws/02`).

---

## Part A — Build a weak image → Artifact Registry
```bash
gcloud artifacts repositories create lab02 --repository-format=docker --location=$REGION
gcloud auth configure-docker $REGION-docker.pkg.dev
mkdir -p /tmp/lab02gcp && cd /tmp/lab02gcp
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
REPO=$REGION-docker.pkg.dev/$PROJECT/lab02
docker build -t $REPO/app:weak -f Dockerfile.weak . && docker push $REPO/app:weak
```

## Part B — Attack / observe
```bash
trivy image $REPO/app:weak
trivy image --scanners secret $REPO/app:weak         # baked-in API_KEY
docker run --rm $REPO/app:weak id                    # uid=0 root ❌
gcloud artifacts docker images list $REPO --show-occurrences 2>/dev/null   # Artifact Analysis CVEs
bash ../../dod/scripts/generate_sbom.sh $REPO/app:weak
```
**Console:** **Artifact Registry → lab02 → app → digest → Vulnerabilities**.

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
docker build -t $REPO/app:secure -f Dockerfile.secure . && docker push $REPO/app:secure
# Secret → Secret Manager; registry least-privilege
gcloud secrets create lab02-api-key --replication-policy=automatic
echo -n supersecret123 | gcloud secrets versions add lab02-api-key --data-file=-
gcloud artifacts repositories add-iam-policy-binding lab02 --location=$REGION \
  --member="serviceAccount:app-sa@$PROJECT.iam.gserviceaccount.com" --role="roles/artifactregistry.reader"
```

## Part D — Prove the supply chain + Binary Authorization
```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 $REPO/app:secure
syft $REPO/app:secure -o spdx-json > sbom.spdx.json
cosign generate-key-pair && cosign sign --key cosign.key $REPO/app:secure && cosign verify --key cosign.pub $REPO/app:secure
docker run --rm $REPO/app:secure id                  # non-root ✅
# Binary Authorization: require an attestation before deploy
gcloud container binauthz policy export > /tmp/binauthz.yaml
# edit /tmp/binauthz.yaml → defaultAdmissionRule.evaluationMode: REQUIRE_ATTESTATION + your attestor
gcloud container binauthz policy import /tmp/binauthz.yaml
```
**Console:** **Security → Binary Authorization → Policy** → default rule =
*Require attestations* → add your attestor (enforced in Lab 03 on GKE).

## Part E — CI gate
Reuse `../../cloud/cicd/pipeline_gate.sh`; fail on HIGH/CRITICAL, missing SBOM, or
missing attestation.

## Cleanup
```bash
gcloud artifacts repositories delete lab02 --location=$REGION --quiet
gcloud secrets delete lab02-api-key --quiet
```

## Portfolio artifact
- Weak vs secure Dockerfile + scan deltas; SBOM + `cosign verify`; the **Binary
  Authorization policy** (the GCP differentiator — admission by attestation).

## Stretch goals
- Prove Binary Authorization **blocks** an unsigned image at deploy (Lab 03).
- Compare distroless vs alpine vs fat base.
- Add a custom Semgrep rule (`../../appsec/sast/rules/`) in CI.
