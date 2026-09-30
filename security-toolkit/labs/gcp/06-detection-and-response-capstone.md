# Lab 06 — Detection & Response (GCP Capstone)

**Skills practiced:** Security Command Center · Cloud Audit Logs · log-based
hunting (Logs Explorer / BigQuery) · detection engineering · automated response
(Pub/Sub → Cloud Functions) · IR writeup.
**Proves (JD):** see and stop an attack across identity, container, orchestration,
tenant, and network layers.

## Objective
Turn on detection, simulate a cross-layer attack against your own project, hunt
it in the logs, automate a response, and write an incident report.

## Est. time / cost
3–4 h · **~$1–3** (SCC Premium if used + logs; disable after).

## Prerequisites
- Labs 00–05 done. Tools: `../../cloud/detection/cloudtrail_hunt.md` (concept),
  `../../soc/incident/incident_report.py`.

---

## Part A — Turn on the eyes
```bash
# SCC (Standard free; Premium adds Event/Container Threat Detection)
gcloud scc settings services enable --service=SECURITY_CENTER --organization=<ORG_ID> 2>/dev/null \
  || echo "Console: Security → Security Command Center → enable"
# Ensure Data Access logs on for tested services (Lab 00). Sink audit logs to BigQuery:
bq --location=US mk -d lab06_logs 2>/dev/null || true
gcloud logging sinks create lab06-bq bigquery.googleapis.com/projects/$PROJECT/datasets/lab06_logs \
  --log-filter='logName:"cloudaudit.googleapis.com"'
```
Confirm GKE audit logs (Lab 03) and VPC Flow Logs (Lab 05) are flowing.

## Part B — Attack (against your own project)
1. **Identity:** unusual API calls / a risky grant → Event Threat Detection.
2. **IAM escalation:** try to grant `roles/owner` from a low-priv SA (denied by
   Lab 01) → find the deny in Cloud Audit Logs.
3. **Container/orchestration:** pod → metadata server (blocked in Lab 03) +
   `kubectl get secrets -A` → GKE audit + Container Threat Detection.
4. **Cross-tenant:** attempt the Lab 04 cross-tenant read (denied).
5. **Exfil / perimeter:** attempt a VPC-SC violation (blocked in Lab 04/05).

## Part C — Hunt (Logs Explorer / BigQuery)
```
# Logs Explorer queries:
logName:"cloudaudit.googleapis.com" protoPayload.methodName:"SetIamPolicy"
protoPayload.authorizationInfo.granted=false
resource.type="k8s_cluster" protoPayload.methodName:~"secrets"
```
```sql
-- BigQuery over the sink:
SELECT protopayload_auditlog.authenticationInfo.principalEmail, protopayload_auditlog.methodName, timestamp
FROM `PROJECT.lab06_logs.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName LIKE '%SetIamPolicy%' ORDER BY timestamp DESC;
```
Correlate an SCC finding → the exact audit events; build the **timeline**.

## Part D — Respond (automate)
```bash
# SCC finding / log alert → Pub/Sub → Cloud Function (remove binding / disable SA / isolate VM)
gcloud pubsub topics create lab06-findings
# Create a log-based alert or SCC notification to the topic, then deploy a function:
# gcloud functions deploy respond --trigger-topic lab06-findings --runtime python312 --entry-point handle
```
**Console:** **SCC → Settings → Continuous Exports → Pub/Sub**; **Cloud
Functions** subscribes and remediates. Map detections with
`../../grc/compliance/crosswalk.py`.

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py    # structured IR report
```

## Verify
Each simulated step produced evidence you found, at least one detection
auto-responds, and you have a written incident report with a timeline.

## Cleanup
```bash
gcloud logging sinks delete lab06-bq --quiet
bq rm -r -d -f $PROJECT:lab06_logs
gcloud pubsub topics delete lab06-findings --quiet
# Disable SCC Premium if enabled; tear down remaining lab resources.
```

## Portfolio artifact (the big one)
- Polished **incident report**; a **detection-coverage matrix** (technique →
  source → detection → response, mapped to MITRE ATT&CK); the Cloud Function.

## Stretch goals
- Detections as code (Terraform log-based metrics / SCC notifications) in CI.
- Hunt in **Chronicle**; build a dashboard.
- Re-run one attack with hardening reverted to show the control delta.
