# Security Governance — Roles & Responsibilities (RACI)

R = Responsible · A = Accountable · C = Consulted · I = Informed
Adapt roles/names to your org. One **A** per activity.

| Activity | Board/Risk Cmte | CISO | Security/SecOps | IT/Eng | Risk Officer | Data/Biz Owner |
|----------|:---------------:|:----:|:---------------:|:------:|:------------:|:--------------:|
| Set risk appetite | A | C | I | I | R | C |
| Maintain risk register | I | A | C | C | R | C |
| Policy approval | A | R | C | C | C | C |
| Vulnerability remediation | I | A | R | R | I | C |
| Incident response | I | A | R | C | I | I |
| Access reviews | I | A | C | R | I | C (approver) |
| Vendor / third-party risk | I | A | C | I | R | C |
| Control implementation | I | A | R | R | C | C |
| Audit / assessment liaison | I | A | C | C | R | I |
| Continuous monitoring / KRIs | I | A | R | C | C | I |
| Business continuity / DR | A | C | C | R | C | A (per service) |

## Committees / cadence (template)
- **Risk Committee** — quarterly: review top risks, appetite breaches, treatment progress.
- **Change Advisory Board** — as needed: significant changes.
- **Security review** — monthly: KRIs, incidents, vuln SLA, POA&M, control health.

## How this maps to the toolkit
- Risk register → `risk/risk_register.py`
- Control health across frameworks → `compliance/crosswalk.py`
- Policy governance → `governance/policy_review_tracker.py`
- Aggregate posture for the committee → `reporting/grc_dashboard.py`
