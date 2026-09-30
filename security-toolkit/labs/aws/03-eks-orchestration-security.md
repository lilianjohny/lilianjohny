# Lab 03 — EKS Orchestration Security

**Skills practiced:** EKS cluster hardening · Kubernetes RBAC · **IRSA / Pod
Identity** (workload identity, no node keys) · Pod Security Standards · network
policies (default-deny) · secrets management · admission control (signed-image /
policy enforcement) · control-plane logging.
**Proves (JD):** *"orchestration security."*

## Objective
Stand up an EKS cluster, exploit the classic orchestration weaknesses
(over-broad RBAC, node-role credential theft, flat pod networking, privileged
pods), then harden each to a Zero-Trust posture and verify.

## Est. time / cost
3–4 h · **$$ — real cost.** EKS control plane (~$0.10/hr) + NAT Gateway + any
LoadBalancer + worker nodes. **Do this in one sitting and run teardown at the
end.** Set a budget alarm (Lab 00).

## Prerequisites
- Labs 00–02 done (you'll deploy the Lab 02 secure image).
- `eksctl`, `kubectl`, `helm`, AWS CLI v2.
- Reuse toolkit: `../../cloud/kubernetes/kube_security_scan.sh` and
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build: a minimal EKS cluster
```bash
eksctl create cluster --name lab03 --nodes 2 --node-type t3.small \
  --with-oidc --managed --region <your-region>
kubectl get nodes
```
Deploy a workload (use your **secure image from Lab 02** in ECR). Start with
**deliberately weak** settings: default service account, no network policy, a
pod that runs privileged.

## Part B — Attack / observe: orchestration weaknesses
1. **Over-broad RBAC:** bind a service account to `cluster-admin`, exec into the
   pod, and show it can read all secrets / list all pods:
   ```bash
   kubectl auth can-i --list --as=system:serviceaccount:default:app
   kubectl get secrets -A          # should NOT be possible for an app
   ```
2. **Node-role credential theft (no IRSA):** from inside a pod, hit IMDS and
   assume the **node instance role** — the app inherits node permissions:
   ```bash
   kubectl exec -it <pod> -- sh -c 'curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/'
   ```
   Note: without IRSA + IMDSv2 hop-limit, the pod gets the node's AWS access.
3. **Flat network:** exec into one pod, reach another pod/namespace directly
   (no network policy = everything talks to everything).
4. **Privileged pod:** run a `privileged: true` / `hostPath: /` pod and show it
   can see the host filesystem — container escape surface.
5. Scan it:
   ```bash
   bash ../../cloud/kubernetes/kube_security_scan.sh
   ```

## Part C — Harden: Zero-Trust orchestration
1. **RBAC least privilege:** replace `cluster-admin` with a Role granting only
   what the app needs, in its namespace only. No wildcard verbs/resources.
2. **IRSA / EKS Pod Identity:** give the pod its **own** IAM role (least
   privilege) via OIDC; **block IMDS** from pods (hop limit 1 / deny 169.254.169.254
   egress) so it can't steal the node role.
3. **Pod Security Standards:** enforce **`restricted`** on the namespace
   (no privileged, no host namespaces, non-root, read-only rootfs, drop caps).
4. **Network policy default-deny:** apply a deny-all ingress/egress, then allow
   only the flows you need (e.g., app → DB, app → DNS).
5. **Secrets:** stop using plain k8s Secrets for cloud creds — use IRSA; for app
   secrets use **Secrets Manager + External Secrets** or CSI driver; enable
   **envelope encryption (KMS)** for etcd secrets.
6. **Admission control:** enforce policy with **Kyverno** (apply
   `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`) — and require
   **signed images** (from Lab 02) so only verified images run.
7. **Control-plane logging:** enable EKS audit/authenticator logs → CloudWatch.
8. Private cluster posture: private API endpoint / restricted CIDR, nodes in
   private subnets (ties to Lab 05).

## Part D — Verify
```bash
# Toolkit posture scan should now be clean
bash ../../cloud/kubernetes/kube_security_scan.sh

# Prove each fix:
kubectl auth can-i get secrets -A --as=system:serviceaccount:app-ns:app   # no
kubectl exec <pod> -- curl -s --max-time 3 http://169.254.169.254/ || echo "IMDS blocked (good)"
kubectl exec <pod-a> -- nc -zv <pod-b-ip> <port> || echo "network policy blocks (good)"
kubectl run bad --image=... --privileged=true   # rejected by PSS/Kyverno
cosign verify <your-signed-image>                # only signed images admitted
```
Success = namespaced RBAC, pod has its own IRSA role, IMDS blocked from pods,
default-deny networking, `restricted` PSS enforced, unsigned/privileged pods
rejected, audit logs flowing.

## Cleanup (do NOT skip — this is the pricey lab)
```bash
eksctl delete cluster --name lab03 --region <your-region>
# confirm NAT Gateway, ELBs, and ENIs are gone; check the console + Budgets.
```

## Portfolio artifact
- A **threat-model diagram** of the cluster: attacker in a pod → what they could
  reach before vs after (RBAC, IRSA/IMDS, network policy, PSS, admission).
- The hardened manifests (RBAC Role, NetworkPolicy, Kyverno policy, IRSA
  service-account) committed as your own IaC.
- `kube_security_scan.sh` output before/after.

## Stretch goals
- Add **runtime detection** (Falco or GuardDuty EKS Protection) and trigger an
  alert by doing something bad in a pod — feeds Lab 06.
- Enforce **mTLS + L7 authz** with a service mesh (Istio/Linkerd) — per-request
  Zero Trust between services (`../../zero-trust/architecture/aws.md`).
- Compare **ECS Fargate** for the same app: how does the orchestration threat
  model change with no nodes to own?
