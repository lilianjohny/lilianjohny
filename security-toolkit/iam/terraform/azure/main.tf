# Azure / Entra IAM secure baseline (reference).
#
# Implements: keyless CI via GitHub → Entra workload identity federation
# (federated credential, no client secret), a management-group Azure Policy
# assignment (region lock example), and PIM role-settings guidance.
# Human SSO + Conditional Access + PIM eligibility are configured in Entra
# (portal / Graph / dedicated providers) — see architecture/azure.md.
#
# terraform init && terraform plan

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.53"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "github_org" { type = string }
variable "github_repo" { type = string }
variable "github_environment" {
  type    = string
  default = "production"
}
variable "management_group_id" { type = string } # /providers/Microsoft.Management/managementGroups/<id>
variable "allowed_locations" {
  type    = list(string)
  default = ["eastus", "westus2"]
}

# --- Keyless CI: GitHub Actions OIDC → Entra app federated credential --------
resource "azuread_application" "github_ci" {
  display_name = "github-ci-${var.github_repo}"
}

resource "azuread_service_principal" "github_ci" {
  client_id = azuread_application.github_ci.client_id
}

resource "azuread_application_federated_identity_credential" "github" {
  application_id = azuread_application.github_ci.id
  display_name   = "github-${var.github_repo}-${var.github_environment}"
  description    = "GitHub Actions OIDC — no client secret stored"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_org}/${var.github_repo}:environment:${var.github_environment}"
}
# Grant the SP a LEAST-PRIVILEGE role at the narrowest scope it needs
# (azurerm_role_assignment) — do NOT assign Owner/Contributor at subscription root.

# --- Guardrail: region lock via Azure Policy at management-group scope --------
resource "azurerm_management_group_policy_assignment" "allowed_locations" {
  name                 = "allowed-locations"
  display_name         = "Allowed locations (region lock)"
  management_group_id  = var.management_group_id
  # Built-in "Allowed locations" definition id:
  policy_definition_id = "/providers/Microsoft.Authorization/policyDefinitions/e56962a6-4747-49cd-b67b-bf8b01975c4c"
  parameters = jsonencode({
    listOfAllowedLocations = { value = var.allowed_locations }
  })
}

# NOTE: Additional deny/audit assignments (public network access, HTTPS-only,
# diagnostic settings) follow the same pattern with their built-in definition
# ids — see policies/azure-policy-baseline.md. Assign the "Microsoft cloud
# security benchmark" initiative for broad coverage.

output "github_ci_client_id" {
  value       = azuread_application.github_ci.client_id
  description = "Use as AZURE_CLIENT_ID in GitHub Actions azure/login (OIDC)."
}
