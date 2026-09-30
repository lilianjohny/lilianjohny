# SOC 1 / 2 / 3 — readiness command runbook

The commands to run the AICPA SOC readiness workflow, including where each input
comes from. **A SOC report is issued only by a licensed CPA firm** — these tools
assess readiness and organize evidence.

## 0. Prerequisites
```bash
# Pure Python + CSV; no external tools required.
python --version    # 3.9+
```

## 1. Build / maintain your control matrix
Map each control to the Trust Services Criteria and set its status. Start from
the sample and edit for your environment:
```bash
cp soc2/controls_matrix.csv my_controls.csv
$EDITOR my_controls.csv        # control_id, tsc_criteria, status, owner, evidence
# Full criteria reference: soc2/trust_services_criteria.csv
```

## 2. SOC 2 / SOC 3 readiness assessment
```bash
# Security (Common Criteria) is always in scope; add categories you commit to.
python soc2/readiness_assessment.py \
    --tsc soc2/trust_services_criteria.csv \
    --controls my_controls.csv \
    --categories security,availability,confidentiality
# SOC 3 readiness == SOC 2 readiness (same TSC).
```

## 3. Gap analysis (remediation plan)
```bash
python gap_analysis/gap_report.py \
    --controls my_controls.csv \
    --tsc soc2/trust_services_criteria.csv \
    --out gap_report.md
```

## 4. SOC 1 (financial-reporting controls / ICFR)
```bash
# SOC 1 uses control OBJECTIVES you define (no fixed TSC). Fill the template:
cp soc1/icfr_control_objectives.md my_soc1_objectives.md
$EDITOR my_soc1_objectives.md
```

## 5. Evidence / PBC tracking (Type I and especially Type II)
```bash
cp evidence/evidence_request_list.csv pbc.csv
$EDITOR pbc.csv                 # add requests, owners, due dates, sample counts
python evidence/evidence_tracker.py pbc.csv --due-days 14
```

## 6. Auto-link toolkit evidence to SOC 2 controls (wired, not manual)
Generate the CC evidence with the toolkit, drop the artifacts into one folder,
then let the collector map them to controls and set status from what's found:
```bash
mkdir -p evidence_artifacts
# Generate evidence (examples — run what applies to your scope):
python ../cloud/ciem/aws_least_privilege.py            > evidence_artifacts/ciem.txt   # CC6 access
python ../cloud/detection/aws_detection_coverage.py    > evidence_artifacts/detection.json # CC7.2
bash   ../cloud/prowler_scan.sh aws --severity critical,high --output-dir evidence_artifacts/prowler
python ../vulnmgmt/report/vm_metrics.py deduped.jsonl  --out evidence_artifacts/vm_report.md # CC7.1
bash   ../dod/scripts/generate_sbom.sh --path . --out evidence_artifacts --name app         # SBOM
python ../devsecops/secrets_scan.py .  # (or gitleaks -> evidence_artifacts/secrets.sarif)  # CC6.1
python ../recon/tls_cert_check.py app.example.com      > evidence_artifacts/tls.txt          # CC6.7

# Auto-link artifacts -> controls (status set from evidence found):
python evidence/collect_evidence.py \
    --sources soc2/evidence_sources.csv \
    --evidence-dir evidence_artifacts \
    --out controls_evidence.csv

# Now readiness/gap run against LIVE evidence, not a hand-edited matrix:
python soc2/readiness_assessment.py --tsc soc2/trust_services_criteria.csv \
    --controls controls_evidence.csv --categories security,availability,confidentiality
python gap_analysis/gap_report.py --controls controls_evidence.csv \
    --tsc soc2/trust_services_criteria.csv --out gap_report.md
```
`soc2/evidence_sources.csv` maps each control → TSC criteria → the evidence
glob and the toolkit command that produces it. See `../soc/frameworks/control_mapping.csv`
for the NIST SP 800-53 crosswalk.

## 7. Vendor / subservice organizations
- Track vendors as controls (see `soc2/controls_matrix.csv` CTL-13).
- Read each vendor's SOC 2/1 report and implement the CUECs they assign to you
  (`shared/cuecs.md`); record carve-out vs inclusive (`shared/subservice_orgs.md`).

## Where inputs come from (summary)
| Input | Produced by |
|-------|-------------|
| `my_controls.csv` | you, mapping controls → TSC (from `controls_matrix.csv`) |
| `pbc.csv` | the auditor's PBC list (start from `evidence_request_list.csv`) |
| CC evidence | the toolkit scanners (cloud/vulnmgmt/dod) per the crosswalk |
