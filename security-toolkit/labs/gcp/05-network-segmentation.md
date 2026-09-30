# Lab 05 — Network Segmentation (GCP)

**Skills practiced:** VPC design · subnet tiers · firewall by service-account/tag ·
Private Google Access / PSC · Cloud NAT egress · IAP (no public management) ·
VPC Flow Logs.
**Proves (JD):** securing a deployment "from construction to multi-tenant use" —
the network layer.

## Objective
Design a segmented VPC like a secure datacenter: tiers talk only in the intended
direction, no data/management plane on the internet, private Google access,
controlled egress, full visibility.

## Est. time / cost
2–3 h · **~$1–2** (Cloud NAT + any LB bill hourly).

## Prerequisites
- Lab 00 done. Tool: `../../cloud/gcp/firewall_audit.sh`.

---

## Part A — Build a flat/open network first
```bash
gcloud compute networks create lab05 --subnet-mode=custom
gcloud compute networks subnets create flat --network=lab05 --region=$REGION --range=10.0.0.0/24
# Wide-open firewall (anti-pattern)
gcloud compute firewall-rules create open-ssh --network=lab05 --allow=tcp:22 --source-ranges=0.0.0.0/0
gcloud compute firewall-rules create open-db  --network=lab05 --allow=tcp:5432 --source-ranges=0.0.0.0/0
gcloud compute firewall-rules create open-web --network=lab05 --allow=tcp:80 --source-ranges=0.0.0.0/0
```

## Part B — Attack / observe
```bash
bash ../../cloud/gcp/firewall_audit.sh     # flags 0.0.0.0/0 on 22 and 5432
# Against a launched VM with an external IP: nc -zv <ext-ip> 5432 / 22 → open ❌
```

## Part C — Harden (segment like a datacenter)
```bash
# Tiered subnets + private-google-access
for s in web:10.0.1.0/24 app:10.0.2.0/24 data:10.0.3.0/24; do
  gcloud compute networks subnets create ${s%%:*} --network=lab05 --region=$REGION \
    --range=${s##*:} --enable-private-ip-google-access; done
# Firewall by SERVICE ACCOUNT / TAG, not IP; default-deny
gcloud compute firewall-rules delete open-ssh open-db open-web --quiet
gcloud compute firewall-rules create allow-web --network=lab05 --allow=tcp:443 \
  --target-tags=web --source-ranges=0.0.0.0/0
gcloud compute firewall-rules create app-from-web --network=lab05 --allow=tcp:443 \
  --target-tags=app --source-tags=web
gcloud compute firewall-rules create db-from-app --network=lab05 --allow=tcp:5432 \
  --target-tags=data --source-tags=app
gcloud compute firewall-rules create deny-all --network=lab05 --action=DENY --rules=all \
  --direction=INGRESS --priority=65534 --source-ranges=0.0.0.0/0
# No public management: IAP TCP forwarding for admin (no external IP, no open 22)
gcloud compute firewall-rules create allow-iap-ssh --network=lab05 \
  --allow=tcp:22 --source-ranges=35.235.240.0/20   # IAP range only
# Cloud NAT for private egress; VPC Flow Logs on the app subnet
gcloud compute routers create lab05-router --network=lab05 --region=$REGION
gcloud compute routers nats create lab05-nat --router=lab05-router --region=$REGION \
  --nat-all-subnet-ip-ranges --auto-allocate-nat-external-ips
gcloud compute networks subnets update app --region=$REGION --enable-flow-logs
```
**Console:** VPC network → **Firewall / Subnets / Cloud NAT**; connect to VMs via
**SSH → IAP** (no external IP). `gcloud compute ssh <vm> --tunnel-through-iap`.

## Part D — Verify
```bash
bash ../../cloud/gcp/firewall_audit.sh           # clean
bash ../../cloud/benchmarks/cis_benchmark.sh     # network CIS checks
# gcloud compute ssh <vm> --tunnel-through-iap    # admin via IAP, not open 22
```

## Cleanup (delete NAT + router FIRST — hourly)
```bash
gcloud compute routers nats delete lab05-nat --router=lab05-router --region=$REGION --quiet
gcloud compute routers delete lab05-router --region=$REGION --quiet
gcloud compute firewall-rules list --filter="network=lab05" --format="value(name)" | xargs -r gcloud compute firewall-rules delete --quiet
gcloud compute networks subnets list --filter="network=lab05" --format="value(name,region)" | while read n r; do gcloud compute networks subnets delete $n --region=$r --quiet; done
gcloud compute networks delete lab05 --quiet
```

## Portfolio artifact
- VPC segmentation diagram (tiers, SA/tag firewall, private access, NAT egress);
  `firewall_audit.sh` before/after; "datacenter → GCP" mapping (VLANs→subnets,
  firewall→SA/tag rules, jump host→IAP).

## Stretch goals
- **Shared VPC** (host + service projects); centralized firewall.
- **PSC** to expose one internal service to another VPC/tenant (ties to Lab 04).
- Turn the VPC into Terraform; `checkov`.
