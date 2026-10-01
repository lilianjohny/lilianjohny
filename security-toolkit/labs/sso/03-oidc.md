# Lab 03 — OpenID Connect

**Skills practiced:** OIDC discovery · ID token (claims, `nonce`, `aud`, `iss`) ·
userinfo · JWKS & signature validation · provider posture review.
**Proves (JD):** design & support **OpenID Connect** integrations.

## Objective
Use OIDC on top of OAuth: pull the discovery document, obtain and validate an
**ID token**, call **userinfo**, and review the provider's posture with the toolkit.

## Est. time / cost
1–1.5 h · **~$0**. Prereq: Labs 00 + 02 (reuse `spa-pkce`).

---

## Part A — Discovery & posture
```bash
ISS=http://localhost:8080/realms/sso-lab
curl -s $ISS/.well-known/openid-configuration -o /tmp/disc.json
python3 ../../sso/tools/oidc_discover.py --file /tmp/disc.json
# Checks: required endpoints, issuer HTTPS (note: local http is a lab exception),
# PKCE S256, id_token alg != none, openid scope, implicit-flow warnings.
jq '{jwks:.jwks_uri, userinfo:.userinfo_endpoint}' /tmp/disc.json
```
(Study the structure with the committed sample: `../../sso/tools/sample.discovery.json`.)

## Part B — Get an ID token (auth-code + PKCE, `scope=openid`)
Repeat the PKCE flow from Lab 02 but request `scope=openid email profile`; the
token response now includes an **`id_token`**:
```bash
RESP=$(curl -s -X POST $ISS/protocol/openid-connect/token \
  -d grant_type=authorization_code -d client_id=spa-pkce \
  -d redirect_uri=http://localhost:9999/callback \
  -d code="$CODE" -d code_verifier="$VERIFIER")
ID=$(echo "$RESP" | jq -r .id_token)
python3 ../../appsec/crypto/jwt_inspect.py "$ID"
```

## Part C — Validate the ID token (the support checklist)
From the decoded token, confirm:
- **`iss`** == the discovery `issuer`.
- **`aud`** == your client_id (`spa-pkce`).
- **`exp`** in the future, **`iat`** recent; **`nonce`** matches what you sent.
- **`alg`** is RS256/ES256 (never `none`); the signing key is in the **JWKS**:
  ```bash
  curl -s $(jq -r .jwks_uri /tmp/disc.json) | jq '.keys[].kid'
  # the token header 'kid' must be one of these keys.
  ```

## Part D — userinfo + break/fix
```bash
curl -s $(jq -r .userinfo_endpoint /tmp/disc.json) \
  -H "Authorization: Bearer $(echo "$RESP" | jq -r .access_token)" | jq .
```
Support cases: **`aud` mismatch** (token minted for another client → reject),
**`nonce` missing/replayed** (CSRF/replay), **`kid` not in JWKS** (rotated keys /
wrong issuer). Each is a real "login works then breaks after a key rotation" ticket.

## Verify
```bash
python3 ../../sso/tools/oidc_discover.py --file /tmp/disc.json     # posture
python3 ../../appsec/crypto/jwt_inspect.py "$ID"                   # iss/aud/exp/alg
```
Success = discovery clean, ID token validates (iss/aud/exp/nonce/alg), userinfo
returns the expected claims.

## Portfolio artifact
- The discovery posture output + a validated ID token with each claim annotated.
- A "OIDC vs OAuth" note (OIDC = authentication layer / `id_token` on top of OAuth
  authorization).

## Stretch goals
- Rotate the realm keys and show the token's `kid` → JWKS binding update.
- Add a custom claim mapper (groups) and consume it.
- Compare **front-channel vs back-channel logout**.
