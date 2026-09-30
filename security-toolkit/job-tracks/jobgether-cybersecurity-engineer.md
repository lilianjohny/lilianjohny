# Cybersecurity Engineer (SOC / Incident Response) — via Jobgether

**Role:** investigate escalated security issues, respond to SOC alerts,
coordinate incidents end-to-end, drive remediation and change management, and
document it all. Hands-on across enterprise security + infrastructure tools;
mentors juniors; on-call rotation.
**Certs (a plus):** CompTIA CySA+, Security+, Network+; ISC2 CCSP or SSCP; MCSE.

> Legend: ✅ covered · 🆕 built to close a gap · 📁 reference.

## Requirement → evidence matrix
| JD requirement | Evidence |
|----------------|----------|
| Investigate & resolve escalated security issues | 🆕 **`../soc/ir/triage.py`** + ✅ `../soc/incident/incident_report.py` |
| Monitor/respond to **SOC escalations & alerts** | 🆕 **`../soc/ir/triage.py`** (score → P1-P4, NIST phase, first action) |
| **Incident response lifecycle** (investigate→coordinate→remediate→resolve) | 🆕 **`../labs/soc/01-incident-response.md`**; ✅ `../soc/incident/` |
| Lead incident coordination w/ regulatory alignment | ✅ `../soc/` (FISMA/CIRCIA timelines), `../grc/` |
| Firewall / network tools (Palo Alto, FortiGate, Meraki, SonicWall) | 🆕 **`../soc/network/firewall_rule_audit.py`** (vendor-neutral rule audit) |
| EDR (SentinelOne, Defender, ThreatLocker) | 🆕 `../labs/soc/02-soc-alert-triage.md` (EDR alert → triage flow) |
| Content filtering / **protective DNS** | 📁 `../labs/soc/02` (DNS-layer detection/response) |
| **Microsoft 365 / Azure / Entra** security | 🆕 **`../soc/m365/graph_security_audit.py`** + 🆕 **`../labs/soc/03-m365-entra-hardening.md`** |
| Scripting & **API endpoints (Microsoft Graph)** | 🆕 `graph_security_audit.py` (Graph app-only pattern) |
| OSINT / investigation techniques | 📁 `../pentest/` recon phases, `../labs/soc/01` (enrichment) |
| Ticketing / ITSM (ConnectWise, ServiceNow) | 🆕 `triage.py --format json` (emits a ticket-ready record) |
| Security remediation & change management | ✅ `../grc/governance/`, `../vulnmgmt/track/` (SLA), `../soc/poam/` |
| Technical writing (policies, docs) | ✅ `../grc/`, `../soc-reports/`, `../zero-trust/policy/` |
| Vulnerability management | ✅ `../vulnmgmt/` (normalize→KEV/EPSS→dedupe→SLA→report) |

## Tools built to close the gaps (run them)
```bash
# SOC alert triage: score, prioritize (P1-P4), map to NIST 800-61, suggest first action
echo '{"title":"Beaconing to C2","severity":"high","category":"c2","asset_criticality":"crown_jewel"}' \
  | python3 soc/ir/triage.py -
python3 soc/ir/triage.py alerts.json --format json > triage.json   # ticket-ready

# Vendor-neutral firewall rule-base audit (any-any, exposed mgmt ports, cleartext)
python3 soc/network/firewall_rule_audit.py soc/network/rules.example.csv

# M365 / Entra security posture (offline JSON export or live Graph)
python3 soc/m365/graph_security_audit.py --input soc/m365/posture.example.json
```

## Labs to do (produce portfolio artifacts)
1. 🆕 `../labs/soc/01-incident-response.md` — full NIST 800-61 IR lifecycle on a simulated incident.
2. 🆕 `../labs/soc/02-soc-alert-triage.md` — build a triage workflow from EDR/DNS/firewall alerts.
3. 🆕 `../labs/soc/03-m365-entra-hardening.md` — harden a tenant; prove posture with the Graph tool.
4. ✅ `../vulnmgmt/` — run the VM pipeline end-to-end for the remediation/SLA story.

## Certs & study
- **Security+ / Network+ / CySA+** — `../grc/`, `../soc/`, `../vulnmgmt/`, and the
  IR/firewall/M365 tools map directly to the blue-team objectives.
- **CCSP / SSCP** — cloud + operational security, covered across `../cloud/`,
  `../zero-trust/`, `../iam/`.

## Interview talking points
- "I wrote a triage engine that scores every SOC alert by severity × asset
  criticality × threat category × confidence, buckets it P1–P4 with an SLA, maps
  it to the NIST 800-61 phase, and emits a ticket-ready record — consistent
  triage with an audit trail."
- "I audit firewall rule bases vendor-neutrally — any-any allows, management
  ports exposed to the internet, cleartext protocols, and allow-rules with
  logging off."
- "For M365/Entra I check the posture that actually gets tenants breached: users
  without MFA, legacy auth enabled, too many Global Admins, missing Conditional
  Access."
