# Lab 02 — Unified Posture / CSPM (Multi-Cloud)

**Skills practiced:** cross-cloud posture assessment · normalizing findings to one
schema · a single risk view over AWS+Azure+GCP · prioritizing across providers.
**Proves (JD):** securing multi-cloud deployments — you can see the whole estate,
not three disconnected consoles.

## Objective
Scan all three clouds, **normalize** the findings into one schema, and produce a
single prioritized report — so "what's our worst exposure right now?" has one
answer across providers.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Sandbox AWS + Azure + GCP with read/security-audit access in each.
- The toolkit's unified CSPM: `../../cloud/multicloud/` (`scan_all.sh`,
  `normalize.py`, `report.py`, `baseline.csv`) and `../../cloud/prowler_scan.sh`.

---

## Part A — Build: something wrong in each cloud
Deliberately introduce one misconfig per cloud (in your sandbox):
- **AWS:** a public S3 bucket (or an over-broad SG).
- **Azure:** a storage account with public blob access (or an NSG open to `*`).
- **GCP:** a bucket with public access (allUsers) or a `0.0.0.0/0` firewall.

## Part B — Attack / observe: three consoles problem
1. Note that each cloud reports these differently (different names, severities,
   fields). Cross-cloud triage by hand doesn't scale.

## Part C — Harden the *process*: one pane
1. Run the unified scan:
   ```bash
   bash ../../cloud/multicloud/scan_all.sh          # runs per-cloud scanners
   python3 ../../cloud/multicloud/normalize.py ...  # → one schema (category, severity, resource)
   python3 ../../cloud/multicloud/report.py ...     # single prioritized report
   ```
2. Confirm the three misconfigs surface in **one** report with a **consistent
   category** (e.g., all three "public data exposure" land in the Data category —
   this is exactly what `normalize.py`'s category rules do).
3. Compare against `baseline.csv` to track drift over time.

## Part D — Remediate + verify
1. Fix each misconfig (block public access, tighten the rule).
2. Re-run the unified scan → the findings clear in the single report.
```bash
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py
python3 ../../cloud/aws/s3_public_check.py      # AWS-specific confirm
```
Success = one normalized report showed all three exposures with consistent
categorization/severity, and re-scan shows them resolved.

## Cleanup
Remove the deliberately-misconfigured resources.

## Portfolio artifact
- The **before/after unified report** (three clouds, one schema) — a strong
  "single pane of glass" artifact.
- A short note on **why normalization matters**: cross-cloud prioritization is
  impossible if severities/categories don't line up.

## Stretch goals
- Extend `normalize.py`'s mapping to a new finding type; add a test case.
- Feed the normalized output into `../../vulnmgmt/` for SLA tracking + KEV/EPSS
  enrichment.
- Schedule the scan (cron/CI) and diff against `baseline.csv` to alert on drift.
