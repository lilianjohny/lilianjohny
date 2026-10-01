# Lab 01 — SAML 2.0 SSO

**Skills practiced:** SP↔IdP metadata exchange · SAML redirect/POST bindings ·
assertion structure · signing & conditions · tracing and validating a login.
**Proves (JD):** design & support **SAML** integrations.

## Objective
Federate a Service Provider to Keycloak over SAML, log in, capture the assertion,
and validate it with the toolkit — then break signing to see the failure.

## Est. time / cost
1–2 h · **~$0**. Prereq: Lab 00 stack up.

---

## Part A — Build: an SP client in Keycloak
**GUI:** Keycloak → realm `sso-lab` → **Clients → Create client** → Type **SAML**
→ Client ID = `https://sp.example.com/metadata` (this is the SP entityID) →
**Valid redirect URIs / Master SAML Processing URL** = `https://sp.example.com/acs`
→ Save. Under **Keys**, keep **Sign assertions = On**.
Grab the IdP metadata (contains the signing cert + SSO endpoints):
```bash
curl -s http://localhost:8080/realms/sso-lab/protocol/saml/descriptor -o idp-metadata.xml
xmllint --format idp-metadata.xml | head -40      # IdP entityID, SSO URLs, X509 cert
```

## Part B — Use / trace: perform a login and capture the assertion
A SAML login is: SP → `AuthnRequest` (Redirect) → IdP login → `Response` (POST to ACS).
You can trace it in the browser dev-tools **Network** tab (filter `SAML`) at the
`/acs` POST, or generate one via Keycloak's SAML test. Save the base64
`SAMLResponse` form field to a file:
```bash
# paste the SAMLResponse value:
printf '%s' '<base64-SAMLResponse>' > /tmp/resp.b64
# Decode + pretty-print to read it:
base64 -d /tmp/resp.b64 | xmllint --format -
```
(No live capture handy? Use the committed sample to learn the structure:
`../../sso/tools/sample.saml.b64`.)

## Part C — Validate with the toolkit
```bash
python3 ../../sso/tools/saml_inspect.py /tmp/resp.b64 \
  --audience https://sp.example.com/metadata
# Checks: Status=Success, signature present, Conditions window, AudienceRestriction
# matches YOUR entityID, SubjectConfirmation Recipient = your ACS, attributes released.
```
Read each line against the spec: the **Audience** must equal your SP entityID,
the **Recipient** must equal your ACS URL, and the assertion must be **signed**.

## Part D — Break & fix (support muscle)
1. **Turn off assertion signing** on the client (Keycloak → client → Keys →
   Sign assertions = Off), log in again, re-run `saml_inspect.py` → it FAILs on
   "no signature". Turn it back on. (This is the single most common real SAML
   misconfig.)
2. **Audience mismatch:** run the inspector with a wrong `--audience` → FAIL.
   This mirrors the classic "works for app A, fails for app B" ticket.
3. **Clock skew:** note how an expired `NotOnOrAfter` fails — the #1 cause of
   intermittent SAML failures (fix = NTP on SP and IdP).

## Verify
```bash
python3 ../../sso/tools/saml_inspect.py /tmp/resp.b64 --audience https://sp.example.com/metadata
# Success = Status Success, signature present, within window, audience + recipient match.
```

## Portfolio artifact
- The decoded, annotated assertion + `saml_inspect.py` output (signed/valid).
- A short "SAML login flow" diagram (AuthnRequest → IdP → signed Response → ACS).
- A note on the three break/fix cases (unsigned, wrong audience, clock skew).

## Stretch goals
- Add an **AttributeMapper** (groups/role) in Keycloak and confirm it appears.
- Configure **SP-initiated vs IdP-initiated** SSO and compare.
- Enforce **signed AuthnRequests** and **encrypted assertions**.
