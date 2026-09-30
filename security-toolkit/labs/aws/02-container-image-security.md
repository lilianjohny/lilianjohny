# Lab 02 — Container Image Security

**Skills practiced:** Dockerfile hardening · ECR + scan-on-push · SBOM (Syft) ·
vuln scanning (Trivy/Grype) · image signing (cosign) · distroless bases ·
registry access control · CI gating.
**Proves (JD):** *"container security."*

## Objective
Find what's wrong with a deliberately vulnerable image, rebuild it
secure-by-design, and prove the supply chain: scanned, SBOM'd, signed,
least-privilege, in a locked registry — gated in CI.

## Est. time / cost
2–3 h · **~$0–1** (ECR storage pennies).

## Prerequisites
- Lab 00 done. Docker running (`docker info`).
- Tools: `trivy`, `grype`, `syft`, `cosign`:
  ```bash
  # Linux (adjust for your distro/arch); or see each tool's docs / brew on macOS
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin
  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh  | sudo sh -s -- -b /usr/local/bin
  go install github.com/sigstore/cosign/v2/cmd/cosign@latest 2>/dev/null || echo "install cosign per sigstore docs"
  bash ../../setup.sh --doctor      # confirm what you have
  ```

---

## Part A — Build: a deliberately weak image
```bash
mkdir -p /tmp/lab02 && cd /tmp/lab02
cat > server.js <<'EOF'
require('http').createServer((_,res)=>res.end('ok')).listen(3000);
EOF
cat > package.json <<'EOF'
{ "name":"lab02","version":"1.0.0","dependencies":{} }
EOF
cat > Dockerfile.weak <<'EOF'
FROM node:18
WORKDIR /app
COPY . .
RUN npm install
ENV API_KEY=supersecret123
USER root
CMD ["node","server.js"]
EOF
docker build -t lab02-app:weak -f Dockerfile.weak .

# Push to ECR (scan-on-push enabled)
aws ecr create-repository --repository-name lab02-app \
  --image-scanning-configuration scanOnPush=true --region "$AWS_REGION"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS \
  --password-stdin $ACCT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag lab02-app:weak $ACCT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/lab02-app:weak
docker push $ACCT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/lab02-app:weak
```

## Part B — Attack / observe
```bash
trivy image lab02-app:weak                         # OS + library CVEs (lots)
grype lab02-app:weak                               # second opinion
trivy image --scanners secret lab02-app:weak       # finds baked-in API_KEY
docker history --no-trunc lab02-app:weak | grep -i api_key   # secret in a layer
docker run --rm lab02-app:weak id                  # uid=0(root)  ❌
bash ../../dod/scripts/generate_sbom.sh lab02-app:weak
```
**GUI:** Console → **ECR → Repositories → lab02-app → Images** → click the digest
→ see **scan findings** (critical/high counts).

## Part C — Harden: secure-by-design image
```bash
cd /tmp/lab02
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
docker build -t lab02-app:secure -f Dockerfile.secure .

# Move the secret to Secrets Manager (read at runtime via the task/pod role)
aws secretsmanager create-secret --name lab02/api-key --secret-string "supersecret123"

# Lock the ECR repo: immutable tags + KMS + pull only for your workload role
aws ecr put-image-tag-mutability --repository-name lab02-app --image-tag-mutability IMMUTABLE
```
**GUI:** ECR → repo → **Edit** → **Tag immutability = Enabled**, **Scan on push =
Enabled**, **Encryption = KMS**. Add a **Permissions** policy limiting `ecr:Get*`/
`BatchGetImage` to your workload role ARN.

## Part D — Prove the supply chain
```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 lab02-app:secure   # gate passes (0)
syft lab02-app:secure -o spdx-json > sbom.spdx.json                   # keep SBOM
bash ../../dod/scripts/generate_sbom.sh lab02-app:secure
cosign generate-key-pair                                              # or keyless: cosign sign --yes <ref>
cosign sign --key cosign.key $ACCT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/lab02-app:secure 2>/dev/null || echo "push secure first, then sign by digest"
docker run --rm lab02-app:secure id                                   # non-root uid=1000 ✅
trivy image --scanners secret lab02-app:secure                       # clean ✅
```

## Part E — Gate it in CI (shift-left)
Reuse `../../cloud/cicd/pipeline_gate.sh` and the workflow patterns in
`../../.github/workflows/devsecops.yml`. Minimum gate:
```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 <image>   # fail build on High/Critical
test -s sbom.spdx.json                                       # require an SBOM
cosign verify --key cosign.pub <image>                       # require a signature
```

## Cleanup
```bash
aws ecr delete-repository --repository-name lab02-app --force --region "$AWS_REGION"
aws secretsmanager delete-secret --secret-id lab02/api-key --force-delete-without-recovery
docker image rm lab02-app:weak lab02-app:secure 2>/dev/null
```

## Portfolio artifact
- **Weak vs secure Dockerfile** + scan output before/after (CVE counts, secret
  gone, root → non-root).
- The **SBOM** and the **cosign verify** output.
- A "build → scan → SBOM → sign → admit" supply-chain diagram.

## Stretch goals
- Enforce **signature verification at deploy** (feeds Lab 03 admission control).
- Diff **distroless vs alpine vs slim** on size + CVE count.
- Add a **custom Semgrep rule** (`../../appsec/sast/rules/`) and catch it in CI.
