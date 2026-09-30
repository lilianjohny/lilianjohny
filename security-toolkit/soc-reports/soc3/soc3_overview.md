# SOC 3 — General-Use Report

A **SOC 3** report covers the **same Trust Services Criteria as SOC 2**, but is a
**general-use** report: it contains management's assertion and the auditor's
opinion **without** the detailed description of the system, the specific
controls, or the auditor's tests and results. That makes it freely
distributable (website, marketing) — unlike a SOC 2, which is restricted-use
and shared under NDA.

## SOC 2 vs SOC 3 at a glance

| | SOC 2 | SOC 3 |
|--|-------|-------|
| Criteria | Trust Services Criteria | Trust Services Criteria (same) |
| Detail | System description + controls + tests + results | Assertion + opinion only |
| Distribution | Restricted (NDA) | General use / public |
| Typical use | Customer due diligence | Public trust seal / marketing |

## How to get one
- A SOC 3 is issued by the **same CPA firm** performing your SOC 2, usually as a
  companion deliverable — the underlying examination is the SOC 2 (Type II).
- Readiness for SOC 3 == readiness for SOC 2. Use `../soc2/readiness_assessment.py`
  and close gaps via `../gap_analysis/gap_report.py`.

## Using the seal / report
- Publish only the CPA-issued SOC 3 report/seal; do not alter it.
- Do not represent internal readiness output from this toolkit as a SOC 3 —
  only the CPA firm's issued report is a SOC 3.
- Keep the report current (typically annual, matching the SOC 2 period).
