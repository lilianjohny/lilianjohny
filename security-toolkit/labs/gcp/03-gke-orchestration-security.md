# Lab 03 — GKE Orchestration Security

**Skills practiced:** GKE hardening · Kubernetes RBAC · **GKE Workload Identity**
(keyless) · Pod Security (PSA) · network policy (default-deny) · Secret Manager
CSI · **Binary Authorization** admission · Shielded/Confidential nodes · audit
logging.
**Proves (JD):** *"orchestration security."*

## Objective
Stand up GKE, exploit the classic orchestration weaknesses (over-broad RBAC,
metadata/credential theft, flat pod networking, privileged pods), then harden to
a Zero-Trust posture and verify.

## Est. time / cost
3–4 h · **$$ — real cost** (GKE + LB + Cloud NAT). **One sitting; teardown at
the end.** Budget alarm from Lab 00. (Autopilot secures many defaults for you —
Standard is used here to *see* the controls.)

## Prerequisites
- Labs 00–02 done (deploy the Lab 02 attested image; enforce Binary Auth).
- `kubectl`, `helm`, gcloud.
- Toolkit: `../../cloud/kubernetes/kube_security_scan.sh`,
  `../../cloud/kubernetes/policies/kyverno-pod-security.yaml`.

---

## Part A — Build
```bash
gcloud container clusters create lab03 --num-nodes=2 --machine-type=e2-small \
  --workload-pool=<project>.svc.id.goog --enable-shielded-nodes \
  --enable-network-policy --region=<region>
gcloud container clusters get-credentials lab03 --region=<region>
```
Deploy the Lab 02 image with **deliberately weak** settings first (default KSA,
no network policy, a privileged pod, Binary Auth in dry-run).

## Part B — Attack / observe
1. **Over-broad RBAC:** bind a KSA to `cluster-admin`; exec in and
   `kubectl get secrets -A` / list everything.
2. **Metadata/credential theft (no Workload Identity):** from a pod, hit the
   **metadata server** for the **node SA** token:
   ```bash
   kubectl exec <pod> -- curl -s -H "Metadata-Flavor: Google" \
     http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
   ```
   The pod inherits node-SA permissions (why you need Workload Identity + metadata
   concealment).
3. **Flat network:** reach another namespace's pod directly (no network policy).
4. **Privileged pod:** run `privileged: true` / `hostPath: /` → read host FS.
5. Scan: `bash ../../cloud/kubernetes/kube_security_scan.sh`.

## Part C — Harden (Zero Trust)
1. **RBAC least privilege:** no `cluster-admin` for apps; namespaced Roles with
   only needed verbs/resources.
2. **GKE Workload Identity:** bind the KSA → a least-privilege Google SA; **enable
   metadata concealment / block the metadata server** so pods can't steal the
   node SA.
3. **Pod Security Admission:** enforce **`restricted`** on the namespace
   (no privileged/hostPath/host ns, non-root, drop caps, read-only rootfs).
4. **Network policy default-deny**, then allow only needed flows.
5. **Secrets:** **Secret Manager CSI driver** (via Workload Identity) instead of
   plain k8s Secrets; enable **application-layer secrets encryption (CMEK)**.
6. **Binary Authorization enforce:** only **attested** images (Lab 02) admitted.
7. **Shielded/Confidential nodes**, private cluster (private nodes + authorized
   networks for the API), **kube audit logs → Cloud Logging**.

## Part D — Verify
```bash
bash ../../cloud/kubernetes/kube_security_scan.sh                # clean
kubectl auth can-i get secrets -A --as=... ; # no
kubectl exec <pod> -- curl -s --max-time 3 -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/.../token || echo "metadata blocked ✅"
kubectl run bad --image=<unsigned> # rejected by Binary Authorization ✅
kubectl run priv --image=... --privileged=true  # rejected by PSA ✅
```
Success = namespaced RBAC, pod uses Workload Identity (no node-SA theft),
default-deny networking, `restricted` enforced, unsigned/privileged pods rejected,
audit logs flowing.

## Cleanup (do NOT skip — pricey)
```bash
gcloud container clusters delete lab03 --region=<region> -q
# confirm LB/Cloud NAT/forwarding rules gone; check Budgets.
```

## Portfolio artifact
- Threat-model diagram: attacker in a pod → reachable before vs after.
- Hardened manifests (RBAC, NetworkPolicy, PSA labels, Workload-Identity KSA) +
  the Binary Authorization policy.
- `kube_security_scan.sh` before/after.

## Stretch goals
- Compare **GKE Autopilot** — how many of these controls are on by default?
- Add **GKE runtime security / SCC Container Threat Detection**; trigger an alert
  (feeds Lab 06).
- Add a **service mesh** (Anthos Service Mesh/Istio) for mTLS + L7 authz.
