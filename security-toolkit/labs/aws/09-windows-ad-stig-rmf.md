# Lab 09 — Windows Server, Active Directory, DISA STIG & RMF Evidence

**Skills practiced:** Windows Server on EC2 · Active Directory / GPO / DNS / IIS ·
DoD PKI / CAC integration · DISA STIG hardening · SSM patching · RMF A&A evidence.
**Proves (JD — KBR):** the Windows-administration + STIG/RMF-compliance core.

## Objective
Deploy and harden a Windows Server environment on EC2 to DISA STIG, integrate AD
and (conceptually) DoD PKI/CAC, patch via SSM, and produce the STIG/RMF evidence
an A&A package needs — verified with the toolkit's STIG evaluator.

## Est. time / cost
3–4 h · **~$1–2** (2× Windows EC2; tear down). Windows AMIs cost more than Linux.

## Prerequisites
- Labs 00, 05 done. AWS CLI v2. RDP via **SSM/Bastion** (not open 3389 — lab 05).
- Tools: `../../compliance/stig/stig_eval.py`, `../../cloud/aws/ssm_patch_audit.py`.
- DISA STIG Viewer + the relevant Windows Server STIG (download from DoD Cyber
  Exchange on your own machine).

---

## Part A — Build: AD + member server
1. Launch 2 Windows Server EC2 instances in **private** subnets (lab 05).
2. Promote one to a **Domain Controller** (AD DS); configure **DNS**.
3. Join the second as a member server; install **IIS** on it.
4. Create **GPOs** for a baseline (password policy, audit policy, lockout).
5. Access only via **SSM Session Manager / Fleet Manager** — no public RDP.

## Part B — Attack / observe: unhardened baseline
1. Run a STIG scan (SCAP/STIG Viewer) against the fresh build → many open
   findings (weak audit policy, legacy protocols, no logon banner, etc.).
2. Export the results as a `.ckl` and score them:
   ```bash
   python3 ../../compliance/stig/stig_eval.py windows.ckl --fail-on cat1
   ```
   Expect open CAT I/II → exit 2. This is your "before".
3. Check patch posture: `python3 ../../cloud/aws/ssm_patch_audit.py`.

## Part C — Harden: STIG, PKI/CAC, patching
1. Apply the **Windows Server STIG**: audit policy, SMB signing, disable legacy
   protocols (SMBv1, TLS 1.0/1.1), logon banner, account policies, service
   hardening — via GPO where possible.
2. **DoD PKI / CAC (smart-card) auth:** configure smart-card logon
   requirements and trust the DoD root/intermediate CAs (in a real environment).
   Document the design here even if you can't fully replicate CAC hardware.
3. **Patch** via SSM Patch Manager (baseline + maintenance window); confirm
   compliance.
4. Harden **IIS** (remove unused modules, TLS config, request filtering).

## Part D — Verify & produce RMF evidence
```bash
# STIG findings resolved (open CAT I cleared):
python3 ../../compliance/stig/stig_eval.py windows.ckl --fail-on cat1   # exit 0/1
# Patch compliance:
python3 ../../cloud/aws/ssm_patch_audit.py                              # compliant
```
Collect evidence for the A&A package: STIG `.ckl` (before/after), patch-compliance
report, GPO backups, and a short control-implementation narrative. Map controls
with `../../grc/compliance/crosswalk.py` and track residual items in
`../../soc/poam/poam_tracker.py`.

## Cleanup
Delete both Windows instances, the AD/DNS config, and any static DNS records.

## Portfolio artifact
- **STIG before/after** (`stig_eval.py` output + finding counts by CAT).
- An **RMF evidence bundle**: STIG results, patch report, GPO baseline, control
  narrative, POA&M for residuals.
- A note mapping your hardening to **NIST 800-53** controls (via the crosswalk).

## Stretch goals
- Automate STIG application with a **STIG GPO baseline / PowerShell DSC**.
- Add **CloudWatch** Windows event-log collection (lab 07) for the audit trail.
- Extend the STIG gate into CI so a drifted server fails a scheduled scan.
