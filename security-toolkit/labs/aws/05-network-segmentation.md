# Lab 05 — Network Segmentation

**Skills practiced:** VPC design · public/private tiers · Security Groups vs
NACLs · SG-to-SG rules · VPC endpoints/PrivateLink · egress control · SSM instead
of open SSH · flow logs.
**Proves (JD):** "securing … deployments from construction to multi-tenant use" —
the network layer.

## Objective
Build a segmented VPC like a secure datacenter: tiers that talk only in the
intended direction, no data/management plane on the internet, private AWS
access, controlled egress, full visibility.

## Est. time / cost
2–3 h · **~$1–2** (NAT Gateway + interface endpoints bill hourly — tear down).

## Prerequisites
- Lab 00 done. Tool: `../../cloud/aws/sg_audit.py`.

---

## Part A — Build a deliberately flat/open network
```bash
VPC=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text)
SUB=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.0.0/24 --query Subnet.SubnetId --output text)
IGW=$(aws ec2 create-internet-gateway --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC
RT=$(aws ec2 create-route-table --vpc-id $VPC --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id $RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
aws ec2 associate-route-table --route-table-id $RT --subnet-id $SUB
# Wide-open SG (anti-pattern)
SG=$(aws ec2 create-security-group --group-name lab05-open --description open --vpc-id $VPC --query GroupId --output text)
for P in 22 3306 80; do aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port $P --cidr 0.0.0.0/0; done
```
(Launch an app + "DB" instance in $SUB with public IPs if you want live proof —
use the latest Amazon Linux AMI via SSM parameter.)

## Part B — Attack / observe
```bash
python3 ../../cloud/aws/sg_audit.py     # flags 0.0.0.0/0 on 22 (SSH) and 3306 (DB)
# From your laptop against a launched public instance:
# nc -zv <db-public-ip> 3306   # open to the world ❌
# nc -zv <app-public-ip> 22    # SSH open to the world ❌
```

## Part C — Harden: segment like a datacenter
```bash
# 1. Private subnets (no public IP) across 2 AZs + a public subnet for the ALB only
AZ1=${AWS_REGION}a; AZ2=${AWS_REGION}b
PUB=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.1.0/24 --availability-zone $AZ1 --query Subnet.SubnetId --output text)
APP=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.0.2.0/24 --availability-zone $AZ1 --query Subnet.SubnetId --output text)
DB=$(aws ec2 create-subnet  --vpc-id $VPC --cidr-block 10.0.3.0/24 --availability-zone $AZ2 --query Subnet.SubnetId --output text)

# 2. SG-to-SG rules (reference SGs, not CIDRs)
ALBSG=$(aws ec2 create-security-group --group-name alb-sg --description alb --vpc-id $VPC --query GroupId --output text)
APPSG=$(aws ec2 create-security-group --group-name app-sg --description app --vpc-id $VPC --query GroupId --output text)
DBSG=$(aws ec2 create-security-group  --group-name db-sg  --description db  --vpc-id $VPC --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $ALBSG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APPSG --protocol tcp --port 443 --source-group $ALBSG
aws ec2 authorize-security-group-ingress --group-id $DBSG  --protocol tcp --port 3306 --source-group $APPSG

# 3. NAT for private egress; gateway endpoint for S3 (no internet needed)
EIP=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
NAT=$(aws ec2 create-nat-gateway --subnet-id $PUB --allocation-id $EIP --query NatGateway.NatGatewayId --output text)
aws ec2 create-vpc-endpoint --vpc-id $VPC --service-name com.amazonaws.$AWS_REGION.s3 \
  --route-table-ids $RT --vpc-endpoint-type Gateway
# Interface endpoints for SSM (so you can manage instances without SSH/internet):
for S in ssm ssmmessages ec2messages; do
  aws ec2 create-vpc-endpoint --vpc-id $VPC --vpc-endpoint-type Interface \
    --service-name com.amazonaws.$AWS_REGION.$S --subnet-ids $APP --security-group-ids $APPSG
done

# 4. Flow logs → CloudWatch
aws ec2 create-flow-logs --resource-type VPC --resource-ids $VPC \
  --traffic-type ALL --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/lab05 --deliver-logs-permission-arn arn:aws:iam::$ACCT_ID:role/flowlogsRole 2>/dev/null || \
  echo "create an IAM role for flow logs first (see docs), or use --log-destination-type s3"
```
**No public management:** remove SSH-from-internet; reach instances via **SSM
Session Manager**: `aws ssm start-session --target <instance-id>`.
**GUI:** VPC console → **Subnets/Route tables/Security groups/Endpoints/NAT
gateways**; EC2 → connect via **Session Manager** tab (not SSH).

## Part D — Verify
```bash
python3 ../../cloud/aws/sg_audit.py            # clean (no 0.0.0.0/0 on sensitive ports)
bash ../../cloud/benchmarks/cis_benchmark.sh   # network CIS checks
# aws ssm start-session --target <instance-id>   # admin via SSM, not open 22
```

## Cleanup (delete NAT + endpoints FIRST — hourly cost)
```bash
aws ec2 delete-nat-gateway --nat-gateway-id $NAT
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC --query 'VpcEndpoints[].VpcEndpointId' --output text | xargs -n1 aws ec2 delete-vpc-endpoints --vpc-endpoint-ids
aws ec2 release-address --allocation-id $EIP
# then delete subnets, SGs, route table, IGW, and the VPC (after instances are gone)
```

## Portfolio artifact
- A **VPC segmentation diagram** (tiers, SG references, endpoints, egress path).
- `sg_audit.py` before/after (open-to-world → tiered).
- A "datacenter → cloud" mapping (DMZ→public subnet, VLANs→private tiers, firewall
  rules→SGs/NACLs, jump host→SSM).

## Stretch goals
- Centralize egress + inspection with **AWS Network Firewall** / a shared egress
  VPC via **Transit Gateway**.
- Expose one internal service with **PrivateLink** (ties to Lab 04).
- Turn the whole VPC into Terraform; `checkov` it.
