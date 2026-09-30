# Cloud Threat Hunting — query pack

Ready-to-adapt detection queries for the three clouds' audit logs. Run against
your log store (Athena/CloudWatch Logs Insights, Log Analytics/KQL, BigQuery).
Tune account IDs, time windows, and known-good principals before use.

> These hunt for **attacker behavior**, not just misconfig. Pair with the
> enablement checks (`aws_detection_coverage.py`) so the logs actually exist.

## AWS — CloudTrail (Athena)

**Root account usage (should be near-zero):**
```sql
SELECT eventtime, eventname, sourceipaddress, useragent
FROM cloudtrail_logs
WHERE useridentity.type = 'Root'
  AND eventtime > date_add('day', -7, now());
```

**Disabling/deleting security controls (defense evasion):**
```sql
SELECT eventtime, useridentity.arn, eventname, requestparameters
FROM cloudtrail_logs
WHERE eventname IN (
  'StopLogging','DeleteTrail','UpdateTrail',
  'DeleteDetector','DisassociateFromMasterAccount',
  'DisableSecurityHub','DeleteConfigurationRecorder','StopConfigurationRecorder')
  AND eventtime > date_add('day', -14, now());
```

**IAM persistence (new keys, users, or trust-policy changes):**
```sql
SELECT eventtime, useridentity.arn, eventname, requestparameters
FROM cloudtrail_logs
WHERE eventname IN (
  'CreateAccessKey','CreateUser','CreateLoginProfile',
  'AttachUserPolicy','PutUserPolicy','UpdateAssumeRolePolicy','CreateRole')
  AND eventtime > date_add('day', -7, now());
```

**Console logins without MFA / from new geographies:**
```sql
SELECT eventtime, useridentity.arn, sourceipaddress,
       additionaleventdata
FROM cloudtrail_logs
WHERE eventname = 'ConsoleLogin'
  AND json_extract_scalar(additionaleventdata, '$.MFAUsed') = 'No';
```

## Azure — Activity / Sign-in logs (KQL, Log Analytics)

**Privileged role assignments:**
```kql
AuditLogs
| where OperationName has "Add member to role"
| where Result == "success"
| project TimeGenerated, InitiatedBy, TargetResources
```

**Risky sign-ins / legacy auth:**
```kql
SigninLogs
| where RiskLevelDuringSignIn in ("high","medium")
   or ClientAppUsed in ("Other clients","IMAP4","POP3","SMTP")
| project TimeGenerated, UserPrincipalName, IPAddress, AppDisplayName, RiskLevelDuringSignIn
```

**NSG / firewall changes (defense evasion):**
```kql
AzureActivity
| where OperationNameValue has_any ("networkSecurityGroups/write","firewallRules/write")
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup
```

## GCP — Cloud Audit Logs (BigQuery)

**Service-account key creation (persistence):**
```sql
SELECT timestamp, protopayload_auditlog.authenticationInfo.principalEmail AS actor,
       protopayload_auditlog.methodName
FROM `PROJECT.DATASET.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName = 'google.iam.admin.v1.CreateServiceAccountKey'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY);
```

**IAM policy changes granting broad/primitive roles:**
```sql
SELECT timestamp, protopayload_auditlog.authenticationInfo.principalEmail AS actor,
       protopayload_auditlog.resourceName
FROM `PROJECT.DATASET.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName = 'SetIamPolicy'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY);
```

**Logging sink deletion (evasion):**
```sql
SELECT timestamp, protopayload_auditlog.authenticationInfo.principalEmail AS actor
FROM `PROJECT.DATASET.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName = 'google.logging.v2.ConfigServiceV2.DeleteSink';
```

## Mapping to MITRE ATT&CK for Cloud
- Root/priv use, new keys/users → **Persistence (T1098)**, **Privilege Escalation**
- StopLogging / DeleteTrail / sink deletion → **Defense Evasion (T1562 Impair Defenses)**
- Risky sign-ins, legacy auth → **Initial Access / Valid Accounts (T1078)**
- SetIamPolicy to broad roles → **Privilege Escalation (T1098)**
