# Lab 06 — Detection & Response (Capstone)

**Skills practiced:** GuardDuty · CloudTrail analysis · log-based threat hunting ·
detection engineering · automated response (EventBridge → Lambda/SSM) · incident
triage & writeup.
**Proves (JD):** ties the whole stack together — you can *see* and *stop* an
attack across identity, container, orchestration, tenant, and network layers.

## Objective
Turn on detection across everything you built, **simulate a realistic attack
chain** against your own sandbox, hunt it in the logs, and build an **automated
response**. Finish with an incident report — the artifact that most impresses in
a portfolio.

## Est. time / cost
3–4 h · **~$1–3** (GuardDuty + log storage; disable after).

## Prerequisites
- Labs 00–05 done (you'll attack the things you hardened).
- Toolkit: `../../cloud/detection/aws_detection_coverage.py`,
  `../../cloud/detection/cloudtrail_hunt.md`, `../../soc/incident/incident_report.py`.

---

## Part A — Build: turn on the eyes
1. **GuardDuty** (with S3, EKS, Malware, and RDS protections as available).
2. Confirm **CloudTrail** (Lab 00) is all-Region + log file validation on.
3. **VPC Flow Logs** (Lab 05) and **EKS audit logs** (Lab 03) flowing.
4. Centralize to CloudWatch Logs / an S3 log bucket.
5. Baseline coverage:
   ```bash
   python3 ../../cloud/detection/aws_detection_coverage.py
   ```

## Part B — Attack: run a realistic chain (against your own account)
Do each, then find it in the logs:
1. **Recon / cred abuse:** call APIs from an unusual context; disable/anonymize
   an S3 bucket setting → GuardDuty `Policy`/`Discovery` findings.
2. **IAM escalation attempt:** try to attach an admin policy from a low-priv role
   (should be denied by Lab 01 boundaries) — find the `AccessDenied` in CloudTrail.
3. **Container/orchestration:** from a pod, hit IMDS (blocked in Lab 03) and try
   `kubectl get secrets -A` → EKS audit + GuardDuty EKS finding.
4. **Cross-tenant:** attempt the Lab 04 cross-tenant read (denied) — find it.
5. **Exfil path:** attempt egress from a data subnet (blocked in Lab 05) — find it
   in Flow Logs.

## Part C — Hunt: find it in the logs
Work through `../../cloud/detection/cloudtrail_hunt.md` queries:
- Who did what, from where, when? Pivot on principal, source IP, user agent.
- Correlate a GuardDuty finding → the exact CloudTrail events behind it.
- Write the **attack timeline** from the evidence.

## Part D — Respond: automate it
1. **EventBridge rule** on high-severity GuardDuty findings →
2. **Lambda/SSM automation:** e.g., revoke the offending role's sessions
   (attach a deny-all boundary), isolate an instance's SG, or disable a key.
3. Test it: trigger the finding again, watch the automated containment fire.
4. Map your detections to a framework (`../../soc/`, `../../grc/compliance/crosswalk.py`).

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py   # generate a structured IR report
```
Fill in: detection → triage → scope → containment → eradication → lessons.

## Verify
Success = every simulated step produced evidence you found, at least one
detection auto-responds, and you have a written incident report with a timeline.

## Cleanup
Disable GuardDuty, stop flow/audit logs if not needed, empty/delete log buckets,
remove EventBridge rules + Lambda. Tear down any remaining lab resources.

## Portfolio artifact (the big one)
- A polished **incident report**: attack chain, detection sources, timeline,
  screenshots of findings, the automated response, and remediation.
- A **detection-coverage matrix**: attack technique → data source → detection →
  response (map to MITRE ATT&CK for cloud/containers).
- This report + the six labs' artifacts = a cohesive AWS security portfolio.

## Stretch goals
- Recreate a couple of detections as **detection-as-code** and gate them in CI.
- Add **Security Hub** to aggregate findings; write an automation rule.
- Redo the hunt in a **SIEM** (OpenSearch / your tool) and build a dashboard.
- Repeat one attack after **every** hardening was reverted, to show the delta the
  controls make — great "why this matters" slide.
