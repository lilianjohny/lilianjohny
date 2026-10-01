# Lab 04 — LDAP

**Skills practiced:** LDAP bind & search · DNs, objectClasses, attributes · adding
users/groups · federating an IdP to an LDAP directory (user federation) · LDAPS.
**Proves (JD):** design & support **LDAP** integrations.

## Objective
Operate an LDAP directory (bind, search, add, modify), then federate Keycloak to
it so directory users can SSO — the classic "IdP in front of corporate LDAP/AD".

## Est. time / cost
1–1.5 h · **~$0**. Prereq: Lab 00 stack up (`openldap`). Needs `ldap-utils`.

---

## Part A — Bind & search
```bash
BASE="dc=example,dc=org"; ADMIN="cn=admin,$BASE"; PW=adminpw
# Who/what is in the tree?
ldapsearch -x -H ldap://localhost -D "$ADMIN" -w "$PW" -b "$BASE" -LLL "(objectClass=*)" dn
```
Understand the pieces: **DN** (distinguished name = the path), **objectClass**
(schema: `inetOrgPerson`, `groupOfNames`), **attributes** (`uid`, `mail`, `cn`).

## Part B — Add an OU, a user, and a group
```bash
cat > /tmp/seed.ldif <<'LDIF'
dn: ou=people,dc=example,dc=org
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=example,dc=org
objectClass: organizationalUnit
ou: groups

dn: uid=jsmith,ou=people,dc=example,dc=org
objectClass: inetOrgPerson
uid: jsmith
cn: Jordan Smith
sn: Smith
mail: jsmith@example.com
userPassword: Passw0rd!

dn: cn=platform-readonly,ou=groups,dc=example,dc=org
objectClass: groupOfNames
cn: platform-readonly
member: uid=jsmith,ou=people,dc=example,dc=org
LDIF
ldapadd -x -H ldap://localhost -D "$ADMIN" -w "$PW" -f /tmp/seed.ldif
# Verify + test the user's own bind (authentication):
ldapsearch -x -H ldap://localhost -D "$ADMIN" -w "$PW" -b "ou=people,$BASE" -LLL "(uid=jsmith)" mail cn
ldapwhoami -x -H ldap://localhost -D "uid=jsmith,ou=people,$BASE" -w 'Passw0rd!'   # authenticates as the user
```

## Part C — Federate the IdP to LDAP (user federation)
**Keycloak GUI:** realm `sso-lab` → **User federation → Add Ldap provider**:
- Connection URL `ldap://openldap:389` (container network) or `ldap://localhost:389`
- Bind DN `cn=admin,dc=example,dc=org`, Bind credential `adminpw`
- Users DN `ou=people,dc=example,dc=org`, Username LDAP attribute `uid`,
  RDN `uid`, UUID `entryUUID`, User object classes `inetOrgPerson`
- **Save → Synchronize all users.** Now `jsmith` from LDAP can log in via OIDC/SAML.
Add a **group-ldap-mapper** to import `ou=groups` → Keycloak groups.

## Part D — Harden & break/fix
- **LDAPS / StartTLS:** plain LDAP sends the bind password in cleartext. In prod
  use `ldaps://…:636` or StartTLS; test with `ldapsearch -H ldaps://localhost:636`.
- **Service-account least privilege:** the bind DN should be read-only (+ password
  reset if needed), not a directory admin.
- Support cases: **wrong Users DN / username attribute** (users don't appear),
  **referral chasing** (AD multi-domain), **account lockout** on bad binds.

## Verify
```bash
ldapwhoami -x -H ldap://localhost -D "uid=jsmith,ou=people,$BASE" -w 'Passw0rd!'   # dn:uid=jsmith...
# In Keycloak: Users → jsmith shows as federated (LDAP) and can log in.
```

## Portfolio artifact
- Your seed LDIF + search output, and a screenshot of the Keycloak LDAP
  federation + group mapper.
- A note: **LDAP = directory/authN source**; the **IdP** fronts it to speak
  SAML/OIDC to apps — and why LDAPS matters.

## Stretch goals
- Point federation at a **real AD** schema (sAMAccountName, memberOf).
- Configure **sync modes** (import vs read-only) and a periodic full sync.
- Enforce **LDAPS** and verify the cert.
