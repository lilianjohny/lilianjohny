# OMB M-21-31 — Event Logging (reference)

M-21-31 ("Improving the Federal Government's Investigative and Remediation
Capabilities") sets tiered event-logging maturity for federal agencies.
Assess your posture with `log_coverage_check.py`.

> Verify specifics against the memorandum and your agency's implementation
> guidance; tiers and criteria are summarized here.

## Maturity tiers
| Tier | Meaning |
|------|---------|
| **EL0** | Not effective — logging requirements not met |
| **EL1** | Basic — highest-criticality logging in place |
| **EL2** | Intermediate — plus enterprise correlation/centralization |
| **EL3** | Advanced — full logging, retention, and advanced analytics |

## Retention (commonly cited)
- **12 months** active (hot) storage, **18 months** cold storage → **30 months** total.
- Access-controlled, integrity-protected, and available to CISA/FBI on request.

## Required log categories (map to NIST SP 800-53 AU family)
- Authentication & authorization events
- Account/identity management changes
- Process execution / command-line
- Network flow / connection logs
- DNS query logs
- HTTP/web proxy logs
- File & object access (incl. cloud storage)
- Cloud control-plane / API audit (CloudTrail / Activity / Audit Logs)
- Endpoint/EDR telemetry
- Email security events
- Database access/audit

## SOC actions
- Centralize sources into the SIEM; ensure time sync (UTC) across sources.
- Verify retention meets 12+18 months; test restore from cold storage.
- Close coverage gaps flagged by `log_coverage_check.py` (open POA&Ms).
- Tie cloud control-plane coverage to `../../cloud/detection/aws_detection_coverage.py`.
