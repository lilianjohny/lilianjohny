# Lab 03 — Microsoft 365 / Entra ID Hardening

**Skills practiced:** M365/Entra security posture · Conditional Access · MFA &
legacy-auth · admin-role hygiene · Microsoft Graph (API) · Secure Score.
**Proves (JD — SOC/Cyber Eng):** "familiarity with Office 365 and Azure,"
"scripting … with API endpoints such as Microsoft Graph."

## Objective
Assess a tenant's posture, harden what actually gets tenants breached, and prove
the improvement with the toolkit's Graph posture auditor.

## Est. time / cost
2–3 h · **~$0** (free M365 developer tenant, or the offline sample).

## Prerequisites
- Tool: `../../soc/m365/graph_security_audit.py` + `../../soc/m365/posture.example.json`.
- (Live mode) `pip install msal requests` + an app registration with
  `Policy.Read.All`, `Reports.Read.All`, `Directory.Read.All` (app-only).

---

## Part A — Baseline the posture
```bash
# Offline (sample) — start here:
python3 ../../soc/m365/graph_security_audit.py --input ../../soc/m365/posture.example.json
# Expect: users without MFA, legacy auth enabled, too many Global Admins, guests, stale users.
```
For a real tenant, export the same fields (Entra portal / Graph / Secure Score)
into your own `posture.json`, or use live mode:
```bash
export GRAPH_CLIENT_SECRET=<app-secret>
python3 ../../soc/m365/graph_security_audit.py --graph --tenant <tenant-id> --client-id <app-id>
```

## Part B — Harden identity  *(Entra portal + confirm via tool)*
1. **MFA everywhere** — phishing-resistant (FIDO2/passkeys); register all users.
   (Entra → **Protection → Authentication methods**.)
2. **Block legacy authentication** via Conditional Access (Entra → **Protection →
   Conditional Access → New policy**).
3. **Right-size Global Admins** (2–5); move privileged roles to **PIM**
   (eligible/JIT) — ties to `../azure/01-authn-authz.md`.
4. **Conditional Access baseline:** require MFA, compliant device for sensitive
   apps, block risky sign-ins, bounded session lifetime — see
   `../../zero-trust/policies/conditional-access-baseline.md`.
5. **Guest & lifecycle hygiene:** restrict guest permissions; disable stale
   accounts; block sign-in on shared mailboxes.

## Part C — Verify
```bash
# Produce an "after" posture (re-export or live) and re-run:
cat > /tmp/posture.after.json <<'EOF'
{"users_total":240,"users_without_mfa":0,"global_admins":3,"legacy_auth_enabled":false,
 "security_defaults_enabled":false,
 "ca_policies":[{"name":"Require MFA all","state":"enabled"},{"name":"Block legacy auth","state":"enabled"}],
 "guest_users":4,"stale_users_90d":0,"shared_mailboxes_signin_enabled":false}
EOF
python3 ../../soc/m365/graph_security_audit.py --input /tmp/posture.after.json   # expect exit 0/1
```

## Part D — Graph scripting (the API skill)
Use **Microsoft Graph** (app-only, `Microsoft Graph .default` scope) to pull
sign-in logs / CA policies / risky users programmatically — the tool's
`fetch_from_graph()` shows the msal app-only pattern to build on. Script a
recurring posture export so the audit runs on a schedule.

## Cleanup
```bash
rm -f /tmp/posture.after.json
```

## Portfolio artifact
- **Before/after posture** (`graph_security_audit.py` output) with the specific
  hardening applied.
- A short **Graph script** that collects posture (the API-skill proof).
- A mapping of changes to **CIS M365 Benchmark** / Secure Score items.

## Stretch goals
- Automate posture collection via Graph on a schedule → your SIEM.
- Add **CA policy-as-code** and diff against the live tenant.
- Extend the tool with more checks (app consent grants, admin-consent workflow).
