# SOC 1 — Control Objectives (ICFR) template

A SOC 1 (SSAE 18, AT-C 320) reports on a service organization's controls that
are **relevant to user entities' internal control over financial reporting
(ICFR)**. Unlike SOC 2's fixed Trust Services Criteria, **you define the control
objectives** for the services in scope; the auditor tests controls against them.

> Type I = design at a point in time. Type II = design + operating effectiveness
> over the period (sampled evidence).

## How to scope
1. Identify the services that affect user entities' financial statements
   (e.g., payroll processing, payments, claims, SaaS that records transactions).
2. For each process, write **control objectives** (what must be true for the
   financials to be complete, accurate, valid, authorized, and restricted).
3. List the **controls** that achieve each objective, with owner + evidence.
4. Define **Complementary User Entity Controls (CUECs)** — see `../shared/cuecs.md`.

## Common control-objective areas (adapt to your service)

| # | Control objective (illustrative) | Example controls |
|---|----------------------------------|------------------|
| CO-1 | New transactions are authorized, complete, and accurately recorded | Input validation; maker-checker; interface reconciliations |
| CO-2 | Transaction processing is complete and accurate | Batch totals; automated edit checks; exception handling |
| CO-3 | Data is processed timely | SLA monitoring; job scheduling + failure alerting |
| CO-4 | Master data changes are authorized and accurate | Change approval; segregation of duties |
| CO-5 | Logical access to the application/data is restricted to authorized users | Provisioning/deprovisioning; access reviews; MFA |
| CO-6 | Changes to applications are authorized, tested, and approved | Change management; code review; CI gates |
| CO-7 | IT operations support complete and accurate processing | Backup/restore; job monitoring; incident management |
| CO-8 | Data is protected in transit and at rest | Encryption; key management |

## Control matrix (fill in)

| Objective | Control ID | Control description | Owner | Frequency | Evidence | Type II samples |
|-----------|-----------|---------------------|-------|-----------|----------|-----------------|
| CO-1 | | | | per transaction / daily | | |
| CO-5 | | | | quarterly | | |

## Notes
- Reuse the toolkit's technical controls (access reviews, change gates, logging)
  as evidence where they support a financial-reporting objective.
- Track evidence with `../evidence/evidence_tracker.py`.
- The SOC 1 report itself (description of system, management assertion, auditor's
  opinion) is authored by management + the CPA firm — this template feeds it.
