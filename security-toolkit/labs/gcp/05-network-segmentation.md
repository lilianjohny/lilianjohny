# Lab 05 — Network Segmentation (GCP)

**Skills practiced:** VPC design · subnet tiers · firewall rules (by service
account/tag, not just CIDR) · **Private Google Access / Private Service Connect**
· Cloud NAT egress control · **IAP** (no public management) · Shared VPC ·
VPC Flow Logs.
**Proves (JD):** securing a deployment "from construction to multi-tenant use" —
the network layer.

## Objective
Design a segmented VPC like a secure datacenter: tiers that talk only in the
intended direction, no data/management plane on the internet, private paths to
Google services, controlled egress, full visibility.

## Est. time / cost
2–3 h · **~$1–2** (Cloud NAT + any LB bill hourly — tear down).

## Prerequisites
- Lab 00 done. gcloud CLI. Toolkit: `../../cloud/gcp/firewall_audit.sh`.

---

## Part A — Build a flat/open network first
1. One VPC, one subnet; an app VM + a "DB" VM, both with **external IPs**.
2. Firewall rules allowing `0.0.0.0/0` on 22 (SSH), 3306/5432 (DB), 80.
   (Anti-pattern.)

## Part B — Attack / observe
```bash
nc -zv <db-external-ip> 5432    # DB open to the world ❌
nc -zv <app-external-ip> 22     # SSH open to the world ❌
bash ../../cloud/gcp/firewall_audit.sh   # flags 0.0.0.0/0 on sensitive ports
```
Management (SSH) and data (DB) planes publicly reachable; one flat segment.

## Part C — Harden (segment like a datacenter)
1. **Tiered subnets:** `web`, `app`, `data` — app/DB lose external IPs.
2. **Firewall by identity, not IP:** rules keyed on **service accounts / network
   tags** (web-sa→app-sa:443; app-sa→db-sa:5432); default-deny the rest.
3. **No public management:** remove SSH-from-internet; use **IAP TCP forwarding**
   (`gcloud compute ssh --tunnel-through-iap`) — no external IP, no open 22.
4. **Private Google access:** enable **Private Google Access** on subnets and/or
   **Private Service Connect** so VMs reach Google APIs without the internet.
5. **Controlled egress:** **Cloud NAT** for private egress; restrict/allowlist;
   data subnet — no egress if possible.
6. **VPC Flow Logs** on (feeds Lab 06); optionally **Shared VPC** (host/service
   projects) for the multi-project "campus" design.

## Part D — Verify
```bash
nc -zv <old-db-ip> 5432        # unreachable / no external IP ✅
curl https://<lb-dns>/          # app only via front door ✅
gcloud compute ssh <vm> --tunnel-through-iap    # admin via IAP, not open 22
bash ../../cloud/gcp/firewall_audit.sh          # clean
bash ../../cloud/benchmarks/cis_benchmark.sh    # network CIS checks
```
Success = data/management planes private, tier-to-tier flows only, IAP vs open
SSH, private Google access, egress controlled, flow logs on.

## Cleanup
Delete **Cloud NAT + LB first** (hourly), then VMs, then the VPC.

## Portfolio artifact
- VPC segmentation diagram (tiers, SA/tag-based firewall, private access, NAT egress).
- `firewall_audit.sh` before/after.
- "Datacenter → GCP" mapping (DMZ→web subnet, VLANs→tiers, firewall→SA/tag rules,
  jump host→IAP).

## Stretch goals
- **Shared VPC** with a host project + service projects; centralized firewall.
- **PSC** to expose one internal service to another VPC/tenant (ties to Lab 04).
- Turn the VPC into Terraform; `checkov` it.
