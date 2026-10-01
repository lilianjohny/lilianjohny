# SSO / Identity Integration Engineer

**Role line:** *"Design and support Single Sign-On (SSO) integrations utilizing
SAML, OAuth, OpenID Connect, LDAP, Kerberos, and SCIM technologies."*

> Legend: ✅ covered · 🆕 built to close a gap · 📁 reference.

## Requirement → evidence matrix
| Technology | Design evidence | Support / hands-on evidence |
|------------|-----------------|------------------------------|
| **SAML** | 📁 `../sso/architecture/` (federation design), `../sso/architecture/diagram.md` (SAML sequence) | 🆕 `../labs/sso/01-saml.md` + 🆕 `../sso/tools/saml_inspect.py` |
| **OAuth 2.0** | 📁 `../sso/architecture/overview.md` (protocols table) | 🆕 `../labs/sso/02-oauth2.md` (auth-code+PKCE, client-credentials) + ✅ `../appsec/crypto/jwt_inspect.py` |
| **OpenID Connect** | 📁 `../sso/architecture/` + `../iam/` (OIDC workload federation) | 🆕 `../labs/sso/03-oidc.md` + 🆕 `../sso/tools/oidc_discover.py` |
| **LDAP** | 📁 `../sso/architecture/multicloud.md` (IdP ← directory) | 🆕 `../labs/sso/04-ldap.md` (bind/search/add + IdP user federation) |
| **Kerberos** | 📁 `../iam/` (on-prem identity), `../labs/onprem/` | 🆕 `../labs/sso/05-kerberos.md` (TGT/keytab/SPN + SPNEGO) |
| **SCIM** | 📁 `../sso/architecture/` + `../sso/process/implementation.md` (JML lifecycle) | 🆕 `../labs/sso/06-scim.md` + 🆕 `../sso/tools/scim_probe.py` |
| Federation architecture (cloud) | ✅ `../sso/` + `../sso/terraform/` (Identity Center / Entra / Workforce IF) | ✅ `../labs/multicloud/00-unified-identity-sso.md` |
| Zero-standing-privilege / MFA / JIT | ✅ `../iam/`, `../zero-trust/` | ✅ per-cloud `../labs/*/01-authn-authz.md` |
| Deprovisioning / lifecycle (the leaver test) | 📁 `../sso/process/implementation.md` | 🆕 `../labs/sso/06-scim.md` (active=false) + ✅ `../labs/multicloud/00` |

## Tools built to close the gaps (run them)
```bash
# SAML Response/assertion: status, signature presence, conditions, audience, recipient
python3 sso/tools/saml_inspect.py sso/tools/sample.saml.b64 --audience https://sp.example.com/metadata

# OIDC discovery posture: endpoints, issuer HTTPS, PKCE S256, alg != none, implicit warnings
python3 sso/tools/oidc_discover.py --file sso/tools/sample.discovery.json

# SCIM 2.0: validate a User (active/deprovision) and a ServiceProviderConfig (PATCH/filter)
python3 sso/tools/scim_probe.py sso/tools/sample.scim-user.json
python3 sso/tools/scim_probe.py sso/tools/sample.spconfig.json

# OAuth/OIDC JWT: alg/exp/aud/scope
python3 appsec/crypto/jwt_inspect.py <token>
```

## Labs to do (produce portfolio artifacts)
`../labs/sso/00-setup.md` (local Keycloak + OpenLDAP + Kerberos KDC) → then
`01-saml` · `02-oauth2` · `03-oidc` · `04-ldap` · `05-kerberos` · `06-scim`.
Each ends with a traced/validated flow + break/fix notes — the "support" half of
the JD, not just "design".

## Interview talking points
- "I can stand up an IdP, a directory, and a KDC locally and drive all six
  protocols end to end — and I wrote validators for the SAML assertion, the OIDC
  discovery doc, and SCIM resources to troubleshoot them fast."
- "The failures I've reproduced are the ones that actually page you: an unsigned
  SAML assertion, an audience/recipient mismatch, OIDC key rotation (`kid`↔JWKS),
  Kerberos clock skew / stale keytab, and a SCIM target with no PATCH or no
  `active` (so you can't cleanly deprovision a leaver)."
- "Deprovisioning is `active=false`, not delete — and I prove the leaver path."
