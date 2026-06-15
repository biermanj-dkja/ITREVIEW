# Module 2 — Data Governance Audit
# Rule Schema and Scoring Weights
## Version 0.1

> ⚠ **Design reference only — not a canonical or current source.**
> This document was generated from the codebase at v0.7.1 to capture design intent and
> guide implementation. It has not been updated since and will not match the current rule
> set, question weights, finding IDs, or scoring logic in the live codebase.
> For current behaviour, read `rules_engine_dg.py` and `module_2.yaml` directly.

**Derived from:** `rules_engine_dg.py`, `module_2.yaml`, and `report_generator_dg.py` as of v0.7.1.

---

## Module Overview

**Module ID:** module_2
**Full title:** Data Governance and Data Flow Audit
**Primary operator:** IT Director (with Business Office input for contract questions)
**Report audience:** IT Director, with summary sections for Head of School

**Purpose:** Assess the school's data governance posture for each system that holds school or
student data. Produce a per-system grade, a school-wide governance score, and a prioritised
action plan.

**Structure:**
- **DG1** — Discovery: school identity pre-fill and system inventory (list of systems to audit)
- **DG_SYS_N** — Per-system worksheets (one generated per system named in DG1)
- **DG2** — School-Wide Governance: cross-system policies, ownership, and processes

---

## Scoring Philosophy

### Two separate scoring dimensions

Module 2 uses two severity scales that operate independently:

**System-level status** (`urgent / concern / watch / healthy`) is derived from the system's
overall score percentage across all assessed controls. It summarises how the system as a whole
performed.

**Finding severity** (`critical / high / medium / low`) reflects the direct risk level of each
individual control gap, independent of the overall score. A system can score Watch overall
but still carry a Critical finding that needs immediate attention.

The report renders both scales. A legend box in the Per-System Findings section of the DOCX
explains the distinction.

### Score thresholds

| Score % | Grade | System Status |
|---------|-------|---------------|
| 90–100% | A | Healthy |
| 80–89%  | B | Healthy |
| 65–79%  | C | Watch |
| 50–64%  | D | Concern |
| 0–49%   | F | Urgent |

The exact boundary between Watch and Healthy is 85% for the status label
(not 80%, which only applies to the grade). This means a system scoring 82%
receives grade B but status Watch.

### What is scored (per-system)

Only questions with explicit entries in `QUESTION_WEIGHTS` in `rules_engine_dg.py` contribute to
the score. Context-only questions (points=0 in the YAML) are collected for report narrative
but do not affect the grade.

### Context-only questions (collected but not scored)

The following per-system questions are collected for environmental context and report narrative
but contribute 0 points to the section score:

| Question ID | Purpose |
|-------------|---------|
| SYS.ID.name | System name confirmation (pre-filled) |
| SYS.ID.dept | Primary department using this system |
| SYS.ID.status | Active / inactive / decommissioned (gate for SYS.5.3 vs SYS.5.4) |
| SYS.ID.vendor | Vendor name |
| SYS.1.2 | Access roles (role-based / flat / unknown) |
| SYS.1.2a | Whether role-based access is documented |
| SYS.1.4 | Whether system is connected to SSO |
| SYS.2.1a | Who manages the backup |
| SYS.2.1b | Where backups are stored |
| SYS.3.1 | Whether system syncs to other systems |
| SYS.3.1a | What systems it syncs to and what data is transferred |
| SYS.3.2 | Whether data flows out of the system to external parties |
| SYS.3.3 | Whether a data flow map exists |
| SYS.3.3a | What the data flow map covers |
| SYS.3.4 | Whether staff manually export data outside the school |
| SYS.3.4a | What data is exported, to whom, and under what agreement |
| SYS.3.5 | Whether the vendor sub-processes with named sub-processors |
| SYS.5.1 | Data categories held (used to generate `data_context` in findings) |
| SYS.5.2 | Retention period for each data category |

---

## Per-System Scoring Weights

### Scoring weight table

