# SSO Integration Lab Track — Progress & Portfolio Tracker

## Status
| # | Lab | Protocol | Done | Portfolio evidence (link) |
|---|-----|----------|:----:|---------------------------|
| 00 | Local SSO lab stack | setup | ☐ | |
| 01 | SAML 2.0 SSO | SAML | ☐ | |
| 02 | OAuth 2.0 | OAuth | ☐ | |
| 03 | OpenID Connect | OIDC | ☐ | |
| 04 | LDAP | LDAP | ☐ | |
| 05 | Kerberos | Kerberos | ☐ | |
| 06 | SCIM 2.0 provisioning | SCIM | ☐ | |

## For each lab, capture
- [ ] A traced/validated flow (assertion, token, bind, ticket, or SCIM run)
- [ ] Tool output (`saml_inspect` / `oidc_discover` / `scim_probe` / `jwt_inspect`)
- [ ] A short protocol diagram
- [ ] The break/fix notes (the support muscle)

## Skills evidence map (for the JD line)
| "...utilizing..." | Backed by |
|-------------------|-----------|
| SAML | Lab 01 validated signed assertion + break/fix (unsigned/audience/skew) |
| OAuth | Lab 02 auth-code+PKCE + client-credentials flows, decoded tokens |
| OpenID Connect | Lab 03 discovery posture + validated ID token (iss/aud/exp/nonce/alg) |
| LDAP | Lab 04 bind/search/add + IdP user federation + LDAPS |
| Kerberos | Lab 05 TGT/service ticket/keytab + SPNEGO + skew/kvno/SPN fixes |
| SCIM | Lab 06 JML lifecycle (create→PATCH→deprovision) + SP-config validation |

## Notes / log
- 
