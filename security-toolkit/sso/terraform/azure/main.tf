# Azure SSO reference — Entra ID enterprise application (SAML SSO) + group
# assignment.
#
# Entra is both IdP and Azure identity plane. This file registers a SAML SSO app
# and assigns access by GROUP. Conditional Access, PIM eligibility, and SCIM
# provisioning jobs are configured in Entra/Graph (see
# ../../process/implementation.md Phase 3) — some are Graph-only, not Terraform.
#
# terraform init && terraform plan

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.53"
    }
  }
}

variable "app_display_name" {
  type        = string
  default     = "Internal SSO App (SAML)"
  description = "Display name of the enterprise application."
}

variable "assigned_group_object_id" {
  type        = string
  description = "Object id of the Entra group that should get SSO access."
}

# Use the Microsoft-published gallery template for SAML custom apps, or register
# a bespoke application. Here: a custom SAML application registration.
resource "azuread_application" "sso" {
  display_name = var.app_display_name

  # Expose an app role so the app receives the user's assignment in the token.
  app_role {
    allowed_member_types = ["User"]
    description          = "Standard application user."
    display_name         = "User"
    enabled              = true
    id                   = "18d14569-c3bd-439b-9a66-3a2aee01d14f"
    value                = "User"
  }

  # Require explicit assignment — no implicit access for the whole directory.
  # (Enforced on the service principal below.)
}

resource "azuread_service_principal" "sso" {
  client_id                     = azuread_application.sso.client_id
  app_role_assignment_required  = true # only assigned users/groups can sign in
  preferred_single_sign_on_mode = "saml"
}

# Assign the group to the app's "User" role (group-based, not per user).
resource "azuread_app_role_assignment" "group" {
  app_role_id         = "18d14569-c3bd-439b-9a66-3a2aee01d14f"
  principal_object_id = var.assigned_group_object_id
  resource_object_id  = azuread_service_principal.sso.object_id
}

output "sso_service_principal_id" {
  value       = azuread_service_principal.sso.object_id
  description = "Service principal to finish SAML SSO config (URLs, claims) in Entra."
}
