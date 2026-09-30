# On-Prem & Datacenter Security — Hands-On Lab Track

Securing infrastructure you **physically own** — from datacenter construction
through bare-metal, firmware, and multi-tenant use. Built to close the gap most
cloud-only portfolios have, and to match roles that span **on-prem + cloud**
(e.g. GPU superclusters, sensitive model-weight storage).

> ⚠️ **Lab/design track.** Some steps need real hardware (BMC/IPMI, TPM, a
> switch) — where you can't replicate it, do the **design + checklist** and note
> the control. Attack steps target only equipment/VMs **you own**. Never touch a
> datacenter or device you're not authorized for.

> **Runnable where hardware allows:** labs give real commands (`ipmitool`,
> `tpm2-tools`, `cryptsetup`/`systemd-cryptenroll`, Vault, `openssl`) plus
> BIOS/BMC GUI steps; where a step needs physical hardware you don't have, do the
> documented design + checklist instead.

## Why this track
Cloud abstracts away the physical layer; on-prem doesn't. Roles securing
datacenters and bare-metal (and protecting high-value data like model weights)
need the layers **below** the OS: facility, hardware, firmware/BMC, boot chain,
network fabric, and multi-tenant isolation without a hypervisor vendor doing it
for you.

## Labs
| # | Lab | Focus |
|---|-----|-------|
| 01 | [Datacenter security (construction → multi-tenant)](01-datacenter-security.md) | physical, facility, cage/rack, network fabric, tenant isolation |
| 02 | [Bare-metal & firmware security](02-baremetal-firmware.md) | BMC/IPMI, UEFI/Secure Boot, TPM, measured boot, supply chain |
| 03 | [Secret management](03-secret-management.md) | vaulting, dynamic secrets, rotation, machine identity, no static creds |
| 04 | [Sensitive-data / model-weight protection](04-sensitive-data-protection.md) | classification, encryption at rest/in transit, access pathways, exfil control |

## How it complements the cloud tracks
- **Identity / authZ** → `../../iam/`, `../../sso/`, `../../zero-trust/` (same
  principles, applied to on-prem via your IdP + PKI).
- **Orchestration** → `../aws/03`, `../azure/03`, `../gcp/03` (self-managed
  Kubernetes on bare metal reuses the same hardening).
- **Zero Trust** → `../../zero-trust/` — "assume breach" and "no network-position
  trust" apply *inside* the datacenter too.

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md). The datacenter + firmware
artifacts are rare in a portfolio and signal real infrastructure depth.
