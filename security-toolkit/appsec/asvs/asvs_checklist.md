# OWASP ASVS Verification Checklist (working subset)

A practical L1/L2 checklist from the OWASP Application Security Verification
Standard, annotated with which tool in this toolkit gives evidence for each.
Use it as the AppSec Definition of Done; record results in your test evidence.

> This is a curated subset for day-to-day gating, not the full ASVS. Map to the
> current ASVS version for a formal assessment.

## V1 — Architecture & Threat Modeling
- [ ] Threat model exists and is current → `threat-model/stride-template.md`
- [ ] Trust boundaries and data flows documented
- [ ] Security requirements derived from the threat model

## V2 — Authentication
- [ ] No default/hardcoded credentials → SAST (`sast/semgrep_scan.sh`), secrets scan
- [ ] Passwords stored with a strong KDF (bcrypt/argon2/scrypt) → SAST `weak-hash-*`
- [ ] MFA available for privileged accounts
- [ ] Anti-automation / rate limiting on auth endpoints → `api/openapi_security_audit.py` (429)

## V3 — Session Management
- [ ] Session cookies: Secure + HttpOnly + SameSite → `web/cookie_audit.py`
- [ ] Tokens expire; short lifetimes; rotation on privilege change → `crypto/jwt_inspect.py`
- [ ] Logout invalidates server-side session/token

## V4 — Access Control
- [ ] Deny by default; object-level authz enforced (no BOLA) → `api/api_auth_probe.py`
- [ ] Function-level authz enforced (no BFLA) → `api/api_auth_probe.py`
- [ ] No sensitive functions reachable unauthenticated → `api/openapi_security_audit.py`

## V5 — Validation, Sanitization & Encoding
- [ ] Input validated server-side; parameterized queries (no SQLi) → SAST
- [ ] No injection sinks: eval/exec/os.system/shell=True → SAST custom rules
- [ ] Output encoded to prevent XSS (no raw innerHTML) → SAST `js-dangerous-innerhtml`

## V6 — Stored Cryptography
- [ ] Approved algorithms; no MD5/SHA1 for security → SAST `weak-hash-*`
- [ ] Secrets from a manager, not source → secrets scan, SAST `hardcoded-*`

## V7 — Error Handling & Logging
- [ ] No stack traces / secrets in responses → DAST, `api/openapi_security_audit.py`
- [ ] Security events logged; logs shipped centrally → `../monitoring/`

## V9 — Communications
- [ ] TLS everywhere; no cleartext HTTP → `api/openapi_security_audit.py`, `web/security_headers.py`
- [ ] TLS verification never disabled → SAST `python-requests-verify-false`
- [ ] Valid, unexpired certificates → `../recon/tls_cert_check.py`

## V13 — API & Web Service
- [ ] CORS not over-permissive → `web/cors_audit.py`
- [ ] Security scheme applied to every operation → `api/openapi_security_audit.py`
- [ ] Rate limiting / quotas documented and enforced

## V14 — Configuration
- [ ] Security headers present (HSTS/CSP/etc.) → `web/security_headers.py`
- [ ] Dependencies free of known-vulnerable versions → `deps/sca_scan.sh`
- [ ] SBOM generated per build → `../dod/scripts/generate_sbom.sh`
