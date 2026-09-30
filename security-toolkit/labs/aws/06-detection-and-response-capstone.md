# Lab 06 — Detection & Response (Capstone)

**Skills practiced:** GuardDuty · CloudTrail analysis · log-based hunting ·
detection engineering · automated response (EventBridge → Lambda) · IR writeup.
**Proves (JD):** see and stop an attack across identity, container, orchestration,
tenant, and network layers.

## Objective
Turn on detection, simulate a realistic attack chain against your own sandbox,
hunt it in the logs, build an automated response, and write an incident report.

## Est. time / cost
3–4 h · **~$1–3** (GuardDuty + logs; disable after).

## Prerequisites
- Labs 00–05 done. Tools: `../../cloud/detection/aws_detection_coverage.py`,
  `../../cloud/detection/cloudtrail_hunt.md`, `../../soc/incident/incident_report.py`.

---

## Part A — Turn on the eyes
```bash
DET=$(aws guardduty create-detector --enable --query DetectorId --output text)
# (S3, EKS, Malware protections are on by default in current GuardDuty)
aws cloudtrail get-trail-status --name org-trail --query IsLogging   # from Lab 00: true
python3 ../../cloud/detection/aws_detection_coverage.py
```
**GUI:** Console → **GuardDuty → Enable GuardDuty**; **CloudTrail → Trails**
confirm `org-trail` is logging; **Config** on from Lab 00.

## Part B — Attack (against your own account) — generate real findings
```bash
# GuardDuty ships sample findings so you can build detection/response safely:
aws guardduty create-sample-findings --detector-id "$DET" \
  --finding-types "UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom" \
                  "Discovery:S3/AnomalousBehavior" \
                  "CredentialAccess:IAMUser/AnomalousBehavior"
# Real denied action to find in CloudTrail (assume a low-priv role and try admin):
aws iam attach-role-policy --role-name app-reader --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>&1 | grep -i denied || true
```
Also re-run, from earlier labs: pod → IMDS (Lab 03, blocked), cross-tenant read
(Lab 04, denied), data-subnet egress (Lab 05, blocked) — each leaves a trail.

## Part C — Hunt: find it in the logs
Use `../../cloud/detection/cloudtrail_hunt.md`. Quick starts:
```bash
aws guardduty list-findings --detector-id "$DET" --query 'FindingIds' --output text | \
  xargs aws guardduty get-findings --detector-id "$DET" --finding-ids

# CloudTrail: who did what (via Athena, or lookup-events for recent):
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AttachRolePolicy \
  --query 'Events[].{User:Username,Time:EventTime}' --output table
```
Build the **attack timeline** from the correlated events.

## Part D — Respond: automate it
```bash
# EventBridge rule on high-severity GuardDuty findings → SNS/Lambda
aws sns create-topic --name lab06-alerts
cat > /tmp/pattern.json <<'EOF'
{"source":["aws.guardduty"],"detail-type":["GuardDuty Finding"],"detail":{"severity":[{"numeric":[">=",7]}]}}
EOF
aws events put-rule --name lab06-gd-high --event-pattern file:///tmp/pattern.json
aws events put-targets --rule lab06-gd-high \
  --targets "Id=1,Arn=arn:aws:sns:$AWS_REGION:$ACCT_ID:lab06-alerts"
```
Attach a **Lambda** target that revokes the offending role's sessions / isolates
an instance SG (write the function; template in `../../cloud/detection/`).
**GUI:** **EventBridge → Rules → Create rule** → event pattern (GuardDuty, severity
≥ 7) → target = Lambda/SNS.

## Part E — Report
```bash
python3 ../../soc/incident/incident_report.py    # structured IR report
# Fill: detection → triage → scope → containment → eradication → lessons
```

## Verify
Success = each simulated step produced evidence you found, at least one detection
auto-responds, and you have a written incident report with a timeline.

## Cleanup
```bash
aws events remove-targets --rule lab06-gd-high --ids 1
aws events delete-rule --name lab06-gd-high
aws sns delete-topic --topic-arn arn:aws:sns:$AWS_REGION:$ACCT_ID:lab06-alerts
aws guardduty delete-detector --detector-id "$DET"
aws iam detach-role-policy --role-name app-reader --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true
```

## Portfolio artifact (the big one)
- A polished **incident report**: attack chain, detection sources, timeline,
  finding screenshots, the automated response, remediation.
- A **detection-coverage matrix**: technique → data source → detection → response
  (map to MITRE ATT&CK for cloud/containers).
- This + the six labs' artifacts = a cohesive AWS security portfolio.

## Stretch goals
- Recreate a couple of detections as **detection-as-code**, gate them in CI.
- Add **Security Hub** to aggregate findings; write an automation rule.
- Re-run one attack after reverting a hardening to show the control delta.
