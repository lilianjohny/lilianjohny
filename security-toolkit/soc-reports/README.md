# SOC 1 / SOC 2 / SOC 3 — Reporting readiness

Tooling and references to **prepare for and manage** AICPA System and
Organization Controls (SOC) examinations under **SSAE 18**.

> ℹ️ **Not the same as `../soc/`.** This directory is about the **AICPA SOC
> reports** (auditor attestations). The `../soc/` directory is about a
> **Security Operations Center** (DoD/public-sector cyber operations). Different
> "SOC".
>
> ⚠️ **A SOC report can only be issued by a licensed CPA firm.** These tools
> assess *readiness*, organize *evidence*, and manage *gaps* — they do not
> certify you and are not a substitute for the auditor's examination.

## The three reports

| Report | Subject | Audience | Based on |
|--------|---------|----------|----------|
| **SOC 1** | Controls relevant to **user entities' financial reporting (ICFR)** | User entities + their auditors | Control objectives you define (SSAE 18, AT-C 320) |
| **SOC 2** | Controls over **security, availability, processing integrity, confidentiality, privacy** | Customers, prospects, regulators (under NDA) | **Trust Services Criteria** (AT-C 205) |
| **SOC 3** | Same TSC as SOC 2, **general-use summary** (a seal/public report) | Public / marketing | Trust Services Criteria |

**Type I** = design of controls at a point in time. **Type II** = design **and
operating effectiveness** over a period (typically 3–12 months) — requires
evidence sampled across the period.

## Trust Services Criteria (SOC 2 / SOC 3)

- **Security (Common Criteria, CC1–CC9)** — always required.
- **Availability (A1)**, **Confidentiality (C1)**, **Processing Integrity
  (PI1)**, **Privacy (P1–P8)** — included only if in scope.

The full criteria are in `soc2/trust_services_criteria.csv`.

## Layout

```
soc-reports/
├── soc2/
│   ├── trust_services_criteria.csv   Full TSC (CC1-9, A1, C1, PI1, P1-8)
│   ├── controls_matrix.csv           Sample control → TSC → status → evidence
│   └── readiness_assessment.py       Score coverage vs TSC for in-scope categories
├── soc1/
│   └── icfr_control_objectives.md    SOC 1 control-objective template (ICFR)
├── soc3/
│   └── soc3_overview.md              SOC 3 general-use report + seal guidance
├── evidence/
│   ├── evidence_request_list.csv     PBC (prepared-by-client) request template
│   └── evidence_tracker.py           Track PBC/evidence status + Type II samples
├── gap_analysis/
│   └── gap_report.py                 Gap-analysis report from the controls matrix
└── shared/
    ├── cuecs.md                      Complementary User Entity Controls
    └── subservice_orgs.md            Carve-out vs inclusive; vendor SOC reports
```

## Workflow

```bash
# 1. Map your controls to the TSC and set each status (edit controls_matrix.csv)
# 2. Assess readiness for your in-scope categories
python soc2/readiness_assessment.py --tsc soc2/trust_services_criteria.csv \
    --controls soc2/controls_matrix.csv --categories security,availability,confidentiality

# 3. Produce a gap-analysis report for remediation
python gap_analysis/gap_report.py --controls soc2/controls_matrix.csv \
    --tsc soc2/trust_services_criteria.csv --out gap_report.md

# 4. During the exam period, track evidence / PBC requests
python evidence/evidence_tracker.py evidence/evidence_request_list.csv --due-days 14
```

Many SOC 2 CC controls are satisfied by the same evidence the rest of this
toolkit produces (access reviews, vuln scans, change gates, logging, IR) — see
`../soc/frameworks/control_mapping.csv` for the NIST 800-53 crosswalk.

## Standards
- AICPA **SSAE 18** (AT-C 105/205/320); **2017 Trust Services Criteria**
  (with 2022 revised points of focus). Confirm the applicable TSC version and
  scope with your CPA firm.
