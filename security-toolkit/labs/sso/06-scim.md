# Lab 06 — SCIM 2.0 Provisioning

**Skills practiced:** SCIM Users/Groups · create/update/**deprovision** (active=false)
· PATCH vs PUT · ServiceProviderConfig · validating SCIM resources · the JML
(joiner-mover-leaver) lifecycle.
**Proves (JD):** design & support **SCIM** integrations.

## Objective
Drive the SCIM lifecycle against a real SCIM endpoint (Keycloak's SCIM, a SCIM
test server, or raw HTTP), and validate the resources with the toolkit — then
prove the **leaver** path (deprovision) actually disables access.

## Est. time / cost
1–1.5 h · **~$0**. Prereq: Lab 00 stack up. Needs `curl`, `jq`.

---

## Part A — Study the resources (offline, no server needed)
```bash
python3 ../../sso/tools/scim_probe.py ../../sso/tools/sample.scim-user.json     # a User
python3 ../../sso/tools/scim_probe.py ../../sso/tools/sample.spconfig.json      # ServiceProviderConfig
```
Note the key fields: `schemas`, `id`, `userName`, **`active`** (the
enable/disable switch for deprovisioning), `emails`, the enterprise extension,
and — in SP config — whether **PATCH** and **filter** are supported.

## Part B — Stand up a SCIM target
Pick one:
- **SCIM test server** (quickest): `docker run -p 8880:8080 suvera/scim2-server`
  (or any SCIM 2.0 reference server), base URL `http://localhost:8880/scim/v2`.
- **Keycloak SCIM**: enable a SCIM provisioning extension/client, or treat
  Keycloak as the **source** pushing SCIM to an app that exposes `/scim/v2`.
```bash
SCIM=http://localhost:8880/scim/v2
TOK="Bearer devtoken"       # or whatever your server expects
curl -s $SCIM/ServiceProviderConfig -H "Authorization: $TOK" | tee /tmp/spc.json | jq .
python3 ../../sso/tools/scim_probe.py /tmp/spc.json
```

## Part C — The JML lifecycle (create → update → deprovision)
```bash
# JOINER: create a user
curl -s -X POST $SCIM/Users -H "Authorization: $TOK" -H 'Content-Type: application/scim+json' -d '{
 "schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],
 "userName":"jsmith@example.com","active":true,
 "name":{"givenName":"Jordan","familyName":"Smith"},
 "emails":[{"value":"jsmith@example.com","primary":true}]}' | tee /tmp/u.json | jq .
UID=$(jq -r .id /tmp/u.json)
python3 ../../sso/tools/scim_probe.py /tmp/u.json

# MOVER: PATCH a single attribute (incremental — needs PATCH support)
curl -s -X PATCH $SCIM/Users/$UID -H "Authorization: $TOK" -H 'Content-Type: application/scim+json' -d '{
 "schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
 "Operations":[{"op":"replace","path":"name.givenName","value":"Jordy"}]}' | jq .name

# LEAVER (the critical one): deprovision = set active=false, do NOT just delete
curl -s -X PATCH $SCIM/Users/$UID -H "Authorization: $TOK" -H 'Content-Type: application/scim+json' -d '{
 "schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
 "Operations":[{"op":"replace","path":"active","value":false}]}' | jq '{active}'
```

## Part D — Verify & break/fix
```bash
# Confirm the leaver is disabled (active=false) — access should be gone:
curl -s $SCIM/Users/$UID -H "Authorization: $TOK" | tee /tmp/u2.json | jq '{userName,active}'
python3 ../../sso/tools/scim_probe.py /tmp/u2.json
# Filter/lookup (reconciliation): find by userName
curl -s "$SCIM/Users?filter=userName%20eq%20%22jsmith@example.com%22" -H "Authorization: $TOK" | jq '.totalResults'
```
Support cases: **no PATCH support** (SP config `patch.supported=false`) forces
full PUT replaces and risks clobbering fields; **no `active`** means a leaver can
only be hard-deleted (loses audit trail); **filter unsupported** breaks
reconciliation. The toolkit flags all three.

## Verify
```bash
python3 ../../sso/tools/scim_probe.py /tmp/u2.json     # active=false represented
# Success = joiner created, mover PATCHed one field, leaver disabled (active=false),
# and lookup-by-filter works.
```

## Portfolio artifact
- The full JML run (create → PATCH → deprovision) with responses, and
  `scim_probe.py` validation of a User + the ServiceProviderConfig.
- A note: **deprovision = active=false, not delete** — and why PATCH + filter
  support matter for safe, incremental sync.

## Stretch goals
- Provision **Groups** and PATCH membership (add/remove one member).
- Wire **Keycloak/Entra → this SCIM endpoint** and watch a real sync.
- Handle **pagination** (`startIndex`/`count`) on a large `/Users` list.
