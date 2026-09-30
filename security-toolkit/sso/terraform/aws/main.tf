# AWS SSO reference — IAM Identity Center permission sets & assignments.
#
# Assumes IAM Identity Center is already enabled and the external IdP is
# connected via SAML + SCIM (bootstrapped once in the console; see
# ../../process/implementation.md Phase 2). This file defines the *entitlements*
# as code: least-privilege permission sets assigned to IdP GROUPS per account.
#
# terraform init && terraform plan

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

variable "identity_store_id" {
  type        = string
  description = "Identity Center identity store id (d-xxxxxxxxxx)."
}

variable "target_account_id" {
  type        = string
  description = "AWS account id to assign access into."
}

variable "readonly_group_name" {
  type        = string
  default     = "role-platform-all-readonly"
  description = "IdP group (synced via SCIM) that should get read-only access."
}

variable "session_duration" {
  type        = string
  default     = "PT1H" # short sessions; elevate via JIT, not long sessions
  description = "ISO-8601 max session duration for the permission set."
}

# The Identity Center instance (there is one per organization).
data "aws_ssoadmin_instances" "this" {}

locals {
  instance_arn      = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  identity_store_id = tolist(data.aws_ssoadmin_instances.this.identity_store_ids)[0]
}

# --- Least-privilege permission set (job function) ---------------------------
resource "aws_ssoadmin_permission_set" "readonly" {
  name             = "ReadOnlyScoped"
  description      = "Read-only access; elevate via JIT for changes."
  instance_arn     = local.instance_arn
  session_duration = var.session_duration
}

# Attach an AWS-managed policy (swap for a customer-managed least-privilege
# policy in production). ViewOnlyAccess is intentionally narrow.
resource "aws_ssoadmin_managed_policy_attachment" "readonly" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}

# --- Resolve the IdP group (provisioned via SCIM) ----------------------------
data "aws_identitystore_group" "readonly" {
  identity_store_id = local.identity_store_id
  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = var.readonly_group_name
    }
  }
}

# --- Assign: (group x permission set x account) ------------------------------
# Access is granted by GROUP membership, never to individual users.
resource "aws_ssoadmin_account_assignment" "readonly" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
  principal_id       = data.aws_identitystore_group.readonly.group_id
  principal_type     = "GROUP"
  target_id          = var.target_account_id
  target_type        = "AWS_ACCOUNT"
}

output "permission_set_arn" {
  value       = aws_ssoadmin_permission_set.readonly.arn
  description = "The read-only permission set assigned to the IdP group."
}
