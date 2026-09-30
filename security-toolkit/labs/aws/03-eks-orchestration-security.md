# Lab 03 — EKS Orchestration Security

**Skills practiced:** EKS hardening · Kubernetes RBAC · IRSA/Pod Identity · Pod
Security Standards · network policies · secrets · admission control · audit logs.
**Proves (JD):** *"orchestration security."*

## Objective
Exploit the classic orchestration weaknesses on a real EKS cluster, then harden
each to a Zero-Trust posture and verify.

## Est. time / cost
3–4 h · **$$ real cost** (EKS control plane ~$0.10/hr + NAT + nodes). **One
sitting; run teardown at the end.**

## Prerequisites
- Labs 00–02 done. Install `eksctl`, `kubectl`, `helm`:
  ```bash
  curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp && sudo mv /tmp/eksctl /usr/local/bin
  curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && sudo mv kubectl /usr/local/bin
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ```
- Tools: `../../cloud/kubernetes/kube_security_scan.sh`,
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build a minimal cluster
```bash
eksctl create cluster --name lab03 --region "$AWS_REGION" \
  --nodes 2 --node-type t3.small --managed --with-oidc
kubectl get nodes
kubectl create namespace app-ns
# Deploy the Lab 02 secure image, deliberately weak first:
kubectl -n app-ns create deployment app \
  --image=$ACCT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/lab02-app:secure
```

## Part B — Attack / observe
```bash
# 1. Over-broad RBAC: bind default SA to cluster-admin, then it can read all secrets
kubectl create clusterrolebinding pwn --clusterrole=cluster-admin \
  --serviceaccount=app-ns:default
POD=$(kubectl -n app-ns get pod -l app=app -o jsonpath='{.items[0].metadata.name}')
kubectl -n app-ns exec "$POD" -- sh -c 'apk add --no-cache curl 2>/dev/null; \
  curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/'  # node role theft (no IRSA + no IMDS hop limit)
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default    # yes = bad

# 2. Privileged pod escape surface
kubectl -n app-ns run bad --image=busybox --restart=Never --privileged \
  --overrides='{"spec":{"hostPID":true,"volumes":[{"name":"h","hostPath":{"path":"/"}}],"containers":[{"name":"bad","image":"busybox","command":["sleep","3600"],"securityContext":{"privileged":true},"volumeMounts":[{"name":"h","mountPath":"/host"}]}]}}'
kubectl -n app-ns exec bad -- ls /host    # sees the node filesystem ❌

bash ../../cloud/kubernetes/kube_security_scan.sh
```

## Part C — Harden (Zero Trust)
```bash
# 1. Least-privilege RBAC (remove cluster-admin; namespaced Role only)
kubectl delete clusterrolebinding pwn
cat <<'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {namespace: app-ns, name: app-role}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get","list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {namespace: app-ns, name: app-rb}
subjects: [{kind: ServiceAccount, name: default, namespace: app-ns}]
roleRef: {kind: Role, name: app-role, apiGroup: rbac.authorization.k8s.io}
EOF

# 2. IRSA (pod gets its own least-priv IAM role) + block IMDS from pods
eksctl create iamserviceaccount --cluster lab03 --region "$AWS_REGION" \
  --namespace app-ns --name app-sa \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess --approve
kubectl -n app-ns patch deployment app -p '{"spec":{"template":{"spec":{"serviceAccountName":"app-sa"}}}}'
# Block pod access to IMDS (hop limit 1 on the node ASG launch template, or:)
kubectl -n app-ns set env deployment/app AWS_EC2_METADATA_DISABLED=true

# 3. Pod Security Standards: enforce "restricted" on the namespace
kubectl label ns app-ns pod-security.kubernetes.io/enforce=restricted --overwrite

# 4. Network policy default-deny, then allow DNS only
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {namespace: app-ns, name: default-deny}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
EOF

# 5. Admission control: install Kyverno + apply the pod-security policy
helm repo add kyverno https://kyverno.github.io/kyverno/ && helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl apply -f ../../cloud/kubernetes/policies/kyverno-pod-security.yaml

# 6. Control-plane logging
eksctl utils update-cluster-logging --enable-types=audit,authenticator \
  --cluster lab03 --region "$AWS_REGION" --approve
```

## Part D — Verify
```bash
bash ../../cloud/kubernetes/kube_security_scan.sh                       # clean
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:default   # no ✅
kubectl -n app-ns exec "$POD" -- sh -c 'curl -s --max-time 3 http://169.254.169.254/ || echo IMDS-blocked'  # blocked ✅
kubectl -n app-ns run bad2 --image=busybox --privileged --restart=Never    # rejected by PSS/Kyverno ✅
```

## Cleanup (do NOT skip — pricey)
```bash
eksctl delete cluster --name lab03 --region "$AWS_REGION"
# Confirm NAT Gateway, ELBs, ENIs gone in the console; check Budgets.
```

## Portfolio artifact
- A **threat-model diagram**: attacker in a pod → reachable before vs after (RBAC,
  IRSA/IMDS, network policy, PSS, admission).
- The hardened manifests (Role/RoleBinding, NetworkPolicy, Kyverno policy, IRSA SA).
- `kube_security_scan.sh` before/after.

## Stretch goals
- Add **GuardDuty EKS Protection** and trigger a finding (feeds Lab 06).
- Enforce **signed-image admission** (cosign/Ratify) from Lab 02.
- Add a service mesh (Istio/Linkerd) for mTLS + L7 authz.
