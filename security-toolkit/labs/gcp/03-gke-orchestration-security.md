# Lab 03 — GKE Orchestration Security

**Skills practiced:** GKE hardening · Kubernetes RBAC · GKE Workload Identity ·
Pod Security (PSA) · network policy · Secret Manager CSI · Binary Authorization ·
Shielded nodes · audit logging.
**Proves (JD):** *"orchestration security."*

## Objective
Exploit the classic orchestration weaknesses on GKE, then harden to Zero-Trust
and verify.

## Est. time / cost
3–4 h · **$$ real cost** (GKE + LB + Cloud NAT). **One sitting; teardown at end.**

## Prerequisites
- Labs 00–02 done. `kubectl`, `helm`, `gke-gcloud-auth-plugin`:
  ```bash
  gcloud components install kubectl gke-gcloud-auth-plugin
  ```
- Tools: `../../cloud/kubernetes/kube_security_scan.sh`,
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build
```bash
gcloud container clusters create lab03 --region=$REGION --num-nodes=1 \
  --machine-type=e2-small --enable-shielded-nodes \
  --workload-pool=$PROJECT.svc.id.goog --enable-network-policy
gcloud container clusters get-credentials lab03 --region=$REGION
kubectl create namespace app-ns
kubectl -n app-ns create deployment app --image=nginx
```

## Part B — Attack / observe
```bash
kubectl create clusterrolebinding pwn --clusterrole=cluster-admin --serviceaccount=app-ns:default
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default   # yes = bad
POD=$(kubectl -n app-ns get pod -l app=app -o jsonpath='{.items[0].metadata.name}')
# Metadata-server node-SA token theft (no Workload Identity / metadata concealment)
kubectl -n app-ns exec "$POD" -- sh -c 'apt-get update>/dev/null 2>&1; apt-get install -y curl>/dev/null 2>&1; \
  curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' | head -c 120
# Privileged pod → host FS
kubectl -n app-ns run bad --image=busybox --restart=Never --privileged \
  --overrides='{"spec":{"containers":[{"name":"bad","image":"busybox","command":["sleep","3600"],"securityContext":{"privileged":true},"volumeMounts":[{"name":"h","mountPath":"/host"}]}],"volumes":[{"name":"h","hostPath":{"path":"/"}}]}}'
bash ../../cloud/kubernetes/kube_security_scan.sh
```

## Part C — Harden (Zero Trust)
```bash
kubectl delete clusterrolebinding pwn
# Namespaced RBAC
cat <<'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {namespace: app-ns, name: app-role}
rules: [{apiGroups: [""], resources: ["configmaps"], verbs: ["get","list"]}]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {namespace: app-ns, name: app-rb}
subjects: [{kind: ServiceAccount, name: default, namespace: app-ns}]
roleRef: {kind: Role, name: app-role, apiGroup: rbac.authorization.k8s.io}
EOF
# Pod Security Standards
kubectl label ns app-ns pod-security.kubernetes.io/enforce=restricted --overwrite
# Default-deny network policy
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {namespace: app-ns, name: default-deny}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
EOF
# GKE Workload Identity: bind a KSA to a least-priv Google SA + block metadata
gcloud iam service-accounts create gke-app
kubectl -n app-ns create serviceaccount app-ksa
gcloud iam service-accounts add-iam-policy-binding gke-app@$PROJECT.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT.svc.id.goog[app-ns/app-ksa]"
kubectl -n app-ns annotate serviceaccount app-ksa \
  iam.gke.io/gcp-service-account=gke-app@$PROJECT.iam.gserviceaccount.com
# (Workload Identity conceals the node metadata SA from pods.)
# Admission control: Kyverno + Binary Authorization (from Lab 02)
helm repo add kyverno https://kyverno.github.io/kyverno/ && helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl apply -f ../../cloud/kubernetes/policies/kyverno-pod-security.yaml
gcloud container clusters update lab03 --region=$REGION --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE
```
**Console:** enable **Binary Authorization** on the cluster; Cloud Audit Logs for
GKE are on by default → **Logging**.

## Part D — Verify
```bash
bash ../../cloud/kubernetes/kube_security_scan.sh
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default    # no ✅
kubectl -n app-ns run bad2 --image=busybox --privileged --restart=Never         # rejected ✅
kubectl -n app-ns run unsigned --image=docker.io/library/redis --restart=Never  # Binary Auth blocks ✅
```

## Cleanup (do NOT skip — pricey)
```bash
gcloud container clusters delete lab03 --region=$REGION --quiet
gcloud iam service-accounts delete gke-app@$PROJECT.iam.gserviceaccount.com --quiet
```

## Portfolio artifact
- Threat-model diagram (pod attacker before vs after); hardened manifests + the
  Binary Authorization policy; scan before/after.

## Stretch goals
- Compare **GKE Autopilot** (how many controls are default-on?).
- Add **SCC Container Threat Detection**; trigger an alert (feeds Lab 06).
- Add **Anthos Service Mesh/Istio** for mTLS + L7 authz.
