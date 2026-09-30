# Security Toolkit

A collection of **defensive and assessment** scripts for cybersecurity work.
Organized by discipline so you can reach for the right tool quickly.

> ⚠️ **Authorized use only.** Every script here is meant to be run against
> systems you **own** or are **explicitly contracted/authorized** to test,
> monitor, or defend. Scanning, probing, or collecting from systems without
> permission may be illegal. You are responsible for how you use these tools.

## Layout

| Directory      | Purpose                                                        |
|----------------|----------------------------------------------------------------|
| `recon/`       | Asset discovery & attack-surface mapping (your own estate)     |
| `vuln/`        | Vulnerability & misconfiguration checks                        |
| `hardening/`   | System hardening audits & CIS-style baseline checks            |
| `monitoring/`  | Log watching, file-integrity monitoring, detection helpers     |
| `incident/`    | Incident-response triage & IOC hunting                         |
| `crypto/`      | Hashing, password-strength, and crypto hygiene utilities       |
| `cloud/`       | DevSecOps: AWS/Azure/GCP posture audits, IaC scan, CI/CD gate  |
| `dod/`         | DoD DevSecOps software factory: mandatory control gates, SBOM/SWFT, cATO evidence, Sigstore signing |
| `appsec/`      | Application security: OpenAPI/API audit, CORS/cookie/JWT, SAST rules, DAST, ASVS, threat model |
| `devsecops/`   | Cross-cutting shift-left tools (e.g. secret scanning)          |
| `grc/`         | Governance, Risk & Compliance: risk register, multi-framework crosswalk, policy governance, GRC dashboard |
| `pentest/`     | Authorized, phase-ordered penetration testing (cloud + app), scope-gated |
| `soc/`         | SOC compliance (DoD CSSP + public sector): incident reporting, ConMon, M-21-31 logging, POA&M |
| `soc-reports/` | AICPA SOC 1/2/3 readiness: Trust Services Criteria, controls matrix, evidence & gap tracking |
| `vulnmgmt/`    | Vulnerability management program: normalize/enrich (KEV+EPSS)/dedupe/SLA-track/report |
| `lib/`         | Shared helpers used across the toolkit                         |

See `cloud/README.md` for the cloud DevSecOps suite (per-provider audits,
`iac/iac_scan.sh`, and `cicd/pipeline_gate.sh`).

## Getting started (how to run these)

The scripts live in this `security-toolkit/` directory. To get them onto your
machine and run them:

```bash
# 1. Get the code
git clone https://github.com/lilianjohny/lilianjohny.git
cd lilianjohny
git checkout security-toolkit          # this PR's branch (skip once it's merged)
cd security-toolkit

# 2. One-command setup: installs Python deps, makes scripts executable,
#    and prints a "doctor" of which optional CLIs you have.
bash setup.sh                # add --venv to use a virtualenv, --cloud for boto3

# 3. Run any script directly — Python or Bash:
python3 vuln/header_check.py https://example.com     # web security headers
bash    hardening/ssh_audit.sh                        # local sshd hardening
python3 grc/risk/risk_register.py grc/risk/risk_register.csv --appetite 9
```

That's it — most core scripts need only Python + `requests` + `PyYAML`
(installed by `setup.sh`). Anything that wraps an external tool (`nmap`,
`trivy`, `prowler`, `aws`/`az`/`gcloud`, …) uses it **only if installed** and
tells you what to install otherwise. Run `bash setup.sh --doctor` any time to
see what you have.

### Requirements
- **Python 3.9+** and **Bash** (Linux/macOS; WSL on Windows).
- Required Python: `requests`, `PyYAML` (`requirements.txt`); `boto3` for the
  AWS scripts (`requirements-cloud.txt`).
- Optional CLIs per area — see each folder's `README.md` / `COMMANDS.md`.

### How to read results
Every script uses the same **exit codes**: `0` clean · `1` warnings · `2`
findings · `3` setup/auth error — so they slot into CI, cron, or a pipeline.
Output is tagged `[OK]/[INFO]/[WARN]/[FAIL]`. Scripts that act on a target
(scanners, pentest, cloud) are **read-only by default** and only touch systems
you're authorized to test.

## Quick start

```bash
# HTTP security headers of a site you own
python vuln/header_check.py https://example.com

# TLS certificate expiry
python recon/tls_cert_check.py example.com

# Audit local sshd config
bash hardening/ssh_audit.sh

# Watch auth log for brute-force patterns
sudo python monitoring/log_watch.py /var/log/auth.log
```

## Conventions

- Scripts exit `0` on clean/pass, non-zero on findings or error, so they slot
  into CI and cron.
- Read-only by default. Anything that changes state says so and asks first.
- No hardcoded targets, credentials, or secrets.

## License

Use internally at your own discretion. Add a formal LICENSE file before
distributing.