| Question ID | Area | Max Points | What it measures |
|-------------|------|-----------|-----------------|
| SYS.1.1 | Access Control | 8 | User roster availability |
| SYS.1.1a | Access Control | 4 | Former staff accounts active (answered only if 1.1 partially available) |
| SYS.1.2 | Access Control | 0 | Context only — see above |
| SYS.1.3 | Access Control | 8 | MFA status |
| SYS.1.4 | Access Control | 0 | Context only |
| SYS.1.4a | Access Control | 4 | Shared or generic logins (answered when SSO is not used) |
| SYS.1.5 | Access Control | 6 | Audit log quality and review |
| SYS.2.1 | Backup & Recovery | 8 | Whether and how backups exist |
| SYS.2.3 | Backup & Recovery | 7 | Backup restore test recency (skipped if no backups) |
| SYS.2.4 | Backup & Recovery | 6 | Whether backups are stored separately (skipped if no backups) |
| SYS.3.2a | Data Flows | 8 | Outbound data transfer encryption |
| SYS.4.1 | Vendor & Contract | 10 | Data Processing Agreement status |
| SYS.4.2 | Vendor & Contract | 8 | Breach notification clause (scored only if DPA on file) |
| SYS.4.3 | Vendor & Contract | 7 | Vendor deletion obligation (scored only if DPA on file) |
| SYS.4.4 | Vendor & Contract | 4 | Vendor security review (SOC 2 etc.) |
| SYS.5.3 | Retention & Disposal | 5 | Data deletion process (skipped for decommissioned systems) |
| SYS.5.4 | Retention & Disposal | 15 | Decommissioned system shutdown documentation (only for decommissioned) |

**Maximum possible points (active system with DPA):** 98
**Maximum possible points (active system without DPA):** 83
**Maximum possible points (decommissioned system):** varies

### Conditional scoring rules

- `SYS.2.3` and `SYS.2.4` are excluded from scoring when `SYS.2.1` is `No — not backed up` or `Unknown`
- `SYS.4.2` and `SYS.4.3` are only scored when `SYS.4.1` is `Yes — signed DPA on file`
- `SYS.5.3` is excluded when the system is decommissioned or inactive
- `SYS.5.4` replaces `SYS.5.3` for decommissioned systems (worth 15 points)

### Partial credit rules

| Question | Answer | Points | Rationale |
|----------|--------|--------|-----------|
| SYS.1.1 | Yes — complete list available | 8 | Full credit |
| SYS.1.1 | Partial — list available but may be incomplete | 4 | Half credit |
| SYS.1.1 | No / Unknown | 0 | |
| SYS.1.1a | No unconfirmed accounts found | 4 | Full credit |
| SYS.1.1a | Yes — unconfirmed accounts exist | 0 | Active risk |
| SYS.1.1a | Unknown | 0 | |
| SYS.1.3 | Yes — required for all users | 8 | Full credit |
| SYS.1.3 | Partial — available but not required | 4 | Half credit |
| SYS.1.3 | No / Unknown | 0 | |
| SYS.1.4a | No shared logins (or SSO connected) | 4 | Full credit |
| SYS.1.4a | Yes — shared/generic logins in use | 0 | |
| SYS.1.5 | Logs retained 90+ days and reviewed regularly | 6 | Full credit |
| SYS.1.5 | Logs exist but not reviewed / retention unknown | 3 | Partial |
| SYS.1.5 | No logs / Unknown | 0 | |
| SYS.2.1 | School manages / Both school and vendor | 8 | Full credit |
| SYS.2.1 | Vendor manages only | 5 | Partial — less control |
| SYS.2.1 | No — not backed up / Unknown | 0 | |
| SYS.2.3 | Within last 12 months — documented | 7 | Full credit |
| SYS.2.3 | Within last 12 months — not documented | 5 | |
| SYS.2.3 | More than 12 months ago | 3 | |
| SYS.2.3 | Never tested / Unknown | 0 | |
| SYS.2.4 | Yes — offsite/separate storage | 6 | Full credit |
| SYS.2.4 | No / Unknown | 0 | |
| SYS.3.2a | All outbound transfers encrypted | 8 | Full credit |
| SYS.3.2a | Partial | 4 | |
| SYS.3.2a | Not encrypted / Unknown | 0 | |
| SYS.4.1 | Signed DPA on file | 10 | Full credit |
| SYS.4.1 | Terms of service only | 3 | Significant gap |
| SYS.4.1 | No agreement / Unknown | 0 | |
| SYS.4.1 | Free tool — no contract | 5 | Partial — free tools have different risk profile |
| SYS.4.2 | 72 hours or less | 8 | Full credit |
| SYS.4.2 | More than 72 hours | 5 | |
| SYS.4.2 | Timeframe not specified | 3 | |
| SYS.4.2 | No breach notification clause / Unknown | 0 | |
| SYS.4.3 | Deletion required with written confirmation | 7 | Full credit |
| SYS.4.3 | Deletion required, no written confirmation | 4 | |
| SYS.4.3 | Contract silent / Unknown | 0 | |
| SYS.4.4 | SOC 2 or equivalent reviewed | 4 | Full credit |
| SYS.4.4 | Published documentation only | 2 | |
| SYS.4.4 | Not reviewed / Unknown | 0 | |
| SYS.5.3 | Documented deletion with log | 5 | Full credit |
| SYS.5.3 | Deletion occurs but not documented | 3 | |
| SYS.5.3 | Vendor handles — confirmed in writing | 5 | |
| SYS.5.3 | Vendor handles — not confirmed | 2 | |
| SYS.5.3 | No deletion process / Unknown | 0 | |

