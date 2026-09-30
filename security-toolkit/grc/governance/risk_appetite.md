# Risk Appetite Statement (template)

Approved by: _<Board / Risk Committee>_ · Date: _<date>_ · Review: annual

## Purpose
Defines how much risk the organization is willing to accept in pursuit of its
objectives, and the thresholds that trigger escalation or treatment.

## Overall posture
_<e.g., We are risk-averse for anything affecting customer data confidentiality
and regulatory compliance, and risk-tolerant for experimental internal tooling.>_

## Appetite by category (5×5 residual score, 1–25)

| Risk category | Appetite (max acceptable residual) | Escalate above |
|---------------|-----------------------------------|----------------|
| Customer data confidentiality | Low (≤ 4) | Any Medium+ |
| Regulatory / compliance | Low (≤ 4) | Any Medium+ |
| Service availability | Medium (≤ 9) | High (≥ 10) |
| Financial | Medium (≤ 9) | High (≥ 10) |
| Operational / internal tooling | High (≤ 14) | Critical (≥ 15) |

> `risk/risk_register.py --appetite N` flags open risks whose **residual** score
> exceeds `N`. Set `N` to your lowest-category threshold, or run per-category.

## Tolerances / KRIs (examples)
- Critical vulnerabilities open past SLA: **0** (any breach escalates).
- KEV (known-exploited) findings open: **0**.
- Endpoints without EDR: **< 2%**.
- Overdue POA&M items: **0** critical/high.
- Vendors without a current SOC 2: **0** for those handling customer data.

## Escalation
Risks above appetite are escalated to _<Risk Committee>_ within _<N business
days>_ with a treatment plan (mitigate / transfer / avoid) or a time-boxed,
approved acceptance recorded in the risk register (`acceptance_expiry`).
