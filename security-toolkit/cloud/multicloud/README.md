# Multi-Cloud Security (unified)

A single pane over AWS, Azure, and GCP: scan every cloud you're logged into in
**one run**, normalize the findings into **one schema**, and get **one
cross-cloud posture view** measured against a common baseline.

This complements the per-provider tools in `../` (which go deep on each cloud)
by giving you the **unified, comparable** picture across all of them.

> Read-only. Uses your own authenticated sessions (`aws`, `az login`,
> `gcloud auth`). Nothing is changed in any account.

## Pieces

| File | Role |
|------|------|
| `scan_all.sh` | Detects logged-in clouds and runs Prowler (severity-gated) for each → per-cloud JSON-OCSF |
| `normalize.py` | Merges each cloud's OCSF output into one common finding schema + a cross-cloud **category** (Identity / Network / Data / Logging / Config) |
| `report.py` | Unified report: provider × severity, provider × category, **systemic issues across clouds**, baseline coverage |
| `baseline.csv` | Cross-cloud control baseline — one control mapped to each provider's specific check |

## One-command flow

```bash
cd cloud/multicloud

# 1. Scan every cloud you're authenticated to (or --clouds aws,azure,gcp)
bash scan_all.sh --out mc-out --severity critical,high

# 2. Normalize all providers' output into one stream
python3 normalize.py mc-out/**/*.ocsf.json > mc-out/findings.jsonl

# 3. Unified cross-cloud posture report
python3 report.py mc-out/findings.jsonl --baseline baseline.csv --out mc-out/report.md
```

## What the unified view shows

- **Provider × severity** — where the critical/high risk concentrates.
- **Provider × category** — is "public storage" an AWS problem, or everywhere?
- **Systemic issues** — a category failing on 2+ clouds → fix it once as a
  cross-cloud guardrail (AWS SCP / Azure Policy / GCP Org Policy) rather than
  per-account.
- **Baseline coverage** — one standard (MFA, no public storage, encryption,
  logging, threat detection) measured across every cloud.

## Ties into the rest of the toolkit

- **Prioritize**: pipe findings to `../../vulnmgmt/` for KEV/EPSS/criticality
  risk scoring and SLAs.
- **Comply**: the categories map to `../../grc/compliance/crosswalk.py`
  (NIST/ISO/SOC 2/PCI/CIS/CMMC) — one cross-cloud control set, many frameworks.
- **Detect**: pair with `../detection/` (per-cloud threat-detection coverage)
  and `../kubernetes/` (KSPM) for full CNAPP breadth.

## Notes
- `scan_all.sh` runs Prowler via `../prowler_scan.sh` (native binary or the
  official container), so it needs `prowler` or `docker` available.
- Azure/GCP OCSF field names vary by Prowler version; `normalize.py` extracts
  provider/severity/resource best-effort and degrades gracefully.