---

## Per-System Finding Rules

Finding severity uses the `critical / high / medium / low` scale.
Timing buckets: `immediate` = do within 30 days · `near_term` = within 90 days · `planned` = this year.

### Access Control Findings

**DG-A1 — User roster not readily available**
- Trigger: `SYS.1.1` = `No` or `Unknown`
- Severity: high · Timing: immediate
- Owner: IT Director

**DG-A2 — Former staff accounts still active**
- Trigger: `SYS.1.1a` = `yes`
- Severity: critical · Timing: immediate
- Owner: IT Director
- Note: This is the only critical-severity finding in the per-system access control rules.

**DG-A3 — MFA not enabled**
- Trigger: `SYS.1.3` = `No — not available or not enabled`
- Severity: high · Timing: immediate
- Owner: IT Director

**DG-A4 — MFA available but not required**
- Trigger: `SYS.1.3` = `Partial — available but not required`
- Severity: medium · Timing: near_term
- Owner: IT Director

**DG-A5 — Shared or generic logins in use**
- Trigger: `SYS.1.4a` = `yes` (i.e., SSO not connected and shared logins confirmed)
- Severity: medium · Timing: near_term
- Owner: IT Director

**DG-A6 — Audit logs not being reviewed**
- Trigger: `SYS.1.5` = `logs exist but not reviewed` or `retention period unknown`
- Severity: low · Timing: planned
- Owner: IT Director

**DG-A7 — No audit logging capability**
- Trigger: `SYS.1.5` = `No — system does not support audit logs` or `Unknown`
- Severity: medium · Timing: near_term
- Owner: IT Director

### Backup & Recovery Findings

**DG-B1 — No backup in place**
- Trigger: `SYS.2.1` = `No — not backed up`
- Severity: high · Timing: immediate (critical if system is primary data store)
- Owner: IT Director
- Note: Severity escalates to critical when system holds student health or financial data.

**DG-B2 — Backup restore never tested or overdue**
- Trigger: `SYS.2.3` = `Never tested` or `Unknown`
- Severity: high · Timing: immediate
- Owner: IT Director

**DG-B3 — Backup restore tested but overdue**
- Trigger: `SYS.2.3` = `More than 12 months ago`
- Severity: medium · Timing: near_term
- Owner: IT Director

**DG-B4 — Backups not stored separately**
- Trigger: `SYS.2.4` = `no` (backups on same system or location as live data)
- Severity: medium · Timing: near_term
- Owner: IT Director

### Vendor & Contract Findings

**DG-D1 — No Data Processing Agreement on file**
- Trigger: `SYS.4.1` = `No agreement on file` or `Unknown`
- Severity: critical · Timing: immediate
- Owner: Business Office

**DG-D2 — Terms of service only, no formal DPA**
- Trigger: `SYS.4.1` = `Terms of service only — no formal DPA`
- Severity: high · Timing: immediate
- Owner: Business Office

**DG-D3 — No breach notification clause in contract**
- Trigger: `SYS.4.1` = DPA on file AND `SYS.4.2` = `No breach notification clause` or `Unknown`
- Severity: high · Timing: immediate
- Owner: Business Office

**DG-D4 — Breach notification window exceeds best practice**
- Trigger: `SYS.4.1` = DPA on file AND `SYS.4.2` = `Yes — more than 72 hours`
- Severity: medium · Timing: near_term
- Owner: Business Office

**DG-D5 — Vendor security practices not reviewed**
- Trigger: `SYS.4.4` = `No — not reviewed` or `Unknown`
- Severity: low · Timing: planned
- Owner: IT Director

### Retention & Disposal Findings

**DG-E1 — Data deletion process not documented**
- Trigger: `SYS.5.3` = `Deletion occurs but is not documented`
- Severity: low · Timing: planned
- Owner: IT Director

**DG-E2 — No data deletion process**
- Trigger: `SYS.5.3` = `No deletion process — data accumulates indefinitely`
- Severity: medium · Timing: near_term
- Owner: IT Director

**DG-E3 — Decommissioned system: data status unknown**
- Trigger: system is decommissioned AND `SYS.5.4` = `Data NOT exported`, `No shutdown documentation`, `Unknown`, or unanswered
- Severity: critical · Timing: immediate
- Owner: IT Director

**DG-E4 — Decommissioned system: data exported but vendor deletion not confirmed**
- Trigger: system is decommissioned AND `SYS.5.4` = `Data exported but deletion not confirmed`
- Severity: medium · Timing: near_term
- Owner: IT Director

