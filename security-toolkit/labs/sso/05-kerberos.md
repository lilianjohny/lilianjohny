# Lab 05 — Kerberos

**Skills practiced:** realms, principals, KDC · `kinit`/`klist`/`kdestroy` ·
keytabs · service principals (SPNs) · SPNEGO desktop SSO · ticket troubleshooting.
**Proves (JD):** design & support **Kerberos** integrations.

## Objective
Operate a Kerberos realm: get a TGT, create a service principal + keytab, request
a service ticket, and wire **SPNEGO** so a Kerberos-authenticated desktop gets
SSO into the IdP — the "already logged into Windows/AD, no re-prompt" experience.

## Est. time / cost
1.5–2 h · **~$0**. Prereq: Lab 00 stack up (`kdc`). Needs `krb5-user`.

---

## Part A — Point your client at the realm
```bash
sudo tee /etc/krb5.conf >/dev/null <<'CONF'
[libdefaults]
  default_realm = EXAMPLE.ORG
  dns_lookup_kdc = false
[realms]
  EXAMPLE.ORG = { kdc = localhost:88  admin_server = localhost:749 }
[domain_realm]
  .example.org = EXAMPLE.ORG
CONF
```

## Part B — Principals & tickets
```bash
# Create a user principal in the KDC (kadmin inside the container)
docker compose -f ~/sso-lab/docker-compose.yml exec kdc \
  kadmin.local -q "addprinc -pw Passw0rd! jsmith"
# Get a TGT as that user, then list it:
kinit jsmith            # enter Passw0rd!
klist                   # shows krbtgt/EXAMPLE.ORG@EXAMPLE.ORG (the TGT) + lifetimes
```
Read `klist`: the **TGT** (`krbtgt/REALM`) is your "login" ticket; **service
tickets** are issued from it per service.

## Part C — Service principal + keytab (how a service joins the realm)
```bash
docker compose -f ~/sso-lab/docker-compose.yml exec kdc \
  kadmin.local -q "addprinc -randkey HTTP/app.example.org@EXAMPLE.ORG"
docker compose -f ~/sso-lab/docker-compose.yml exec kdc \
  kadmin.local -q "ktadd -k /tmp/app.keytab HTTP/app.example.org@EXAMPLE.ORG"
docker compose -f ~/sso-lab/docker-compose.yml cp kdc:/tmp/app.keytab ./app.keytab
klist -kte app.keytab   # lists the SPN + enctypes stored in the keytab
# Request a service ticket for that SPN (proves end-to-end issuance):
kvno HTTP/app.example.org@EXAMPLE.ORG && klist
```

## Part D — SPNEGO desktop SSO (IdP) + break/fix
**Keycloak GUI:** realm `sso-lab` → **User federation → (your LDAP/Kerberos
provider) → Kerberos integration**: set **Kerberos realm** `EXAMPLE.ORG`,
**Server principal** `HTTP/app.example.org@EXAMPLE.ORG`, upload **`app.keytab`**,
enable **HTTP SPNEGO**. A browser configured to trust the host then gets SSO with
no password (the Negotiate/SPNEGO header carries the service ticket).
Support cases you'll see constantly:
- **Clock skew > 5 min** → `KRB_AP_ERR_SKEW`. Fix = NTP everywhere.
- **Wrong/old keytab (kvno mismatch after a password change)** → decrypt errors.
  Fix = re-`ktadd` and redeploy the keytab.
- **SPN not registered / duplicate SPN** → no ticket. Fix = one SPN per service.

## Verify
```bash
klist                                   # TGT present after kinit
kvno HTTP/app.example.org@EXAMPLE.ORG   # service ticket issued → SPN + keytab are correct
klist -kte app.keytab                   # keytab holds the SPN
```

## Portfolio artifact
- `klist` (TGT), `kvno` (service ticket), and `klist -kte` (keytab) outputs.
- A ticket-flow diagram (client → AS-REQ/TGT → TGS-REQ/service ticket → service).
- The three break/fix notes (skew, keytab/kvno, SPN) — real Kerberos support.

## Stretch goals
- Add **constrained delegation (S4U2proxy)** conceptually; document the flow.
- Compare **Kerberos (intranet, ticket-based) vs SAML/OIDC (web, token-based)**.
- Enable **AES-only** enctypes; remove RC4.
