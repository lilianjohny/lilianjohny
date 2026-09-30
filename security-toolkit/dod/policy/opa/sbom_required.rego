# Control gate 9 (policy): an SBOM must exist for the release and be
# machine-readable CycloneDX or SPDX JSON with at least one component.
#
# Evaluate with conftest against a small release manifest JSON, e.g.:
#   conftest test release.json --policy dod/policy/opa
#
# Expected input shape (release.json):
#   { "sbom": { "format": "cyclonedx-json", "components": ytc, "path": "sbom/app.cdx.json" } }
package dod.sbom

import rego.v1

allowed_formats := {"cyclonedx-json", "spdx-json"}

deny contains msg if {
	not input.sbom
	msg := "SWFT: no SBOM present for the release artifact"
}

deny contains msg if {
	input.sbom
	not allowed_formats[input.sbom.format]
	msg := sprintf("SWFT: SBOM format %q is not machine-readable (need cyclonedx-json or spdx-json)", [input.sbom.format])
}

deny contains msg if {
	input.sbom.components == 0
	msg := "SWFT: SBOM has zero components — generation likely failed"
}
