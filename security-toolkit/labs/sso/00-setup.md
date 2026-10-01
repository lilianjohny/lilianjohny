# Lab 00 — Local SSO Lab Stack (Docker)

**Skills practiced:** standing up an IdP, a directory, and a KDC locally so you
can design/support SSO without cloud or production access.
**Proves (JD):** the foundation for every protocol lab that follows.

## Objective
Run **Keycloak** (SAML + OAuth2 + OIDC IdP), **OpenLDAP** (directory), and an
**MIT Kerberos KDC** locally in Docker, plus client CLIs. One stack serves every
other lab in this track.

## Est. time / cost
30–45 min · **~$0** (all local containers).

## Prerequisites
```bash
docker --version && docker compose version    # Docker + Compose v2
# Client CLIs:
# Debian/Ubuntu:
sudo apt-get update && sudo apt-get install -y ldap-utils krb5-user libxml2-utils jq curl openssl
# macOS: brew install openldap krb5 libxml2 jq ; (krb5/openldap are keg-only — add to PATH)
```

---

## Part A — Create the stack
```bash
mkdir -p ~/sso-lab && cd ~/sso-lab
cat > docker-compose.yml <<'YAML'
services:
  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    command: start-dev
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: admin
    ports: ["8080:8080"]
  openldap:
    image: osixia/openldap:1.5.0
    environment:
      LDAP_ORGANISATION: "Example Org"
      LDAP_DOMAIN: "example.org"
      LDAP_ADMIN_PASSWORD: "adminpw"
    ports: ["389:389", "636:636"]
  kdc:
    image: gcavalcante8808/krb5-server
    environment:
      KRB5_REALM: EXAMPLE.ORG
      KRB5_KDC: localhost
      KRB5_PASS: kdcpw
    ports: ["88:88", "749:749"]
YAML
docker compose up -d
docker compose ps            # all three Up
```

## Part B — Verify each service
```bash
# Keycloak admin console (browser): http://localhost:8080  (admin/admin)
curl -s http://localhost:8080/realms/master/.well-known/openid-configuration | jq .issuer

# OpenLDAP: anonymous/admin bind + base search
ldapsearch -x -H ldap://localhost -b "dc=example,dc=org" \
  -D "cn=admin,dc=example,dc=org" -w adminpw -LLL "(objectClass=*)" dn

# Kerberos KDC reachable (kinit comes in Lab 05)
docker compose logs kdc | tail -5
```

## Part C — Create a realm + a test user (Keycloak)
**GUI:** http://localhost:8080 → admin → **Create realm** → name `sso-lab` →
**Users → Create user** `jsmith` → **Credentials** → set password (temporary off)
→ **Email** `jsmith@example.com`.
**CLI (kcadm):**
```bash
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master --user admin --password admin
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create realms -s realm=sso-lab -s enabled=true
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create users -r sso-lab \
  -s username=jsmith -s email=jsmith@example.com -s enabled=true
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh set-password -r sso-lab \
  --username jsmith --new-password 'Passw0rd!'
```

## Verify
```bash
docker compose ps                                   # keycloak, openldap, kdc all Up
curl -s http://localhost:8080/realms/sso-lab/.well-known/openid-configuration | jq .issuer
```
Success = the `sso-lab` realm resolves, LDAP binds, the KDC container is up.

## Cleanup (after you finish the whole track)
```bash
cd ~/sso-lab && docker compose down -v
```

## Portfolio artifact
- The `docker-compose.yml` + a screenshot of the Keycloak realm and an LDAP
  search result — proof you can stand up an IdP + directory + KDC from scratch.

## Notes
- Images are examples; if one tag moves, pick the current official image (Keycloak
  `quay.io/keycloak/keycloak`, OpenLDAP `osixia/openldap` or `bitnami/openldap`,
  a maintained `krb5-server`). The protocols and commands in the labs are stable.
