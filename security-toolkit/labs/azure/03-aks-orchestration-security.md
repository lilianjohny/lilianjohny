# Lab 03 — AKS Orchestration Security

**Skills practiced:** AKS hardening · Entra-integrated Kubernetes RBAC · **Workload
Identity** (federated, no secrets) · Pod Security (Azure Policy/Gatekeeper) ·
network policy (default-deny) · secrets via Key Vault CSI · admission control
(signed images) · control-plane/audit logging.
**Proves (JD):** *"orchestration security."*

## Objective
Stand up AKS, exploit the classic orchestration weaknesses (over-broad RBAC,
metadata/credential theft, flat pod networking, privileged pods), then harden to
a Zero-Trust posture and verify.

## Est. time / cost
3–4 h · **$$ — real cost** (AKS nodes + Load Balancer + any Firewall).
**One sitting; run teardown at the end.** Budget alarm from Lab 00.

## Prerequisites
- Labs 00–02 done (deploy the Lab 02 secure image from ACR).
- `kubectl`, `helm`, Azure CLI.
- Toolkit: `../../cloud/kubernetes/kube_security_scan.sh`,
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build
```bash
az aks create -g rg-lab03 -n lab03 --node-count 2 --node-vm-size Standard_B2s \
  --enable-aad --enable-azure-rbac --enable-oidc-issuer --enable-workload-identity \
  --network-plugin azure --network-policy calico --generate-ssh-keys
az aks get-credentials -g rg-lab03 -n lab03
```
Deploy the Lab 02 image with **deliberately weak** settings first (default SA,
no network policy, a privileged pod).

## Part B — Attack / observe
1. **Over-broad RBAC:** bind a SA to `cluster-admin`; exec in and
   `kubectl get secrets -A` / list all pods.
2. **Metadata/credential theft:** from a pod without Workload Identity, hit
   **IMDS** (`169.254.169.254`) to grab the node's managed-identity token.
3. **Flat network:** reach another namespace's pod directly (no network policy).
4. **Privileged pod:** run `privileged: true` / `hostPath: /` and read the host FS.
5. Scan: `bash ../../cloud/kubernetes/kube_security_scan.sh`.

## Part C — Harden (Zero Trust)
1. **RBAC least privilege** via **Entra + Azure RBAC for Kubernetes**: no
   `cluster-admin` for apps; namespaced Roles with only needed verbs.
2. **Workload Identity (federated):** give the pod its own Entra identity via the
   OIDC issuer; **block pod access to IMDS** so it can't steal the node identity.
3. **Pod Security:** enforce the **`restricted`** standard via **Azure Policy for
   AKS (Gatekeeper)** — no privileged/hostPath/host namespaces, non-root, drop caps.
4. **Network policy default-deny** (Calico/Cilium), then allow only needed flows.
5. **Secrets:** **Key Vault CSI driver** (via Workload Identity), not plain k8s
   Secrets; enable encryption for etcd secrets.
6. **Admission control:** apply `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`
   (or Gatekeeper) and require **signed images** (Ratify) from Lab 02.
7. **Private + logged:** private API server / authorized IP ranges; nodes in
   private subnets (Lab 05); **AKS diagnostic/audit logs → Log Analytics**.

## Part D — Verify
```bash
bash ../../cloud/kubernetes/kube_security_scan.sh                 # clean
kubectl auth can-i get secrets -A --as=... ; # no
kubectl exec <pod> -- curl -s --max-time 3 http://169.254.169.254/ || echo "IMDS blocked ✅"
kubectl run bad --image=... --privileged=true   # rejected by policy ✅
```
Success = namespaced RBAC, pod has its own federated identity, IMDS blocked,
default-deny networking, `restricted` enforced, unsigned/privileged pods rejected,
audit logs flowing.

## Cleanup (do NOT skip — pricey)
```bash
az aks delete -g rg-lab03 -n lab03 -y
az group delete -n rg-lab03 -y   # confirm LB/public IPs/NAT gone; check Budgets
```

## Portfolio artifact
- Threat-model diagram: attacker in a pod → reachable before vs after.
- Hardened manifests (RBAC, NetworkPolicy, Gatekeeper/Kyverno, workload-identity SA).
- `kube_security_scan.sh` before/after.

## Stretch goals
- Add **Defender for Containers** runtime alerts; trigger one (feeds Lab 06).
- Add a **service mesh** (Istio/Linkerd/Open Service Mesh) for mTLS + L7 authz.
- Compare **Azure Container Apps / ACI** threat model (no nodes to own).
