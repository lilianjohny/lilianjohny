# DoD Software Factory — Control Gates

Mandatory artifact-promotion control gates (per the DoD Enterprise DevSecOps
Reference Design, which states these gates **cannot be waived**), mapped to the
lifecycle phase, the implementing script, the enforcing policy, and the primary
NIST SP 800-53 Rev 5 / SP 800-218 (SSDF) controls each provides evidence for.

> The 800-53 mappings are indicative, for building your control-implementation
> narrative — they are not a substitute for your SSP or AO's determination.

| # | Gate | Lifecycle phase | Script | Hard/Soft | Primary 800-53 / SSDF |
|---|------|-----------------|--------|-----------|------------------------|
| 1 | **Secrets detection** | Develop | `gate_secrets.sh` | Hard | IA-5, SA-11, SC-28; SSDF PW.4 |
| 2 | **SAST** (static analysis) | Develop | `gate_sast.sh` | Hard | SA-11(1), RA-5, SI-2; SSDF PW.7/PW.8 |
| 3 | **SCA + license** | Build | `gate_sca.sh` | Hard | SA-11(2), RA-5, SR-3, SR-4; SSDF PW.4/RV.1 |
| 4 | **SBOM generation** (SWFT) | Build | `generate_sbom.sh` | Hard | SA-10, SR-3, SR-4, SR-11; SSDF PS.3/PW.4 |
| 5 | **Container vulnerability scan** | Test | `gate_container_scan.sh` | Hard | RA-5, SI-2, SI-3, CM-6; SSDF PW.7 |
| 6 | **STIG / compliance scan** | Test | `gate_stig.sh` | Hard | CM-6, CM-7, RA-5, SI-2 |
| 7 | **DAST** (dynamic analysis) | Test | `gate_dast.sh` | Hard* | SA-11(8), CA-8, RA-5; SSDF PW.8 |
| 8 | **Artifact signing + attestation** | Release/Deliver | `sign_and_attest.sh` | Hard | SA-10, SR-4(3)(4), CM-5, SI-7; SSDF PS.2 |
| 9 | **Policy gate** (present + passing) | Release/Deploy | `policy/opa/*.rego` | Hard | CM-3, CM-5, SA-10, SA-15 |

\* DAST is a hard gate for deployable services; it degrades to a documented
non-applicable (N/A) for libraries with no running endpoint. Record the N/A as
evidence — do not silently skip.

## Lifecycle → activities (Infinity loop)

| Phase | Security activities encoded / referenced here |
|-------|-----------------------------------------------|
| **Plan** | Threat modeling (manual; record as evidence), define control-gate thresholds |
| **Develop / Code** | Secrets detection, SAST, IaC scan (see `../cloud/iac`), pre-commit hooks |
| **Build** | SCA + license, **SBOM (SPDX + CycloneDX)**, reproducible build, unit/coverage |
| **Test** | Container vuln scan, **STIG/OpenSCAP**, DAST/IAST, quality gate |
| **Release / Deliver** | **cosign sign + SBOM attestation**, OPA policy gate, promote to hardened registry |
| **Deploy** | IaC compliance, admission control (Gatekeeper/Kyverno), config validation |
| **Operate** | Runtime security (Falco/NeuVector), least-privilege, network policy |
| **Monitor** | Continuous monitoring (ConMon), centralized logging/SIEM, vuln management → **cATO evidence** |

## Enforcement model

- **Hard gate** = pipeline fails and the artifact is **not promoted**. This is
  the default for gates 1–9 above.
- **Severity threshold** — vulnerability gates block on `CRITICAL,HIGH` by
  default (`--severity`); tune to your AO-approved risk posture, never below it.
- **Evidence** — every gate writes a machine-readable result (SARIF/JSON/SBOM)
  into the evidence bundle for cATO continuous monitoring and SWFT submission.
- **Policy evaluation** — the OPA policies live in `dod.*` packages; evaluate
  with `conftest test <input.json> --policy dod/policy/opa --all-namespaces`.
- **No waivers in-pipeline** — a finding is remediated or carried as an
  AO-approved POA&M reference recorded in evidence; it is never silently
  skipped, disabled, or quarantined to force a green run.

## cATO continuous-monitoring pillars (what the evidence supports)

1. **Continuous monitoring** of RMF/CSRMC controls — the gate evidence bundle.
2. **Active cyber defense** — runtime detection references (Operate/Monitor).
3. **DevSecOps Reference Design adoption** — this software factory itself.

## SWFT SBOM expectations (2026)

- **Machine-readable** (SPDX and/or CycloneDX JSON) — not a static PDF.
- **Regenerated on every code change** (wired into the build gate here).
- Covers **production and sandbox** builds.
- Suitable for **third-party attestation** and submission via the SWFT path.
