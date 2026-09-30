# Lab 01 — Datacenter Security (Construction → Multi-Tenant)

**Skills practiced:** physical/facility security · cage & rack isolation · network
fabric segmentation · out-of-band management isolation · multi-tenant isolation
without a cloud provider · environmental & supply-chain controls.
**Proves (JD — OpenAI InfraSec):** *"securing on-prem deployments and datacenters
from construction to multi-tenant use."*

## Objective
Design a datacenter security architecture across its whole lifecycle — from build
to multi-tenant operation — and produce the controls, diagram, and threat model.
This is primarily a **design + checklist** lab (most of it is physical), with
hands-on network/segmentation where you have gear or VMs.

## Est. time / cost
2–3 h · **~$0** (design; optional lab switch/VMs).

---

## Part A — Construction & facility (design)
Document controls for each layer:
- **Site & perimeter:** location risk, fencing, bollards, CCTV, mantraps, guard
  posts, no exterior signage.
- **Access control:** badge + biometric, visitor escort, tailgating prevention,
  least-privilege zones (loading dock → general → cage → secure hall).
- **Environmental:** power (A/B feeds, UPS, generator), cooling redundancy, fire
  suppression, leak/temperature/humidity sensors.
- **Build-phase supply chain:** vetted contractors, equipment provenance, tamper-
  evident receiving, asset tagging before install.

## Part B — Cage, rack & cabling
- Per-tenant **locking cages/racks**; separate power whips; sealed cable paths.
- **Structured cabling** with labeled, segregated tenant runs; no shared patch
  panels across trust boundaries.
- Console/OOB ports physically secured.

## Part C — Network fabric & OOB management
- **Segment the fabric:** production, storage, and a fully **isolated
  out-of-band management network** (BMC/IPMI, switch mgmt) — never on the tenant
  data plane (ties to lab 02).
- Default-deny between tenant segments; microsegmentation (VLANs/VRFs/EVPN or a
  host firewall) — the same "no network-position trust" as `../../zero-trust/`.
- Encrypt inter-site/spine links; 802.1X for port access; disable unused ports.

## Part D — Multi-tenant isolation (the hard part)
Map each isolation layer for a shared facility (compare to the cloud version in
`../aws/04-multi-tenant-isolation.md`):
| Layer | Control |
|-------|---------|
| Physical | per-tenant cage/rack, separate power, locked |
| Network | per-tenant VLAN/VRF, default-deny east-west, no shared mgmt |
| Compute | dedicated hosts (no shared hypervisor) for high-sensitivity tenants |
| Storage | per-tenant encryption keys; physically/logically separated volumes |
| Identity | per-tenant admin scoping via central IdP + PKI |
| Monitoring | per-tenant log separation; tamper-evident audit |

## Verify (checklist)
- [ ] OOB management is on a physically separate, isolated network.
- [ ] Default-deny between tenant segments (test with a host in each).
- [ ] No shared power/cabling/patch across trust boundaries.
- [ ] Each tenant's data is encrypted with keys the other can't use.
- [ ] Physical + logical access both least-privilege and logged.

## Portfolio artifact
- A **datacenter security architecture doc + diagram** (facility → fabric →
  tenant isolation) and a **multi-tenant isolation matrix**.
- A **threat model**: insider on the floor, rogue tenant, compromised BMC,
  supply-chain implant — and the control that stops each.

## Stretch goals
- Build the **fabric segmentation** on real/virtual switches and prove
  default-deny east-west.
- Add a **hardware asset inventory** with provenance + tamper checks.
- Extend to a **colo vs owned** comparison (who owns which control).
