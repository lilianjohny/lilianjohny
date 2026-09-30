# Lab 02 — Bare-Metal & Firmware Security

**Skills practiced:** BMC/IPMI hardening · UEFI Secure Boot · TPM & measured boot ·
firmware integrity/supply-chain · boot-chain attestation · TPM-sealed disk keys.
**Proves (JD — OpenAI InfraSec):** securing "bare-metal hardware and firmware/BMC."

## Objective
Harden a server from firmware up: lock the BMC, enforce Secure Boot, use the TPM
for measured boot + key sealing, establish firmware integrity. Hands-on with a
real BMC/TPM or a vTPM VM; design where hardware isn't available.

## Est. time / cost
2–3 h · **~$0** (own hardware or a vTPM-capable VM).

## Prerequisites
```bash
sudo apt-get install -y ipmitool tpm2-tools cryptsetup    # Debian/Ubuntu
```

---

## Part A — Attack / observe: the pre-OS surface
- **BMC/IPMI** (iDRAC/iLO/BMC) is a full OOB computer with power over the host —
  default creds or LAN exposure = total compromise, invisible to the OS.
- **Firmware/UEFI** implants persist through OS reinstall + disk wipe.
- Without **Secure Boot + measured boot**, a tampered bootloader/kernel runs silently.
```bash
# Inspect the local BMC (needs the ipmi kernel modules):
sudo modprobe ipmi_devintf ipmi_si
sudo ipmitool mc info
sudo ipmitool user list 1        # look for default 'ADMIN'/'root' accounts
sudo ipmitool lan print 1        # is IPMI-over-LAN exposed?
```

## Part B — Harden the BMC
```bash
# Change default creds; disable an unused default user; set a strong password
sudo ipmitool user set name 2 bmcadmin
sudo ipmitool user set password 2
sudo ipmitool user priv 2 4 1                 # ADMIN priv on channel 1
sudo ipmitool user disable 1                  # disable the default 'ADMIN' if unused
# Restrict/disable IPMI-over-LAN if you manage OOB physically:
sudo ipmitool lan set 1 access off            # (only if a dedicated OOB path exists)
```
Put the BMC on the **isolated OOB network only** (Lab 01); update BMC firmware;
alert on BMC logins. **GUI (BMC web UI / BIOS):** iDRAC/iLO → **Users** (remove
defaults), **Network** (dedicated OOB NIC), **Services** (disable unused),
**Update** (latest firmware).

## Part C — Secure the boot chain
```bash
# Confirm Secure Boot state
mokutil --sb-state                             # "SecureBoot enabled"
# TPM present + read PCRs (measured boot state)
sudo tpm2_getcap properties-fixed | head
sudo tpm2_pcrread sha256:0,7                    # firmware + Secure Boot measurements
# Seal a LUKS disk key to the TPM so the disk unlocks only on an attested-good boot
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=0+7 /dev/sdX   # (target the right device!)
```
**GUI (BIOS/UEFI setup):** enable **Secure Boot** (enroll your own keys), set a
**firmware/BIOS password**, disable legacy/CSM + external boot, enable **TPM**.
Establish firmware integrity: track expected versions/hashes; apply only
**vendor-signed** firmware; verify before flashing.

## Part D — Attestation (design + optional hands-on)
Use TPM **remote attestation** so a machine proves its boot state before it's
trusted with sensitive data (the hardware root for a Zero Trust "device" signal —
`../../zero-trust/`). Deny sensitive workloads (model-weight access, Lab 04) to
hosts that fail attestation.

## Verify (checklist)
- [ ] BMC: no default creds, OOB-only, latest firmware, logging on.
- [ ] `mokutil --sb-state` = enabled; firmware password set.
- [ ] TPM present; `tpm2_pcrread` shows measurements; disk key sealed to PCRs.
- [ ] Firmware versions inventoried; only signed updates applied.

## Portfolio artifact
- A **bare-metal hardening checklist** (BMC → Secure Boot → TPM → firmware) with
  configured vs designed.
- A **boot-chain trust diagram** (firmware → bootloader → kernel → attestation).
- "Why the BMC is the most dangerous box in the rack."

## Stretch goals
- Prove LUKS won't unlock after a boot-measurement change (alter a PCR input).
- Stand up a simple **attestation check** and gate an action on PCR state.
- A **firmware SBOM / version-drift check** across a fleet.
