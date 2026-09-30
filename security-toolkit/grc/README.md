# GRC — Governance, Risk & Compliance

The layer that ties the toolkit's compliance pieces together: **governance**
(policies, roles, risk appetite), **risk** (register, scoring, treatment), and
**compliance** (one control set measured across many frameworks).

> Decision support for a security/risk program — not a substitute for your GRC
> platform, auditors, or legal counsel. Registers here are templates to adapt.

## The three pillars

| Pillar | What it answers | Here |
|--------|-----------------|------|
| **Governance** | Who owns what? Are policies current? What risk will we accept? | `governance/` |
| **Risk** | What could hurt us, how bad, and are we treating it? | `risk/` |
| **Compliance** | Do our controls satisfy the frameworks we're held to? | `compliance/` |

## Layout

```
grc/
├── governance/
│   ├── policy_register.csv        Policies, owners, review cadence
│   ├── policy_review_tracker.py   Flags policies overdue for review
│   ├── risk_appetite.md           Risk appetite statement (template)
│   └── raci.md                    Roles & responsibilities (RACI)
├── risk/
│   ├── risk_register.csv          Risk register (template)
│   └── risk_register.py           Inherent/residual scoring, heat map, appetite breaches
├── compliance/
│   ├── control_catalog.csv        Master controls → NIST 800-53 / CSF 2.0 / ISO 27001
│   │                              / SOC 2 / PCI-DSS / CIS v8 / CMMC L2
│   └── crosswalk.py               Coverage per framework from one control-status file
└── reporting/
    └── grc_dashboard.py           Aggregate risk + coverage + policy (+ POA&M/vuln) → exec report
```

## Quick start

```bash
# Risk register: inherent/residual scores, heat map, appetite breaches
python risk/risk_register.py risk/risk_register.csv --appetite 9

# "Implement once, comply many": coverage across every framework at once
#   (status can be soc-reports/.../controls_evidence.csv — same control IDs)
python compliance/crosswalk.py --catalog compliance/control_catalog.csv \
    --status <your_control_status.csv>

# Governance: which policies are overdue for review?
python governance/policy_review_tracker.py governance/policy_register.csv --due-days 60

# One executive roll-up for the risk committee
python reporting/grc_dashboard.py \
    --risk risk/risk_register.csv \
    --catalog compliance/control_catalog.csv --status <control_status.csv> \
    --policies governance/policy_register.csv \
    --poam ../soc/poam/poam_template.csv \
    --out grc_dashboard.md
```

## How it connects to the rest of the toolkit

The **same control IDs** (`CTL-*`) run through everything:

- **Evidence** for those controls is produced by the scanners and auto-linked in
  `../soc-reports/evidence/collect_evidence.py`.
- **Compliance regimes** consume them: SOC 2/3 (`../soc-reports/`), DoD &
  public-sector ConMon / cATO (`../soc/`, `../dod/`).
- **Risk** is informed by live signals: KEV/SLA breaches from `../vulnmgmt/`,
  CSPM findings from `../cloud/`, POA&Ms from `../soc/poam/`.

So one control implemented → evidence collected once → measured against SOC 2,
NIST, ISO, PCI, CIS, CMMC, and folded into the risk register and the exec
dashboard.

## Frameworks in the crosswalk
NIST SP 800-53 · NIST CSF 2.0 · ISO/IEC 27001 (Annex A) · SOC 2 (TSC) ·
PCI-DSS v4 · CIS Controls v8 · CMMC Level 2. Mappings are **indicative** —
confirm exact control equivalences with your assessor for a formal audit.
