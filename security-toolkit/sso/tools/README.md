# SSO protocol tools

Small, offline-capable validators for the artifacts you handle when designing and
supporting SSO integrations. All follow the toolkit's exit-code contract
(`0` clean · `1` warn · `2` findings · `3` setup error) and `[OK]/[WARN]/[FAIL]`
output. Used throughout `../../labs/sso/`.

| Tool | Validates | Example |
|------|-----------|---------|
| `saml_inspect.py` | SAML 2.0 Response/assertion: status, signature presence, Conditions window, AudienceRestriction, SubjectConfirmation recipient, attributes | `python3 saml_inspect.py sample.saml.b64 --audience https://sp.example.com/metadata` |
| `oidc_discover.py` | OIDC discovery doc: endpoints, HTTPS issuer, PKCE S256, `id_token` alg ≠ `none`, implicit-flow warnings (offline `--file` or live `--url`) | `python3 oidc_discover.py --file sample.discovery.json` |
| `scim_probe.py` | SCIM 2.0 User/Group/ListResponse/ServiceProviderConfig: required attrs, `active` (deprovisioning), PATCH/filter support | `python3 scim_probe.py sample.scim-user.json` |

For OAuth/OIDC **JWTs** (access & ID tokens), use `../../appsec/crypto/jwt_inspect.py`.

Fixtures (`sample.*`) are synthetic and safe to commit — no real tokens or
secrets. `saml_inspect.py` reports whether a signature is *present*; cryptographic
signature verification needs the IdP cert + an xmlsec library and is out of scope
for an offline inspector.
