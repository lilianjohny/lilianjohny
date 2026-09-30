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
| `lib/`         | Shared helpers used across the toolkit                         |

## Requirements

- Python 3.9+
- Bash (for `.sh` scripts; Linux/macOS)
- Optional external tools the wrappers can use if present: `nmap`, `openssl`,
  `pip-audit`, `npm`.

Install Python deps:

```bash
pip install -r requirements.txt
```

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
