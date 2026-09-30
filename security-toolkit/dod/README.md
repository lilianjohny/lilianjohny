# DoD DevSecOps Software Factory

A production-grade implementation of the **DoD Enterprise DevSecOps** control
gates and the enforcement mechanisms in force as of 2026 — the mandatory
software-factory gates, **SWFT** machine-readable SBOMs, **cATO** continuous
monitoring evidence, and Sigstore artifact signing/attestation.

> ⚠️ **Authoritative sources.** This encodes the *publicly documented* DoD
> DevSecOps model. The binding requirements live in DoD/DISA publications that
> version frequently and are partly CUI/CAC-gated. **Validate against the
> current authoritative documents and your Authorizing Official (AO) before
> relying on this for an ATO.** See "References" below.

## What the DoD mandates (2026 snapshot)

| Framework / program | What it is | Status as of 2026 |
|---------------------|------------|-------------------|
| **DoD Enterprise DevSecOps Fundamentals v2.5** (Jan 2025) | The reference model: Software Factory, Infinity-loop lifecycle, control gates | Current |
| **DevSecOps Activities & Tools Guidebook v2.5** (Apr 2025) | Per-phase activities and the tool categories that satisfy each gate | Current |
| **Reference Designs** (CNCF Kubernetes, cloud-managed) | Concrete platform blueprints (Platform One / Big Bang lineage) | Current |
| **Software Fast Track (SWFT)** | Paved-road acquisition path; **machine-readable SBOMs that update every code change**, third-party attestation, from prod + sandbox | Requirement (piloted May 2025 → in force) |
| **cATO** (Continuous Authorization to Operate) | Replaces point-in-time ATO via continuous monitoring, active cyber defense, and RD adoption | Enforced |
| **CSRMC** (Cybersecurity Risk Management Construct) | Successor to the Risk Management Framework (RMF), announced Sep 2025 | Transitioning — **confirm applicability with your AO** |

Key rule the RD is explicit about: **artifact-promotion control gates are
mandatory and cannot be waived.** This directory encodes them as hard gates.

## Mandatory control gates (encoded here)

See `control-gates.md` for the full gate → tool → NIST SP 800-53 mapping. In
short, every artifact must pass, in the pipeline, before promotion:

1. **Secrets detection** — no credentials in source/history
2. **SAST** — static application security testing
3. **SCA + license** — dependency vulnerabilities and license policy
4. **SBOM generation** — SPDX + CycloneDX, per SWFT (machine-readable, per build)
5. **Container vulnerability scan** — image CVEs against severity policy
6. **STIG / compliance scan** — DISA STIG baseline (OpenSCAP)
7. **DAST** — dynamic testing of the running app
8. **Artifact signing + attestation** — Sigstore/cosign signature + SBOM attestation
9. **Policy gate** — OPA/conftest enforces the above are present and passing

## Layout

```
dod/
├── control-gates.md              Gate → tool → 800-53 control mapping
├── pipeline/
│   └── dod-software-factory.yml  GitHub Actions software factory (all gates)
├── scripts/
│   ├── run_all_gates.sh          Orchestrator (local/CI), emits cATO evidence
│   ├── gate_secrets.sh  gate_sast.sh  gate_sca.sh  gate_container_scan.sh
│   ├── gate_stig.sh     gate_dast.sh
│   ├── generate_sbom.sh          Syft → SPDX + CycloneDX (SWFT-style)
│   └── sign_and_attest.sh        cosign keyless signing + SBOM attestation
├── policy/opa/                   Rego policies enforced by conftest
└── evidence/
    └── collect_cato_evidence.sh  Aggregate gate results into a ConMon bundle
```

## Toolchain

Open-source, runnable defaults that map to the DoD tool categories (swap in
your program's licensed equivalents — Fortify, SonarQube, Prisma/Twistlock,
NeuVector, Anchore Enterprise — where mandated):

| Gate | Default (OSS) | Common DoD equivalent |
|------|---------------|-----------------------|
| Secrets | gitleaks | — |
| SAST | Semgrep | Fortify SCA, SonarQube |
| SCA/SBOM | Grype + Syft (Anchore OSS) | Anchore Enterprise |
| Container scan | Grype / Trivy | Prisma Cloud, NeuVector |
| STIG | OpenSCAP (`oscap`) | Evaluate-STIG, ACAS/Tenable |
| DAST | OWASP ZAP | — |
| Signing | cosign (Sigstore) | — |
| Policy | OPA / conftest | Gatekeeper, Kyverno (admission) |
| Hardened base | **Iron Bank** `registry1.dso.mil` | (mandated) |

## Quick start

```bash
# Run every mandatory gate locally; writes evidence to ./cato-evidence/
bash dod/scripts/run_all_gates.sh --path . --image registry1.dso.mil/ironbank/opensource/nginx/nginx:1.27

# Generate SWFT-style SBOMs only
bash dod/scripts/generate_sbom.sh --path . --out sbom/

# Sign + attest an image (keyless, Sigstore/Fulcio)
bash dod/scripts/sign_and_attest.sh myregistry/app@sha256:... --sbom sbom/app.cdx.json
```

Iron Bank pulls and STIG SCAP content require DoD access (CAC / `registry1`
robot account, DISA STIG downloads). Scripts detect missing access and tell
you what to provide rather than failing silently.

## References (validate the current versions)

- DoD Cyber Exchange — DevSecOps Reference Design v2 (CAC/public sections)
- DoD CIO Library — DevSecOps Fundamentals v2.5, Activities & Tools Guidebook v2.5
- DoD CIO — Software Fast Track (SWFT) implementation guidance (2025)
- DoD cATO guidance; NIST SP 800-53 Rev 5, SP 800-218 (SSDF), SP 800-37
- Platform One / Big Bang; Iron Bank (`ironbank.dso.mil`)
