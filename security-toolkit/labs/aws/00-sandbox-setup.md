# Lab 00 — Sandbox Setup & Guardrails

**Skills practiced:** account hardening · budget/cost guardrails · IAM Identity
Center · secure CLI access (no long-lived keys) · baseline logging.
**Proves (JD):** "securing … deployments from construction" — you secure the
foundation *before* building on it.

## Objective
Stand up a **safe, isolated AWS sandbox**: an admin identity that isn't root, a
low-privilege identity to test with, budget alarms, org-level guardrails, and
audit logging.

## Est. time / cost
45–60 min · **~$0** (all free-tier / no-cost services).

## Prerequisites
- A **dedicated AWS account** you own.
- AWS CLI v2 installed (`aws --version`) — install:
  ```bash
  # macOS
  brew install awscli
  # Linux
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
  unzip awscliv2.zip && sudo ./aws/install
  aws --version   # expect aws-cli/2.x
  ```
- A FIDO2 security key or an authenticator app for MFA.

> Set these once; later labs reuse them:
> ```bash
> export AWS_REGION=us-east-1        # your home region
> export ACCT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
> ```

---

## Part A — Lock down the root user  *(GUI — root can't be done by CLI)*
1. Sign in at **https://console.aws.amazon.com/** as **root** (email + password)
   — the only time you should.
2. **Enable MFA on root:** top-right account name → **Security credentials** →
   **Multi-factor authentication (MFA)** → **Assign MFA device** → choose
   **Security Key** (FIDO2) or **Authenticator app** → follow prompts.
3. **Remove root access keys:** same **Security credentials** page → **Access
   keys** section → if any exist, **Actions → Delete**.
4. **Set contacts:** top-right → **Account** → **Alternate Contacts** → add a
   **Security** contact.

> Why: root is unrestricted. From here you never use it again.

## Part B — IAM Identity Center (your day-to-day access)
1. **Enable it (GUI):** Console → search **IAM Identity Center** → **Enable** →
   (accept the default, or **Enable with AWS Organizations** if prompted).
2. **Create permission sets (GUI):** IAM Identity Center → **Permission sets** →
   **Create permission set** → **Predefined** → `AdministratorAccess` → name it
   `AdminForLabs` → **Create**. Repeat with `ReadOnlyAccess` → name `ReadOnlyTester`.
3. **Create your user (GUI):** IAM Identity Center → **Users** → **Add user** →
   fill username/email → **Next** → (skip groups) → **Add user**. Accept the
   email invite and set a password + register MFA.
4. **Assign access (GUI):** IAM Identity Center → **AWS accounts** → select your
   account → **Assign users or groups** → pick your user → select **both**
   permission sets → **Submit**.
5. **Find your start URL:** IAM Identity Center → **Settings** → copy the
   **AWS access portal URL** (like `https://d-xxxx.awsapps.com/start`).
6. **Configure the CLI with SSO (no static keys):**
   ```bash
   aws configure sso
   #  SSO start URL:      <paste the access portal URL>
   #  SSO region:         us-east-1
   #  account + role:     pick AdminForLabs
   #  CLI default region: us-east-1
   #  profile name:       admin-labs
   export AWS_PROFILE=admin-labs
   aws sts get-caller-identity          # confirm: an AWSReservedSSO_AdminForLabs role, NOT root
   ```

## Part C — Cost guardrails
1. **Budget (GUI):** Console → **Billing and Cost Management** → **Budgets** →
   **Create budget** → **Use a template** → **Monthly cost budget** → amount
   **$5** → enter your email → **Create budget** (alerts fire at 85% & 100%).
