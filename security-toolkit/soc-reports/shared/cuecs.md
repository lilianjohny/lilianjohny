# Complementary User Entity Controls (CUECs)

CUECs are controls that the **service organization assumes its customers (user
entities) will implement** for the overall control objectives / criteria to be
met. They appear in SOC 1 and SOC 2 reports so user entities know what they are
responsible for. Identify them during scoping and list them in the report.

## How to identify CUECs
For each control objective / TSC criterion, ask: *"Is there anything the
customer must do for this control to be effective end-to-end?"* If yes, it's a
CUEC.

## Common CUECs (adapt)
- Manage their own user accounts within the service (create/review/remove).
- Enforce their own password/MFA settings where the service offers them.
- Configure the service securely per provided guidance (hardening, RBAC).
- Review reports/alerts the service makes available and act on exceptions.
- Protect API keys/credentials issued to them; rotate on compromise.
- Ensure data they submit is accurate, authorized, and lawful to process.
- Notify the service organization of security incidents affecting the service.
- Maintain their own BC/DR for data they are responsible for.

## Template

| CUEC ID | Related objective / criterion | User-entity control | Why it's needed |
|---------|-------------------------------|---------------------|-----------------|
| CUEC-1 | CC6.1 / CO-5 | Customer manages and reviews its own user access | Service cannot see business need for each user |
| CUEC-2 | CC6.6 | Customer protects issued API credentials | Credential custody is on the customer side |
| CUEC-3 | PI1.2 | Customer validates accuracy of submitted data | Only the customer knows the source-of-truth |
