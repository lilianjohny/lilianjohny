# Lab 06 — Detection & Response (GCP Capstone)

**Skills practiced:** Security Command Center · Cloud Audit Logs analysis ·
log-based threat hunting (Logs Explorer / BigQuery / Chronicle) · detection
engineering · automated response (Cloud Functions/Workflows) · incident triage &
writeup.
**Proves (JD):** ties the stack together — see and stop an attack across identity,
container, orchestration, tenant, and network layers.

## Objective
Turn on detection across everything you built, simulate a realistic attack chain
against your own sandbox, hunt it in the logs, automate a response, and produce
an incident report.

## Est. time / cost
3–4 h · **~$1–3** (SCC Premium if used + log storage; disable after).

## Prerequisites
- Labs 00–05 done.
- Toolkit: `../../cloud/detection/cloudtrail_hunt.md` (concept ref),
  `../../soc/incident/incident_report.py`, `../../soc/` scripts.

---

## Part A — Turn on the eyes
1. **Security Command Center** (Standard free; Premium for threat detection —
   Event Threat Detection, Container Threat Detection).
2. Confirm **Cloud Audit Logs** (Admin Activity always on; enable Data Access for
   tested services) and **GKE audit logs** (Lab 03), **VPC Flow Logs** (Lab 05).
3. Sink logs → **BigQuery** and/or **Chronicle** for hunting.

## Part B — Attack (against your own project)
1. **Identity abuse:** unusual API calls / a risky grant → **Event Threat
   Detection** finding.
2. **IAM escalation attempt:** try to grant `roles/owner` from a low-priv SA
   (denied by Lab 01) → find the deny in Cloud Audit Logs.
3. **Container/orchestration:** from a pod, hit the metadata server (blocked in
   Lab 03) and `kubectl get secrets -A` → GKE audit + Container Threat Detection.
4. **Cross-tenant:** attempt the Lab 04 cross-tenant read (denied) → find it.
5. **Exfil path:** attempt egress from the data subnet / a VPC-SC violation
   (blocked in Labs 04/05) → find the perimeter-violation log.

## Part C — Hunt (Logs Explorer / BigQuery)
Pivot on principal / caller IP / method. Examples (Logs Explorer):
```
logName:"cloudaudit.googleapis.com" protoPayload.methodName:"SetIamPolicy"
protoPayload.authorizationInfo.granted=false          # denied actions
resource.type="k8s_cluster" protoPayload.methodName:~"secrets"
```
Correlate an SCC finding → the exact audit events; build the **timeline**.

## Part D — Respond (automate)
1. **SCC finding / log-based alert** → **Pub/Sub** →
2. **Cloud Function / Workflow:** e.g. remove the offending IAM binding, disable
   the SA/key, quarantine the VM (isolate via firewall tag), or revoke a session.
3. Re-trigger and watch containment fire.
4. Map detections to a framework (`../../grc/compliance/crosswalk.py`, `../../soc/`).

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py   # structured IR report
```
Fill in detection → triage → scope → containment → eradication → lessons.

## Verify
Success = each simulated step produced evidence you found, at least one detection
auto-responds, and you have a written incident report with a timeline.

## Cleanup
Disable SCC Premium, stop extra audit/flow logs, delete sinks/functions, tear
down remaining lab resources.

## Portfolio artifact (the big one)
- Polished **incident report**: attack chain, data sources, timeline, finding
  screenshots, the automated response, remediation.
- **Detection-coverage matrix**: technique → data source → detection → response
  (map to MITRE ATT&CK for cloud/containers).
- This + the six labs = a cohesive GCP security portfolio.

## Stretch goals
- Detections as code (Terraform log-based metrics / SCC notifications) gated in CI.
- Hunt in **Chronicle**; build a dashboard.
- Re-run one attack with hardening reverted to show the control delta.
