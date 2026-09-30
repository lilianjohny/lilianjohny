# Lab 03 — AKS Orchestration Security

**Skills practiced:** AKS hardening · Entra-integrated K8s RBAC · Workload
Identity · Pod Security (Azure Policy/Gatekeeper) · network policy · Key Vault
CSI · signed-image admission · audit logging.
**Proves (JD):** *"orchestration security."*

## Objective
Exploit the classic orchestration weaknesses on AKS, then harden to Zero-Trust
and verify.

## Est. time / cost
3–4 h · **$$ real cost** (AKS nodes + LB). **One sitting; teardown at the end.**

## Prerequisites
- Labs 00–02 done. `kubectl`, `helm` (see `../aws/03` install lines).
- Tools: `../../cloud/kubernetes/kube_security_scan.sh`,
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build
```bash
az group create -n rg-lab03 -l "$LOCATION"
az aks create -g rg-lab03 -n lab03 --node-count 2 --node-vm-size Standard_B2s \
  --enable-aad --enable-azure-rbac --enable-oidc-issuer --enable-workload-identity \
  --network-plugin azure --network-policy calico --generate-ssh-keys
az aks get-credentials -g rg-lab03 -n lab03 --admin
kubectl create namespace app-ns
kubectl -n app-ns create deployment app --image=nginx   # weak defaults first
```

## Part B — Attack / observe
```bash
# Over-broad RBAC
kubectl create clusterrolebinding pwn --clusterrole=cluster-admin --serviceaccount=app-ns:default
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default   # yes = bad
# Metadata/credential theft from a pod (no Workload Identity)
POD=$(kubectl -n app-ns get pod -l app=app -o jsonpath='{.items[0].metadata.name}')
kubectl -n app-ns exec "$POD" -- sh -c 'apt-get update>/dev/null 2>&1; apt-get install -y curl>/dev/null 2>&1; \
  curl -s -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"' | head -c 200
# Privileged pod
kubectl -n app-ns run bad --image=busybox --restart=Never --privileged --overrides='{"spec":{"hostPID":true,"containers":[{"name":"bad","image":"busybox","command":["sleep","3600"],"securityContext":{"privileged":true}}]}}'
bash ../../cloud/kubernetes/kube_security_scan.sh
```

## Part C — Harden (Zero Trust)
```bash
kubectl delete clusterrolebinding pwn
# Namespaced RBAC via Azure RBAC for Kubernetes (assign a least-priv role to your Entra group at the namespace scope in the portal), plus:
kubectl label ns app-ns pod-security.kubernetes.io/enforce=restricted --overwrite
# Default-deny network policy
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {namespace: app-ns, name: default-deny}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
EOF
# Workload Identity: federate a K8s SA to an Entra managed identity
az identity create -n wi-app -g rg-lab03
CLIENT=$(az identity show -n wi-app -g rg-lab03 --query clientId -o tsv)
ISSUER=$(az aks show -g rg-lab03 -n lab03 --query oidcIssuerProfile.issuerUrl -o tsv)
kubectl -n app-ns create serviceaccount app-sa
kubectl -n app-ns annotate serviceaccount app-sa azure.workload.identity/client-id=$CLIENT
az identity federated-credential create --name fc-app -g rg-lab03 --identity-name wi-app \
  --issuer "$ISSUER" --subject system:serviceaccount:app-ns:app-sa
# Block pod access to IMDS (deny egress to 169.254.169.254 via the default-deny + explicit allows)
# Admission control: Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/ && helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl apply -f ../../cloud/kubernetes/policies/kyverno-pod-security.yaml
# Audit/diagnostic logs → Log Analytics
az monitor diagnostic-settings create --name aks-audit \
  --resource $(az aks show -g rg-lab03 -n lab03 --query id -o tsv) \
  --workspace $(az monitor log-analytics workspace show -g rg-security -n lab-law --query id -o tsv) \
  --logs '[{"category":"kube-audit","enabled":true},{"category":"kube-audit-admin","enabled":true}]'
```
**Portal:** enable **Azure Policy for AKS** add-on (Defender for Cloud → apply the
"restricted" pod-security initiative to the cluster).

## Part D — Verify
```bash
bash ../../cloud/kubernetes/kube_security_scan.sh
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default   # no ✅
kubectl -n app-ns run bad2 --image=busybox --privileged --restart=Never        # rejected ✅
```

## Cleanup (do NOT skip — pricey)
```bash
az group delete -n rg-lab03 --yes --no-wait   # confirm LB/public IPs removed
```

## Portfolio artifact
- Threat-model diagram (pod attacker before vs after); hardened manifests
  (RBAC/NetworkPolicy/Kyverno/workload-identity SA); scan before/after.

## Stretch goals
- Add **Defender for Containers** runtime alerts (feeds Lab 06).
- Add a service mesh (Istio/Linkerd/OSM) for mTLS + L7 authz.
- Compare **Azure Container Apps/ACI** threat model (no nodes to own).
