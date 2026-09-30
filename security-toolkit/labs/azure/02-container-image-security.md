# Lab 02 — Container Image Security (Azure)

**Skills practiced:** Dockerfile hardening · ACR + Defender for Containers image
scanning · SBOM (Syft) · Trivy/Grype · image signing (cosign / ACR content
trust) · minimal/distroless bases · registry access control (managed-identity
pull) · CI gating.
**Proves (JD):** *"container security."*

## Objective
Take a weak image, expose its flaws with scanners, rebuild it secure-by-design,
and prove the supply chain: scanned, SBOM'd, signed, non-root, secret-free,
stored in a locked-down ACR — gated in CI.

## Est. time / cost
2–3 h · **~$0–1** (ACR Basic + a little storage; delete after).

## Prerequisites
- Docker, Azure CLI. `trivy`, `grype`, `syft`, `cosign`
  (`bash ../../setup.sh --doctor`).

---

## Part A — Build: a weak image → ACR
Use the same `Dockerfile.weak` pattern as `../aws/02-container-image-security.md`
(fat base, unpinned deps, baked-in secret, runs as root). Then:
```bash
az acr create -g rg-lab02 -n lab02acr<unique> --sku Basic
az acr build -r lab02acr<unique> -t lab02-app:weak .   # or docker push
```

## Part B — Attack / observe
1. **Vuln scan:** `trivy image <acr>/lab02-app:weak` and `grype ...`.
2. **Secret in image:** `trivy image --scanners secret ...`;
   `docker history --no-trunc ... | grep -i secret`.
3. **Runs as root:** `docker run --rm <img> id` → uid 0.
4. **Defender for Containers:** enable the plan; view ACR **image scan** findings
   in Defender for Cloud.
5. Toolkit: `bash ../../dod/scripts/generate_sbom.sh <img>`,
   `bash ../../appsec/sast/semgrep_scan.sh .`.

## Part C — Harden
Rebuild `Dockerfile.secure` (multi-stage, pinned, **distroless**, `USER 1000`,
`.dockerignore`, HEALTHCHECK) — same as the AWS lab. Then Azure-specifics:
- Secret → **Azure Key Vault**, read via the workload's **managed identity**.
- Lock **ACR**: disable admin user, **managed-identity/AAD auth only**, private
  endpoint, retention/quarantine, and (optional) **content trust** / cosign.
- Restrict pull to your workload's identity via **AcrPull** role, scoped.

## Part D — Prove the supply chain
```bash
trivy image --severity HIGH,CRITICAL --exit-code 1 <acr>/lab02-app:secure
syft <acr>/lab02-app:secure -o spdx-json > sbom.spdx.json
cosign sign <acr>/lab02-app:secure && cosign verify <acr>/lab02-app:secure ...
docker run --rm <acr>/lab02-app:secure id            # non-root
trivy image --scanners secret <acr>/lab02-app:secure # clean
```
Success = HIGH/CRITICAL gate passes, SBOM produced, image signed & verifiable,
non-root, no baked secret, ACR AAD-only + private.

## Part E — Gate in CI
Reuse `../../cloud/cicd/pipeline_gate.sh` and the patterns in
`../../.github/workflows/devsecops.yml`; fail on HIGH/CRITICAL, missing SBOM, or
unsigned image. (Feeds Lab 03: only signed images admitted to AKS.)

## Cleanup
```bash
az acr delete -n lab02acr<unique> -g rg-lab02 -y
az group delete -n rg-lab02 -y
```

## Portfolio artifact
- Weak vs secure Dockerfile + scan deltas (CVEs, secret gone, root→non-root).
- SBOM + `cosign verify` output.
- ACR hardening note (admin disabled, AAD-only, private endpoint).

## Stretch goals
- Enforce signature/attestation at deploy with **Ratify + Gatekeeper** on AKS.
- Compare **distroless vs alpine vs the fat base** on size + CVEs.
- Add a **custom Semgrep rule** (`../../appsec/sast/rules/`) and catch it in CI.