### Sub-processor Finding

**DG-F1 — Sub-processors exist and are not named in the contract**
- Trigger: `SYS.3.5` = `Yes — sub-processors exist but are not named`
- Severity: medium · Timing: near_term
- Owner: Business Office

---

## School-Wide Governance (DG2) Finding Rules

DG2 findings fire against the school-wide governance section answers, not per-system answers.

### DG2 Finding Table

| Finding | Trigger question | Trigger values | Severity | Timing |
|---------|-----------------|----------------|----------|--------|
| No formal data governance policy | DG2.1 | Draft only / No / Unknown / null | high | immediate |
| No designated data privacy officer | DG2.2 | No / Unknown / null | high | immediate |
| No master data register | DG2.3 | No — this audit is first attempt / Unknown / null | medium | near_term |
| Master data register incomplete | DG2.3 | Partial — incomplete or outdated | low | planned |
| No documented breach response plan | DG2.4 | Informal / No / Unknown / null | high | immediate |
| No software approval process | DG2.5 | No — staff can adopt without IT review / Unknown / null | medium | near_term |
| No regular staff data privacy training | DG2.6 | Ad hoc / No / Unknown / null | medium | near_term |
| Data privacy training not reaching all staff | DG2.6 | Partial — some staff trained | low | planned |
| No documented offboarding process | DG2.7 | Informal / No / Unknown / null | high | immediate |
| Offboarding process incomplete | DG2.7 | Partial — relies on memory | medium | near_term |
| No formal vendor review process | DG2.8 | No — approved without security review / Unknown / null | medium | near_term |
| No data retention schedule | DG2.9 | No / Unknown / null | medium | near_term |

### DG2 scoring

DG2 questions are scored in the YAML but the DG2 section score is not separately displayed in
the current report — school-wide findings are shown in a dedicated section alongside per-system
results. A separate DG2 section score display is a ⚠ known gap.

### Cross-system coverage check

After all per-system findings are generated, `check_data_source_coverage()` runs a cross-system
scan. It checks whether systems in the inventory that were flagged as holding student data all
have at least one answered SYS.4.1 (DPA) question. If any system holding sensitive data appears
to have no DPA review at all, a school-wide finding is added. This is the only cross-system
finding rule currently implemented.

---

## Overall Report Grade

The overall grade shown on the report cover page is a **sensitivity-weighted average** of all
per-system score percentages. Systems holding higher-sensitivity data carry more weight,
preventing a strong score on low-risk tools from masking critical failures in the school's
primary data systems.

### Sensitivity multipliers (derived from SYS.5.1 data categories)

| Multiplier | Trigger categories |
|------------|-------------------|
| 3× | Student health records (medical, counseling, nurse) · Staff HR records · Financial and payment data |
| 2× | Student academic records · Student behavioral records · Admissions and enrollment data · Authentication credentials |
| 1× | All other categories (content filters, logging tools, communications, etc.) |

A system with no SYS.5.1 answer defaults to 1×.

**Example:** If Veracross (SIS holding health + academic records) scores 29% and a content
filter scores 65%, the weighted average will be pulled substantially toward the 29% score,
reflecting that Veracross's data exposure is the more consequential risk. A simple average
would return ~47%; the sensitivity-weighted average returns a lower number that better
represents the school's actual risk posture.

---

## Severity Vocabulary Reference

| Scale | Values | Where used |
|-------|--------|-----------|
| System status | urgent / concern / watch / healthy | Per-system overall status; derived from score % |
| Finding severity | critical / high / medium / low | Individual control gaps; independent of score |
| Grade | A / B / C / D / F | Display label for system score; maps to same thresholds as status |
| Timing | immediate / near_term / planned | Action plan bucketing |

---

## Known Gaps and Deferred Items

| # | Gap | Status |
|---|-----|--------|
| 1 | DG2 section score not separately displayed in report | Deferred |
| 2 | Overall grade uses simple average, not sensitivity-weighted average | **Resolved v0.7.2** — see Overall Report Grade section above |
| 3 | Notes passthrough — user-typed notes not quoted in finding descriptions | Deferred to FUTURE_IDEAS.md |
| 4 | Per-section data quality annotations (R10-007 equivalent for Module 2) | Deferred to FUTURE_IDEAS.md |
| 5 | DG2.3 "Partial" answer fires a low finding but DG2.3 scoring partial credit is not defined in YAML | Minor — no user impact |
| 6 | SYS.4.4 finding is low severity even though it is a scored question with real weight | Review in next schema revision |

---

*Document version 0.1 — derived from source code v0.7.1. Review and correct any items that do
not match design intent before using as a specification for new development.*
