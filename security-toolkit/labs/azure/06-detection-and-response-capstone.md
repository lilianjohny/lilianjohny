# Lab 06 — Detection & Response (Azure Capstone)

**Skills practiced:** Defender for Cloud · Microsoft Sentinel · KQL threat
hunting · detection engineering · automated response (Logic App playbooks) ·
incident triage & writeup.
**Proves (JD):** ties the stack together — see and stop an attack across identity,
container, orchestration, tenant, and network layers.

## Objective
Turn on detection across everything you built, simulate a realistic attack chain
against your own sandbox, hunt it with KQL, automate a response, and produce an
incident report.

## Est. time / cost
3–4 h · **~$1–3** (Defender plans + Sentinel ingestion; disable after).

## Prerequisites
- Labs 00–05 done.
- Toolkit: `../../cloud/detection/aws_detection_coverage.py` (concept ref),
  `../../soc/incident/incident_report.py`, `../../soc/` ConMon/logging scripts.

---

## Part A — Turn on the eyes
1. **Defender for Cloud** plans (Servers, Containers, Storage, Key Vault, etc.).
2. **Microsoft Sentinel** on your Log Analytics workspace; connect data:
   **Entra sign-in/audit**, **Activity Log**, **AKS/diagnostic**, **NSG flow logs**.
3. Confirm all Lab 00–05 logs are flowing to the workspace.

## Part B — Attack (against your own tenant)
1. **Identity abuse:** sign in from odd context / impossible travel; attempt a
   privileged role activation outside policy → Entra + Defender alerts.
2. **RBAC escalation attempt:** try to assign Owner from a low-priv identity
   (denied by Lab 01) → find the deny in Activity Log.
3. **Container/orchestration:** from a pod, hit IMDS (blocked in Lab 03) and try
   `kubectl get secrets -A` → AKS audit + Defender for Containers alert.
4. **Cross-tenant:** attempt the Lab 04 cross-tenant read (denied) → find it.
5. **Exfil path:** attempt egress from the data subnet (blocked in Lab 05) → find
   it in NSG flow logs.

## Part C — Hunt with KQL
In Sentinel, pivot on principal / IP / operation. Examples:
```kusto
SigninLogs | where ResultType != 0 | summarize count() by IPAddress, UserPrincipalName
AzureActivity | where OperationNameValue has "roleAssignments/write" | project Caller, ActivityStatusValue, _ResourceId
AzureDiagnostics | where Category == "kube-audit" | where log_s has "secrets"
```
Correlate a Defender alert → the exact events behind it; build the **timeline**.

## Part D — Respond (automate)
1. **Analytics rule** on the high-severity signal →
2. **Automation rule → Logic App playbook:** e.g. disable the user, revoke
   sessions, isolate the NIC/NSG, or rotate a key.
3. Re-trigger and watch containment fire.
4. Map detections to a framework (`../../grc/compliance/crosswalk.py`, `../../soc/`).

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py   # structured IR report
```
Fill in detection → triage → scope → containment → eradication → lessons.

## Verify
Success = each simulated step produced evidence you found in KQL, at least one
detection auto-responds, and you have a written incident report with a timeline.

## Cleanup
Disable Defender plans + Sentinel, stop diagnostic settings if unneeded, delete
the workspace/playbooks, tear down remaining lab resources.

## Portfolio artifact (the big one)
- Polished **incident report**: attack chain, data sources, timeline, alert
  screenshots, the playbook, remediation.
- **Detection-coverage matrix**: technique → data source → detection → response
  (map to MITRE ATT&CK for cloud/containers).
- This + the six labs = a cohesive Azure security portfolio.

## Stretch goals
- Detections as **analytics-rules-as-code** (ARM/Bicep) gated in CI.
- Build a **Sentinel workbook** dashboard.
- Re-run one attack with hardening reverted to show the control delta.
