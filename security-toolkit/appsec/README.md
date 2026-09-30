# Application Security (AppSec)

Application-layer security tooling: the tests and checks that target **your
code and running application** — OWASP Top 10 / API Top 10 classes, auth,
session, crypto-in-transit, and design-time threat modeling — organized to
plug into the SDLC.

> ⚠️ **Authorized use only.** The dynamic tools (DAST, CORS/cookie/API probes)
> send requests to a target. Run them only against applications you own or are
> explicitly authorized to test.

## How this complements the rest of the toolkit

AppSec shares tools with DevSecOps but has a distinct focus. To avoid
duplication:

| Concern | Where it lives |
|---------|----------------|
| SAST (static analysis) | `sast/` here (app rules) — same engine as `../dod/scripts/gate_sast.sh` |
| SCA / dependencies / SBOM | `deps/` here → delegates to `../dod/scripts/generate_sbom.sh` + Grype |
| Secrets | `../devsecops/secrets_scan.py` |
| DAST | `dast/` here (with authenticated scans) |
| **API security** | `api/` — OpenAPI audit + broken-authorization probing |
| **Web session/transport** | `web/` — CORS, cookies, security headers |
| **Token security** | `crypto/jwt_inspect.py` |
| **Design-time** | `threat-model/` (STRIDE), `asvs/` (verification checklist) |

## Layout

```
appsec/
├── sast/
│   ├── semgrep_scan.sh          Semgrep: OWASP + custom app rules → SARIF
│   └── rules/custom-appsec.yml  Custom rules (SSRF sink, weak crypto, eval, etc.)
├── dast/
│   └── zap_scan.sh              OWASP ZAP baseline/full, with optional auth
├── api/
│   ├── openapi_security_audit.py  Static audit of an OpenAPI/Swagger spec
│   └── api_auth_probe.py          BOLA/BFLA (broken object/function authz) probe
├── web/
│   ├── security_headers.py      Response security headers (delegates to vuln/)
│   ├── cors_audit.py            CORS misconfiguration detector
│   └── cookie_audit.py          Cookie flags: Secure / HttpOnly / SameSite
├── crypto/
│   └── jwt_inspect.py           JWT analysis: alg=none, weak alg, expiry, claims
├── threat-model/
│   └── stride-template.md       STRIDE threat model template
├── asvs/
│   └── asvs_checklist.md        OWASP ASVS L1/L2 checklist mapped to these tools
└── pipeline/
    └── appsec.yml               CI: SAST + SCA + secrets + headers + DAST (SARIF)
```

## Quick start

```bash
# Static: audit an API contract before a line of code ships
python appsec/api/openapi_security_audit.py openapi.yaml

# Static: SAST over the codebase with app-focused rules
bash appsec/sast/semgrep_scan.sh --path .

# Dynamic (authorized target only):
python appsec/web/cors_audit.py https://app.example.com
python appsec/web/cookie_audit.py https://app.example.com
bash appsec/dast/zap_scan.sh --target https://app.example.com

# Token hygiene
python appsec/crypto/jwt_inspect.py "$JWT"
```

## Standards this maps to

- **OWASP Top 10 (2021)** and **OWASP API Security Top 10 (2023)**
- **OWASP ASVS** (Application Security Verification Standard) — `asvs/`
- **NIST SSDF (SP 800-218)** practices PW.4–PW.8 (review, test, remediate)

Exit codes follow the toolkit convention: `0` clean · `1` warn · `2` findings
· `3` setup error — so every tool gates a pipeline.
