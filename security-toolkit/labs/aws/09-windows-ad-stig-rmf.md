# Lab 09 — Windows Server, Active Directory, DISA STIG & RMF Evidence

**Skills practiced:** Windows Server on EC2 · AD/GPO/DNS/IIS · DoD PKI/CAC · DISA
STIG hardening · SSM patching · RMF A&A evidence.
**Proves (JD — KBR):** Windows administration + STIG/RMF compliance.

## Objective
Deploy and harden Windows Server on EC2 to DISA STIG, integrate AD (and
conceptually DoD PKI/CAC), patch via SSM, and produce STIG/RMF evidence —
verified with the toolkit's STIG evaluator.

## Est. time / cost
3–4 h · **~$1–2** (2× Windows EC2; tear down). Windows AMIs cost more than Linux.

## Prerequisites
- Labs 00, 05 done. Tools: `../../compliance/stig/stig_eval.py`,
  `../../cloud/aws/ssm_patch_audit.py`.
- DISA **STIG Viewer** + the Windows Server STIG + **SCAP** tool (download from
  DoD Cyber Exchange on your own machine).

---

## Part A — Build: launch 2 Windows servers (private subnet, SSM-managed)
```bash
# Latest Windows Server 2022 AMI via SSM public parameter
AMI=$(aws ssm get-parameter --name /aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base \
  --query 'Parameter.Value' --output text)
# Launch into the PRIVATE app subnet from Lab 05, with the SSM instance role:
aws ec2 run-instances --image-id $AMI --instance-type t3.medium --count 2 \
  --iam-instance-profile Name=SSMInstanceProfile \
  --subnet-id <private-subnet-from-lab05> --security-group-ids <app-sg> \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=lab09-win}]'
```
Connect with **SSM** (no public RDP): SSM → **Fleet Manager** → select instance →
**Remote Desktop**, or SSM Session Manager PowerShell. **GUI:** EC2 → instance →
**Connect → RDP client → Fleet Manager** (not a public IP).

## Part B — Configure AD + a member server  *(PowerShell on instance #1)*
```powershell
# Promote to a Domain Controller (DNS installs with AD DS)
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools
Install-ADDSForest -DomainName "lab09.local" -InstallDns -SafeModeAdministratorPassword `
  (ConvertTo-SecureString "P@ssw0rd-Change-Me!" -AsPlainText -Force) -Force
# After reboot, create a baseline GPO
New-GPO -Name "Lab09-Baseline" | New-GPLink -Target "DC=lab09,DC=local"
# On instance #2: join domain + install IIS
Add-Computer -DomainName "lab09.local" -Restart
Install-WindowsFeature Web-Server -IncludeManagementTools
```
**GUI:** Server Manager → **Add roles and features** → AD DS / IIS; **Group
Policy Management** console for GPOs.

## Part C — Attack / observe: unhardened baseline
1. Run a **SCAP/STIG** scan against the fresh build (STIG Viewer / SCC) → many
   open findings. Export results as a `.ckl`.
2. Score them:
   ```bash
   python3 ../../compliance/stig/stig_eval.py windows.ckl --fail-on cat1   # open CAT I/II → exit 2
   ```
3. Patch posture: `python3 ../../cloud/aws/ssm_patch_audit.py`.

## Part D — Harden: STIG, PKI/CAC, patching
```powershell
# Examples of STIG-aligned settings (apply via GPO in production):
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force          # disable SMBv1
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force     # SMB signing
# Disable TLS 1.0/1.1 (registry); enforce audit policy:
auditpol /set /category:"Logon/Logoff","Account Logon" /success:enable /failure:enable
# Logon banner:
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" legalnoticecaption "DoD Notice"
```
**DoD PKI/CAC:** configure smart-card logon + trust the DoD root/intermediate CAs
(document the design if you lack CAC hardware). **Patch** via SSM Patch Manager:
```bash
aws ssm create-patch-baseline --name lab09-baseline --operating-system WINDOWS \
  --approval-rules '{"PatchRules":[{"PatchFilterGroup":{"PatchFilters":[{"Key":"MSRC_SEVERITY","Values":["Critical","Important"]}]},"ApproveAfterDays":0}]}'
# then register targets + a maintenance window, or run AWS-RunPatchBaseline via SSM.
```

## Part E — Verify & produce RMF evidence
```bash
python3 ../../compliance/stig/stig_eval.py windows.ckl --fail-on cat1   # open CAT I cleared → exit 0/1
python3 ../../cloud/aws/ssm_patch_audit.py                              # compliant
```
Collect the A&A evidence bundle: STIG `.ckl` (before/after), patch-compliance
report, GPO backups, control narrative. Map controls with
`../../grc/compliance/crosswalk.py`; track residuals in
`../../soc/poam/poam_tracker.py`.

## Cleanup
```bash
aws ec2 terminate-instances --instance-ids <id1> <id2>
aws ssm delete-patch-baseline --baseline-id <id>
```

## Portfolio artifact
- **STIG before/after** (`stig_eval.py` output + finding counts by CAT).
- An **RMF evidence bundle**: STIG results, patch report, GPO baseline, control
  narrative, POA&M for residuals.
- A mapping of your hardening to **NIST 800-53** (via the crosswalk).

## Stretch goals
- Automate STIG application with a **STIG GPO baseline / PowerShell DSC**.
- Collect **Windows event logs to CloudWatch** (Lab 07) for the audit trail.
- Put the STIG gate in CI so a drifted server fails a scheduled scan.
