# Zero Trust ABAC decision (example) — policy-as-code for a Policy Enforcement
# Point (PEP): an identity-aware proxy, API gateway, or service-mesh sidecar asks
# this policy "may this subject reach this resource, right now?" on EVERY request.
#
# Evaluate:
#   opa eval -d opa-abac-example.rego -i request.json 'data.zerotrust.authz.decision'
#   conftest test request.json --policy .   # (deny rules)
#
# Expected input (request.json) — signals gathered by the PEP/PDP:
#   {
#     "subject":  { "authenticated": true, "mfa": "fido2",
#                   "groups": ["role-payments-prod-readonly"], "risk": "low" },
#     "device":   { "managed": true, "compliant": true },
#     "resource": { "id": "svc:payments-api", "sensitivity": "high",
#                   "allowed_groups": ["role-payments-prod-readonly"] },
#     "context":  { "ip_trusted": true, "impossible_travel": false }
#   }
package zerotrust.authz

import rego.v1

# Phishing-resistant methods only (NIST 800-63B / FIDO2). SMS/voice are not.
phishing_resistant := {"fido2", "passkey", "webauthn", "cba"}

default allow := false

# Grant only when EVERY Zero Trust condition holds (verify explicitly,
# least privilege, per request). Any failure below denies.
allow if {
	count(deny) == 0
}

# --- Identity: authenticated with phishing-resistant MFA ---------------------
deny contains msg if {
	not input.subject.authenticated
	msg := "subject is not authenticated"
}

deny contains msg if {
	not phishing_resistant[input.subject.mfa]
	msg := sprintf("MFA method %q is not phishing-resistant", [input.subject.mfa])
}

# --- Device: managed + compliant required for sensitive resources ------------
deny contains msg if {
	input.resource.sensitivity == "high"
	not input.device.compliant
	msg := "high-sensitivity resource requires a compliant device"
}

deny contains msg if {
	input.resource.sensitivity == "high"
	not input.device.managed
	msg := "high-sensitivity resource requires a managed device"
}

# --- Context: block high risk and impossible travel --------------------------
deny contains msg if {
	input.subject.risk == "high"
	msg := "sign-in risk is high — deny and revoke session"
}

deny contains msg if {
	input.context.impossible_travel
	msg := "impossible travel detected — step-up or deny"
}

# --- Least privilege: subject's group must be allowed on THIS resource -------
deny contains msg if {
	not group_authorized
	msg := sprintf("no group in %v is authorized for resource %q", [input.subject.groups, input.resource.id])
}

group_authorized if {
	some g in input.subject.groups
	g in input.resource.allowed_groups
}

# Structured decision for the PEP (allow + reasons when denied).
decision := {
	"allow": allow,
	"deny_reasons": deny,
}
