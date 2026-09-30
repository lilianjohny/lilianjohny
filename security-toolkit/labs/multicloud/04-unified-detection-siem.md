# Lab 04 — Unified Detection & SIEM (Multi-Cloud)

**Skills practiced:** centralizing AWS+Azure+GCP logs into one SIEM · correlating
a single identity's activity across clouds · a shared detection catalog · one
response runbook.
**Proves (JD):** securing multi-cloud deployments — you can detect an attacker who
moves *between* clouds, not just within one.

## Objective
Get all three clouds' audit/identity logs into **one SIEM**, then detect an attack
that crosses cloud boundaries by correlating on the **same identity**.

## Est. time / cost
3–4 h · **~$1–3** (log ingestion; disable after).

## Prerequisites
- Sandbox AWS + Azure + GCP with logging on (per-cloud Lab 00/06).
- A SIEM you can use (Microsoft Sentinel, Google Chronicle/SecOps, Splunk, or
  self-hosted OpenSearch).
- Reference: `../../zero-trust/architecture/multicloud.md` (visibility pillar),
  `../../cloud/detection/`, `../../soc/`.

---

## Part A — Build: pipe all three clouds to one SIEM
1. **AWS:** CloudTrail (org/all-Region) → SIEM connector / S3 → ingest.
2. **Azure:** Entra sign-in/audit + Activity Log → Sentinel/connector.
3. **GCP:** Cloud Audit Logs → Pub/Sub → SIEM / Chronicle.
4. Normalize identities so the **same person** (via the IdP from Lab 00) is
   recognizable across all three sources.

## Part B — Attack: a cross-cloud chain (your own accounts)
Using the single federated identity from Lab 00, do a chain that spans clouds:
1. Recon in **AWS** (unusual API calls).
2. An IAM/role change attempt in **GCP** (denied by Lab 01 least privilege).
3. A privileged activation attempt in **Azure** (outside policy).
4. A cross-tenant/cross-cloud data reach (denied by earlier labs).

## Part C — Hunt: correlate one identity across clouds
1. Query the SIEM for the identity across all three sources; build a **single
   timeline** that stitches AWS + Azure + GCP events together.
2. This is the multi-cloud detection payoff: three consoles would have shown three
   unrelated blips; the SIEM shows **one actor, one campaign**.
3. Reuse hunt patterns from `../../cloud/detection/cloudtrail_hunt.md` and adapt to
   each cloud's schema.

## Part D — Respond: one runbook, three enforcement points
1. Build a shared response: on a high-severity correlated finding, **disable the
   identity in the IdP** (kills access in all three clouds at once) and trigger
   per-cloud containment (revoke sessions / isolate).
2. Test it: re-run the chain, watch the IdP-level disable cut access everywhere.
3. Map detections to a framework (`../../grc/compliance/crosswalk.py`, `../../soc/`).

## Verify
```bash
# One report shows the cross-cloud timeline for a single identity
python3 ../../soc/incident/incident_report.py
```
Success = all three clouds' logs land in one SIEM, a single identity's cross-cloud
activity is correlated into one timeline, and disabling the identity at the IdP
contains it everywhere.

## Cleanup
Stop the log connectors/ingestion, delete SIEM content if just for the lab, tear
down attack resources.

## Portfolio artifact (senior-level)
- A **cross-cloud attack timeline** (one identity, three clouds) from your SIEM.
- A **detection-coverage matrix** spanning AWS+Azure+GCP (technique → source →
  detection → response), mapped to MITRE ATT&CK.
- The **IdP-level containment** writeup — killing access in all clouds at once is
  the multi-cloud response lesson.

## Stretch goals
- Add **UEBA**/anomaly detection for the federated identity.
- Build a **single dashboard** across the three clouds.
- Show **mean-time-to-contain** with IdP-level disable vs per-cloud manual.
