# Lab 01 — Datacenter Security (Construction → Multi-Tenant)

**Skills practiced:** physical/facility security · cage & rack isolation · network
fabric segmentation · out-of-band management isolation · multi-tenant isolation ·
environmental & supply-chain controls.
**Proves (JD — OpenAI InfraSec):** *"securing on-prem deployments and datacenters
from construction to multi-tenant use."*

## Objective
Design a datacenter security architecture across its lifecycle and produce the
controls, diagram, and threat model. Mostly **design + checklist** (physical),
with hands-on network segmentation you can do on VMs / a managed switch / Linux
bridges.

## Est. time / cost
2–3 h · **~$0**.

---

## Part A — Construction & facility (design checklist)
Document controls for each layer (this is the deliverable):
- **Site/perimeter:** location risk, fencing, bollards, CCTV, mantraps, no signage.
- **Access:** badge + biometric, visitor escort, tailgating prevention, zoned
  least-privilege (dock → general → cage → secure hall).
- **Environmental:** A/B power, UPS, generator, N+1 cooling, fire suppression,
  leak/temp/humidity sensors.
- **Build-phase supply chain:** vetted contractors, equipment provenance,
  tamper-evident receiving, asset tagging before install.

## Part B — Cage, rack & cabling (design)
Per-tenant locking cages/racks; separate power whips; sealed, labeled,
segregated cable runs; no shared patch panels across trust boundaries; console/
OOB ports physically secured.

## Part C — Network fabric & OOB (hands-on where possible)
Segment production, storage, and a fully **isolated OOB management** network.
On Linux you can prove default-deny east-west between "tenant" segments:
```bash
# Two namespaces as two tenant segments, bridged — then default-deny between them
sudo ip netns add tenantA; sudo ip netns add tenantB
# (wire veth pairs to a bridge, give each an IP, then:)
sudo iptables -A FORWARD -s 10.10.10.0/24 -d 10.10.20.0/24 -j DROP   # A cannot reach B
sudo iptables -A FORWARD -s 10.10.20.0/24 -d 10.10.10.0/24 -j DROP
sudo iptables -P FORWARD DROP                                        # default-deny
```
On a managed switch, the equivalent is per-tenant **VLANs/VRFs** + ACLs, an
isolated **management VLAN** for BMC/switch mgmt, and **802.1X** on access ports.
Encrypt inter-site/spine links (MACsec/IPsec). This mirrors the cloud version in
`../aws/05-network-segmentation.md` ("no network-position trust").

## Part D — Multi-tenant isolation matrix (deliverable)
| Layer | Control |
|-------|---------|
| Physical | per-tenant cage/rack, separate power, locked |
| Network | per-tenant VLAN/VRF, default-deny east-west, isolated mgmt |
| Compute | dedicated hosts (no shared hypervisor) for high-sensitivity tenants |
| Storage | per-tenant encryption keys; separated volumes |
| Identity | per-tenant admin scoping via central IdP + PKI |
| Monitoring | per-tenant log separation; tamper-evident audit |

## Verify (checklist)
- [ ] OOB management on a physically separate, isolated network.
- [ ] Default-deny between tenant segments (test a host in each — the iptables demo).
- [ ] No shared power/cabling/patch across trust boundaries.
- [ ] Each tenant's data encrypted with keys the other can't use (Lab 04).
- [ ] Physical + logical access both least-privilege and logged.

## Cleanup
```bash
sudo iptables -F FORWARD; sudo ip netns del tenantA; sudo ip netns del tenantB
```

## Portfolio artifact
- A **datacenter security architecture doc + diagram** (facility → fabric → tenant
  isolation) and the **multi-tenant isolation matrix**.
- A **threat model**: insider on the floor, rogue tenant, compromised BMC,
  supply-chain implant — and the control that stops each.

## Stretch goals
- Build the fabric segmentation on real/virtual switches; prove default-deny.
- A **hardware asset inventory** with provenance + tamper checks.
- A **colo vs owned** comparison (who owns which control).