2. **Or by CLI:**
   ```bash
   cat > /tmp/budget.json <<EOF
   {"BudgetName":"lab-monthly-5usd","BudgetLimit":{"Amount":"5","Unit":"USD"},
    "TimeUnit":"MONTHLY","BudgetType":"COST"}
   EOF
   cat > /tmp/notify.json <<EOF
   [{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN",
     "Threshold":80,"ThresholdType":"PERCENTAGE"},
     "Subscribers":[{"SubscriptionType":"EMAIL","Address":"you@example.com"}]}]
   EOF
   aws budgets create-budget --account-id "$ACCT_ID" \
     --budget file:///tmp/budget.json --notifications-with-subscribers file:///tmp/notify.json
   ```
3. Cost drivers to watch later: **EKS control plane, NAT Gateway, ALB/NLB,
   GuardDuty** — labs flag these; tear them down same-session.

## Part D — Baseline logging & guardrails
1. **CloudTrail (CLI):** create an all-Region trail to a locked bucket.
   ```bash
   BUCKET=cloudtrail-$ACCT_ID-$AWS_REGION
   aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
     $( [ "$AWS_REGION" != us-east-1 ] && echo --create-bucket-configuration LocationConstraint=$AWS_REGION )
   aws s3api put-public-access-block --bucket "$BUCKET" \
     --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   # Bucket policy allowing CloudTrail to write:
   cat > /tmp/ct-policy.json <<EOF
   {"Version":"2012-10-17","Statement":[
     {"Sid":"AWSCloudTrailAclCheck","Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},
      "Action":"s3:GetBucketAcl","Resource":"arn:aws:s3:::$BUCKET"},
     {"Sid":"AWSCloudTrailWrite","Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},
      "Action":"s3:PutObject","Resource":"arn:aws:s3:::$BUCKET/AWSLogs/$ACCT_ID/*",
      "Condition":{"StringEquals":{"s3:x-amz-acl":"bucket-owner-full-control"}}}]}
   EOF
   aws s3api put-bucket-policy --bucket "$BUCKET" --policy file:///tmp/ct-policy.json
   aws cloudtrail create-trail --name org-trail --s3-bucket-name "$BUCKET" --is-multi-region-trail
   aws cloudtrail start-logging --name org-trail
   ```
   **GUI equivalent:** Console → **CloudTrail** → **Create trail** → name
   `org-trail`, new S3 bucket, **Enable for all accounts in my organization** if
   available → **Next** → **Create**.
2. **AWS Config (GUI):** Console → **Config** → **Get started** → accept the
   default recording (all resources) → choose/create an S3 bucket → **Confirm**.
3. **IAM Access Analyzer (CLI):**
   ```bash
   aws accessanalyzer create-analyzer --analyzer-name acct-analyzer --type ACCOUNT
   ```
4. **(Org only) baseline SCP:** adapt `../../iam/policies/aws-scp-baseline.json`;
   attach via Console → **AWS Organizations** → **Policies** → **Service control
   policies** → **Create policy** → paste → attach to the root/OU.

---

## Verify
```bash
aws sts get-caller-identity                         # SSO role, not root
python3 ../../cloud/aws/iam_audit.py                # expect clean / documented exceptions
python3 ../../cloud/detection/aws_detection_coverage.py   # logging/detection on?
aws cloudtrail get-trail-status --name org-trail --query IsLogging   # true
```
Success = root has MFA + no keys, you operate via SSO, budgets alert, CloudTrail
+ Config + Access Analyzer are on.

## Cleanup
Keep this foundation — later labs reuse it. To fully decommission:
```bash
aws cloudtrail delete-trail --name org-trail
aws s3 rb "s3://$BUCKET" --force
aws accessanalyzer delete-analyzer --analyzer-name acct-analyzer
```

## Portfolio artifact
- A one-page "secure account baseline" writeup + screenshots of your budget,
  CloudTrail, and Identity Center config. Note the **order** (root → identities →
  guardrails → logging).

## Stretch goals
- Add a **break-glass** IAM user (hardware MFA, CloudWatch alarm on its use) per
  `../../iam/architecture/aws.md`.
- Stand up a **second member account** via Organizations (preview of Lab 04).
- Codify this baseline as Terraform and `checkov` it.
