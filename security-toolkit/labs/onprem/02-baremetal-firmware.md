# Lab 02 — Bare-Metal & Firmware Security

**Skills practiced:** BMC/IPMI hardening · UEFI Secure Boot · TPM & measured boot ·
firmware update/supply-chain integrity · boot-chain attestation · disk encryption
rooted in hardware.
**Proves (JD — OpenAI InfraSec):** securing "bare-metal hardware and firmware/BMC"
— the layers below the OS that protect GPU clusters and sensitive workloads.

## Objective
Harden a server from the firmware up: lock down the BMC, enforce Secure Boot,
use the TPM for measured boot + key sealing, and establish firmware integrity.
Design + hands-on where you have access to a real BMC/TPM (or a VM with vTPM).

## Est. time / cost
2–3 h · **~$0** (own hardware or a vTPM-capable VM).

---

## Part A — Attack / observe: the pre-OS attack surface
Understand why this layer matters:
- **BMC/IPMI** (iDRAC/iLO/BMC) is a full out-of-band computer with power over the
  host — default creds or exposure = total compromise, invisible to the OS.
- **Firmware/UEFI** implants persist through OS reinstall and disk wipe.
- Without **Secure Boot + measured boot**, a tampered bootloader/kernel runs
  silently.

## Part B — Harden the BMC
- Change default credentials; unique strong creds per device; integrate with
  central auth where supported.
- Put the BMC on the **isolated OOB network only** (lab 01) — never routable from
  the data plane or internet.
- Disable unused services (IPMI-over-LAN if not needed — it has known weaknesses),
  enforce TLS, latest BMC firmware.
- Alert on BMC logins and config changes.

## Part C — Secure the boot chain
- Enable **UEFI Secure Boot**; enroll your own keys (don't rely only on vendor
  defaults); disable legacy/CSM boot.
- Set a **firmware/BIOS password**; disable unused boot devices & external boot.
- Use the **TPM**: enable measured boot (PCR measurements), and **seal disk-
  encryption keys to the TPM** (BitLocker/LUKS) so the disk only unlocks on an
  attested-good boot state.
- Establish **firmware integrity**: track expected versions/hashes; only apply
  **signed firmware** from the vendor; verify before flashing (supply chain).

## Part D — Attestation (design)
- Use TPM **remote attestation** so a machine proves its boot state to a
  verifier before it's trusted with sensitive data/workloads (the hardware root
  for a Zero Trust "device" signal — ties to `../../zero-trust/`).
- Deny sensitive workloads (e.g. model-weight access) to hosts that fail attestation.

## Verify (checklist)
- [ ] BMC: no default creds, OOB-only, latest firmware, logging on.
- [ ] Secure Boot enabled with your keys; firmware password set.
- [ ] TPM present; measured boot on; disk key sealed to TPM.
- [ ] Firmware versions inventoried; only signed updates applied.
- [ ] (Stretch) attestation gates sensitive-workload placement.

## Portfolio artifact
- A **bare-metal hardening checklist** (BMC → Secure Boot → TPM → firmware) with
  what you configured vs. designed.
- A **boot-chain trust diagram** (firmware → bootloader → kernel → attestation).
- A short writeup: "why the BMC is the most dangerous box in the rack."

## Stretch goals
- Implement **LUKS with TPM-sealed keys** on a Linux host; prove it won't unlock
  after a boot-measurement change.
- Stand up a simple **attestation check** and gate an action on PCR state.
- Add a **firmware SBOM / version-drift check** across a fleet.
