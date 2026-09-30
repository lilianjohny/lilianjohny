# AWS IAM secure baseline (reference). Apply from the Organizations management
# account (or delegated admin) against a non-prod OU first.
#
# Implements: keyless CI via GitHub OIDC, SCP + RCP guardrails, org-wide
# unused-access analyzer. Human SSO is via IAM Identity Center (permission sets)
# — a minimal example is included; wire your IdP as the identity source.
#
# terraform init && terraform plan   (review before apply)

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

variable "github_org" { type = string }                 # e.g. "lilianjohny"
variable "github_repo" { type = string }                # e.g. "lilianjohny"
variable "allowed_branches" {                            # keyless CI trust scope
  type    = list(string)
  default = ["main"]
}
variable "target_ou_id" { type = string }               # OU to attach guardrails
variable "org_id" { type = string }                     # o-xxxxxxxxxx (for RCP)

data "aws_organizations_organization" "this" {}

# --- Keyless CI: GitHub Actions OIDC → scoped role (no static keys) ----------
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [for b in var.allowed_branches :
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${b}"]
    }
  }
}

resource "aws_iam_role" "github_ci" {
  name                 = "github-ci-deploy"
  assume_role_policy   = data.aws_iam_policy_document.github_trust.json
  max_session_duration = 3600
  # Attach a LEAST-PRIVILEGE managed/customer policy for what CI actually needs.
  # (Left intentionally unattached — do not grant AdministratorAccess.)
}

# --- Guardrails: Service Control Policy (principals) --------------------------
resource "aws_organizations_policy" "scp_baseline" {
  name        = "scp-security-baseline"
  description = "Preventive guardrails: no leave-org, protect logging, region lock, no IAM users, IMDSv2."
  type        = "SERVICE_CONTROL_POLICY"
  content     = file("${path.module}/../../policies/aws-scp-baseline.json")
}

resource "aws_organizations_policy_attachment" "scp_attach" {
  policy_id = aws_organizations_policy.scp_baseline.id
  target_id = var.target_ou_id
}

# --- Guardrails: Resource Control Policy (resources / data perimeter) ---------
# Substitute the real org id into the perimeter policy at render time.
resource "aws_organizations_policy" "rcp_perimeter" {
  name        = "rcp-data-perimeter"
  description = "Only org principals (or trusted services) may access S3/STS/KMS/SQS/Secrets Manager; require TLS."
  type        = "RESOURCE_CONTROL_POLICY"
  content = replace(
    file("${path.module}/../../policies/aws-rcp-data-perimeter.json"),
    "o-EXAMPLEORGID", var.org_id
  )
}

resource "aws_organizations_policy_attachment" "rcp_attach" {
  policy_id = aws_organizations_policy.rcp_perimeter.id
  target_id = var.target_ou_id
}

# --- Continuous least-privilege: org-wide unused-access analyzer -------------
resource "aws_accessanalyzer_analyzer" "org_unused" {
  analyzer_name = "org-unused-access"
  type          = "ORGANIZATION_UNUSED_ACCESS"
  configuration {
    unused_access {
      unused_access_age = 90
    }
  }
}

output "github_ci_role_arn" {
  value       = aws_iam_role.github_ci.arn
  description = "Assume this role from GitHub Actions via OIDC (no stored keys)."
}
