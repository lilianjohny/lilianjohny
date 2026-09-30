# Lab 05 — Network Segmentation (Azure)

**Skills practiced:** vNet design · subnet tiers · NSGs (+ ASGs) · Private
Endpoint/Private Link · Azure Firewall egress control · Azure Bastion (no public
management) · hub-and-spoke · NSG flow logs.
**Proves (JD):** securing a deployment "from construction to multi-tenant use" —
the network layer of building a safe estate.

## Objective
Design a segmented vNet like a secure datacenter: tiers that talk only in the
intended direction, no data/management plane on the internet, private paths to
Azure PaaS, controlled egress, full visibility.

## Est. time / cost
2–3 h · **~$1–3** (Azure Firewall + Bastion + Private Endpoints bill hourly —
tear down).

## Prerequisites
- Lab 00 done. Azure CLI. Toolkit: `../../cloud/azure/nsg_audit.sh`.

---

## Part A — Build a flat/open network first
1. One vNet, one subnet; an app VM + a "DB" VM, both with **public IPs**.
2. NSG allowing `0.0.0.0/0` on 22 (SSH), 3306/1433 (DB), 80. (Anti-pattern.)

## Part B — Attack / observe
```bash
nc -zv <db-public-ip> 1433     # DB open to the world ❌
nc -zv <app-public-ip> 22      # SSH open to the world ❌
bash ../../cloud/azure/nsg_audit.sh   # flags 0.0.0.0/0 on sensitive ports
```
Management (SSH) and data (DB) planes publicly reachable; one flat segment.

## Part C — Harden (segment like a datacenter)
1. **Tiered subnets** across the vNet: `snet-web` (LB/App GW only), `snet-app`,
   `snet-data` — app/DB lose public IPs.
2. **NSG rules by ASG**, not CIDR: web-ASG→app-ASG:443; app-ASG→db-ASG:1433;
   deny the rest. Use **Application Security Groups** to reference workloads.
3. **No public management:** remove SSH-from-internet; use **Azure Bastion** (or
   JIT VM access) for admin.
4. **Private PaaS access:** **Private Endpoints** for Storage/Key Vault/etc. so
   VMs reach PaaS without the internet; disable those services' public access.
5. **Controlled egress:** route via **Azure Firewall** with an FQDN/allow policy;
   data subnet: no outbound if possible.
6. **NSG flow logs** → Log Analytics/Storage (feeds Lab 06); optionally
   **hub-and-spoke** with the Firewall in the hub.

## Part D — Verify
```bash
nc -zv <old-db-ip> 1433        # unreachable / no public IP ✅
curl https://<appgw-or-lb-dns>/ # app only via front door ✅
az network bastion ssh ...      # admin via Bastion, not open 22
bash ../../cloud/azure/nsg_audit.sh          # clean
bash ../../cloud/benchmarks/cis_benchmark.sh # network CIS checks
```
Success = data/management planes private, tier-to-tier flows only, Bastion vs open
SSH, private PaaS access, egress controlled, flow logs on.

## Cleanup
Delete **Azure Firewall + Bastion + Private Endpoints first** (hourly), then VMs,
then the vNet/RG.

## Portfolio artifact
- vNet segmentation diagram (tiers, ASG rules, private endpoints, egress via FW).
- `nsg_audit.sh` before/after.
- "Datacenter → Azure" mapping (DMZ→web subnet, VLANs→tiers, firewall→NSG/ASG+FW,
  jump host→Bastion).

## Stretch goals
- Full **hub-and-spoke** with centralized inspection and forced tunneling.
- **Private Link service** to expose one internal service to another vNet/tenant
  (ties to Lab 04).
- Turn the vNet into Bicep/Terraform; `checkov` it.
