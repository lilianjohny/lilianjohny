# SOC Compliance — command runbook

The actual commands to run the DoD / public-sector SOC compliance workflow,
**including how to produce each input** (so nothing is only "referenced").

> Decision support — verify deadlines/controls against current issuances and
> your AO/ISSM/CSSP.

## 0. Prerequisites
```bash
pip install pyyaml            # scope/log-source YAML parsing
# Cloud detection inputs (optional) use aws/az/gcloud + boto3 already in the toolkit.
```

## 1. Continuous Monitoring (vulnerabilities)

**Produce the input** from what your SOC actually runs, then feed ConMon:
```bash
# a) From Nessus / ACAS export (.nessus XML)
python continuous_monitoring/ingest_scans.py scan.nessus > vulns.json

# b) From the toolkit's own scanners via the VM pipeline
#    (Trivy/Grype/nuclei/Prowler -> normalized -> ConMon)
python ../vulnmgmt/ingest/normalize.py --asset web01 trivy.json grype.json > findings.jsonl
python continuous_monitoring/ingest_scans.py findings.jsonl > vulns.json

# c) Run the ConMon KPIs (vuln aging vs SLA + POA&M status)
python continuous_monitoring/conmon_metrics.py --vulns vulns.json --poam poam.csv \
    --sla critical=15,high=30,medium=90,low=180
```

## 2. POA&M management
```bash
# Start from the template, keep it updated, then track aging/overdue:
cp poam/poam_template.csv poam.csv
python poam/poam_tracker.py poam.csv --due-days 30
```

## 3. Event logging (OMB M-21-31)

**Produce `log_sources.json`** describing your logging, then assess:
```bash
cat > log_sources.json <<'JSON'
{ "retention_active_months": 12, "retention_cold_months": 18, "centralized": true,
  "categories": { "authentication": true, "network": true, "dns": true,
                  "cloud_control_plane": true, "endpoint_edr": true } }
JSON
python logging/log_coverage_check.py --sources log_sources.json

# Cloud control-plane coverage can be verified live:
python ../cloud/detection/aws_detection_coverage.py        # CloudTrail/GuardDuty/etc.
```

## 4. Incident handling & reporting
```bash
# DoD (CJCSM category -> JIMS -> JFHQ-DODIN), computes the deadline:
python incident/incident_report.py --regime dod --category 1 \
    --discovered 2026-02-01T14:30:00Z --summary "root-level intrusion on host X"

# Federal civilian (CISA within 1 hour):
python incident/incident_report.py --regime federal \
    --discovered 2026-02-01T14:30:00Z --summary "confirmed breach"

# Critical infrastructure (CIRCIA 72h / 24h ransom):
python incident/incident_report.py --regime critical_infrastructure --ransom-paid \
    --discovered 2026-02-01T14:30:00Z --summary "ransomware, payment made"
```
Follow `incident/ir_playbook.md` for the full lifecycle; timelines in
`incident/reporting_timelines.md`.

## 5. Monthly posture rollup
```bash
python reporting/soc_posture_report.py --regime federal \
    --vulns vulns.json --poam poam.csv --sources log_sources.json \
    --out soc_posture.md
```

## 6. Control coverage / crosswalk
`frameworks/control_mapping.csv` maps each SOC capability → NIST SP 800-53 →
regime → the toolkit script that provides evidence. Run those scripts to
generate the evidence (e.g. STIG, SBOM, CSPM, detection coverage):
```bash
bash ../dod/scripts/gate_stig.sh --content <stig-datastream.xml> --profile <id>
bash ../cloud/prowler_scan.sh aws --severity critical,high
bash ../dod/evidence/collect_cato_evidence.sh --evidence cato-evidence
```

## Where inputs come from (summary)
| Input | Produced by |
|-------|-------------|
| `vulns.json` | `ingest_scans.py` from Nessus/ACAS `.nessus` or vulnmgmt findings |
| `poam.csv` | your RMF/FedRAMP POA&M (start from `poam/poam_template.csv`) |
| `log_sources.json` | your logging inventory (+ `cloud/detection/` for cloud) |
| incident details | the SOC analyst during triage |
