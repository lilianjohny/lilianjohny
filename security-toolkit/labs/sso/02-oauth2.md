# Lab 02 — OAuth 2.0

**Skills practiced:** authorization-code + PKCE flow · client-credentials flow ·
token endpoint, scopes, access/refresh tokens · token introspection.
**Proves (JD):** design & support **OAuth** integrations.

## Objective
Run the two OAuth flows you'll support most — **authorization code + PKCE** (user
apps) and **client credentials** (machine-to-machine) — end to end against
Keycloak, and inspect the tokens.

## Est. time / cost
1–2 h · **~$0**. Prereq: Lab 00 stack up.

---

## Part A — Build: an OAuth client
**GUI:** Keycloak → realm `sso-lab` → **Clients → Create client** → Type
**OpenID Connect** → Client ID `app-oauth` → **Client authentication = On** for
the client-credentials part; add a **public** client `spa-pkce`
(Client authentication Off, Standard flow On, redirect URI
`http://localhost:9999/callback`) for the PKCE part.
```bash
ISS=http://localhost:8080/realms/sso-lab
curl -s $ISS/.well-known/openid-configuration | jq '{authz:.authorization_endpoint, token:.token_endpoint}'
```

## Part B — Authorization code + PKCE (public client)
```bash
# 1. Make a PKCE verifier + challenge
VERIFIER=$(openssl rand -base64 60 | tr -d '\n=+/' | cut -c1-64)
CHALLENGE=$(printf '%s' "$VERIFIER" | openssl dgst -sha256 -binary | openssl base64 | tr '+/' '-_' | tr -d '=\n')
# 2. Open the authorize URL in a browser, log in as jsmith, copy ?code= from the redirect:
echo "$ISS/protocol/openid-connect/auth?response_type=code&client_id=spa-pkce&redirect_uri=http://localhost:9999/callback&scope=openid%20email&code_challenge=$CHALLENGE&code_challenge_method=S256"
# 3. Exchange the code (PKCE verifier proves it's the same client — no secret):
CODE='<paste-code>'
curl -s -X POST $ISS/protocol/openid-connect/token \
  -d grant_type=authorization_code -d client_id=spa-pkce \
  -d redirect_uri=http://localhost:9999/callback \
  -d code="$CODE" -d code_verifier="$VERIFIER" | jq .
```

## Part C — Client credentials (machine-to-machine)
```bash
SECRET=$(docker compose -f ~/sso-lab/docker-compose.yml exec keycloak \
  /opt/keycloak/bin/kcadm.sh get clients -r sso-lab -q clientId=app-oauth \
  --fields 'secret' 2>/dev/null | jq -r '.[0].secret' 2>/dev/null)
# (or copy the secret from the client's Credentials tab)
curl -s -X POST $ISS/protocol/openid-connect/token \
  -d grant_type=client_credentials -d client_id=app-oauth -d client_secret="$SECRET" | jq .
```

## Part D — Inspect & break/fix
```bash
# Inspect the access token (JWT): alg, exp, scope, aud
ACCESS=$(curl -s -X POST $ISS/protocol/openid-connect/token \
  -d grant_type=client_credentials -d client_id=app-oauth -d client_secret="$SECRET" | jq -r .access_token)
python3 ../../appsec/crypto/jwt_inspect.py "$ACCESS"
```
Support cases to try: **wrong `redirect_uri`** at the token step (→ invalid_grant),
**missing PKCE verifier** on a public client (→ error), **expired code** (codes are
single-use + short-lived). These are the exact errors you'll triage in tickets.

## Verify
- PKCE exchange returns an `access_token` (+ `id_token` with `openid` scope).
- Client-credentials returns an app token with the right `aud`/scopes.
- `jwt_inspect.py` shows a strong `alg` (not `none`) and a short `exp`.

## Portfolio artifact
- A traced **auth-code+PKCE** sequence (authorize → code → token) and a
  **client-credentials** call, with the decoded tokens.
- A note on **why PKCE** (public clients can't hold a secret) and **when to use
  client-credentials** (no user present).

## Stretch goals
- Add a **refresh_token** flow; rotate and revoke.
- Enforce **audience** and **scope**-based access on a protected resource.
- Try **token introspection** (`/token/introspect`) for opaque-token validation.
