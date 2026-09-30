# Lab 02 — Container Image Security (GCP)

**Skills practiced:** Dockerfile hardening · Artifact Registry + **Artifact
Analysis** (vuln scanning) · SBOM (Syft) · Trivy/Grype · **Binary Authorization**
+ cosign attestations · distroless bases · registry access control · CI gating.
**Proves (JD):** *"container security."*

## Objective
Take a weak image, expose its flaws, rebuild secure-by-design, and prove the
supply chain: scanned, SBOM'd, signed/attested, non-root, secret-free, stored in
a locked-down Artifact Registry — and enforce **Binary Authorization** so only
verified images can deploy.

## Est. time / cost
2–3 h · **~$0–1** (Artifact Registry storage + Artifact Analysis pennies).

## Prerequisites
- Docker, gcloud CLI. `trivy`, `grype`, `syft`, `cosign`
  (`bash ../../setup.sh --doctor`).

---

## Part A — Build: a weak image → Artifact Registry
Use the `Dockerfile.weak` pattern from `../aws/02-container-image-security.md`
(fat base, unpinned deps, baked-in secret, runs as root).
```bash
gcloud artifacts repositories create lab02 --repository-format=docker --location=<region>
gcloud auth configure-docker <region>-docker.pkg.dev
docker build -t <region>-docker.pkg.dev/<p>/lab02/app:weak . && docker push ...
```

## Part B — Attack / observe
1. **Vuln scan:** `trivy image <img>` + `grype <img>`; also **Artifact Analysis**
   automatic scan results (`gcloud artifacts vulnerabilities list ...`).
2. **Secret in image:** `trivy image --scanners secret <img>`; `docker history`.
3. **Runs as root:** `docker run --rm <img> id` → uid 0.
4. Toolkit: `bash ../../dod/scripts/generate_sbom.sh <img>`,
   `bash ../../appsec/sast/semgrep_scan.sh .`.

## Part C — Harden
Rebuild `Dockerfile.secure` (multi-stage, pinned, **distroless**, `USER 1000`,
`.dockerignore`, HEALTHCHECK). GCP-specifics:
- Secret → **Secret Manager**, read via the workload's identity (WIF/GKE WI).
- Lock **Artifact Registry**: least-privilege `roles/artifactregistry.reader`
  scoped to your workload SA; CMEK encryption; immutable tags where possible.

## Part D — Prove the supply chain + Binary Authorization
```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 <img-secure>
syft <img-secure> -o spdx-json > sbom.spdx.json
cosign sign <img-secure> && cosign verify <img-secure> ...
docker run --rm <img-secure> id            # non-root
```
Then **Binary Authorization**:
- Create an **attestor**; require a cosign/attestation before deploy.
- Set a policy: **deny** images without the attestation (enforced in Lab 03 on GKE).
```bash
gcloud container binauthz attestors list
gcloud container binauthz policy import policy.yaml
```
Success = HIGH/CRITICAL gate passes, SBOM produced, image signed + attested,
non-root, no baked secret, registry locked, Binary Authorization policy set.

## Part E — Gate in CI
Reuse `../../cloud/cicd/pipeline_gate.sh` and `../../.github/workflows/devsecops.yml`;
fail on HIGH/CRITICAL, missing SBOM, or missing attestation.

## Cleanup
```bash
gcloud artifacts repositories delete lab02 --location=<region> -q
```

## Portfolio artifact
- Weak vs secure Dockerfile + scan deltas.
- SBOM + `cosign verify` + the **Binary Authorization policy** (the GCP
  differentiator — admission based on attestation).

## Stretch goals
- Prove Binary Authorization **blocks** an unsigned image at deploy (Lab 03).
- Compare distroless vs alpine vs fat base (size + CVEs).
- Add a custom Semgrep rule (`../../appsec/sast/rules/`) and catch it in CI.
