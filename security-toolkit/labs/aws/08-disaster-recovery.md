# Lab 08 — Disaster Recovery, RTO/RPO & DR Exercises

**Skills practiced:** AWS Backup · cross-region replication · AWS Elastic
Disaster Recovery · RTO/RPO alignment · DR exercise execution & documentation ·
failover verification.
**Proves (JD — KBR):** the DR/contingency core — configure, test, validate, and
document recovery aligned to documented Recovery Time/Point Objectives.

## Objective
Protect a small workload with AWS-native DR, declare its RTO/RPO, and **prove the
objectives are achievable** with a real DR exercise — then verify the register
with the toolkit.

## Est. time / cost
3–4 h · **~$1–3** (AWS Backup storage, cross-region copy, brief restore; tear
down restored resources).

## Prerequisites
- Labs 00, 05 done. AWS CLI v2. A small workload (EC2 + EBS, maybe RDS/S3).
- Tool: `../../cloud/dr/dr_readiness.py` + `../../cloud/dr/dr_register.example.csv`.

---

## Part A — Build: declare objectives & protect
1. Write a **DR register** (copy `dr_register.example.csv`): for each system set
   `tier`, `rto_hours`, `rpo_hours`, `backup_frequency_hours`, `cross_region`,
   `last_dr_test_days`.
2. Create an **AWS Backup** plan: schedule matching the RPO, a vault, and a
   **cross-region copy action** for mission-tier systems.
3. (Optional) Set up **AWS Elastic Disaster Recovery** for a server for low-RTO
   replication.

## Part B — Attack / observe: can the objective actually be met?
1. Run the readiness tool against your register:
   ```bash
   python3 ../../cloud/dr/dr_readiness.py --register cloud/dr/dr_register.csv
   ```
   It flags where **backup interval > RPO** (data-loss window violates the
   objective) and **mission systems without cross-region** copy.
2. Fix the register/backup config until the offline check is clean.

## Part C — Harden / operate: run a DR exercise
1. **Execute a restore** in the recovery Region: restore a backup / fail over
   with Elastic DR to a recovery instance.
2. **Time it** — measure actual **RTO** (time to usable) and **RPO** (data age at
   recovery). Compare to the documented objectives.
3. **Verify integrity:** app comes up, data is consistent, monitoring works in
   the recovery Region (ties to lab 07).
4. **Document** the exercise: steps, timings, screenshots, gaps, corrective
   actions. Update `last_dr_test_days` to 0.

## Part D — Verify
```bash
# Register now aligns AND live AWS Backup has plans + cross-region copy:
python3 ../../cloud/dr/dr_readiness.py --register cloud/dr/dr_register.csv --aws
# Expect: RPO met for all, cross-region present for mission, exit 0.
```

## Cleanup
Delete recovery-Region resources, backup copies (mind retention/legal hold), the
recovery instances, and the DR drill artifacts you don't need.

## Portfolio artifact
- A **DR exercise report**: objectives vs. measured RTO/RPO, timeline, evidence,
  gaps, corrective actions (the exact deliverable the JD names).
- The **DR register** + `dr_readiness.py` output (gaps → aligned).
- A recovery-architecture diagram (primary → cross-region recovery).

## Stretch goals
- Add **pilot-light vs warm-standby** options and compare cost vs RTO.
- Automate the DR drill (Step Functions / runbook) and re-measure RTO.
- Chaos-style: kill the primary and run an unplanned failover.
