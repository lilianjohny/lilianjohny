# Lab 05 — Network Segmentation

**Skills practiced:** VPC design · public/private subnet tiers · Security Groups
vs NACLs · least-privilege SG references · private service access (VPC
endpoints/PrivateLink) · egress control · no-public-management posture · flow
logs.
**Proves (JD):** *"securing … deployments from construction to multi-tenant use"*
— the network layer of building a datacenter/estate safely.

## Objective
Design and build a segmented VPC the way you'd design a secure datacenter: tiers
that can only talk in the intended direction, no data plane exposed to the
internet, private paths to AWS services, controlled egress, and full traffic
visibility.

## Est. time / cost
2–3 h · **~$1–2** (NAT Gateway + interface endpoints bill hourly — tear down).

## Prerequisites
- Lab 00 done. AWS CLI v2. (Optional: reuse in Labs 03/06.)
- Toolkit: `../../cloud/aws/sg_audit.py`.

---

## Part A — Build: a deliberately flat/open network first
1. A VPC with **one public subnet**; put an app EC2 + a "database" EC2 in it.
2. Security Group with `0.0.0.0/0` on 22 (SSH), 3306 (DB), and 80.
3. Public IPs on both. (This is the anti-pattern: flat, internet-exposed.)

## Part B — Attack / observe: the flat-network problem
1. From your laptop, reach **SSH and the DB port** directly over the internet:
   ```bash
   nc -zv <db-public-ip> 3306      # open to the world  ❌
   nc -zv <app-public-ip> 22       # SSH open to the world  ❌
   ```
2. Note: management (SSH) and data (DB) planes are publicly reachable, and
   everything shares one broadcast domain.
3. Scan it:
   ```bash
   python3 ../../cloud/aws/sg_audit.py       # flags 0.0.0.0/0 on sensitive ports
   ```

## Part C — Harden: segment like a datacenter
1. **Tiered subnets:** public (ALB only) · private-app · private-data — across 2
   AZs. App and DB move to **private** subnets (no public IPs).
2. **SG-to-SG rules (not CIDRs):** ALB-SG → app-SG:443; app-SG → db-SG:3306;
   nothing else. Reference SGs by ID, not IP ranges.
3. **No public management:** remove SSH-from-internet; use **SSM Session
   Manager** (no bastion, no open 22) for access.
4. **Private AWS access:** add **VPC endpoints** (S3 gateway; interface endpoints
   for ECR/SSM/etc.) so instances reach AWS services without the internet.
5. **Controlled egress:** private subnets egress only via **NAT** (or endpoints);
   optionally an egress allowlist. Data subnet: no egress at all if possible.
6. **NACLs** as a coarse second layer between tiers (defense in depth).
7. **VPC Flow Logs** → CloudWatch/S3 for visibility (feeds Lab 06).

## Part D — Verify
```bash
# DB/SSH no longer reachable from the internet
nc -zv <old-db-ip> 3306      # no route / no public IP  ✅
# App reachable ONLY via the ALB on 443
curl https://<alb-dns>/      # works
# Instance reached via SSM, not SSH
aws ssm start-session --target <instance-id>
# Private AWS access works without internet
aws s3 ls    # from the instance, via the gateway endpoint

python3 ../../cloud/aws/sg_audit.py          # clean
bash ../../cloud/benchmarks/cis_benchmark.sh # network-related CIS checks
```
Success = data/management planes private, tier-to-tier flows only, SSM instead of
open SSH, private service access, egress controlled, flow logs on.

## Cleanup
Delete NAT Gateway + interface endpoints **first** (hourly cost), then EC2, then
the VPC.

## Portfolio artifact
- A **VPC segmentation diagram** (tiers, SG references, endpoints, egress path).
- `sg_audit.py` before/after (open-to-world → tiered).
- A short "datacenter → cloud" mapping note: DMZ→public subnet, app/DB
  VLANs→private tiers, firewall rules→SGs/NACLs, jump host→SSM.

## Stretch goals
- Centralize egress and inspection with **AWS Network Firewall** / a shared
  egress VPC via **Transit Gateway** — the multi-VPC "campus" design.
- Add **PrivateLink** to expose one internal service to another VPC/tenant
  without peering — ties to Lab 04 multi-tenant.
- Turn the whole VPC into Terraform; `checkov` it; diff against the console.
