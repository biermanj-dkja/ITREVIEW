# Test Data — Bit-By-Bit Academy

Completed assessment exports for use in import/export testing. These files can be imported into the engine as many times as needed (each import requires a unique `session_id` — see note below).

## Files

| File | Module | Answers | Status |
|---|---|---|---|
| `BitByBit_Academy_module-1_export.json` | Module 1 — Small Private School IT Overview and Action Plan | 150 | Complete |
| `Bit-By-Bit_Academy_module-2_export_UPDATED.json` | Module 2 — Data Governance and Data Flow Audit | 164 | Complete |
| `Bit-By-Bit_Academy_module-3_export_UPDATED.json` | Module 3 — Software, Licensing, and Vendor Register | 314 | Complete |

## School Details

- **School name:** Bit-By-Bit Academy
- **Website:** bitbybitacademy.org
- **Address:** 4200 Logic Lane, Silicon Heights, CA 94102
- **Grades served:** K–8
- **Student enrollment:** ~340
- **Faculty and staff:** ~52
- **Report author:** Rhoda Report, Director of Technology

## Module 1 — IT Overview Scenario Summary

Bit-By-Bit Academy is a single-IT-director K–8 school operating across two sites (main campus with 4 buildings, athletics annex). The school uses Google Workspace as its primary platform, a Sophos XGS firewall, Ubiquiti UniFi for networking, Veracross as its SIS, and a mix of Chromebooks (grades 3–5), iPads (K–2), and MacBooks (grades 6–8).

**Key findings embedded in the data:**
- MFA is not enforced for all staff
- Emergency credential documentation does not exist
- Backup restore testing is overdue (last tested > 18 months ago)
- A staff laptop was reported missing without formal incident response
- Known Wi-Fi dead spots in the gymnasium wing
- Single-person dependencies on firewall, phone system, and backup configuration
- Several unused subscriptions still auto-renewing (Adobe CC, Zoom Pro)

## Module 2 — Data Governance Scenario Summary

The module 2 export covers 5 systems: Veracross (SIS), Google Workspace, Seesaw, Lightspeed Filter, and Bark for Schools. A school-wide governance section (DG2) is also complete.

**Key findings embedded in the data:**
- Veracross contract and DPA cannot be located — signed by a previous Head of School
- Seesaw was adopted without IT review and has no DPA on file
- No master data register exists prior to this audit
- No written data retention schedule has been formally adopted
- Offboarding process relies on memory and does not cover all platforms
- Former staff account in Veracross unconfirmed as deactivated
- No annual staff data privacy training


## Module 3 — Vendor Register Scenario Summary

The module 3 export covers 13 vendors, sourced directly from the system names established in module 2 plus the additional subscriptions mentioned across module 1 (questions 6.5, 6.11, 6.12, 8.2). Vendors: Veracross, Google Workspace for Education Plus, Seesaw, Lightspeed Filter, Bark for Schools, Panorama Education, Kami, Comcast Business, Sophos Central, Veeam Backup, 8x8 (VoIP), Adobe Creative Cloud, and Zoom Pro.

**Key findings embedded in the data:**
- Veracross contract cannot be located — renewal in August 2025, DPA status unknown
- Seesaw: no DPA, unknown renewal date, admin access held by department head only, cost unconfirmed — complete shadow IT profile
- Panorama Education: student SEL data held with no DPA, IT has no admin access, renewal in September 2025
- 8x8: no admin access (lost with previous IT staff), no contract on file, poor support history — named single-vendor dependency from module 1
- Adobe Creative Cloud: zombie subscription (~$3,300/year) on decommissioned devices, auto-renewing to an unmonitored card
- Zoom Pro: COVID-era holdover (~$180/year), not in budget, credentials unknown, Google Meet covers all needs
- No shared password manager in use for most vendors — most credentials in personal password manager only
- No annual vendor review process — zombie subscriptions are a direct result
- DPA register incomplete: Veracross, Seesaw, Panorama, and Kami all have open DPA gaps

## How to Import

1. Go to the app home page and click **Import Session**
2. Upload one of these JSON files
3. The session will be restored with all answers populated and all sections marked complete
4. Navigate to the session summary or generate a report

## Re-Importing (For Repeated Testing)

The engine intentionally blocks importing a session whose `session_id` already exists — this is a safety feature that protects real users from accidentally overwriting a session they are actively working in. For normal use, this is the correct behavior.

For **test purposes only** (since these files are meant to be imported repeatedly), you have two options to work around this:
- **Clear the database** between test runs (delete `data/assessments.db` and restart the app), or
- **Edit the `session_id`** field in the JSON before each import (e.g. change `bba-m1-test-2025-0514-001` to `bba-m1-test-2025-0514-002`)

The `session_id` is the only field that must be unique. All other fields can remain identical.
