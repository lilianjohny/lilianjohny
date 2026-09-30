# Google Cloud IAM secure baseline (reference).
#
# Implements: keyless CI via GitHub → Workload Identity Federation (no exported
# SA keys), key org-policy guardrails, and a least-privilege service account.
# Human SSO uses Workforce Identity Federation (configured with your IdP) — see
# architecture/gcp.md. Privileged access uses PAM (JIT).
#
# terraform init && terraform plan

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.40" }
  }
}

variable "project_id" { type = string }
variable "org_id" { type = string }                      # numeric org id
variable "project_number" { type = string }
variable "github_org" { type = string }
variable "github_repo" { type = string }
variable "github_sub" {
  type        = string
  default     = "environment:production" # or "ref:refs/heads/main"
  description = "GitHub OIDC subject suffix to trust (environment or branch ref)."
}
variable "allowed_locations" {
  type    = list(string)
  default = ["in:us-locations"]
}

# --- Guardrails: organization policy constraints -----------------------------
resource "google_org_policy_policy" "disable_sa_keys" {
  name   = "organizations/${var.org_id}/policies/iam.disableServiceAccountKeyCreation"
  parent = "organizations/${var.org_id}"
  spec {
    rules { enforce = "TRUE" }
  }
}

resource "google_org_policy_policy" "public_access_prevention" {
  name   = "organizations/${var.org_id}/policies/storage.publicAccessPrevention"
  parent = "organizations/${var.org_id}"
  spec {
    rules { enforce = "TRUE" }
  }
}

resource "google_org_policy_policy" "resource_locations" {
  name   = "organizations/${var.org_id}/policies/gcp.resourceLocations"
  parent = "organizations/${var.org_id}"
  spec {
    rules {
      values { allowed_values = var.allowed_locations }
    }
  }
}

# --- Keyless CI: GitHub Actions OIDC → Workload Identity Federation ----------
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  # Pin the exact GitHub OIDC subject (repo + environment/branch) — a specific
  # subject, not any repo. (Satisfies least-privilege federation trust.)
  attribute_condition = "assertion.sub == 'repo:${var.github_org}/${var.github_repo}:${var.github_sub}'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Least-privilege service account CI impersonates (grant it only what it needs).
resource "google_service_account" "ci" {
  project      = var.project_id
  account_id   = "github-ci"
  display_name = "GitHub CI (keyless via WIF)"
}

resource "google_service_account_iam_member" "ci_wif" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  member = "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_org}/${var.github_repo}"
}

output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "Use with google-github-actions/auth (no SA key)."
}
output "ci_service_account_email" {
  value = google_service_account.ci.email
}
