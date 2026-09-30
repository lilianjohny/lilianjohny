# Lab 03 — Secret Management & Machine Identity

**Skills practiced:** centralized vaulting · dynamic/short-lived secrets ·
rotation · machine identity (no static creds) · secret-sprawl detection.
**Proves (JD — OpenAI InfraSec):** *"secret management"* and *"machine identity."*

## Objective
Replace static, sprawled secrets with a vault-backed model: services authenticate
with a machine identity, fetch short-lived secrets, everything rotates. Detect
sprawl first, then fix it.

## Est. time / cost
2–3 h · **~$0** (HashiCorp Vault dev mode in Docker).

## Prerequisites
- Docker. Toolkit: `../../devsecops/` secret scanning.

---

## Part A — Attack / observe: find the sprawl
```bash
bash ../../devsecops/secret_scan.sh .      # or: gitleaks detect --source .
# Note anti-patterns: secrets in env files, container images (../aws/02), CI vars,
# and long-lived API keys that never rotate.
```

## Part B — Build: a vault + machine identity
```bash
# Vault dev server (lab only — never dev mode in prod)
docker run --rm -d --name vault -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=root -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 hashicorp/vault
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
vault status
# AppRole = a machine identity (a workload proves identity, not a shared password)
vault auth enable approle
vault policy write app - <<'EOF'
path "secret/data/app/*" { capabilities = ["read"] }
EOF
vault write auth/approle/role/app token_policies=app token_ttl=15m token_max_ttl=30m
ROLE_ID=$(vault read -field=role_id auth/approle/role/app/role-id)
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/app/secret-id)
# The workload logs in with its identity and gets a SHORT-LIVED token
APP_TOKEN=$(vault write -field=token auth/approle/login role_id=$ROLE_ID secret_id=$SECRET_ID)
```

## Part C — Harden: dynamic, short-lived, rotated, least-privilege
```bash
vault kv put secret/app/db password=$(openssl rand -base64 18)   # store a secret
VAULT_TOKEN=$APP_TOKEN vault kv get secret/app/db                # app reads via its identity (15m TTL)
# Dynamic DB secrets (unique, short-TTL creds per request) — enable + configure:
vault secrets enable database
# vault write database/config/mydb plugin_name=postgresql-database-plugin ...
# vault write database/roles/app db_name=mydb creation_statements="CREATE ROLE ..." default_ttl=15m
# Least privilege: the 'app' policy can read only secret/data/app/* — test denial:
VAULT_TOKEN=$APP_TOKEN vault kv get secret/other 2>&1 | grep -i denied   # ✅ denied
```
Enable TLS to Vault and KMS/auto-unseal in real deployments; remove the sprawled
secrets from Part A and inject from Vault instead.

## Part D — Verify
```bash
bash ../../devsecops/secret_scan.sh .    # clean — no hardcoded secrets left
# The app gets a 15m token via its machine identity; a different identity/policy
# CANNOT read its secrets (tested above).
```

## Cleanup
```bash
docker rm -f vault
```

## Portfolio artifact
- **Before/after**: secret-scan sprawl → vault-backed, zero hardcoded secrets.
- A **machine-identity diagram**: service → AppRole → scoped policy → short-lived secret.
- A note on **dynamic vs static** secrets and why short TTL shrinks blast radius.

## Stretch goals
- Wire the vault into **Kubernetes** (CSI driver / agent injector) from `../aws/03`.
- Send **secret-access audit logs** → your SIEM (`../../soc/`); alert on anomalies.
- Implement **break-glass** secret access with heavy alerting.
