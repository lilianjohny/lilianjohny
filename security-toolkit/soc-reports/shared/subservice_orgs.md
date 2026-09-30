# Subservice Organizations (carve-out vs inclusive)

A **subservice organization** is a vendor your service relies on whose controls
are relevant to your SOC report (e.g., your cloud IaaS/PaaS provider, a data
center, a payment processor). You choose how to present them.

## Two methods

| Method | What it means | Effect on your report |
|--------|---------------|-----------------------|
| **Carve-out** (common) | The subservice org's controls are **excluded** from your description; you describe the **monitoring controls** you have over them, and rely on **CSOCs**. | Shorter description; you must still monitor the vendor and identify CSOCs |
| **Inclusive** | The subservice org's controls are **included** and tested within your report. | Requires the subservice org's cooperation and auditor access |

Most service orgs use **carve-out** for large cloud providers and rely on the
provider's own SOC 2 / SOC 1.

## Complementary Subservice Organization Controls (CSOCs)
Like CUECs, but for the vendor: controls you **assume the subservice org
performs**. List them in the report and verify via the vendor's SOC report.

## Vendor / subservice management checklist
- [ ] Maintain an inventory of subservice organizations and what they process.
- [ ] Obtain and **review each vendor's current SOC 2 / SOC 1 report** annually.
- [ ] Read the vendor SOC report's **CUEC section** — implement the CUECs they
      assign to you (they become your controls).
- [ ] Check for **exceptions/qualifications** in the vendor's auditor opinion.
- [ ] Confirm the vendor report's **period** covers your audit period (bridge
      letter if there's a gap).
- [ ] Record CSOCs you rely on and how you monitor them.

Track vendors and their SOC reports as controls (see `../soc2/controls_matrix.csv`
CTL-13) and with the toolkit's `../../cloud/` posture checks for the parts you
configure.
