# Lab 07 — CloudWatch Observability & Event-Driven Response

**Skills practiced:** CloudWatch metrics/logs/alarms · unified agent via SSM ·
metric filters · dashboards · EventBridge → Lambda → SNS · log retention.
**Proves (JD — KBR):** the CloudWatch-specialist core.

## Objective
Instrument a small fleet, alarm on what matters, build a dashboard, and wire an
alarm to automated remediation — then verify coverage with the toolkit.

## Est. time / cost
2–3 h · **~$0–1** (CloudWatch free tier + a t3.micro).

## Prerequisites
- Labs 00–01 done. Tool: `../../cloud/aws/cloudwatch_audit.py`.
- An EC2 instance with the **SSM + CloudWatchAgentServerPolicy** role attached.

---

## Part A — Build: collect metrics & logs via the unified agent
```bash
# 1. Store an agent config in SSM Parameter Store (collect mem/disk + a log file)
cat > /tmp/cwagent.json <<'EOF'
{"metrics":{"metrics_collected":{"mem":{"measurement":["mem_used_percent"]},
  "disk":{"measurement":["used_percent"],"resources":["*"]}}},
 "logs":{"logs_collected":{"files":{"collect_list":[
   {"file_path":"/var/log/messages","log_group_name":"/lab07/messages","retention_in_days":365}]}}}}
EOF
aws ssm put-parameter --name AmazonCloudWatch-lab07 --type String \
  --value file:///tmp/cwagent.json --overwrite

# 2. Install + start the agent on your instance(s) via SSM (self-healing fleet-wide)
IID=<your-instance-id>
aws ssm send-command --document-name AWS-ConfigureAWSPackage \
  --parameters 'action=Install,name=AmazonCloudWatchAgent' --instance-ids $IID
aws ssm send-command --document-name AmazonCloudWatch-ManageAgent \
  --parameters 'action=configure,mode=ec2,optionalConfigurationSource=ssm,optionalConfigurationLocation=AmazonCloudWatch-lab07,optionalRestart=yes' \
  --instance-ids $IID

# 3. Set retention on any existing log group (DoD-style 365 days)
aws logs put-retention-policy --log-group-name /lab07/messages --retention-in-days 365
```
**GUI:** Systems Manager → **Run Command** → `AWS-ConfigureAWSPackage`
(Install AmazonCloudWatchAgent) → then `AmazonCloudWatch-ManageAgent`. CloudWatch
→ **Log groups** → select → **Actions → Edit retention**.

## Part B — Attack / observe: the gaps
```bash
python3 ../../cloud/aws/cloudwatch_audit.py --min-retention-days 365
# Expect findings: log groups w/o retention, no metric filters, no alarms, no dashboard.
```

## Part C — Harden: metric filters, alarms, dashboard, auto-response
```bash
# 1. Metric filter + alarm on auth failures in the log
aws logs put-metric-filter --log-group-name /lab07/messages \
  --filter-name auth-failures --filter-pattern '"authentication failure"' \
  --metric-transformations metricName=AuthFailures,metricNamespace=Lab07,metricValue=1
aws sns create-topic --name lab07-alerts
aws cloudwatch put-metric-alarm --alarm-name lab07-auth-failures \
  --namespace Lab07 --metric-name AuthFailures --statistic Sum --period 300 \
  --threshold 5 --comparison-operator GreaterThanThreshold --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:$AWS_REGION:$ACCT_ID:lab07-alerts

# 2. An OS-metric alarm (high memory) — no silent alarms (every alarm has an action)
aws cloudwatch put-metric-alarm --alarm-name lab07-high-mem \
  --namespace CWAgent --metric-name mem_used_percent --statistic Average --period 300 \
  --threshold 90 --comparison-operator GreaterThanThreshold --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:$AWS_REGION:$ACCT_ID:lab07-alerts

# 3. A dashboard
cat > /tmp/dash.json <<EOF
{"widgets":[{"type":"metric","properties":{"metrics":[["CWAgent","mem_used_percent"]],
 "title":"Memory","region":"$AWS_REGION"}}]}
EOF
aws cloudwatch put-dashboard --dashboard-name lab07 --dashboard-body file:///tmp/dash.json

# 4. Event-driven remediation: EventBridge → Lambda (restart svc / isolate)
#    (create the Lambda, then:)
aws events put-rule --name lab07-alarm-rule \
  --event-pattern '{"source":["aws.cloudwatch"],"detail-type":["CloudWatch Alarm State Change"]}'
# aws events put-targets --rule lab07-alarm-rule --targets Id=1,Arn=<lambda-arn>
```
**GUI:** CloudWatch → **Log groups → Metric filters → Create**; **Alarms →
Create alarm** (add an SNS action — never leave it empty); **Dashboards →
Create dashboard**; EventBridge → **Rules → Create** (CloudWatch Alarm State
Change) → target Lambda.

## Part D — Verify
```bash
python3 ../../cloud/aws/cloudwatch_audit.py --min-retention-days 365
# Expect: retention OK, metric filters present, alarms have actions, dashboard present,
# SNS + EventBridge wired → exit 0.
```

## Cleanup
```bash
aws cloudwatch delete-alarms --alarm-names lab07-auth-failures lab07-high-mem
aws cloudwatch delete-dashboards --dashboard-names lab07
aws logs delete-metric-filter --log-group-name /lab07/messages --filter-name auth-failures
aws logs delete-log-group --log-group-name /lab07/messages
aws events delete-rule --name lab07-alarm-rule
aws sns delete-topic --topic-arn arn:aws:sns:$AWS_REGION:$ACCT_ID:lab07-alerts
aws ssm delete-parameter --name AmazonCloudWatch-lab07
```

## Portfolio artifact
- A **dashboard screenshot** + the alarm/metric-filter definitions (as code).
- The **event-driven remediation** diagram (Alarm → EventBridge → Lambda → SNS).
- `cloudwatch_audit.py` before (gaps) → after (clean).

## Stretch goals
- Deploy the agent fleet-wide with an **SSM State Manager association**.
- Add a **composite alarm** to cut noise.
- Send alarms to an ITSM tool (ServiceNow/Jira).
