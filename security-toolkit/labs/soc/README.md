# SOC & Incident Response — Hands-On Lab Track

Blue-team operations: detect, triage, investigate, coordinate, and resolve
security incidents, and harden the enterprise identity/endpoint/network surface.
Built for SOC / cybersecurity-engineer roles (IR lifecycle, alert triage, M365/
Entra, firewall/EDR, ticketing).

> ⚠️ **Own/sandbox systems only.** Simulate incidents against resources you
> control (a lab tenant, test VMs, sample exports). Never investigate or act on
> systems you're not authorized for.

## Labs
| # | Lab | Focus | Tools used |
|---|-----|-------|-----------|
| 01 | [Incident response lifecycle](01-incident-response.md) | NIST 800-61 end to end | `../../soc/ir/triage.py`, `../../soc/incident/incident_report.py` |
| 02 | [SOC alert triage](02-soc-alert-triage.md) | EDR/DNS/firewall alert → prioritized action | `../../soc/ir/triage.py`, `../../soc/network/firewall_rule_audit.py` |
| 03 | [M365 / Entra hardening](03-m365-entra-hardening.md) | tenant security posture | `../../soc/m365/graph_security_audit.py` |

> **Each lab is copy-paste runnable:** it drives the toolkit's own tools with
> real sample inputs (`soc/ir/triage.py`, `soc/network/firewall_rule_audit.py`,
> `soc/m365/graph_security_audit.py`, `soc/incident/incident_report.py`), plus
> Entra/M365 portal steps for the tenant hardening.

## How it fits the toolkit
- **Detection sources** → `../../cloud/detection/`, `../aws|azure|gcp/06` capstones.
- **Vulnerability / remediation SLA** → `../../vulnmgmt/`.
- **Compliance / reporting** → `../../soc/`, `../../grc/`, `../../soc-reports/`.
- **Frameworks** → NIST SP 800-61 (IR), 800-53 (controls), MITRE ATT&CK (mapping).

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md). The capstone artifact is a
polished **incident report** plus a **triage runbook** — exactly what a SOC role
interviews on.
