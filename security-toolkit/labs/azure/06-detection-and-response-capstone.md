# Lab 06 — Detection & Response (Azure Capstone)

**Skills practiced:** Defender for Cloud · Microsoft Sentinel · KQL hunting ·
detection engineering · automated response (Logic App playbooks) · IR writeup.
**Proves (JD):** see and stop an attack across identity, container, orchestration,
tenant, and network layers.

## Objective
Turn on detection, simulate a cross-layer attack against your own tenant, hunt it
with KQL, automate a response, and write an incident report.

## Est. time / cost
3–4 h · **~$1–3** (Defender plans + Sentinel ingestion; disable after).

## Prerequisites
- Labs 00–05 done. Tools: `../../soc/incident/incident_report.py`, `../../soc/`.

---

## Part A — Turn on the eyes
```bash
# Defender plans on the subscription
az security pricing create -n VirtualMachines --tier Standard
az security pricing create -n StorageAccounts --tier Standard
az security pricing create -n KeyVaults --tier Standard
az security pricing create -n Containers --tier Standard
# Sentinel onto the Lab 00 workspace
WS=$(az monitor log-analytics workspace show -g rg-security -n lab-law --query id -o tsv)
az sentinel onboarding-state create -g rg-security --workspace-name lab-law -n default 2>/dev/null \
  || echo "Portal: Microsoft Sentinel → Add → select lab-law"
```
Connect data: **Entra sign-in/audit**, **Activity Log**, **AKS/diagnostic** (Lab
03), **NSG flow logs** (Lab 05). **Portal:** Sentinel → **Data connectors**.

## Part B — Attack (against your own tenant)
1. **Identity:** sign in from an odd context / attempt a privileged PIM activation
   outside policy → Entra + Defender alerts.
2. **RBAC escalation:** try to assign Owner from a low-priv identity (denied by
   Lab 01) → find the deny in Activity Log.
3. **Container/orchestration:** pod → IMDS (blocked in Lab 03) + `kubectl get
   secrets -A` → AKS audit + Defender for Containers.
4. **Cross-tenant:** attempt the Lab 04 cross-tenant read (denied).
5. **Exfil:** egress from the data subnet (blocked in Lab 05) → NSG flow logs.

## Part C — Hunt with KQL (Sentinel → Logs)
```kusto
SigninLogs | where ResultType != 0 | summarize count() by IPAddress, UserPrincipalName
AzureActivity | where OperationNameValue has "roleAssignments/write" | project Caller, ActivityStatusValue, _ResourceId
AzureDiagnostics | where Category == "kube-audit" | where log_s has "secrets"
```
Correlate a Defender alert → the exact events; build the **timeline**.

## Part D — Respond (automate)
**Portal:** Sentinel → **Analytics → Create rule** on the high-severity signal →
**Automation → Add → Playbook (Logic App)**: disable the user / revoke sessions /
isolate the NIC via NSG. Re-trigger and watch containment fire. Map detections
with `../../grc/compliance/crosswalk.py`.

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py    # structured IR report
```

## Verify
Each simulated step produced evidence you found in KQL, at least one detection
auto-responds, and you have a written incident report with a timeline.

## Cleanup
```bash
for p in VirtualMachines StorageAccounts KeyVaults Containers; do az security pricing create -n $p --tier Free; done
# Remove Sentinel/playbooks and the workspace if only for the lab.
```

## Portfolio artifact (the big one)
- Polished **incident report**; a **detection-coverage matrix** (technique →
  source → detection → response, mapped to MITRE ATT&CK); the Logic App playbook.

## Stretch goals
- Analytics-rules-as-code (ARM/Bicep) gated in CI.
- A **Sentinel workbook** dashboard.
- Re-run one attack with hardening reverted to show the control delta.
