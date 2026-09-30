# Lab 03 — Microsoft 365 / Entra ID Hardening

**Skills practiced:** M365/Entra security posture · Conditional Access · MFA &
legacy-auth · admin-role hygiene · Microsoft Graph (API) · Secure Score.
**Proves (JD — SOC/Cyber Eng):** "familiarity with Microsoft technologies
including Office 365 and Azure," "scripting … with API endpoints such as
Microsoft Graph."

## Objective
Assess a Microsoft 365 / Entra tenant's security posture, harden the items that
actually get tenants breached, and prove the improvement with the toolkit's Graph
posture auditor.

## Est. time / cost
2–3 h · **~$0** (a free M365 developer tenant, or the offline sample export).

## Prerequisites
- A test M365/Entra tenant (dev tenant) **or** the offline sample.
- Tool: `../../soc/m365/graph_security_audit.py` +
  `../../soc/m365/posture.example.json`.

---

## Part A — Baseline the posture
1. Collect posture (offline sample to start):
   ```bash
   python3 ../../soc/m365/graph_security_audit.py --input soc/m365/posture.example.json
   ```
   Expect findings: users without MFA, legacy auth enabled, too many Global
   Admins, guest sprawl, stale users.
2. For a real tenant, export the same fields (Entra portal / Graph / Secure
   Score) into a posture JSON, or extend the tool's `--graph` path with your
   app-only Graph app registration (see the module docstring).

## Part B — Harden identity
1. **MFA everywhere** — phishing-resistant (FIDO2/passkeys); register all users.
2. **Block legacy authentication** (it bypasses MFA) via Conditional Access.
3. **Right-size Global Admins** (2–5); move privileged roles to **PIM** (eligible,
   JIT) — ties to `../azure/01-authn-authz.md`.
4. **Conditional Access baseline:** require MFA, compliant device for sensitive
   apps, block risky sign-ins, bounded session lifetime (see
   `../../zero-trust/policies/conditional-access-baseline.md`).
5. **Guest & lifecycle hygiene:** restrict guest permissions; disable stale
   accounts; block sign-in on shared mailboxes.

## Part C — Verify
```bash
# Re-collect posture and re-run:
python3 ../../soc/m365/graph_security_audit.py --input posture.after.json
# Expect: MFA gap closed, legacy auth off, admins in range, CA enabled → exit 0/1.
```

## Part D — Graph scripting (the API skill)
- Use **Microsoft Graph** (app-only auth, `Microsoft Graph .default` scope) to
  pull sign-in logs / CA policies / risky users programmatically. The tool's
  `fetch_from_graph()` shows the msal app-only pattern to build on.
- Script a recurring posture export so the audit runs on a schedule.

## Portfolio artifact
- **Before/after posture** (`graph_security_audit.py` output) with the specific
  hardening you applied.
- A short **Graph script** that collects posture (the API-skill proof).
- A mapping of your changes to **CIS M365 Benchmark** / Secure Score items.

## Stretch goals
- Automate posture collection via Graph on a schedule → your SIEM.
- Add **CA policy-as-code** and diff against the live tenant.
- Extend the tool with more checks (app consent grants, admin-consent workflow).
