# Lab 07 — CloudWatch Observability & Event-Driven Response

**Skills practiced:** CloudWatch metrics/logs/alarms · unified agent deployment ·
metric filters · dashboards · EventBridge → Lambda → SNS event-driven
remediation · log retention for compliance.
**Proves (JD — KBR):** the CloudWatch-specialist core — monitoring, alerting,
dashboards, and automated response for DoD/Navy AvPLM systems.

## Objective
Stand up real observability on a small fleet: collect OS metrics/logs with the
CloudWatch unified agent, alarm on the signals that matter, build a dashboard,
and wire an alarm to automated remediation. Then verify coverage with the
toolkit's auditor.

## Est. time / cost
2–3 h · **~$0–1** (a couple of t3.micro + CloudWatch free tier; tear down).

## Prerequisites
- Labs 00–01 done. AWS CLI v2. 1–2 EC2 instances (Linux and/or Windows).
- Tool: `../../cloud/aws/cloudwatch_audit.py`.

---

## Part A — Build: collect metrics & logs
1. Attach an instance role allowing CloudWatch agent + SSM.
2. Install/deploy the **CloudWatch unified agent** via **SSM** (State Manager
   association so it self-heals across the fleet):
   ```bash
   aws ssm send-command --document-name AWS-ConfigureAWSPackage \
     --parameters 'action=Install,name=AmazonCloudWatchAgent' --targets ...
   ```
3. Push an agent config (collect memory, disk, and `/var/log/*` or Windows event
   logs) to SSM Parameter Store; start the agent.
4. Set **log group retention** explicitly (e.g. 365 days for DoD-style retention).

## Part B — Attack / observe: the gaps
1. Before alarms exist, kill a service / fill a disk on an instance — nothing
   fires. That's the point: metrics without alarms = blind.
2. Run the auditor to see the gaps concretely:
   ```bash
   python3 ../../cloud/aws/cloudwatch_audit.py --min-retention-days 365
   ```
   Expect findings: log groups with no retention, no metric filters, no alarms.

## Part C — Harden: alarms, dashboard, automated response
1. **Metric filters + alarms** on log patterns (e.g. `ERROR`, failed logons,
   `sshd` auth failures) and on OS metrics (CPU, mem, disk, StatusCheckFailed).
2. Give every alarm an **action** (SNS topic) — no silent alarms.
3. Build a **dashboard** with KPIs: instance health, disk/mem, log error rate,
   and a DR-readiness widget (last backup age, replication lag).
4. **Event-driven remediation:** EventBridge rule on a high-severity alarm →
   **Lambda** (e.g. restart the service / isolate) → **SNS** notify → (optional)
   an ITSM webhook.
5. Set retention on **all** log groups to meet the retention policy.

## Part D — Verify
```bash
python3 ../../cloud/aws/cloudwatch_audit.py --min-retention-days 365
# Expect: retention OK, metric filters present, alarms with actions, dashboard present,
# SNS + EventBridge wired → exit 0.
```
Trigger an alarm again and watch the Lambda remediation + SNS notification fire.

## Cleanup
Delete alarms, dashboards, EventBridge rules, Lambda, SNS topics, log groups, and
the EC2 instances.

## Portfolio artifact
- A **dashboard screenshot** + the alarm/metric-filter definitions (as code).
- The **event-driven remediation** diagram (Alarm → EventBridge → Lambda → SNS).
- `cloudwatch_audit.py` output before (gaps) → after (clean).

## Stretch goals
- Deploy the agent fleet-wide with a **State Manager association** so new
  instances are auto-instrumented.
- Add a **composite alarm** to cut alert noise.
- Send alarms to an ITSM tool (ServiceNow/Jira) for the incident-workflow story.
