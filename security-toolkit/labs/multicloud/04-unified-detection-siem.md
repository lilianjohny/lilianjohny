# Lab 04 — Unified Detection & SIEM (Multi-Cloud)

**Skills practiced:** centralizing AWS+Azure+GCP logs into one SIEM · correlating
one identity across clouds · a shared detection catalog · one response runbook.
**Proves (JD):** detect an attacker who moves *between* clouds.

## Objective
Get all three clouds' audit/identity logs into one SIEM, then detect a
cross-cloud attack by correlating on the same identity.

## Est. time / cost
3–4 h · **~$1–3** (log ingestion; disable after).

## Prerequisites
- Sandbox AWS + Azure + GCP with logging on (per-cloud Lab 00/06). A SIEM
  (Sentinel, Chronicle/SecOps, Splunk, or OpenSearch). Reference:
  `../../zero-trust/architecture/multicloud.md`, `../../cloud/detection/`.

---

## Part A — Pipe all three clouds to one SIEM
- **AWS:** CloudTrail (all-Region) → S3/Kinesis → SIEM connector.
  ```bash
  aws cloudtrail get-trail-status --name org-trail --query IsLogging   # from Lab 00
  ```
- **Azure:** Entra sign-in/audit + Activity Log → Sentinel connector (or export
  to your SIEM). `az monitor diagnostic-settings subscription create ...` (Lab 00).
- **GCP:** Cloud Audit Logs → Pub/Sub → SIEM.
  ```bash
  gcloud logging sinks create siem-sink pubsub.googleapis.com/projects/$PROJECT/topics/siem \
    --log-filter='logName:"cloudaudit.googleapis.com"'
  ```
- Normalize identities so the **same person** (from the Lab 00 IdP) is
  recognizable across all three sources.

## Part B — Attack: a cross-cloud chain (your own accounts)
Using the single federated identity from Lab 00:
1. Recon in **AWS** (unusual API calls).
2. An IAM/role change attempt in **GCP** (denied by Lab 01).
3. A privileged activation attempt in **Azure** (outside policy).
4. A cross-tenant/cross-cloud data reach (denied by earlier labs).

## Part C — Hunt: correlate one identity across clouds
Query the SIEM for the identity across all three sources; stitch AWS + Azure +
GCP events into a **single timeline**. Adapt patterns from
`../../cloud/detection/cloudtrail_hunt.md` to each schema. The payoff: three
consoles show three unrelated blips; the SIEM shows **one actor, one campaign**.

## Part D — Respond: one runbook, three enforcement points
On a high-severity correlated finding: **disable the identity in the IdP** (kills
access in all three clouds at once) + trigger per-cloud containment (revoke
sessions / isolate). Re-run the chain and watch the IdP-level disable cut access
everywhere. Map detections with `../../grc/compliance/crosswalk.py`.

## Verify
```bash
python3 ../../soc/incident/incident_report.py   # one report, cross-cloud timeline
```
Success = all three clouds' logs in one SIEM, a single identity's cross-cloud
activity correlated into one timeline, IdP-level disable contains it everywhere.

## Cleanup
```bash
gcloud logging sinks delete siem-sink --quiet
# stop Azure diagnostic settings / AWS SIEM connector; delete SIEM content if just for the lab.
```

## Portfolio artifact (senior-level)
- A **cross-cloud attack timeline** (one identity, three clouds) from your SIEM.
- A **detection-coverage matrix** spanning AWS+Azure+GCP (technique → source →
  detection → response), mapped to MITRE ATT&CK.
- The **IdP-level containment** writeup.

## Stretch goals
- Add **UEBA**/anomaly detection for the federated identity.
- Build a **single dashboard** across the three clouds.
- Show **mean-time-to-contain** with IdP-level disable vs per-cloud manual.
