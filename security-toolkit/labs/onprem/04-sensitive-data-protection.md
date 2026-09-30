# Lab 04 — Sensitive-Data / Model-Weight Protection

**Skills practiced:** data classification · encryption at rest & in transit ·
access-pathway control · checkpoint/large-artifact encryption · exfiltration
control · insider-threat mitigation.
**Proves (JD — OpenAI InfraSec):** protecting "highly sensitive model weights and
user data" — "checkpoint encryption," controlled "access pathways."

## Objective
Treat a high-value data asset (stand in for model weights / checkpoints) as a
protect-surface: classify it, encrypt it end-to-end, tightly control who and what
can reach it, and make exfiltration hard and loud — defending against both
external adversaries and insiders.

## Est. time / cost
2–3 h · **~$0–1** (local or a small bucket + KMS).

## Prerequisites
- Labs `../aws/01` (authZ), `03` (secret mgmt in this track). A KMS/Vault.
- Toolkit: `../../zero-trust/`, `../../cloud/detection/`.

---

## Part A — Classify & model the threat
1. Define the asset: large checkpoints / weights in object storage or a
   filesystem. Classify it top-tier ("crown jewel").
2. Threat model: external theft, a compromised training/inference host, and a
   **malicious insider** with legitimate-ish access. Enumerate the **access
   pathways** (who/what service can read it, over which network path).

## Part B — Encrypt end to end
1. **At rest:** encrypt checkpoints with a **KMS/envelope key**; keys sealed to
   hardware where possible (lab 02 TPM). Different keys per sensitivity tier.
2. **In transit:** TLS/mTLS for every read/write path; no plaintext transfer.
3. **Checkpoint encryption:** encrypt the artifact itself (not just the volume)
   so a stolen file is useless without the key — and the key requires the
   workload's machine identity (lab 03).

## Part C — Control the access pathways
1. **Least privilege + machine identity:** only specific, attested workloads
   (lab 02) with a scoped identity (lab 03) can decrypt — no human standing access.
2. **Network isolation:** the storage is reachable only from the training/
   inference segment (default-deny; ties to `../aws/05` / `onprem/01`).
3. **Zero Trust per request:** each access is authorized on identity + device
   posture + context (`../../zero-trust/policies/opa-abac-example.rego`).
4. **Key/data separation of duties:** whoever can read data can't manage keys,
   and vice versa.

## Part D — Detect & prevent exfiltration
1. **Log every access** to the asset and the keys → SIEM (`../../soc/`).
2. **Alert** on anomalies: bulk reads, access from a new identity/host, off-hours,
   or egress toward the internet.
3. **DLP / egress control:** block large outbound transfers from the data
   segment; require brokered, logged paths.
4. Simulate an insider bulk-download and confirm it's **denied or alerted**.

## Verify (checklist)
- [ ] Checkpoints encrypted at rest with per-tier keys; keys need machine identity.
- [ ] All read/write paths use TLS/mTLS; no plaintext.
- [ ] Only attested workloads with scoped identity can decrypt; no human standing access.
- [ ] Storage reachable only from the intended segment (default-deny elsewhere).
- [ ] Access + key use fully logged; anomaly/exfil alerts fire.

## Portfolio artifact
- A **data-protection architecture** for a crown-jewel asset: classification →
  encryption → access pathways → detection.
- The **insider-threat test**: attempted bulk exfil → denied/alerted evidence.
- A diagram of the **key/identity/network** controls around the asset.

## Stretch goals
- Add **confidential computing** (encrypted-in-use / enclaves) for the inference path.
- Add **honeytokens** in the data path to catch unauthorized access.
- Tie decrypt authorization to **hardware attestation** (lab 02).
