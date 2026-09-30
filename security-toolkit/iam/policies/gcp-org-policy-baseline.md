# GCP Organization Policy — IAM/security baseline (org/folder scope)

Set these constraints at the **organization** (inherited by folders/projects).
Terraform in `../terraform/gcp/` applies a representative set. Test on a
non-prod folder first — some are disruptive if workloads rely on the behavior.

## Identity & keys (highest priority)
| Constraint | Setting | Why |
|-----------|---------|-----|
| `iam.disableServiceAccountKeyCreation` | **enforced** | No exported SA JSON keys — use Workload Identity Federation |
| `iam.disableServiceAccountKeyUpload` | **enforced** | No external keys uploaded to SAs |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | **enforced (disable)** | Default SAs don't get Editor automatically |
| `iam.allowedPolicyMemberDomains` | your customer IDs | Blocks `allUsers`/`allAuthenticatedUsers` + external identities |
| `iam.workloadIdentityPoolProviders` | allowlist issuers | Only trusted OIDC issuers (e.g. GitHub) may federate |

## Public exposure & data
| Constraint | Setting |
|-----------|---------|
| `storage.publicAccessPrevention` | **enforced** |
| `storage.uniformBucketLevelAccess` | **enforced** |
| `sql.restrictPublicIp` | **enforced** |
| `compute.vmExternalIpAccess` | deny (or allowlist) |
| `compute.requireOsLogin` | **enforced** (SSH via IAM, not keys) |
| `compute.requireShieldedVm` | **enforced** |

## Location / governance
| Constraint | Setting |
|-----------|---------|
| `gcp.resourceLocations` | allowed regions only (region lock) |
| `compute.restrictProtocolForwardingCreationForTypes` | as needed |

## Beyond org policy
- **Principal Access Boundary (PAB):** cap which resources a principal set can
  ever access, independent of IAM grants.
- **VPC Service Controls:** perimeters around sensitive APIs (Storage, BigQuery,
  KMS) to prevent data exfiltration even with valid creds.
- **IAM Conditions:** time-bound / resource-scoped role bindings.
- **Privileged Access Manager (PAM):** JIT privileged entitlements.

## Detection
- Aggregated **org log sink** → immutable bucket/BigQuery; **Security Command
  Center**; alert on SA key creation, `allUsers` grants, org-policy changes.

> Verify current constraint names/values in the Org Policy reference — Google
> adds constraints regularly.
