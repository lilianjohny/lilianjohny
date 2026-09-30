# Lab 02 — Container Image Security

**Skills practiced:** Dockerfile hardening · ECR + scan-on-push · SBOM (Syft) ·
vuln scanning (Trivy/Grype) · image signing & verification (cosign) · minimal/
distroless base images · registry access control · shift-left CI gating.
**Proves (JD):** *"container security."*

## Objective
Take a deliberately vulnerable container image, find what's wrong with it the way
an attacker/scanner would, then rebuild it secure-by-design and **prove** the
supply chain: scanned, SBOM'd, signed, least-privilege, stored in a locked-down
registry — and gate all of that in CI.

## Est. time / cost
2–3 h · **~$0–1** (ECR storage pennies; delete images after).

## Prerequisites
- Docker (or `nerdctl`/`podman`), AWS CLI v2.
- `trivy`, `grype`, `syft`, `cosign` — install via `../../security-toolkit/setup.sh`
  helpers or each tool's docs. Check with `bash ../../setup.sh --doctor`.

---

## Part A — Build: a deliberately weak image
Create `Dockerfile.weak`:
```dockerfile
FROM node:18                      # full, fat, outdated base
WORKDIR /app
COPY . .
RUN npm install                   # unpinned deps
ENV API_KEY=supersecret123        # secret baked into the image (!)
USER root                         # runs as root (!)
CMD ["node", "server.js"]
```
Build and push to ECR:
```bash
aws ecr create-repository --repository-name lab02-app --image-scanning-configuration scanOnPush=true
docker build -t lab02-app:weak -f Dockerfile.weak .
# tag + push to your ECR repo...
```

## Part B — Attack / observe: see the weaknesses
1. **Vuln scan:**
   ```bash
   trivy image lab02-app:weak            # OS + library CVEs
   grype lab02-app:weak                  # second opinion
   ```
2. **Secret in the image** (the baked-in `API_KEY`):
   ```bash
   trivy image --scanners secret lab02-app:weak
   docker history --no-trunc lab02-app:weak | grep -i api_key   # it's in a layer
   ```
3. **Runs as root:** `docker run --rm lab02-app:weak id` → `uid=0(root)`.
4. **ECR scan-on-push** findings in the console — note critical/high counts.
5. Confirm the toolkit sees it too:
   ```bash
   bash ../../appsec/sast/semgrep_scan.sh .        # app-code issues
   bash ../../dod/scripts/generate_sbom.sh lab02-app:weak   # SBOM of the mess
   ```

## Part C — Harden: secure-by-design image
Create `Dockerfile.secure`:
```dockerfile
# Pin by digest; use a minimal/distroless runtime
FROM node:18.20.4-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev             # pinned, reproducible, no dev deps
COPY . .

FROM gcr.io/distroless/nodejs18-debian12
WORKDIR /app
COPY --from=build /app /app
USER 1000                         # non-root
# NO secrets in the image — inject at runtime (Secrets Manager / env from task role)
CMD ["server.js"]
```
Also:
- Add a **`.dockerignore`** (drop `.git`, `.env`, node_modules).
- Add a **HEALTHCHECK** (see `../../security-toolkit/Dockerfile` for the pattern).
- Move the secret to **AWS Secrets Manager**, read via the task/pod role.
- Lock the **ECR repo**: immutable tags, scan-on-push, KMS encryption, a
  repository policy limiting pull to your workload roles only.

## Part D — Prove the supply chain
```bash
# 1. Scan is clean (or only accepted, documented findings)
trivy image --severity HIGH,CRITICAL --exit-code 1 lab02-app:secure

# 2. Generate + keep an SBOM
syft lab02-app:secure -o spdx-json > sbom.spdx.json
#    (or the toolkit wrapper)
bash ../../dod/scripts/generate_sbom.sh lab02-app:secure

# 3. Sign the image and verify (keyless via OIDC, or a cosign key)
cosign sign lab02-app:secure
cosign verify lab02-app:secure ...

# 4. Confirm non-root + no secret
docker run --rm lab02-app:secure id           # non-root uid
trivy image --scanners secret lab02-app:secure # clean
```
Success = HIGH/CRITICAL gate passes, SBOM produced, image signed & verifiable,
runs non-root, zero baked-in secrets, ECR locked down.

## Part E — Gate it in CI (shift-left)
Wire the same checks into a pipeline so a bad image can't ship:
- Reuse `../../cloud/cicd/pipeline_gate.sh` and the patterns in
  `../../.github/workflows/devsecops.yml` / `../../dod/pipeline/`.
- Fail the build on HIGH/CRITICAL, missing SBOM, or unsigned image.

## Cleanup
```bash
aws ecr delete-repository --repository-name lab02-app --force
docker image rm lab02-app:weak lab02-app:secure
```

## Portfolio artifact
- **Weak vs secure Dockerfile** side by side, with the scan output before/after
  (CVE counts, secret finding gone, root → non-root).
- The **SBOM** and the **cosign verify** output.
- A short "container supply chain" diagram: build → scan → SBOM → sign → admit.

## Stretch goals
- Add **image-signature enforcement** at deploy (feeds Lab 03: only signed images
  admitted to the cluster).
- Diff **distroless vs alpine vs slim** on image size and CVE count; write it up.
- Add a **custom Semgrep rule** (`../../appsec/sast/rules/`) for a bad pattern in
  your app and catch it in CI.
