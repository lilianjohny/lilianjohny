# Control gate 9 (policy): all mandatory control gates must be PASS (or an
# explicitly recorded, AO-approved N/A). No gate may be missing or FAIL.
#
#   conftest test cato-evidence/summary.json --policy dod/policy/opa
#
# Expected input (summary.json, produced by run_all_gates.sh):
#   { "gates": { "secrets":"PASS","sast":"PASS","sca":"PASS","sbom":"PASS",
#                "container":"PASS","stig":"PASS","dast":"N/A","signing":"PASS" } }
package dod.gates

import rego.v1

# The mandatory, non-waiverable gates.
required := {"secrets", "sast", "sca", "sbom", "container", "stig", "dast", "signing"}

deny contains msg if {
	some g in required
	not input.gates[g]
	msg := sprintf("mandatory control gate %q is missing from the evidence", [g])
}

deny contains msg if {
	some g in required
	input.gates[g] == "FAIL"
	msg := sprintf("mandatory control gate %q is FAIL — artifact must not be promoted", [g])
}
