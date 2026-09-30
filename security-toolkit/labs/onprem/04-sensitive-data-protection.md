# Lab 04 — Sensitive-Data / Model-Weight Protection

**Skills practiced:** classification · encryption at rest & in transit · access-
pathway control · checkpoint/large-artifact encryption · exfiltration control ·
insider-threat mitigation.
**Proves (JD — OpenAI InfraSec):** protecting "highly sensitive model weights and
user data" — "checkpoint encryption," controlled "access pathways."

## Objective
Treat a high-value asset (stand-in for model weights) as a protect-surface:
classify it, encrypt it end-to-end, tightly control who/what can reach it, and
make exfiltration hard and loud — against external adversaries and insiders.

## Est. time / cost
2–3 h · **~$0** (local + openssl/age; or a small bucket + KMS).

## Prerequisites
- Labs `03` (vault/machine identity) here + `../aws/01` (authZ). `openssl` (and
  optionally `age`). Toolkit: `../../zero-trust/`, `../../cloud/detection/`.

---

## Part A — Classify & model the threat
1. Define the asset: a large "checkpoint" file. Classify it crown-jewel.
   ```bash
   head -c 50M /dev/urandom > /tmp/checkpoint.bin   # stand-in for weights
   ```
2. Threat model: external theft, a compromised training/inference host, and a
   **malicious insider** with legitimate-ish access. Enumerate the access
   pathways (who/what service, over which network path).

## Part B — Encrypt end to end
```bash
# Envelope encryption: a data key wraps the artifact; the data key is protected by a KMS/Vault key.
DK=$(openssl rand -base64 32)                                   # data key
openssl enc -aes-256-gcm -pbkdf2 -in /tmp/checkpoint.bin -out /tmp/checkpoint.enc -k "$DK"
# Wrap the data key with Vault (from Lab 03) so only an attested workload identity can unwrap it:
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root
vault secrets enable transit 2>/dev/null; vault write -f transit/keys/weights
WRAPPED=$(echo -n "$DK" | base64 | vault write -field=ciphertext transit/encrypt/weights plaintext=-)
echo "$WRAPPED" > /tmp/checkpoint.key.wrapped
# A stolen /tmp/checkpoint.enc is useless without unwrapping the key via the workload identity.
```
In transit: require **TLS/mTLS** for every read/write path (no plaintext copy).

## Part C — Control the access pathways
1. **Least privilege + machine identity:** only a specific, attested workload
   (Lab 02) with a scoped identity (Lab 03) can unwrap the key — no human standing
   access. Test that another identity's unwrap is denied.
2. **Network isolation:** the storage is reachable only from the training/
   inference segment (default-deny; Lab 01 / `../aws/05`).
3. **Zero Trust per request:** authorize each access on identity + device posture
   (Lab 02 attestation) + context — `../../zero-trust/policies/opa-abac-example.rego`.
4. **Separation of duties:** whoever reads data can't manage keys, and vice versa.

## Part D — Detect & prevent exfiltration
```bash
# Log every access to the artifact + the key; alert on anomalies (bulk reads,
# new identity/host, off-hours, egress to internet). Feed your SIEM (../../soc/).
# Simulate an insider bulk-download from the data segment and confirm it's denied/alerted:
#   (on the isolated segment) egress to the internet should be blocked (Lab 01 default-deny)
```

## Verify (checklist)
- [ ] Checkpoint encrypted at rest (per-tier key); data key wrapped by KMS/Vault.
- [ ] All read/write paths use TLS/mTLS; no plaintext copy.
- [ ] Only an attested workload with scoped identity can unwrap; no human standing access.
- [ ] Storage reachable only from the intended segment (default-deny elsewhere).
- [ ] Access + key use logged; anomaly/exfil alerts fire.

## Cleanup
```bash
rm -f /tmp/checkpoint.bin /tmp/checkpoint.enc /tmp/checkpoint.key.wrapped
vault delete transit/keys/weights 2>/dev/null; docker rm -f vault 2>/dev/null
```

## Portfolio artifact
- A **data-protection architecture** for a crown-jewel asset: classification →
  encryption → access pathways → detection.
- The **insider-threat test**: attempted bulk exfil → denied/alerted evidence.
- A diagram of the **key/identity/network** controls around the asset.

## Stretch goals
- **Confidential computing** (encrypted-in-use / enclaves) for the inference path.
- **Honeytokens** in the data path to catch unauthorized access.
- Tie decrypt authorization to **hardware attestation** (Lab 02).
