# SSO Integration — Hands-On Lab Track (SAML · OAuth2 · OIDC · LDAP · Kerberos · SCIM)

Design, build, and **support** real Single Sign-On integrations across the six
core protocols — hands-on, on your own machine with Docker (no cloud bill, no
real users). Each lab follows the same **build → use/trace → break → fix →
verify** arc and produces a portfolio artifact.

> ⚠️ **Local/sandbox only.** Everything runs in local Docker containers you own
> (Keycloak as the IdP, OpenLDAP, an MIT Kerberos KDC, a SCIM target). Never
> point these at a production directory or a tenant you don't control.

## Maps to the job line
> *"Design and support Single Sign-On (SSO) integrations utilizing SAML, OAuth,
> OpenID Connect, LDAP, Kerberos, and SCIM technologies."*

| Protocol | Lab | What you'll do |
|----------|-----|----------------|
| (setup) | [`00-setup.md`](00-setup.md) | Stand up the local IdP + directory + KDC lab stack |
| **SAML 2.0** | [`01-saml.md`](01-saml.md) | Federate an SP↔IdP; trace & validate the assertion |
| **OAuth 2.0** | [`02-oauth2.md`](02-oauth2.md) | Auth-code + PKCE and client-credentials flows end to end |
| **OpenID Connect** | [`03-oidc.md`](03-oidc.md) | Discovery, ID token, userinfo; validate the token |
| **LDAP** | [`04-ldap.md`](04-ldap.md) | Bind/search a directory; federate the IdP to LDAP |
| **Kerberos** | [`05-kerberos.md`](05-kerberos.md) | KDC, keytabs, tickets, SPNEGO desktop SSO |
| **SCIM 2.0** | [`06-scim.md`](06-scim.md) | Provision/deprovision users & groups; validate resources |

## Tools you'll use (built for this track)
- `../../sso/tools/saml_inspect.py` — decode + validate a SAML Response/assertion.
- `../../sso/tools/oidc_discover.py` — validate an OIDC discovery doc / posture.
- `../../sso/tools/scim_probe.py` — validate SCIM Users / ServiceProviderConfig.
- `../../appsec/crypto/jwt_inspect.py` — inspect OAuth/OIDC JWTs.
- Standard CLIs: `curl`, `jq`, `ldapsearch`/`ldapadd` (openldap-clients),
  `kinit`/`klist`/`kvno` (krb5), `xmllint`, `openssl`, `docker`.

## How it relates to the rest of the toolkit
This is the **protocol-level, hands-on** complement to the architecture-level
`../../sso/` section (federation design for AWS/Azure/GCP) and the identity work
in `../../iam/` and `../../zero-trust/`. Do `00-setup.md` first; the other labs
are independent but share the lab stack.

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md). Each lab says exactly what to
capture (a traced flow, a validated token/assertion, a provisioning run).
