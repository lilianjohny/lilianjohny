# Threat Model — <System / Feature Name>

> Fill this in during design (Plan phase). Keep it in-repo next to the code and
> update it when the architecture or data flows change. Pair with the ASVS
> checklist for verification.

## 1. Scope & context
- **System / feature:**
- **Owner / date / version:**
- **Assets to protect:** (data, credentials, availability, integrity)
- **Trust levels / actors:** (anonymous, authenticated user, admin, service)

## 2. Architecture & data flow
- Components and where they run:
- **Trust boundaries:** (network edges, process/privilege changes, 3rd parties)
- Data flows crossing each boundary (sketch a DFD; note protocols + auth):

## 3. STRIDE analysis
For each element/data-flow crossing a trust boundary, walk STRIDE:

| Threat (STRIDE) | Where it applies | Existing control | Gap / risk | Mitigation & owner |
|-----------------|------------------|------------------|-----------|--------------------|
| **S**poofing (identity) | | | | |
| **T**ampering (integrity) | | | | |
| **R**epudiation (audit) | | | | |
| **I**nformation disclosure (confidentiality) | | | | |
| **D**enial of service (availability) | | | | |
| **E**levation of privilege (authorization) | | | | |

## 4. Prioritized risks
Rank by likelihood × impact. Track each as an issue/POA&M.

| # | Risk | Likelihood | Impact | Priority | Status |
|---|------|-----------|--------|----------|--------|
| 1 | | | | | |

## 5. Verification hooks (how each mitigation is tested)
- Authn/authz → `appsec/api/api_auth_probe.py`, ASVS V2/V4
- Injection/XSS → `appsec/sast/semgrep_scan.sh`
- Transport/crypto → `appsec/web/security_headers.py`, `recon/tls_cert_check.py`
- Session/token → `appsec/web/cookie_audit.py`, `appsec/crypto/jwt_inspect.py`
- Dependencies → `appsec/deps/sca_scan.sh`

## 6. Residual risk & sign-off
- Accepted residual risks (with owner + expiry):
- Reviewer / approver / date:
