# Vulnerability Management

A vulnerability-management **program pipeline** — not another scanner. The
toolkit's scanners (`cloud/`, `dod/`, `appsec/`, `pentest/`, `vuln/`) *find*
vulnerabilities; this turns their output into a managed lifecycle:

```
scan → normalize → enrich/prioritize → dedupe → track SLAs → report → remediate → verify
```

## Why prioritize beyond severity

Severity (CVSS) alone over-counts: most "critical" CVEs are never exploited.
This pipeline prioritizes with the signals defenders actually use (aligned to
CISA's SSVC thinking):

- **CISA KEV** — is it *known-exploited in the wild*? (highest priority)
- **EPSS** — probability it *will* be exploited soon (FIRST.org)
- **CVSS** — technical severity baseline
- **Asset criticality** — does the affected asset matter? (from your inventory)

→ a **risk score (0–10)**, a **priority (P1–P4)**, and an **SLA-dated due date**.

## Pipeline

| Stage | Tool | In → Out |
|-------|------|----------|
| Normalize | `ingest/normalize.py` | Trivy/Grype/nuclei/pip-audit/Prowler JSON → common findings JSONL |
| Enrich/prioritize | `enrich/prioritize.py` (+ `kev_epss.py`) | findings → + KEV/EPSS/criticality/risk/priority/SLA |
| Dedupe | `dedupe/dedupe.py` | collapse the same vuln from multiple scanners |
| Track SLAs | `track/sla_tracker.py` (+ `sla_policy.csv`) | overdue / due-soon / KEV-exposure / compliance % |
| Report | `report/vm_metrics.py` | program KPIs → Markdown |
| Inventory | `assets/asset_inventory.example.csv` | asset → criticality → owner |

## End-to-end example

```bash
cd vulnmgmt
# 1. Normalize outputs from several scanners (tag the asset)
python ingest/normalize.py --asset payments-api trivy.json grype.json > findings.jsonl
python ingest/normalize.py --asset web01 nuclei.jsonl >> findings.jsonl

# 2. Enrich + prioritize (KEV/EPSS from local caches or --allow-fetch)
python enrich/prioritize.py findings.jsonl \
    --kev-file kev.json --epss-file epss.csv \
    --assets assets/asset_inventory.example.csv --sla track/sla_policy.csv \
    > enriched.jsonl

# 3. Dedupe across scanners
python dedupe/dedupe.py enriched.jsonl > deduped.jsonl

# 4. Track SLAs and 5. report
python track/sla_tracker.py deduped.jsonl --due-days 7
python report/vm_metrics.py deduped.jsonl --out vm_report.md
```

## Threat-intel feeds

`enrich/kev_epss.py` loads:
- **CISA KEV** catalog (JSON) — the authoritative known-exploited list.
- **FIRST EPSS** scores (CSV) — daily exploit-probability.

Pass `--allow-fetch` to pull them live, or supply `--kev-file`/`--epss-file`
local caches (recommended in restricted networks — the feeds are refreshed
daily, so cache and update on a schedule).

## Remediation SLAs

`track/sla_policy.csv` sets days-to-remediate per priority (defaults: P1 15,
P2 30, P3 90, P4 180). KEV items land in P1. Tune to your risk appetite /
regulatory driver (e.g., FedRAMP, CISA BOD 22-01 for KEV).

## Ties into the rest of the toolkit
- Feed it `cloud/prowler_scan.sh`, `dod/scripts/gate_sca.sh`, `appsec/deps/sca_scan.sh`,
  and `vuln/dependency_audit.sh` outputs.
- Overdue/KEV metrics map to `soc/continuous_monitoring/` (ConMon) and
  `soc/poam/` (POA&Ms) for compliance reporting.
