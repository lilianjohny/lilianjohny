# Lab 05 — Network Segmentation (Azure)

**Skills practiced:** vNet design · subnet tiers · NSGs + ASGs · Private
Endpoint/Private Link · Azure Firewall egress · Azure Bastion · flow logs.
**Proves (JD):** securing a deployment "from construction to multi-tenant use" —
the network layer.

## Objective
Design a segmented vNet like a secure datacenter: tiers talk only in the intended
direction, no data/management plane on the internet, private PaaS access,
controlled egress, full visibility.

## Est. time / cost
2–3 h · **~$1–3** (Azure Firewall + Bastion + Private Endpoints bill hourly).

## Prerequisites
- Lab 00 done. Tool: `../../cloud/azure/nsg_audit.sh`.

---

## Part A — Build a flat/open network first
```bash
az group create -n rg-lab05 -l "$LOCATION"
az network vnet create -g rg-lab05 -n vnet-lab05 --address-prefix 10.0.0.0/16 \
  --subnet-name flat --subnet-prefix 10.0.0.0/24
# Wide-open NSG (anti-pattern)
az network nsg create -g rg-lab05 -n nsg-open
for pair in 22:SSH 1433:DB 80:HTTP; do p=${pair%%:*}; n=${pair##*:};
  az network nsg rule create -g rg-lab05 --nsg-name nsg-open -n allow-$n \
    --priority $((1000+p%1000)) --access Allow --protocol Tcp --direction Inbound \
    --source-address-prefixes '*' --destination-port-ranges $p; done
```

## Part B — Attack / observe
```bash
bash ../../cloud/azure/nsg_audit.sh     # flags 0.0.0.0/0 (*) on 22 and 1433
# Against a launched public VM: nc -zv <public-ip> 1433 / 22 → open ❌
```

## Part C — Harden (segment like a datacenter)
```bash
# Tiered subnets
for s in web:10.0.1.0/24 app:10.0.2.0/24 data:10.0.3.0/24; do
  az network vnet subnet create -g rg-lab05 --vnet-name vnet-lab05 -n ${s%%:*} --address-prefixes ${s##*:}; done
az network vnet subnet create -g rg-lab05 --vnet-name vnet-lab05 -n AzureBastionSubnet --address-prefixes 10.0.250.0/26
az network vnet subnet create -g rg-lab05 --vnet-name vnet-lab05 -n AzureFirewallSubnet --address-prefixes 10.0.251.0/26

# ASGs + NSG rules by ASG (not CIDR)
for a in web app data; do az network asg create -g rg-lab05 -n asg-$a; done
az network nsg create -g rg-lab05 -n nsg-tiers
az network nsg rule create -g rg-lab05 --nsg-name nsg-tiers -n web-https --priority 100 \
  --access Allow --protocol Tcp --direction Inbound --destination-port-ranges 443 \
  --destination-asgs asg-web --source-address-prefixes Internet
az network nsg rule create -g rg-lab05 --nsg-name nsg-tiers -n app-from-web --priority 110 \
  --access Allow --protocol Tcp --direction Inbound --destination-port-ranges 443 \
  --source-asgs asg-web --destination-asgs asg-app
az network nsg rule create -g rg-lab05 --nsg-name nsg-tiers -n db-from-app --priority 120 \
  --access Allow --protocol Tcp --direction Inbound --destination-port-ranges 1433 \
  --source-asgs asg-app --destination-asgs asg-data
az network nsg rule create -g rg-lab05 --nsg-name nsg-tiers -n deny-all --priority 4000 \
  --access Deny --protocol '*' --direction Inbound --destination-port-ranges '*' --source-address-prefixes '*'

# Private access to a PaaS service (example: storage private endpoint) + Bastion for admin
az network bastion create -g rg-lab05 -n bastion-lab05 --vnet-name vnet-lab05 \
  --public-ip-address $(az network public-ip create -g rg-lab05 -n bastion-pip --sku Standard --query publicIp.id -o tsv) 2>/dev/null || echo "Bastion create can take ~10 min"
```
**Portal:** VM → **Connect → Bastion** (no public IP / no open 22/3389).
**Storage → Networking → Private endpoint**; disable public access. Route egress
through **Azure Firewall** with an FQDN allow policy.

## Part D — Verify
```bash
bash ../../cloud/azure/nsg_audit.sh              # clean
bash ../../cloud/benchmarks/cis_benchmark.sh     # network CIS checks
# Admin only via Bastion; DB unreachable from the internet.
```

## Cleanup (delete Firewall + Bastion + Private Endpoints FIRST — hourly)
```bash
az group delete -n rg-lab05 --yes --no-wait
```

## Portfolio artifact
- vNet segmentation diagram (tiers, ASG rules, private endpoints, egress via FW);
  `nsg_audit.sh` before/after; "datacenter → Azure" mapping (VLANs→subnets,
  firewall→NSG/ASG+FW, jump host→Bastion).

## Stretch goals
- Full **hub-and-spoke** with centralized inspection + forced tunneling.
- **Private Link service** to expose one internal service to another vNet/tenant.
- Turn the vNet into Bicep/Terraform; `checkov`.
