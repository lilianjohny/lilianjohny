# Control gate 9 (policy): release image must be signed, carry an SBOM
# attestation, and be sourced from a hardened (Iron Bank) base.
#
#   conftest test release.json --policy dod/policy/opa
#
# Expected input (release.json):
#   { "image": { "ref": "registry1.dso.mil/ironbank/.../app@sha256:...",
#                 "signed": true, "sbom_attested": true } }
package dod.image

import rego.v1

deny contains msg if {
	not input.image.signed
	msg := "release image is not cosign-signed"
}

deny contains msg if {
	not input.image.sbom_attested
	msg := "release image has no SBOM attestation"
}

deny contains msg if {
	not endswith_digest(input.image.ref)
	msg := "release image must be pinned by digest (image@sha256:...), not a mutable tag"
}

warn contains msg if {
	not is_ironbank(input.image.ref)
	msg := "release image base is not from Iron Bank (registry1.dso.mil)"
}

endswith_digest(ref) if regex.match(`@sha256:[0-9a-f]{64}$`, ref)

is_ironbank(ref) if startswith(ref, "registry1.dso.mil/")
