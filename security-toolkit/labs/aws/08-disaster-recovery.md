# Lab 08 — Disaster Recovery, RTO/RPO & DR Exercises

**Skills practiced:** AWS Backup · cross-region copy · RTO/RPO alignment · DR
exercise execution & documentation · failover verification.
**Proves (JD — KBR):** configure, test, validate, and document recovery aligned
to documented RTO/RPO.

## Objective
Protect a workload with AWS-native DR, declare its RTO/RPO, and **prove the
objectives are achievable** with a real DR exercise — verified with the toolkit.

## Est. time / cost
3–4 h · **~$1–3** (Backup storage + cross-region copy + a brief restore).

## Prerequisites
- Labs 00, 05 done. A small workload (an EC2 instance with an EBS volume; tag it
  `Backup=lab08`). Tool: `../../cloud/dr/dr_readiness.py`.

---

## Part A — Build: declare objectives & protect
```bash
# 1. DR register (copy the example and edit for your systems)
cp ../../cloud/dr/dr_register.example.csv /tmp/dr_register.csv
# edit: set tier, rto_hours, rpo_hours, backup_frequency_hours, cross_region, last_dr_test_days

# 2. A backup vault + plan (hourly-ish schedule; cross-region copy for mission tier)
aws backup create-backup-vault --backup-vault-name lab08-vault
DEST_REGION=us-west-2
aws backup create-backup-vault --backup-vault-name lab08-vault-dr --region $DEST_REGION
cat > /tmp/plan.json <<EOF
{"BackupPlanName":"lab08-plan","Rules":[{
  "RuleName":"hourly","TargetBackupVaultName":"lab08-vault",
  "ScheduleExpression":"cron(0 * ? * * *)","StartWindowMinutes":60,
  "Lifecycle":{"DeleteAfterDays":7},
  "CopyActions":[{"DestinationBackupVaultArn":"arn:aws:backup:$DEST_REGION:$ACCT_ID:backup-vault:lab08-vault-dr"}]}]}
EOF
PLAN_ID=$(aws backup create-backup-plan --backup-plan file:///tmp/plan.json --query BackupPlanId --output text)

# 3. Select resources by tag
cat > /tmp/sel.json <<EOF
{"BackupSelection":{"SelectionName":"lab08-sel","IamRoleArn":"arn:aws:iam::$ACCT_ID:role/service-role/AWSBackupDefaultServiceRole",
 "ListOfTags":[{"ConditionType":"STRINGEQUALS","ConditionKey":"Backup","ConditionValue":"lab08"}]}}
EOF
aws backup create-backup-selection --backup-plan-id "$PLAN_ID" --backup-selection file:///tmp/sel.json
```
**GUI:** Console → **AWS Backup → Backup plans → Create plan** → schedule + a
**Copy to another region** action → **Assign resources** by tag. (Create the
`AWSBackupDefaultServiceRole` first if prompted.)

## Part B — Attack / observe: can the objective be met?
```bash
python3 ../../cloud/dr/dr_readiness.py --register /tmp/dr_register.csv
# Flags where backup interval > RPO, and mission systems without cross-region copy.
# Fix the register / plan until this offline check is clean.
```

## Part C — Operate: run a DR exercise
```bash
# On-demand backup now (don't wait for the schedule):
aws backup start-backup-job --backup-vault-name lab08-vault \
  --resource-arn arn:aws:ec2:$AWS_REGION:$ACCT_ID:instance/<instance-id> \
  --iam-role-arn arn:aws:iam::$ACCT_ID:role/service-role/AWSBackupDefaultServiceRole
# List recovery points, then restore in the DR region and TIME it (measure RTO/RPO):
aws backup list-recovery-points-by-backup-vault --backup-vault-name lab08-vault-dr --region $DEST_REGION
# aws backup start-restore-job --recovery-point-arn <arn> --metadata ... --iam-role-arn ... --region $DEST_REGION
```
Verify integrity (app comes up, data consistent, monitoring works in the DR
Region — ties to Lab 07). **Document** steps, timings, gaps, corrective actions;
set `last_dr_test_days=0` in the register.

## Part D — Verify
```bash
python3 ../../cloud/dr/dr_readiness.py --register /tmp/dr_register.csv --aws --region $AWS_REGION
# Expect: RPO met for all, cross-region present for mission, live Backup plan found → exit 0.
```

## Cleanup
```bash
aws backup delete-backup-selection --backup-plan-id "$PLAN_ID" --selection-id $(aws backup list-backup-selections --backup-plan-id "$PLAN_ID" --query 'BackupSelectionsList[0].SelectionId' --output text)
aws backup delete-backup-plan --backup-plan-id "$PLAN_ID"
# delete recovery points in both vaults (mind retention), then:
aws backup delete-backup-vault --backup-vault-name lab08-vault
aws backup delete-backup-vault --backup-vault-name lab08-vault-dr --region $DEST_REGION
```

## Portfolio artifact
- A **DR exercise report**: objectives vs measured RTO/RPO, timeline, evidence,
  gaps, corrective actions.
- The **DR register** + `dr_readiness.py` output (gaps → aligned).
- A recovery-architecture diagram (primary → cross-region recovery).

## Stretch goals
- Add **pilot-light vs warm-standby** and compare cost vs RTO.
- Automate the drill (Step Functions / SSM runbook) and re-measure RTO.
- Kill the primary and run an unplanned failover.
