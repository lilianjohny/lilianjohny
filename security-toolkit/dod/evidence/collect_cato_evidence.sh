#!/usr/bin/env bash
# Assemble a cATO / SWFT continuous-monitoring evidence bundle from the control
# gate outputs, with a manifest and integrity hashes for submission/retention.
#
# Usage: collect_cato_evidence.sh [--evidence cato-evidence] [--out bundle]
set -uo pipefail
EVID="cato-evidence"; OUT="cato-bundle"
while [[ $# -gt 0 ]]; do case "$1" in
  --evidence) EVID="$2"; shift 2 ;;
  --out) OUT="$2"; shift 2 ;;
  *) shift ;; esac; done

[[ -d "$EVID" ]] || { echo "[FAIL] Evidence dir not found: $EVID (run run_all_gates.sh first)."; exit 3; }
mkdir -p "$OUT"

# Commit + metadata provenance.
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"

cp -r "$EVID/." "$OUT/" 2>/dev/null || true

cat > "$OUT/MANIFEST.json" <<EOF
{
  "bundle_generated": "$(date -u +%FT%TZ)",
  "git_commit": "$COMMIT",
  "git_branch": "$BRANCH",
  "framework": "DoD Enterprise DevSecOps (cATO continuous monitoring)",
  "contents": {
    "gate_summary": "summary.json",
    "secrets": "secrets.sarif",
    "sast": "sast.sarif",
    "sca": "sca.sarif",
    "sbom_spdx": "sbom/artifact.spdx.json",
    "sbom_cyclonedx": "sbom/artifact.cdx.json",
    "container_scan": "container.sarif",
    "stig_report": "stig-report.html",
    "stig_arf": "stig-arf.xml",
    "dast_report": "dast-report.html"
  },
  "note": "Indicative bundle. Map artifacts to your SSP/POA&M and submit per your AO and the SWFT process."
}
EOF

# Integrity manifest over everything in the bundle.
( cd "$OUT" && find . -type f ! -name SHA256SUMS -exec sha256sum {} \; | sort -k2 > SHA256SUMS )

echo "[OK] cATO evidence bundle assembled: $OUT/"
echo "[INFO] Files: $(find "$OUT" -type f | wc -l | tr -d ' '); integrity in $OUT/SHA256SUMS"
[[ -f "$OUT/summary.json" ]] && { echo "[INFO] Gate summary:"; cat "$OUT/summary.json"; }
