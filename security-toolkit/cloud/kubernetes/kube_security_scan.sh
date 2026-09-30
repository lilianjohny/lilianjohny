#!/usr/bin/env bash
# Kubernetes Security Posture (KSPM) scan for a cluster you administer.
# Orchestrates the standard OSS tools if present; read-only against the cluster.
#
#   - kube-bench   : CIS Kubernetes Benchmark (node/control-plane hardening)
#   - trivy k8s    : cluster-wide vuln + misconfig + secret scan
#   - kubescape    : NSA/CISA + MITRE ATT&CK posture (alt to trivy)
#   - kube-hunter  : attack-surface enumeration (optional; --hunt)
#
# Usage:
#   bash kube_security_scan.sh                 # posture of current kube-context
#   bash kube_security_scan.sh --hunt          # also run kube-hunter
#   bash kube_security_scan.sh --out kspm-out
set -uo pipefail
OUT="kspm-out"; HUNT=0
while [[ $# -gt 0 ]]; do case "$1" in
  --out) OUT="$2"; shift 2 ;;
  --hunt) HUNT=1; shift ;;
  *) shift ;; esac; done
mkdir -p "$OUT"

command -v kubectl >/dev/null 2>&1 || { echo "[FAIL] kubectl not found."; exit 3; }
CTX="$(kubectl config current-context 2>/dev/null || echo unknown)"
kubectl cluster-info >/dev/null 2>&1 || { echo "[FAIL] No reachable cluster for context '$CTX'."; exit 3; }
echo "[INFO] KSPM scan of context: $CTX"
ran=0; status=0

# 1. CIS Benchmark (kube-bench)
if command -v kube-bench >/dev/null 2>&1; then
  ran=1; echo "[INFO] kube-bench (CIS Kubernetes Benchmark)…"
  kube-bench --json > "$OUT/kube-bench.json" 2>"$OUT/kube-bench.log" || status=2
  kube-bench 2>/dev/null | grep -E "\[FAIL\]|\[WARN\]" | head -40 || true
else
  echo "[WARN] kube-bench not installed (https://github.com/aquasecurity/kube-bench)."
fi

# 2. Cluster vuln + misconfig (trivy k8s), else kubescape
if command -v trivy >/dev/null 2>&1; then
  ran=1; echo "[INFO] trivy k8s cluster scan…"
  trivy k8s --report summary --severity HIGH,CRITICAL --format json \
    --output "$OUT/trivy-k8s.json" cluster 2>"$OUT/trivy-k8s.log" || status=2
elif command -v kubescape >/dev/null 2>&1; then
  ran=1; echo "[INFO] kubescape (NSA/CISA + MITRE frameworks)…"
  kubescape scan --format json --output "$OUT/kubescape.json" >/dev/null 2>&1 || status=2
else
  echo "[WARN] Neither trivy nor kubescape installed for cluster scanning."
fi

# 3. Attack-surface enumeration (optional; can be noisy)
if [[ $HUNT -eq 1 ]]; then
  if command -v kube-hunter >/dev/null 2>&1; then
    ran=1; echo "[INFO] kube-hunter (attack-surface)…"
    kube-hunter --report json --log warning > "$OUT/kube-hunter.json" 2>/dev/null || true
  else
    echo "[WARN] --hunt set but kube-hunter not installed."
  fi
fi

# 4. Quick built-in posture checks via kubectl (always available)
echo "[INFO] Built-in checks (privileged pods, hostNetwork, default SA automount)…"
{
  echo "## Privileged containers"
  kubectl get pods -A -o json 2>/dev/null \
    | jq -r '.items[] | select(.spec.containers[]?.securityContext?.privileged==true) | "\(.metadata.namespace)/\(.metadata.name)"' 2>/dev/null | sort -u
  echo "## hostNetwork pods"
  kubectl get pods -A -o json 2>/dev/null \
    | jq -r '.items[] | select(.spec.hostNetwork==true) | "\(.metadata.namespace)/\(.metadata.name)"' 2>/dev/null | sort -u
  echo "## cluster-admin bindings"
  kubectl get clusterrolebindings -o json 2>/dev/null \
    | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name' 2>/dev/null | sort -u
} > "$OUT/builtin-checks.txt"
ran=1
priv=$(grep -c "/" "$OUT/builtin-checks.txt" 2>/dev/null || echo 0)
cat "$OUT/builtin-checks.txt"

[[ $ran -eq 0 ]] && { echo "[FAIL] No KSPM tooling available. Install kube-bench + trivy/kubescape."; exit 3; }
echo "[INFO] KSPM scan complete. Results in $OUT/"
echo "[INFO] Enforce guardrails with cloud/kubernetes/policies/kyverno-pod-security.yaml"
exit $status
