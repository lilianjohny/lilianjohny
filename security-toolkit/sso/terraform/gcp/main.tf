# GCP SSO reference — Workforce Identity Federation (external IdP → Google).
#
# Federates your existing IdP (Entra/Okta) to Google Cloud for HUMAN sign-in with
# NO synced passwords in Google. Maps the IdP subject + groups so IAM can bind
# roles by group (principalSet://). IAM role bindings and Context-Aware Access
# access levels are applied separately (see ../../../iam and ../../../zero-trust).
#
# terraform init && terraform plan

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }
}

variable "org_id" {
  type        = string
  description = "Numeric Google Cloud organization id."
}

variable "location" {
  type    = string
  default = "global"
}

variable "issuer_uri" {
  type        = string
  description = "OIDC issuer URI of your IdP (e.g. https://login.microsoftonline.com/<tenant>/v2.0)."
}

variable "oidc_client_id" {
  type        = string
  description = "OIDC audience / client id configured in the IdP for Google."
}

variable "allowed_audience" {
  type        = string
  description = "Audience value the IdP issues for this workforce provider."
}

resource "google_iam_workforce_pool" "external" {
  workforce_pool_id = "external-idp"
  parent            = "organizations/${var.org_id}"
  location          = var.location
  display_name      = "External IdP (workforce)"
  description       = "Human SSO federated from the central IdP; no synced credentials."
  session_duration  = "3600s" # short sessions; elevate privileged access via PAM
}

resource "google_iam_workforce_pool_provider" "oidc" {
  workforce_pool_id  = google_iam_workforce_pool.external.workforce_pool_id
  location           = var.location
  provider_id        = "oidc-provider"
  display_name       = "OIDC via central IdP"
  description        = "OIDC federation; maps subject + groups for IAM bindings."

  # Map the IdP subject and GROUPS so IAM can bind roles by group
  # (principalSet://.../group/<group>) rather than to individuals.
  attribute_mapping = {
    "google.subject"     = "assertion.sub"
    "google.groups"      = "assertion.groups"
    "attribute.email"    = "assertion.email"
  }

  # Only accept tokens minted for this workforce provider's audience.
  attribute_condition = "assertion.aud == '${var.allowed_audience}'"

  oidc {
    issuer_uri = var.issuer_uri
    client_id  = var.oidc_client_id
    web_sso_config {
      response_type            = "CODE"
      assertion_claims_behavior = "MERGE_USER_INFO_OVER_ID_TOKEN_CLAIMS"
    }
  }
}

output "workforce_pool_provider" {
  value       = google_iam_workforce_pool_provider.oidc.name
  description = "Bind IAM roles to principalSet://.../group/<idp-group> using this pool."
}
