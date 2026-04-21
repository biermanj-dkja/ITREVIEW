# Module 1 — Master Rule Schema
## Small Private School IT Overview and Action Plan
### Version 0.2

**v0.2 changes:** Question IDs updated throughout to match current module_1.yaml (v0.2). Section 8 gate question corrected from 8.2→8.1. Section 3 firewall question corrected from 3.6→3.7, AP inventory from 3.8→3.6. Section 7 gate note added. New rules R7-007b (backup storage location) and R8-001b (EP alert monitoring) added.

---

## Purpose
This document defines the complete deterministic rule schema for Module 1. It contains all rules for all sections in a single authoritative source. Each rule has a unique ID, conditions drawn from normalized question answers, a finding with severity, and one or more actions with time horizons.

Rules are evaluated after all answers across all sections are normalized. Cross-section reference rules require the full normalized answer set to be available before evaluation.

New sections are added to this document as their schemas are written and reviewed. Do not create separate per-section rule schema files.

---

## Rule ID Format
- Rules: `RN-XXX` where N = section number, XXX = three-digit sequence
- Composite rules: `RN-CXXX`
- Findings: `FN-XXX` (matching rule ID)
- Actions: `AN-XXXa`, `AN-XXXb` etc.

---

## Severity Scale
- **healthy** — no concern; positive signal
- **watch** — worth monitoring; not immediately risky
- **concern** — material gap; should be addressed
- **urgent** — high risk; immediate attention warranted
- **unknown** — insufficient data to classify

---

## Time Horizon Reference
- **immediate** — within days; do not wait for a scheduled window
- **next_30_days** — within the current or next month
- **next_90_days** — within the current quarter
- **next_12_months** — within the planning year
- **strategic_future** — beyond 12 months; roadmap item

---

## Rule Pattern Reference
All rules in this document use one or more of the following formal patterns. See the design document for full pattern definitions.

- **Pattern 1: Simple Threshold** — single question value triggers a finding at fixed severity
- **Pattern 2: Escalation Modifier** — base finding fires, second condition raises severity
- **Pattern 3: Graduated Severity** — different answer values produce different severities from same rule
- **Pattern 4: Composite** — multiple conditions across multiple questions must all be true
- **Pattern 5: Cross-Section Reference** — answer in one section affects finding in another
- **Pattern 6: Constraint Annotation** — answer attaches a modifier to action plan items rather than generating a finding

---

## Unknown Answer Override (Global)
Per design document Decisions #11 and #12:
- Any unknown answer in a section sets that section's minimum domain status to **watch**
- Each section defines a set of critical questions whose unknown state raises the floor to **concern**
- Unknown answers must never be silently converted to any other status

---

## Cross-Section Key Risk Groups
These groups aggregate findings from multiple sections into named Key Risks for the report. They are defined here as findings are confirmed across sections and updated as new sections are added.

### Key Risk Group A: No accountable IT ownership
- Primary findings: F2-001, F2-003, F2-C01
- Supporting findings: Section 6 systems visibility findings (to be added)
- Aggregated severity: urgent if F2-C01 fires; concern otherwise

### Key Risk Group B: Single-person dependency creates recovery and continuity risk
- Primary findings: F2-C02, F2-008
- Supporting findings: F7-012, Section 9 knowledge concentration findings (to be added)
- Aggregated severity: urgent if F2-C02 or F7-012 fires; concern otherwise

---

# Report Assembly Requirements

This section collects all report assembly behaviors identified during rule schema development. These requirements are for the report assembler — the system layer that takes evaluated findings and constructs the output document. They are gathered here rather than scattered across individual rules so they can be implemented consistently.

**Note:** A decision on whether to move this section to the design document will be made before the build begins. Until then, this is the authoritative location.

---

## RA-001 — Executive Summary mandatory findings

The following findings must always appear in the Executive Summary regardless of overall report score or other section content. They are never suppressed or omitted.

| Finding | Trigger condition |
|---|---|
| F2-C01 | No IT accountability structure exists at any level |
| F7-C01 | No verifiable data protection in place |
| F3-017 | Known connectivity issues currently affecting operations |
| F3-C01 | No network documentation exists at any level |
| F3-C02 | No admin access, no documentation, no config backup |
| F5-C02 | Many unsupported devices in 1:1 program with no refresh plan |
| F6-C01 | No vendor or systems visibility at any level |
| F6-C02 | Server environment completely undocumented |
| F8-C01 | Baseline security hygiene completely absent |
| F8-008 | Known unresolved security concerns (always surfaces when it fires) |
| F9-C01 | No documentation and environment non-transferable |

Any finding marked urgent in the Key Risks section should also be summarised in the Executive Summary. The Executive Summary should never present only positive signals if urgent findings exist elsewhere in the report.

---

## RA-002 — Key Risks section ordering

The Key Risks section must present findings in the following priority order:

1. Composite urgent findings (F2-C01, F2-C02, F7-C01, F3-C01, F3-C02) — if any fire
2. Individual urgent findings — ordered by section number
3. Concern-level findings from Key Risk Groups (aggregated) — ordered by group
4. Remaining concern-level findings — ordered by section number
5. Watch-level findings — ordered by section number

F2-C01 specifically must be the first item in the Key Risks section if it fires. It represents the most fundamental governance failure and sets context for every other finding.

---

## RA-003 — Cross-section Key Risk Group aggregation

Findings tagged with a cross-section aggregation tag must be grouped into named Key Risk entries in the Key Risks section. Each group appears as a single named risk with the contributing findings listed beneath it by ID.

### Currently defined Key Risk Groups

**Key Risk Group A: No accountable IT ownership**
- Primary findings: F2-001, F2-003, F2-C01
- Supporting findings: F3-010 (when urgent), F6-001, F6-C01
- Aggregated severity: urgent if F2-C01 or F6-C01 fires; concern otherwise
- Report title: "No accountable IT ownership structure"

**Key Risk Group B: Single-person dependency creates recovery and continuity risk** *(complete)*
- Primary findings: F2-C02, F2-008
- Supporting findings: F7-012, F3-C02, F6-009 (when urgent), F6-010, F6-C02, F9-005, F9-006, F9-C01
- Aggregated severity: urgent if F2-C02, F7-012, F3-C02, F6-C02, F9-C01, or F9-005 fires at urgent; concern otherwise
- Report title: "Single-person dependency creates recovery and continuity risk"

**Key Risk Group C: Vendor visibility and continuity** *(complete)*
- Primary findings: F2-004, F6-005, F6-006, F6-C01
- Supporting findings: F6-003, F6-007 (vendor dependencies)
- Aggregated severity: urgent if F6-C01 fires; concern otherwise
- Report title: "Vendor relationships and renewal visibility"

**Key Risk Group D: Student data governance** *(complete)*
- Primary findings: F2-011, F6-004
- Supporting findings: F6-003 (if student data subscriptions are untracked)
- Aggregated severity: concern (no urgent path in this group currently)
- Report title: "Student data governance and software approval"

**Key Risk Group E: Privileged access and security posture** *(complete)*
- Primary findings: F4-C01, F4-005 (when urgent), F4-006 (when urgent), F8-C01
- Supporting findings: F2-007, F8-001, F8-004 (when urgent)
- Aggregated severity: urgent if any primary finding fires at urgent; concern otherwise
- Report title: "Privileged access and baseline security posture"

**Key Risk Group F: Lifecycle and refresh planning gap** *(complete)*
- Primary findings: F5-C02, F5-006 (when urgent)
- Supporting findings: F5-005, F6-012, F6-013
- Aggregated severity: urgent if F5-C02 fires; concern otherwise
- Report title: "Device lifecycle and refresh planning gap"

### Aggregation rules
- Individual findings that contribute to a Key Risk Group still appear in their own section findings for completeness
- The Key Risk Group entry in the Key Risks section references all contributing finding IDs
- The aggregated severity is the highest severity among contributing findings that fired
- If no contributing findings fire, the Key Risk Group entry is suppressed

---

## RA-004 — Constraint annotation behavior

When F2-006 fires (budget or staffing constraints noted in question 2.7):
- The report assembler attaches a `constraint_flag` to all action items in the action plan that require budget or additional staffing
- The constraint text from the notes field of 2.7 is included in the annotation
- Actions are never removed or suppressed — the tension is made visible, not hidden
- The constraint marker must be visually distinct in the rendered report (e.g. a warning icon or bracketed note)
- The constraint flag should also appear in the roadmap section where affected items appear

---

## RA-005 — Finding clustering within sections

The following findings should be presented together as clusters within their section's findings page, rather than as separate standalone entries. Clustering reduces visual noise and makes the relationship between related gaps clear.

| Cluster name | Findings | Section |
|---|---|---|
| Network documentation gap | F3-001, F3-002, F3-008 | Section 3 |
| Wireless visibility gap | F3-003, F3-006 | Section 3 |
| Inventory and lifecycle gap | F5-001, F5-002, F5-006 | Section 5 |
| Provisioning and management gap | F5-003, F5-004 | Section 5 |
| Vendor and systems visibility gap | F6-001, F6-002, F6-005, F6-006 | Section 6 |
| Server documentation and access gap | F6-009, F6-010, F6-011 | Section 6 |
| Security hygiene gap | F8-001, F8-002, F8-003 | Section 8 |
| Student protection gap | F8-004, F8-005 | Section 8 |
| Documentation maturity gap | F9-001, F9-002, F9-003, F9-004 | Section 9 |

All clusters are now defined. When findings in a cluster all fire, the cluster is presented as a single named gap with individual finding details beneath it. When only some findings in a cluster fire, they are presented individually with a note referencing the others.

---

## RA-006 — Notes field passthrough to report

The following findings must include the content of their question's notes field directly in the rendered finding description. The notes are not paraphrased — they are quoted as entered by the IT person.

| Finding | Source question | Notes behavior |
|---|---|---|
| F2-006 | 2.7 (constraints) | Passed to constraint annotation on affected actions |
| F3-017 | 3.26 (connectivity pain points) | Quoted directly in finding description |
| F2-C02 | 2.8 notes | Included in emergency access finding context |
| F6-007 | 6.10 (single-vendor/person dependencies) | Each specific dependency quoted by name in finding description |
| F8-008 | 8.11 (known security concerns) | Quoted directly in finding description and Executive Summary |
| F9-006 | 9.6 (knowledge concentration areas) | Specific knowledge areas quoted by name in finding description |

All mandatory notes passthrough cases are now defined.

---

## RA-007 — Plain-language education notes

The following finding descriptions contain plain-language explanations that must appear verbatim in the rendered report. They are written to be usable by the IT person when communicating with leadership or non-technical staff. Do not rewrite or summarise them during report rendering.

| Finding | Topic of plain-language note |
|---|---|
| F7-006 | Cloud availability is not the same as backup |
| Section 9 score display | Why Section 9 is weighted at 10% and why it is still high-leverage for score improvement |
| F8-008 score (yes) | Why acknowledging known security concerns scores higher than unknown |
| F8-008 score (unknown) | Why unknown scores lower than a confirmed yes on security concerns |
| F9-006 score (yes with notes) | Why naming knowledge concentration areas earns partial credit |

All mandatory plain-language notes are now defined.

---

## RA-008 — Composite finding suppression of individual findings

When a composite finding fires, its component individual findings are suppressed from the main findings list and their actions are consolidated into the composite finding's action set. The individual findings are still recorded internally for traceability but are not presented as separate items to the IT person.

| Composite finding | Suppresses individual findings |
|---|---|
| F2-C01 | F2-001, F2-002, F2-003 (actions inherited) |
| F2-C02 | F2-007, F2-008 (actions inherited) |
| F7-C01 | F7-001, F7-002, F7-007, F7-008 (actions inherited) |
| F3-C01 | F3-001, F3-002, F3-009 (actions inherited) |
| F3-C02 | F3-010, F3-001, F3-012 (actions inherited) |
| F4-C01 | F4-005, F4-006, F4-007 (actions inherited) |
| F4-C02 | F4-002, F4-003 (actions inherited) |
| F5-C01 | F5-001, F5-003 (actions inherited) |
| F5-C02 | F5-006, F5-005 (actions inherited) |
| F6-C01 | F6-001, F6-005, F6-006 (actions inherited) |
| F6-C02 | F6-009, F6-010 (actions inherited) |
| F8-C01 | F8-001, F8-002, F8-004 (actions inherited) |
| F9-C01 | F9-001, F9-002, F9-005 (actions inherited) |

Individual findings that contribute to a composite but are not fully subsumed (e.g. F7-003 when F7-C01 fires) are still presented separately with a note referencing the composite.

---

## RA-009 — Scheduling notes on action items

Action items tagged with a school calendar scheduling note must display that note visibly in the action plan. The four scheduling categories are:

| Category | Label in report | Criteria |
|---|---|---|
| 1 | During school year | Non-disruptive; can happen any time |
| 2 | Winter break | Short, disruptive, low tech-support risk |
| 3 | Spring break | Short, disruptive, tech-support risk possible |
| 4 | Summer | Multi-week or high-disruption work |

Action items without an explicit scheduling note default to Category 1 unless the action description implies otherwise.

Currently tagged actions:
- A3-005b (firewall firmware updates) → Category 3
- A7-008a (restore test requiring systems offline) → Category 3 or 4 depending on system criticality
- A3-013b (AP installation or relocation) → Category 4

Additional scheduling tags will be added as remaining sections are written.

---

## RA-010 — Appendix content requirements

The appendix must include the following regardless of which findings fire:
- Full question-by-question response log for all sections
- Unknown answer log — every question answered as unknown, grouped by section
- Documentation gaps list — every finding of type "missing documentation" by section
- Systems and vendors mentioned — drawn from short_text and list_of_items answers in Sections 3, 4, 6
- Planning dates and events — drawn from 1.16, 10.2, 10.3
- Data quality note — drawn from 10.7 and 10.8 (overall confidence and flagged sections)
- Manual score override log — any section or finding where the IT person adjusted the deterministic score, with the original score, adjusted score, and notes recorded

---

# Section 2: Governance, Budget, Staffing, and Ownership

## Section 2 Purpose
Determine whether the environment has clear accountability for systems, vendors, credentials, recurring tasks, and spending. This section is the primary source for ownership and continuity Key Risk groups.

## Section 2 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 2.2 (named IT leader)
- 2.8 (shared credentials documented)
- 2.9 (coverage if IT lead unavailable)

---

### R2-001 — No named IT leader
**Pattern:** Simple Threshold
**Trigger question:** 2.2

**Conditions:**
- 2.2 (named person responsible for IT leadership) is `no` or `unknown`

**Finding — F2-001**
- Title: No named IT leader or accountable owner
- Severity: **urgent**
- Description: There is no person clearly identified as responsible for IT leadership. Without a named accountable owner, decisions about security, systems, vendors, and priorities default to whoever happens to be available — or to no one. This is the foundational accountability gap that makes every other finding harder to resolve.
- Confidence: high
- risk_category: ownership
- affected_entity: IT leadership role

**Actions:**
- A2-001a: Identify and formally designate a named IT lead or accountable owner — even if this is a part-time or shared role
  - Time horizon: immediate
- A2-001b: Document the role's responsibilities, decision-making authority, and escalation paths
  - Time horizon: next_30_days

**Severity modifier:** If 2.3 (day-to-day responsibilities) is also `no` or `unknown`, elevate report prominence — the environment has neither strategic nor operational IT ownership.

**Cross-section aggregation tag:** F2-001 → Key Risk Group A

---

### R2-002 — Day-to-day support responsibilities not assigned
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 2.3

**Conditions:**
- 2.3 (day-to-day support responsibilities clearly assigned) is `no` or `unknown`

**Finding — F2-002**
- Title: Day-to-day IT support responsibilities not clearly assigned
- Severity: **concern**
- Description: There is no clear assignment of who handles routine IT support tasks. This leads to inconsistent response, tasks falling through the cracks, and staff uncertainty about who to contact when something breaks.
- Confidence: high
- risk_category: ownership
- affected_entity: IT operations

**Actions:**
- A2-002a: Define and document who is responsible for day-to-day IT support tasks — help desk requests, device issues, account problems, printing, classroom tech
  - Time horizon: next_30_days

**Escalation modifier:** If 2.2 is also `no` or `unknown` (no named IT leader), escalate to **urgent** — the environment has no IT accountability at any level.

**Judgment call note:** Concern rather than urgent on its own because informal support can be effective in small schools. The finding targets the documentation gap, not necessarily the absence of support.

---

### R2-003 — System owners not documented
**Pattern:** Simple Threshold
**Trigger question:** 2.4

**Conditions:**
- 2.4 (documented list of system owners) is `no` or `unknown`

**Finding — F2-003**
- Title: System ownership not documented
- Severity: **concern**
- Description: There is no documented record of who owns or is accountable for major platforms and services. When something breaks, renews, or needs to be changed, the absence of documented ownership creates delays and increases the risk that critical systems go unmanaged.
- Confidence: high
- risk_category: ownership
- affected_entity: systems and platforms

**Actions:**
- A2-003a: Create a system ownership register listing each major platform, its owner, and the backup contact
  - Time horizon: next_90_days

**Cross-section aggregation tag:** F2-003 → Key Risk Group A (combines with F2-001 and Section 6 systems visibility findings)

---

### R2-004 — Vendor contacts and escalation paths not documented
**Pattern:** Simple Threshold
**Trigger question:** 2.5

**Conditions:**
- 2.5 (documented vendor contacts and escalation paths) is `no` or `unknown`

**Finding — F2-004**
- Title: Vendor contacts and escalation paths not documented
- Severity: **concern**
- Description: There is no documented record of who to contact at key vendors when something goes wrong. In an incident, the time spent finding a support number or contract reference is time the school cannot afford to lose.
- Confidence: high
- risk_category: continuity
- affected_entity: vendor relationships

**Actions:**
- A2-004a: Create a vendor contact sheet listing each major vendor, support contact, contract or account number, and escalation path
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F2-004 → "Vendor visibility and continuity" group (to be formally defined when Section 6 schema is written)

---

### R2-005 — No formal IT budget
**Pattern:** Graduated Severity
**Trigger question:** 2.6

**Conditions and severity by answer value:**

*Branch A — 2.6 is `no` or `unknown`:*
- Finding — F2-005
- Title: No formal IT budget exists
- Severity: **concern**
- Description: IT spending is not formally budgeted. There is no planned allocation for hardware refresh, software renewals, or unexpected failures, and no financial visibility for leadership. Unbudgeted IT environments tend to defer maintenance until failure forces spending at the worst possible time.
- Actions:
  - A2-005a: Work with school leadership to establish a formal annual IT budget covering at minimum: hardware refresh, software renewals, support contracts, and a contingency reserve
    - Time horizon: next_12_months

*Branch B — 2.6 is `informal`:*
- Finding — F2-005-W
- Title: IT budget exists but is not formally structured
- Severity: **watch**
- Description: IT spending happens but is not tied to a formal annual budget. This limits the school's ability to plan for refresh cycles and reduces financial predictability for leadership. Formalizing the budget is a low-effort improvement with meaningful long-term benefit.
- Actions:
  - A2-005-Wa: Work with leadership to formalize the IT budget structure with defined line items for recurring and capital expenditures
    - Time horizon: next_12_months

*Branch C — 2.6 is `yes annual`:*
- No finding generated. Healthy signal.

---

### R2-006 — Budget or staffing constraints noted
**Pattern:** Constraint Annotation
**Trigger question:** 2.7

**Conditions:**
- 2.7 (known budget or staffing constraints this year) is `yes`

**Finding — F2-006**
- Title: Known budget or staffing constraints affecting IT this year
- Severity: **watch**
- Description: The IT person has identified active constraints that will limit what can be accomplished this year. The report's action plan reflects these constraints through annotation rather than suppression — recommendations that require significant spend or additional staff are flagged with a constraint marker.
- Confidence: high — notes field provides additional context
- risk_category: planning
- affected_entity: IT capacity

**Actions:** None generated automatically.

**Report behavior:** When F2-006 fires, the report assembler attaches a constraint_flag to all action items that require budget or additional staffing. The constraint text from the notes field of 2.7 is included in the annotation. Actions are never removed — the tension is made visible, not hidden.

**Judgment call note — confirmed:** Watch and never escalates. The IT person already knows about the constraint. The value is in making it visible for leadership conversations.

---

### R2-007 — Shared credentials and emergency access not documented
**Pattern:** Simple Threshold
**Trigger question:** 2.8

**Conditions:**
- 2.8 (shared credentials or emergency access documented and controlled) is `no` or `unknown`

**Finding — F2-007**
- Title: Shared credentials and emergency access not documented or controlled
- Severity: **urgent**
- Description: There is no documented or controlled record of shared credentials or emergency access methods. In an incident — especially one where the primary IT person is unavailable — the inability to access critical systems through an emergency path can turn a manageable problem into a crisis. Undocumented shared credentials without mitigating controls are frequently identified as a root cause in costly IT failures: they enable unauthorized access, prevent timely recovery, and make it impossible to audit who did what after an incident. This is one of the most impactful and most easily resolved items on this report.
- Confidence: high
- risk_category: continuity
- affected_entity: emergency access and credential control

**Actions:**
- A2-007a: Identify all shared credentials and emergency access methods currently in use across systems
  - Time horizon: immediate
- A2-007b: Document, secure, and control access to these credentials — using a password manager with emergency access, a sealed physical record, or equivalent
  - Time horizon: next_30_days
- A2-007c: Verify that at least one other authorized person can access these credentials without involving the primary IT person
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F2-007 → Key Risk Group B (combines with F2-009/F2-C02 and F7-012)

---

### R2-008 — Primary IT lead cannot be covered for two weeks
**Pattern:** Graduated Severity
**Trigger question:** 2.9

**Conditions and severity by answer value:**

*Branch A — 2.9 is `no`:*
- Finding — F2-008
- Severity: **concern** with elevated report prominence in Key Risks section
- Description: If the primary IT person is unexpectedly unavailable, the school has no reliable path to maintain basic IT operations. This is a single-person dependency that creates ongoing operational risk, particularly during critical periods.

*Branch B — 2.9 is `partially`:*
- Finding — F2-008
- Severity: **concern**
- Description: Basic IT operations could partially continue if the primary IT person were unavailable, but coverage is incomplete. Key systems, vendors, or processes may not be manageable by anyone else.

*Branch C — 2.9 is `unknown`:*
- Finding — F2-008
- Severity: **concern** — treated as effectively `no` for planning purposes

**Actions (all branches):**
- A2-008a: Identify at least one person — internal or external — who could cover basic IT operations in an emergency
  - Time horizon: next_90_days
- A2-008b: Document the minimum knowledge and access that person would need, and begin cross-training or access provisioning
  - Time horizon: next_90_days
- A2-008c: Consider establishing a relationship with an MSP or IT consultant as a coverage backstop if no internal candidate exists
  - Time horizon: next_12_months

**Escalation modifier:** If F2-007 also fires (shared credentials undocumented), escalate F2-008 to **urgent** via composite rule R2-C02.

**Cross-section aggregation tag:** F2-008 → Key Risk Group B

---

### R2-009 — Recurring IT tasks not tracked
**Pattern:** Graduated Severity
**Trigger question:** 2.10

**Conditions and severity by answer value:**

*Branch A — 2.10 is `no`:*
- Finding — F2-009
- Severity: **concern**
- Description: Recurring IT tasks are not being tracked in any system. Firmware reviews, backup checks, account audits, and renewal reminders depend entirely on memory, which is unreliable when workload increases or staff changes.

*Branch B — 2.10 is `partially`:*
- Finding — F2-009
- Severity: **watch**
- Description: Some recurring IT tasks are tracked but the system is incomplete. The report should acknowledge what is being tracked and focus the action on filling gaps rather than rebuilding from scratch.

*Branch C — 2.10 is `unknown`:*
- Finding — F2-009
- Severity: **watch**

**Actions (all branches):**
- A2-009a: Create a recurring IT task calendar or checklist covering at minimum: monthly backup reviews, quarterly admin account audits, firmware review cadence, and annual renewal reminders
  - Time horizon: next_90_days

---

### R2-010 — No ticketing system in use
**Pattern:** Graduated Severity
**Trigger question:** 2.11

**Conditions and severity by answer value:**

*Branch A — 2.11 is `no` or `unknown`:*
- Finding — F2-010
- Title: No ticketing system in use for IT support
- Severity: **watch**
- Description: IT support requests are not being tracked through a ticketing system. Without a record of requests, it is difficult to identify recurring problems, demonstrate workload, or ensure nothing falls through the cracks.
- Actions:
  - A2-010a: Evaluate low-cost or free ticketing tools appropriate for a small school IT environment
    - Time horizon: next_12_months

*Branch B — 2.11 is `yes but limited use`:*
- No finding generated. Observation noted in appendix: ticketing system exists but is underutilized.

*Branch C — 2.11 is `yes in regular use`:*
- No finding generated. Healthy signal.

**Judgment call note — confirmed:** Watch and never urgent. A ticketing system is a maturity improvement, not a safety issue.

---

### R2-011 — Software approval process unclear
**Pattern:** Simple Threshold
**Trigger question:** 2.12

**Conditions:**
- 2.12 (who decides on new classroom software) is blank, unanswered, or explicitly unclear

**Finding — F2-011**
- Title: No clear process for approving new classroom software or digital tools
- Severity: **watch**
- Description: There is no defined process for deciding whether new software or digital tools may be adopted for classroom use. This creates risk around student data privacy (FERPA/COPPA), unsanctioned tool sprawl, and inconsistent IT support obligations.
- Confidence: moderate — optional question; may simply be unanswered
- risk_category: planning
- affected_entity: software governance

**Actions:**
- A2-011a: Define and document who has authority to approve new classroom software, what review criteria apply including student data handling, and how IT is notified
  - Time horizon: next_12_months

**Cross-section aggregation tag:** F2-011 may combine with Section 6 FERPA/COPPA visibility findings → "Student data governance" group (to be formally defined when Section 6 schema is written)

**Judgment call note:** Watch because many schools handle software approval informally but adequately. Most significant when paired with weak FERPA/COPPA visibility in Section 6.

---

## Section 2 Composite Rules

### R2-C01 — No IT accountability at any level
**Pattern:** Composite

**Conditions (all must be true):**
- 2.2 (named IT leader) is `no` or `unknown`
- AND 2.3 (day-to-day responsibilities assigned) is `no` or `unknown`
- AND 2.4 (system owners documented) is `no` or `unknown`

**Finding — F2-C01**
- Title: No IT accountability structure exists at any level
- Severity: **urgent**
- Description: There is no named IT leader, no assignment of day-to-day responsibilities, and no documented system ownership. The IT environment is operating without any formal accountability structure. Every finding in this report should be read in that context — there is currently no clear owner for any of them.
- Confidence: high
- risk_category: ownership
- affected_entity: entire IT function

**Actions:** Inherit A2-001a, A2-001b, A2-002a, A2-003a. Present as a single consolidated urgent finding.

**Report note:** F2-C01 must appear in the Executive Summary. It is the highest-priority governance finding in Module 1 and should be the first item in the Key Risks section if it fires.

**Cross-section aggregation tag:** F2-C01 → Key Risk Group A (primary finding)

---

### R2-C02 — Single-person dependency with no emergency access path
**Pattern:** Composite

**Conditions (all must be true):**
- 2.9 (coverage if IT lead unavailable) is `no` or `unknown`
- AND 2.8 (shared credentials/emergency access documented) is `no` or `unknown`

**Finding — F2-C02**
- Title: Single-person IT dependency with no documented emergency access path
- Severity: **urgent**
- Description: The school depends entirely on one person for IT operations, and there is no documented path for anyone else to access critical systems in an emergency. If that person is unexpectedly unavailable, the school has no way to maintain or recover IT operations.
- Confidence: high
- risk_category: continuity
- affected_entity: IT staffing resilience and emergency access

**Actions:** Inherit A2-007a, A2-007b, A2-007c, A2-008a, A2-008b. Present as a single consolidated urgent finding.

**Cross-section aggregation tag:** F2-C02 → Key Risk Group B (primary finding; always combine with F7-012 and Section 9 knowledge concentration findings)

---

## Section 2 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F2-C01 fires (no accountability at any level) | urgent |
| F2-C02 fires (single-person dependency + no emergency access) | urgent |
| F2-007 fires alone (shared credentials undocumented) | urgent |
| F2-001 fires alone (no named IT leader) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum |

**Unknown override:** Critical questions for this section: 2.2, 2.8, 2.9. If any are unknown, floor rises to concern.

---

## Section 2 Judgment Calls — Confirmed

1. **F2-001 (no named IT leader) is urgent — confirmed.** The foundational governance gap that makes every other finding harder to resolve.
2. **F2-007 (shared credentials undocumented) is urgent — confirmed.** Undocumented shared credentials are a frequent root cause of costly IT failures. Urgent and highly resolvable.
3. **F2-009 separates `partially` (watch) from `no` (concern) — confirmed.** Partial tracking is common and functional; complete absence is a meaningful gap.
4. **F2-005 uses graduated severity — confirmed.** Formal, informal, and absent budgets represent meaningfully different risk levels and warrant different findings.
5. **F2-006 (constraint annotation) never escalates — confirmed.** Constraints are a reality; the report's job is to make the tension visible, not to alarm.

---

# Section 7: Data Protection, Backup, and Recovery

## Section 7 Purpose
Understand whether data protection exists, is documented, and can be relied upon during an incident. This section favors verifiable recovery readiness over optimistic assumptions.

## Section 7 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 7.2 (backups in place)
- 7.8 (restore test performed)
- 7.12 (emergency credential access)
- 7.13 (useful recovery window) — reinforces concern floor when unknown alongside 7.2 or 7.8

---

### R7-001 — No backup platform identified
**Pattern:** Composite (both conditions required)
**Trigger questions:** 7.1, 7.2

**Conditions:**
- 7.1 (backup platform) is blank or unanswered
- AND 7.2 (backups in place) is `no` or `unknown`

**Finding — F7-001**
- Title: No backup platform or coverage identified
- Severity: **urgent**
- Description: No backup service or platform has been identified, and there is no confirmation that critical systems or data are protected. This represents a fundamental continuity and data protection gap.
- Confidence: high when both conditions are met

**Actions:**
- A7-001a: Determine whether any backup service is currently in use, even informally
  - Time horizon: immediate
- A7-001b: If no backup exists, select and implement a backup platform covering at minimum critical servers and cloud data
  - Time horizon: next_30_days

**Judgment call note:** This is the highest-severity rule in Section 7. Do not downgrade based on other positive answers in this section.

---

### R7-002 — Backup existence is assumed, not confirmed
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.2

**Conditions:**
- 7.2 (backups in place) is `maybe or assumed`

**Finding — F7-002**
- Title: Backup coverage assumed but not verified
- Severity: **concern**
- Description: Backups are believed to exist but have not been confirmed. Assumed backups that have never been tested or verified should not be relied upon for recovery planning.
- Confidence: high

**Actions:**
- A7-002a: Confirm what backup service or tool is actually in use and document the platform
  - Time horizon: next_30_days
- A7-002b: Verify backup jobs are running and review recent success logs
  - Time horizon: next_30_days

**Escalation modifier:** If 7.8 (restore test) is also `no` or `unknown`, escalate F7-002 to **urgent**.

---

### R7-003 — Backup scope not documented
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.3

**Conditions:**
- 7.2 is NOT `no`
- AND 7.3 (documented list of what is and is not backed up) is `partial`, `no`, or `unknown`

**Finding — F7-003**
- Title: Backup scope not clearly documented
- Severity: **concern**
- Description: There is no clear documented record of what is and is not backed up. Without this, it is impossible to know what would be lost in a recovery scenario.
- Confidence: high

**Actions:**
- A7-003a: Create and maintain a backup scope document listing every system, data set, and service — and explicitly noting what is excluded
  - Time horizon: next_30_days

**Escalation modifier:** If 7.3 is `no` AND 7.2 is `maybe or assumed`, escalate to **urgent**.

---

### R7-004 — Server backup gap
**Pattern:** Simple Threshold + Cross-Section Reference
**Trigger questions:** 7.4, 6.13

**Conditions:**
- Server infrastructure exists (6.13 > 0 or server infrastructure confirmed)
- AND 7.4 (backups cover servers) is `partial`, `no`, or `unknown`

**Finding — F7-004**
- Title: Server backup coverage incomplete or unconfirmed
- Severity: **urgent**
- Description: Servers are in use but backup coverage is incomplete, absent, or unknown. Server data loss without backup is typically unrecoverable.
- Confidence: high when server existence is confirmed

**Actions:**
- A7-004a: Verify current backup coverage for each server and document gaps
  - Time horizon: next_30_days
- A7-004b: Extend backup coverage to all servers not currently protected
  - Time horizon: next_30_days

**Judgment call note — confirmed:** Partial server coverage is urgent regardless of total server count. Any unprotected server in a small school is effectively a critical server.

---

### R7-005 — Staff device backup gap
**Pattern:** Cross-Section Reference + Graduated Severity
**Trigger questions:** 7.5, 4.1, 4.10

**Conditions:**
- Staff devices store important local data OR endpoint backup is expected
- AND 7.5 (backups cover staff devices) is `partial`, `no`, or `unknown`

**Finding — F7-005**
- Title: Staff device data protection incomplete or absent
- Severity: determined by cross-section reference (see below)
- Description: Staff devices are not fully covered by backup. Severity depends on whether staff primarily work in cloud-synced environments or store critical data locally.
- Confidence: moderate

**Severity logic (cross-section):**
- 4.1 is `google_workspace` or `microsoft_365` AND 4.10 (auto-sync) is `yes fully` → **watch**
- 4.1 is `google_workspace` or `microsoft_365` AND 4.10 is `yes partially` or `unknown` → **concern**
- 4.1 is `local_directory`, `other`, or `unknown` → **concern**

**Actions:**
- A7-005a: Determine which staff devices store irreplaceable local data and whether those devices are backed up
  - Time horizon: next_90_days

**Judgment call note — confirmed:** The cross-reference to 4.10 is the key moderator. Should not fire at concern in a well-configured cloud environment with consistent sync.

---

### R7-006 — Cloud data backup gap
**Pattern:** Simple Threshold
**Trigger question:** 7.6

**Conditions:**
- Cloud systems or online school data are in use (effectively always true in v1)
- AND 7.6 (backups cover critical cloud data) is `partial`, `no`, or `unknown`

**Finding — F7-006**
- Title: Cloud and online school data not fully protected
- Severity: **concern**
- Description: Critical cloud systems or online school data lack confirmed backup coverage. Many schools assume cloud platforms back up their data automatically — this is not always true or sufficient for recovery scenarios. Cloud platforms provide availability, not backup. A deleted file, corrupted record, or ransomware event can propagate through a synced environment before anyone notices. Storing data in Google Drive or Microsoft 365 is not the same as having it backed up.
- Confidence: high

**Actions:**
- A7-006a: Identify which cloud platforms hold critical school data (SIS, LMS, Google Workspace, M365, etc.)
  - Time horizon: next_30_days
- A7-006b: Verify what backup or export options exist for each platform and implement where missing
  - Time horizon: next_90_days

**Judgment call note — confirmed:** Concern is correct. The plain-language note in the description is intentional and should appear verbatim in the report — it is written to be usable by the IT person when educating leadership.

---

### R7-007 — Backup success not regularly reviewed
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.7

**Conditions:**
- 7.2 is not `no`
- AND 7.7 (backup success reviewed regularly) is `irregularly`, `no`, or `unknown`

**Finding — F7-007**
- Title: Backup success not regularly monitored
- Severity: **concern**
- Description: Backups may be running but are not being reviewed for success. Silent backup failures are a common cause of data loss being discovered only at the moment recovery is needed.
- Confidence: high

**Actions:**
- A7-007a: Establish a regular backup review cadence — at minimum weekly review of backup job success logs
  - Time horizon: next_30_days
- A7-007b: Configure alerting so backup failures notify the IT person automatically rather than requiring manual checking
  - Time horizon: next_30_days

**Escalation modifier:** If 7.7 is `no` or `unknown` AND 7.8 is also `no` or `unknown`, escalate to **urgent**.

---
### R7-007b — Backup storage location is onsite only or inconsistent
**Pattern:** Graduated Severity
**Trigger question:** 7.7b
**Note:** This rule was added in v0.1.7 intake engine revision. Not in original schema.

**Conditions:**
- 7.1 is not `No` or `Unknown` (backups exist)
- AND 7.7b (backup storage location) is `Onsite only` or `Inconsistent`

**Severity by answer value:**
- 7.7b is `Onsite only` → **concern** — no offsite copy; a single physical event destroys both primary and backup
- 7.7b is `Inconsistent` → **watch** — some backups have offsite copies, others do not

**Finding — F7-007b**
- Title (concern): Backups stored onsite only — no offsite or cloud copy confirmed
- Title (watch): Backup storage location inconsistent — some offsite, some onsite only
- Description (concern): All backup copies are stored at the school. A single physical event — fire, flood, theft, or power surge — can destroy both the primary data and the only backup simultaneously. Offsite or cloud backup storage is a fundamental component of a complete data protection strategy.
- Description (watch): Backup storage location varies — some backups have offsite copies and some do not. The inconsistency means the coverage of offsite protection is unclear.
- Confidence: high

**Actions:**
- A7-007b-a: Establish offsite or cloud backup storage for all critical systems — options include cloud backup services, encrypted offsite storage, or a managed backup service
  - Time horizon: next_30_days

---

### R7-008 — No recent restore test
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.8

**Conditions:**
- 7.2 is not `no`
- AND 7.8 (restore test in last 12 months) is `more than 12 months ago`, `no`, or `unknown`

**Finding — F7-008**
- Title: Backup restore not tested or not tested recently
- Severity: **concern**
- Description: A backup that has never been tested — or has not been tested within a timeframe proportional to the backup's useful recovery window — cannot be relied upon. The standard for "recent enough" depends on how far back a restore would actually be useful. If the school's retention means data older than one week is unrecoverable in a usable state, restore tests should happen at least that frequently. A restore test performed once and never repeated gives no ongoing confidence.
- Confidence: high

**Actions:**
- A7-008a: Schedule and perform a documented restore test for at least one critical system
  - Time horizon: next_30_days
- A7-008b: Establish a recurring restore test schedule aligned with the backup retention window — see 7.13 and 7.14
  - Time horizon: next_90_days

**Escalation modifier:** If 7.8 is `no` or `unknown` AND 7.2 is `maybe or assumed`, escalate to **urgent**. If 7.8 is `more than 12 months ago` AND 7.9 is `less than annually` or `never`, escalate to **urgent**.

**Scheduling note:** Restore tests requiring systems offline → school calendar category: spring break or summer.

---

### R7-009 — Restore test frequency too low
**Pattern:** Simple Threshold
**Trigger question:** 7.9

**Conditions:**
- 7.8 is `yes` or `more than 12 months ago`
- AND 7.9 (restore test frequency) is `less than annually`, `never`, or `unknown`

**Finding — F7-009**
- Title: Restore tests performed too infrequently relative to backup window
- Severity: **concern**
- Description: Restore tests are happening but not frequently enough to provide reliable recovery confidence. The acceptable frequency is proportional to the useful recovery window, not a fixed calendar interval. A school that can only recover data from the last 30 days needs to know within that window whether its backups are working. See also R7-013 and R7-014.
- Confidence: high

**Actions:**
- A7-009a: Review backup retention policy and determine the useful recovery window
  - Time horizon: next_30_days
- A7-009b: Align restore test frequency with the useful recovery window
  - Time horizon: next_90_days

**Note:** Supplements R7-008. If R7-008 fires at urgent, merge R7-009 actions into the same action set.

---

### R7-010 — No defined recovery priority
**Pattern:** Simple Threshold
**Trigger question:** 7.10

**Conditions:**
- More than one critical system exists (effectively always true in v1)
- AND 7.10 (recovery priority defined) is `partial`, `no`, or `unknown`

**Finding — F7-010**
- Title: No defined recovery priority for critical systems
- Severity: **concern**
- Description: When multiple systems are affected in an incident, the order of recovery matters. Without a defined priority, recovery decisions will be made under pressure without a plan.
- Confidence: high

**Actions:**
- A7-010a: Define and document a recovery priority order for critical systems
  - Time horizon: next_90_days

**Judgment call note:** Planning and documentation finding only. A simple ordered list is sufficient to close it — no vendor help required.

---

### R7-011 — No incident or disaster response reference
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.11

**Conditions:**
- 7.11 (written incident/disaster response reference) is `partial`, `no`, or `unknown`

**Finding — F7-011**
- Title: No written incident or disaster response reference
- Severity: **concern**
- Description: There is no documented reference for how to respond to a significant IT incident or outage. In a crisis, the IT person — or whoever is covering — needs a written starting point, not just institutional knowledge. A one-page reference stored somewhere accessible (including offline) is sufficient to close this finding.
- Confidence: high

**Actions:**
- A7-011a: Create a basic IT incident response reference covering at minimum: who to call, what systems to check first, how to access backup and recovery tools, and how to communicate with staff and leadership during an outage
  - Time horizon: next_90_days

**Escalation modifier:** If 7.12 is also `no` or `unknown`, escalate to **urgent**.

---

### R7-012 — Emergency credential access not secured or unknown
**Pattern:** Simple Threshold + Escalation Modifier
**Trigger question:** 7.12

**Conditions:**
- 7.12 (critical admin credentials accessible in an emergency) is `partially`, `no`, or `unknown`

**Finding — F7-012**
- Title: Emergency access to critical credentials not confirmed
- Severity: **urgent**
- Description: Critical admin credentials and recovery materials are not confirmed to be accessible in an emergency. If the primary IT person is unavailable during an incident, recovery may be impossible without these credentials.
- Confidence: high
- risk_category: continuity
- affected_entity: emergency access and credential control

**Actions:**
- A7-012a: Identify all critical admin credentials and recovery materials (firewall admin, domain admin, backup tool access, cloud platform recovery codes, etc.)
  - Time horizon: immediate
- A7-012b: Store credentials securely in a documented, accessible location — a password manager with emergency access, a sealed physical envelope in a secure location, or equivalent
  - Time horizon: next_30_days
- A7-012c: Verify that at least one other authorized person knows how to access these materials in an emergency
  - Time horizon: next_30_days

**Escalation modifier:** If 7.12 is `no` specifically, A7-012a is marked immediate with no exceptions.

**Cross-section aggregation tag:** F7-012 → Key Risk Group B (combines with F2-C02 and Section 9 knowledge concentration findings)

---

### R7-013 — Backup useful recovery window not defined
**Pattern:** Simple Threshold
**Trigger question:** 7.13

**Conditions:**
- 7.2 is not `no`
- AND 7.13 (useful recovery window) is `unknown` or unanswered

**Finding — F7-013**
- Title: Backup useful recovery window not known
- Severity: **concern**
- Description: The IT person does not know how far back a backup restore would actually be useful. Without understanding the retention window, it is impossible to evaluate whether current backup frequency and restore test cadence are appropriate.
- Confidence: high

**Actions:**
- A7-013a: Review the backup platform's retention policy and determine the practical useful recovery window
  - Time horizon: next_30_days
- A7-013b: Document the retention window and use it to set restore test frequency
  - Time horizon: next_30_days

---

### R7-014 — Restore tests not aligned with backup retention window
**Pattern:** Cross-Section Reference + Simple Threshold
**Trigger questions:** 7.13, 7.14

**Conditions:**
- 7.13 is answered (not unknown)
- AND 7.8 is not `no`
- AND 7.14 (restore tests within useful window) is `no` or `unknown`

**Finding — F7-014**
- Title: Restore test frequency not aligned with backup retention window
- Severity: **concern**
- Description: The school knows how far back a restore is useful but is not testing frequently enough to detect failures within that window. If the useful window is 14 days and restores are only tested annually, up to a year of backup failures could go undetected.
- Confidence: high

**Actions:**
- A7-014a: Establish a restore test schedule aligned with the useful recovery window — at least one test per window period. Lightweight file-level tests are sufficient for routine cadence checks; full system restores can occur annually or during break windows.
  - Time horizon: next_90_days

---

## Section 7 Composite Rules

### R7-C01 — Complete backup confidence failure
**Pattern:** Composite

**Conditions (all must be true):**
- 7.2 is `no` or `unknown`
- AND 7.7 is `no` or `unknown`
- AND 7.8 is `no` or `unknown`

**Finding — F7-C01**
- Title: No verifiable data protection in place
- Severity: **urgent**
- Description: There is no confirmed backup coverage, no backup monitoring, and no restore test history. This environment has no verifiable data protection. A single incident could result in permanent, unrecoverable data loss.
- Confidence: high

**Actions:** Inherit A7-001a, A7-001b, A7-002a, A7-007a, A7-008a. Present as single consolidated urgent finding.

**Report note:** Always appears in Executive Summary and Key Risks. Never suppressed.

---

### R7-C02 — Backup exists but recovery is unverified
**Pattern:** Composite + Escalation Modifier

**Conditions (all must be true):**
- 7.2 is `yes confirmed` or `maybe or assumed`
- AND 7.7 is `irregularly`, `no`, or `unknown`
- AND 7.8 is `more than 12 months ago`, `no`, or `unknown`

**Finding — F7-C02**
- Title: Backups running but recovery confidence is low
- Severity: **concern** — escalates to **urgent** if 7.2 is `maybe or assumed`
- Description: Backups appear to be in place but are not being monitored reliably and have not been tested recently enough to confirm they would succeed in a recovery scenario. The school may believe it is protected when it is not.
- Confidence: high

**Actions:**
- A7-C02a: Perform an immediate backup review — confirm jobs are running, review success logs, and schedule a restore test
  - Time horizon: next_30_days

---

## Section 7 Domain Score Logic

| Condition | Domain Status |
|---|---|
| R7-C01 fires | urgent |
| Any urgent rule fires (R7-001, R7-004, R7-012, R7-C02 escalated) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 7.2, 7.8, or 7.12 are among the unknowns |

**Unknown override:** Critical questions: 7.1, 7.8, 7.12, 7.13. Unknown on any raises floor to concern.

**Gate question note:** 7.1 (Are backups in place?) is the gate question for Section 7. When 7.1 is `No` or `Unknown`, all dependent questions are hidden in the intake engine. In the rules engine, R7-C01 fires directly when 7.1 is `No` or `Unknown` without requiring evaluation of 7.2, 7.7, or 7.8 — those questions are implicitly treated as negative when the gate fires.

---

## Section 7 Judgment Calls — Confirmed

1. **R7-004 (server backup) is urgent even when partial — confirmed.** Any server count, any unprotected server is urgent.
2. **R7-005 (staff device backup) severity is context-dependent — confirmed.** Determined by 4.1 and 4.10 cross-reference.
3. **R7-006 (cloud data backup) is concern — confirmed.** Plain-language availability-vs-backup note must appear in report verbatim.
4. **R7-009 (restore frequency) is concern — confirmed.** Proportional to useful recovery window, not a fixed calendar interval.
5. **Lightweight vs full restore tests — confirmed.** File-level tests satisfy routine cadence; full system restores for annual and break-window schedule.

---

# Section 3: Sites, Buildings, Network, and Internet

## Section 3 Purpose
Establish the physical shape, dependencies, equipment profile, and documentation status of the network environment. This is the most finding-heavy section in Module 1 because missing network visibility tends to block later planning and incident response. Many findings here are documentation gaps rather than technical failures — the environment may be functional but unrecoverable or unsupportable without documentation.

## Section 3 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 3.7 (firewall exists)
- 3.12 (admin access to network infrastructure)
- 3.15 (internet failover)
- 3.18 (switch/wireless config backup)

---

### R3-001 — No current network diagram
**Pattern:** Graduated Severity
**Trigger question:** 3.2

**Severity by answer value:**
- 3.2 is `no` or `unknown` → **concern**
- 3.2 is `yes outdated` → **watch**

**Finding — F3-001**
- Title (concern): No network diagram exists
- Title (watch): Network diagram exists but is outdated
- Description (concern): There is no network diagram for the school's environment. Without a diagram, troubleshooting, planning, and onboarding a new IT person or vendor all become significantly harder. In an incident, the absence of a diagram can substantially extend downtime.
- Description (watch): A network diagram exists but does not reflect the current state of the environment. An outdated diagram can be worse than no diagram — it may lead troubleshooters in the wrong direction.
- Confidence: high

**Actions:**
- A3-001a: Create or update the network diagram to reflect the current environment — internet connections, firewall, core switches, wireless infrastructure, and server connections
  - Time horizon: next_90_days

**Escalation modifier:** If 3.3 (site/rack maps) is also `no` or `unknown`, escalate the concern branch to **urgent** — the environment has no physical or logical network documentation whatsoever.

---

### R3-002 — No site map or closet/rack map
**Pattern:** Graduated Severity
**Trigger question:** 3.3

**Severity by answer value:**
- 3.3 is `no` or `unknown` → **concern**
- 3.3 is `partial` → **watch**

**Finding — F3-002**
- Title (concern): No site or closet/rack maps exist
- Title (watch): Site and closet/rack maps incomplete
- Description (concern): There are no maps documenting where network equipment is physically located across sites or buildings. Physical location knowledge is critical for troubleshooting, vendor visits, and onboarding.
- Description (watch): Some site or closet maps exist but coverage is incomplete. Missing locations represent gaps in physical environment knowledge.
- Confidence: high

**Actions:**
- A3-002a: Create or complete site maps and closet/rack maps for all buildings with network infrastructure — document equipment location, cable paths, and patch panel assignments
  - Time horizon: next_90_days

**Cross-reference note:** Pairs with R3-001. If both fire at concern or above, present together as a combined network documentation gap finding.

---

### R3-003 — AP physical locations not fully known
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 3.4, 3.1

**Conditions:**
- Wireless networking is in scope
- AND 3.4 (AP physical locations known) is `partial`, `no`, or `unknown`

**Severity logic:**
- 3.4 is `no` or `unknown` → **concern** (regardless of floor plan status)
- 3.4 is `partial` AND 3.1 (floor plans) is `no` or `unknown` → **concern**
- 3.4 is `partial` AND 3.1 is `partial` or `yes current` → **watch**

**Finding — F3-003**
- Title: Wireless access point locations not fully documented
- Severity: as above
- Description: The physical location of wireless access points is not fully known or documented. Without this, coverage analysis, troubleshooting, and future wireless planning are all guesswork. Combined with missing floor plans, the environment cannot be meaningfully assessed for wireless adequacy.
- Confidence: high

**Actions:**
- A3-003a: Walk the environment and document the physical location of every access point — building, floor, room, or zone. Photograph or sketch locations if floor plans are unavailable.
  - Time horizon: next_90_days

---

### R3-004 — No firewall or firewall existence unknown
**Pattern:** Simple Threshold
**Trigger question:** 3.7

**Conditions:**
- 3.7 (firewall exists) is `no` or `unknown`

**Finding — F3-004**
- Title: No firewall confirmed or firewall existence unknown
- Severity: **urgent**
- Description: The school either has no firewall protecting its network perimeter or cannot confirm whether one exists. A firewall is the most fundamental perimeter security control. Without one — or without knowing whether one is in place — the school's network is exposed to external threats with no documented defense layer.
- Confidence: high
- risk_category: security
- affected_entity: network perimeter

**Actions:**
- A3-004a: Determine whether a firewall is currently in place — check with ISP, MSP, or any vendor who manages network equipment
  - Time horizon: immediate
- A3-004b: If no firewall exists, procure and deploy one appropriate for the school's size and network architecture
  - Time horizon: next_30_days

**Judgment call note:** Unknown is treated identically to no. The school cannot claim perimeter protection if it does not know whether it has a firewall. This is one of the few cases where unknown and no produce the same urgent outcome.

---

### R3-005 — Firewall details not known
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 3.17, 3.7

**Conditions:**
- 3.7 indicates a firewall exists
- AND 3.17 (firewall platform, firmware, support status known) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.17 is `no` or `unknown` → **concern**
- 3.17 is `partial` → **watch**

**Finding — F3-005**
- Title: Firewall platform, firmware, or support status not fully known
- Severity: as above
- Description: A firewall is in place but its platform details, firmware currency, or support/warranty status are not fully documented. An unpatched or out-of-support firewall may provide less protection than assumed — and firmware updates scheduled without knowing the current version risk breaking the configuration.
- Confidence: high

**Actions:**
- A3-005a: Document the firewall platform, model, current firmware version, and support or warranty expiry date
  - Time horizon: next_30_days
- A3-005b: Verify firmware is current and schedule a review cadence — at minimum twice per year
  - Time horizon: next_30_days

**Scheduling note:** Firewall firmware updates → school calendar Category 3 (spring break). Do not schedule during the school day or winter break.

---

### R3-006 — AP inventory incomplete or absent
**Pattern:** Graduated Severity
**Trigger question:** 3.6

**Conditions:**
- Wireless APs exist
- AND 3.6 (APs inventoried with model and firmware) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.8 is `no` or `unknown` → **concern**
- 3.8 is `partial` → **watch**

**Finding — F3-006**
- Title: Wireless access point inventory incomplete or absent
- Severity: as above
- Description: Access points are not fully inventoried with model and firmware information. Without this, lifecycle planning, firmware management, and vendor support are all impaired.
- Confidence: high

**Actions:**
- A3-006a: Create or complete a wireless AP inventory including: physical location, model, serial number, firmware version, and management platform
  - Time horizon: next_90_days

**Cross-reference note:** Pairs with R3-003 (AP locations). If both fire, present as a single wireless visibility finding.

---

### R3-007 — Switch inventory incomplete or absent
**Pattern:** Graduated Severity
**Trigger question:** 3.9

**Conditions:**
- Switches exist
- AND 3.9 (switches inventoried with model and firmware) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.9 is `no` or `unknown` → **concern**
- 3.9 is `partial` → **watch**

**Finding — F3-007**
- Title: Switch inventory incomplete or absent
- Severity: as above
- Description: Switches are not fully inventoried with model and firmware information. Without this, firmware management, lifecycle planning, and troubleshooting are all impaired.
- Confidence: high

**Actions:**
- A3-007a: Create or complete a switch inventory including: location, model, serial number, firmware version, management platform, and support status
  - Time horizon: next_90_days

---

### R3-008 — No switch topology map
**Pattern:** Graduated Severity
**Trigger question:** 3.10

**Conditions:**
- Switches exist or more than one closet/building exists
- AND 3.10 (switch map) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.10 is `no` or `unknown` → **concern**
- 3.10 is `partial` → **watch**

**Finding — F3-008**
- Title: Switch topology map incomplete or absent
- Severity: as above
- Description: There is no complete map showing how the school's switches connect to one another. In a multi-building or multi-closet environment, the absence of a topology map makes fault isolation extremely difficult — a single failed uplink may be invisible until multiple areas lose connectivity.
- Confidence: high

**Actions:**
- A3-008a: Document the switch topology — which switch connects to which, via which ports, across which buildings or closets
  - Time horizon: next_90_days

**Escalation modifier:** If 3.2 (network diagram) is also `no` or `unknown`, merge these two findings — the switch topology is typically part of the network diagram.

---

### R3-009 — Core network devices not inventoried with support status
**Pattern:** Graduated Severity
**Trigger question:** 3.11

**Conditions:**
- 3.11 (core network devices inventoried with make, model, location, support status) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.11 is `no` or `unknown` → **concern**
- 3.11 is `partial` → **watch**

**Finding — F3-009**
- Title: Core network device inventory incomplete — lifecycle and support status unclear
- Severity: as above
- Description: Core network devices are not fully inventoried with make, model, location, and support status. Without this, it is impossible to know which devices are approaching end of support, which are covered under warranty, or which require urgent lifecycle action.
- Confidence: high

**Actions:**
- A3-009a: Complete a core network device inventory including make, model, serial number, physical location, firmware version, warranty/support expiry, and management access method
  - Time horizon: next_90_days

---

### R3-010 — Administrative access to network infrastructure limited or unknown
**Pattern:** Graduated Severity
**Trigger question:** 3.12

**Severity by answer value:**
- 3.12 is `no` → **urgent**
- 3.12 is `unknown` → **urgent**
- 3.12 is `partial` → **concern**

**Finding — F3-010**
- Title: Administrative access to network infrastructure not confirmed or incomplete
- Severity: as above
- Description: The school does not have full administrative access to its own network infrastructure. Partial or absent admin access creates dependency on a vendor or third party for any change, update, or emergency response. In an incident, waiting for a vendor to respond before accessing a device can dramatically extend downtime.
- Confidence: high
- risk_category: continuity
- affected_entity: network infrastructure control

**Actions:**
- A3-010a: Identify which network devices the school does and does not have admin access to, and document the access method for each
  - Time horizon: immediate
- A3-010b: For devices without school-controlled access, document the vendor escalation path and confirm access can be obtained in an emergency
  - Time horizon: next_30_days
- A3-010c: Where practical, work to obtain and document admin credentials for all critical network devices
  - Time horizon: next_90_days

**Cross-section aggregation tag:** F3-010 (when urgent) → Key Risk Group A — lack of admin access to your own infrastructure is an ownership and control finding.

---

### R3-011 — No internet failover or redundancy
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 3.15, 3.13

**Conditions:**
- Internet connectivity is required (always true in v1)
- AND 3.15 is `no`, `unknown`, or `yes manual`

**Severity by answer value:**
- 3.15 is `no` AND 3.13 = 1 → **concern**
- 3.15 is `unknown` → **concern**
- 3.15 is `yes manual` → **watch**
- 3.15 is `no` AND 3.13 > 1 → **watch** — multiple connections exist but failover behavior undocumented

**Finding — F3-011**
- Title: No automatic internet failover — single point of internet failure
- Severity: as above
- Description: The school has no confirmed automatic failover for internet connectivity. A single ISP outage will take the entire school offline with no recovery path until service is restored. In environments where attendance, communication, and learning platforms are cloud-dependent, even a brief outage has significant operational impact.
- Confidence: high

**Actions:**
- A3-011a: Assess the operational impact of a complete internet outage — what systems fail, what operations stop, and for how long the school can function offline
  - Time horizon: next_90_days
- A3-011b: Evaluate cost and feasibility of a secondary connection or 4G/5G failover solution
  - Time horizon: next_12_months

**Judgment call note:** Concern rather than urgent — internet resilience is a budget and planning question for most small schools. Many operate acceptably on single connections. The finding surfaces the risk and prompts planning without alarming.

---

### R3-012 — Switch and wireless configurations not backed up
**Pattern:** Graduated Severity
**Trigger question:** 3.18

**Conditions:**
- Switches or APs exist
- AND 3.18 (configs backed up or exportable) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.18 is `no` or `unknown` → **urgent**
- 3.18 is `partial` → **concern**

**Finding — F3-012**
- Title: Network device configurations not backed up
- Severity: as above
- Description: Switch and wireless access point configurations are not backed up or exportable. If a device fails and must be replaced, the configuration must be rebuilt from scratch — extending recovery time significantly and risking misconfiguration. In a managed network with VLANs, QoS, or complex routing, a lost configuration can mean days of recovery work.
- Confidence: high
- risk_category: continuity
- affected_entity: network infrastructure

**Actions:**
- A3-012a: Export and save current configurations for all managed switches and wireless access points
  - Time horizon: next_30_days
- A3-012b: Establish a scheduled configuration backup process — at minimum after any change, and on a regular automated cadence where the platform supports it
  - Time horizon: next_30_days

**Judgment call note:** No or unknown is urgent because configuration loss during hardware failure is a near-certain extended outage scenario. This is recovery capability, not documentation maturity.

---

### R3-013 — Wireless coverage inadequate or unknown
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 3.19, 3.4

**Conditions:**
- Wireless is in scope
- AND 3.19 (wireless coverage adequate) is `mixed`, `no`, or `unknown`

**Severity logic:**
- 3.19 is `no` or `mixed` → **concern**
- 3.19 is `unknown` AND 3.4 is `no` or `unknown` → **concern**
- 3.19 is `unknown` AND 3.4 is `yes fully` or `partial` → **watch**

**Finding — F3-013**
- Title: Wireless coverage inadequate or not confirmed in instructional areas
- Severity: as above
- Description: Wireless coverage is either known to be insufficient in some areas or has never been formally assessed. In an environment where instruction, attendance, and classroom tools depend on wireless, coverage gaps directly affect learning and operations.
- Confidence: high when `no` or `mixed`; moderate when unknown

**Actions:**
- A3-013a: Conduct or obtain a wireless coverage assessment — walk the environment with a device and note areas of poor signal
  - Time horizon: next_90_days
- A3-013b: Plan AP additions or relocations to address confirmed coverage gaps
  - Time horizon: next_12_months

**Scheduling note:** Significant AP installation or relocation → summer (Category 4).

---

### R3-014 — VLAN/segment purposes not documented
**Pattern:** Simple Threshold
**Trigger question:** 3.20

**Conditions:**
- VLANs or network segmentation are in use
- AND 3.20 is `partial`, `no`, or `unknown`

**Finding — F3-014**
- Title: Network segmentation not documented
- Severity: **watch**
- Description: VLANs or network segments are in use but their purposes are not documented. Without documentation, segmentation cannot be maintained correctly, new devices may be placed on the wrong segment, and security assumptions about traffic isolation cannot be verified.
- Confidence: high

**Actions:**
- A3-014a: Document each VLAN or segment — its name, purpose, what devices belong to it, and any firewall or ACL rules governing traffic between segments
  - Time horizon: next_90_days

---

### R3-015 — UPS protection incomplete or absent
**Pattern:** Graduated Severity + Escalation Modifier
**Trigger questions:** 3.21, 3.22

**Conditions:**
- On-site network or server equipment exists
- AND 3.21 is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 3.21 is `no` or `unknown` → **concern**
- 3.21 is `partial` → **watch**

**Finding — F3-015**
- Title: UPS protection for critical network and server equipment incomplete or absent
- Severity: as above
- Description: Critical network and server equipment is not fully protected by battery backup. A power event — surge, brownout, or brief outage — can corrupt configurations, damage equipment, or cause uncontrolled shutdowns that require manual recovery.
- Confidence: high

**Actions:**
- A3-015a: Identify which critical devices lack UPS protection and prioritize adding protection
  - Time horizon: next_90_days

**Escalation modifier:** If 3.22 (UPS runtime known) is `no` or `unknown`, reinforce concern floor — the school cannot assess whether existing protection is adequate.

---

### R3-016 — UPS runtime not known
**Pattern:** Simple Threshold
**Trigger question:** 3.22

**Conditions:**
- UPS devices exist (3.21 is `yes fully` or `partial`)
- AND 3.22 is `estimated only`, `no`, or `unknown`

**Finding — F3-016**
- Title: UPS runtime for critical equipment not documented
- Severity: **watch**
- Description: UPS devices are in place but their actual runtime under load is not documented or is only estimated. Without knowing runtime, the school cannot determine whether equipment will survive a typical power event long enough for a controlled shutdown or for power to be restored.
- Confidence: high

**Actions:**
- A3-016a: Test or obtain specifications for UPS runtime under typical load for each protected device group
  - Time horizon: next_90_days

---

### R3-017 — Known connectivity pain points
**Pattern:** Simple Threshold + Constraint Annotation
**Trigger question:** 3.26

**Conditions:**
- 3.26 (known connectivity pain points) is `yes`

**Finding — F3-017**
- Title: Known connectivity issues currently affecting school operations
- Severity: **concern**
- Description: The IT person has identified active connectivity problems affecting school operations. These are confirmed issues with current operational impact, not hypothetical risks.
- Confidence: high — notes field provides specifics

**Actions:**
- A3-017a: Document the specific connectivity pain points and assess root cause — coverage gap, hardware failure, configuration issue, or ISP problem
  - Time horizon: immediate
- A3-017b: Develop a remediation plan for each confirmed pain point
  - Time horizon: next_30_days

**Report behavior:** Notes from 3.26 are quoted directly in the finding description. Active operational problems appear in the Executive Summary.

**Judgment call note:** Always concern when it fires — the IT person is confirming a current operational problem, not a hypothetical. Unlike most Section 3 findings which are documentation or planning gaps, this one represents confirmed service impact.

---

## Section 3 Composite Rules

### R3-C01 — Complete network documentation absence
**Pattern:** Composite

**Conditions (all must be true):**
- 3.2 (network diagram) is `no` or `unknown`
- AND 3.3 (site/rack maps) is `no` or `unknown`
- AND 3.11 (core device inventory) is `no` or `unknown`

**Finding — F3-C01**
- Title: No network documentation exists at any level
- Severity: **urgent**
- Description: There is no network diagram, no site or rack maps, and no device inventory. The network environment is completely undocumented. Any troubleshooting, vendor engagement, or incident response must begin from scratch with no reference material. This represents a fundamental supportability failure.
- Confidence: high

**Actions:** Inherit A3-001a, A3-002a, A3-009a. Present as single consolidated urgent finding.

**Report note:** Always appears in Key Risks if it fires. Combine with R3-010 finding if admin access is also limited or unknown.

---

### R3-C02 — No admin access, no documentation, and no config backup
**Pattern:** Composite

**Conditions (all must be true):**
- 3.12 (admin access) is `no` or `unknown`
- AND 3.2 (network diagram) is `no` or `unknown`
- AND 3.18 (switch/wireless config backup) is `no` or `unknown`

**Finding — F3-C02**
- Title: No administrative access, no documentation, and no configuration backup
- Severity: **urgent**
- Description: The school has no administrative access to its own network, no network diagram, and no backup of device configurations. In the event of a hardware failure, the school cannot access, document, or restore its own network. Recovery would depend entirely on a third party with no reference material to work from.
- Confidence: high
- risk_category: continuity
- affected_entity: network infrastructure

**Actions:** Inherit A3-010a, A3-010b, A3-001a, A3-012a. Present as single consolidated urgent finding.

**Cross-section aggregation tag:** F3-C02 → Key Risk Group B

---

## Section 3 Domain Score Logic

| Condition | Domain Status |
|---|---|
| R3-C01 fires (no documentation at any level) | urgent |
| R3-C02 fires (no access, no docs, no config backup) | urgent |
| R3-004 fires (no firewall or unknown — 3.7) | urgent |
| R3-010 fires at urgent (no or unknown admin access) | urgent |
| R3-012 fires at urgent (no config backup) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 3.7, 3.12, 3.15, or 3.18 are among the unknowns |

**Unknown override:** Critical questions: 3.6, 3.12, 3.15, 3.18. Unknown on any raises floor to concern.

---

## Section 3 Judgment Calls

1. **R3-004 (no firewall or unknown) is urgent.** Unknown and no produce identical outcomes — the school cannot claim perimeter protection without confirming a firewall exists.
2. **R3-012 (no config backup) is urgent when no or unknown.** Configuration loss during hardware failure is a near-certain extended outage scenario.
3. **R3-010 (no admin access) is urgent when no or unknown.** The school cannot manage its own infrastructure. Functionally equivalent to having no control over a critical system.
4. **R3-011 (no internet failover) is concern, not urgent.** Internet resilience is a budget and planning question for most small schools.
5. **R3-017 (known pain points) is always concern.** Active service impact is always at minimum concern.
6. **Several Section 3 findings cluster naturally.** R3-001 + R3-002 + R3-008 are all network documentation gaps and should be presented together. R3-003 + R3-006 cluster as wireless visibility findings.

---

# Section 4: Identity, Accounts, and Access

## Section 4 Purpose
Assess how accounts are managed, secured, and transitioned. Identity and access issues become high-priority actions even when the rest of the environment is only partially documented — a compromised or unmanaged privileged account can affect every other system simultaneously. This section stays strongly deterministic.

## Section 4 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 4.4 (offboarding process for staff accounts)
- 4.6 (MFA on privileged accounts)
- 4.7 (reviewed list of global admins)

---

### R4-001 — No centralized identity or login management
**Pattern:** Graduated Severity
**Trigger question:** 4.2

**Severity by answer value:**
- 4.2 is `no` → **concern**
- 4.2 is `unknown` → **concern**
- 4.2 is `yes cloud-based`, `yes on-premises`, or `yes hybrid` → no finding; used as context for other rules

**Finding — F4-001**
- Title: No centralized login management system identified
- Severity: **concern**
- Description: There is no centralized directory or login management system in place. Without central account management, provisioning, deprovisioning, and access control all become manual and error-prone. Offboarding a staff member without a central directory means hunting through individual systems to revoke access — and gaps are common.
- Confidence: high

**Actions:**
- A4-001a: Evaluate whether a cloud-based identity platform (Google Workspace, Microsoft 365) or on-premises directory (Active Directory) is appropriate for the school's environment and size
  - Time horizon: next_12_months

**Judgment call note:** Concern rather than urgent because some very small schools operate adequately with per-system accounts, particularly if they are Google Workspace or M365 tenants with built-in directory features. Unknown is concern because the absence of knowledge about identity infrastructure is itself a risk.

---

### R4-002 — Staff onboarding process not documented
**Pattern:** Graduated Severity
**Trigger question:** 4.3

**Severity by answer value:**
- 4.3 is `no` or `unknown` → **concern**
- 4.3 is `informal` → **watch**

**Finding — F4-002**
- Title: Staff account onboarding process not documented
- Severity: as above
- Description (concern): There is no documented process for onboarding new staff accounts. Without a checklist or defined process, new staff may receive inconsistent access, miss required systems, or be given more access than their role requires.
- Description (watch): Staff onboarding happens informally. This works until a step is missed or the person who knows the process is unavailable. Formalizing the process is low-effort and high-value.
- Confidence: high

**Actions:**
- A4-002a: Document the staff account onboarding process as a checklist — accounts to create, systems to grant access to, groups to assign, and a sign-off step confirming completion
  - Time horizon: next_90_days

---

### R4-003 — Staff offboarding process not documented
**Pattern:** Graduated Severity
**Trigger question:** 4.4

**Severity by answer value:**
- 4.4 is `no` or `unknown` → **urgent**
- 4.4 is `informal` → **concern**

**Finding — F4-003**
- Title: Staff account offboarding process not documented or formalized
- Severity: as above
- Description (urgent): There is no documented process for offboarding departing staff accounts. Without a defined process, former staff may retain access to school systems, email, financial platforms, student data, and cloud storage indefinitely after leaving. This is one of the most common sources of unauthorized access in school environments.
- Description (concern): Staff offboarding happens informally. Informal processes are prone to missed steps — a forgotten account in one system can mean a former employee retains access longer than intended. Formalizing and documenting the process significantly reduces this risk.
- Confidence: high
- risk_category: security
- affected_entity: account lifecycle

**Actions:**
- A4-003a: Document the staff offboarding process as a checklist — every system, platform, and account that must be deactivated or transferred, with a sign-off step confirming completion
  - Time horizon: next_30_days
- A4-003b: Review whether any former staff still have active accounts in major systems and deactivate where found
  - Time horizon: immediate (if 4.4 is `no` or `unknown`)

**Judgment call note:** Offboarding is urgent when absent or unknown, and concern when informal, because the gap directly enables unauthorized access to live systems. This is a stronger position than onboarding (R4-002) because the risk of an unclosed account is ongoing and asymmetric — the former employee can act; the school cannot see it happening.

---

### R4-004 — Student account lifecycle not documented
**Pattern:** Graduated Severity
**Trigger question:** 4.5

**Conditions:**
- Student accounts are provisioned or managed by the school (per condition trigger on 4.5)
- AND 4.5 is `informal`, `no`, or `unknown`

**Severity by answer value:**
- 4.5 is `no` or `unknown` → **concern**
- 4.5 is `informal` → **watch**

**Finding — F4-004**
- Title: Student account lifecycle process not documented
- Severity: as above
- Description (concern): There is no documented process for provisioning or deprovisioning student accounts. Students who leave mid-year or graduate may retain access to school systems and cloud storage. New students may receive inconsistent access or miss required platforms.
- Description (watch): Student account lifecycle is handled informally. This is common in small schools but creates risk around departing students retaining access to school data and platforms.
- Confidence: high

**Actions:**
- A4-004a: Document the student account lifecycle — when accounts are created, what access is granted by grade or program, and when and how accounts are deactivated at departure or graduation
  - Time horizon: next_90_days

---

### R4-005 — MFA not fully enabled on privileged accounts
**Pattern:** Graduated Severity
**Trigger question:** 4.6

**Severity by answer value:**
- 4.6 is `no` → **urgent**
- 4.6 is `unknown` → **urgent**
- 4.6 is `some privileged` → **concern**

**Finding — F4-005**
- Title: Multi-factor authentication not fully enabled on privileged accounts
- Severity: as above
- Description (urgent): MFA is not enabled on privileged or administrative accounts. A compromised admin credential without MFA gives an attacker immediate, unrestricted access to the school's core systems — email, identity, file storage, and any connected platforms. This is the highest-impact, lowest-cost control gap in this section.
- Description (concern): MFA is enabled on some privileged accounts but not all. Any privileged account without MFA represents a full compromise risk for the systems it can access.
- Confidence: high
- risk_category: security
- affected_entity: privileged accounts

**Actions:**
- A4-005a: Enable MFA on all administrative and privileged accounts immediately — prioritize global admin, domain admin, and IT staff accounts
  - Time horizon: immediate
- A4-005b: Audit all privileged accounts and confirm MFA status for each
  - Time horizon: next_30_days

**Judgment call note:** No and unknown are both urgent. An unknown MFA state on privileged accounts cannot be assumed to be safe — the default assumption must be that MFA is absent until confirmed. This is one of the highest-priority security findings in the entire module.

**Cross-section aggregation tag:** F4-005 (when urgent) → new Key Risk Group E: "Privileged access control gaps" (to be formally defined — will draw from R4-005, R4-006, and Section 8 security findings)

---

### R4-006 — No reviewed list of global admins or privileged roles
**Pattern:** Graduated Severity
**Trigger question:** 4.7

**Conditions:**
- Cloud or centralized identity exists (4.2 is not `no`)
- AND 4.7 is `outdated`, `no`, or `unknown`

**Severity by answer value:**
- 4.7 is `no` or `unknown` → **urgent**
- 4.7 is `outdated` → **concern**

**Finding — F4-006**
- Title: Global admin and privileged role list not current or not reviewed
- Severity: as above
- Description (urgent): There is no known list of who holds global admin or equivalent privileged roles. Without knowing who has the highest-level access to the school's systems, it is impossible to manage that access, audit it, or revoke it when someone leaves.
- Description (concern): A list of privileged roles exists but is outdated. Outdated lists may include former staff, excess permissions granted for a project, or accounts that should have been revoked. An outdated list is better than none, but should not be relied upon.
- Confidence: high
- risk_category: security
- affected_entity: privileged role governance

**Actions:**
- A4-006a: Pull a current list of all global admins and privileged role holders from the identity platform and review for accuracy
  - Time horizon: immediate
- A4-006b: Remove or downgrade any accounts that no longer require privileged access
  - Time horizon: next_30_days
- A4-006c: Establish a quarterly privileged role review as a recurring task
  - Time horizon: next_90_days

**Cross-section aggregation tag:** F4-006 → Key Risk Group E (privileged access control)

---

### R4-007 — Shared accounts not minimized or justified
**Pattern:** Graduated Severity
**Trigger question:** 4.8

**Severity by answer value:**
- 4.8 is `no` → **concern**
- 4.8 is `partially` or `unknown` → **watch**

**Finding — F4-007**
- Title: Shared accounts not minimized or justified
- Severity: as above
- Description (concern): Shared accounts are in active use and have not been reviewed or justified. Shared accounts make it impossible to audit who took a given action, complicate offboarding, and create credential management risk — if one person leaves knowing the shared password, all systems using that account are potentially exposed.
- Description (watch): Some shared accounts exist. This is common in small schools for service or device accounts. The finding is that these accounts have not been formally reviewed or justified, which means the exposure is unclear.
- Confidence: high

**Actions:**
- A4-007a: Inventory all shared accounts currently in use and document their purpose, who has access, and whether the sharing is necessary
  - Time horizon: next_90_days
- A4-007b: Eliminate shared accounts where individual accounts are feasible; document and formally justify any that must remain
  - Time horizon: next_90_days

**Escalation modifier:** If 4.6 is also `no` or `unknown` (no MFA on privileged accounts), elevate report prominence — shared accounts without MFA represent compound credential exposure.

---

### R4-008 — Password reset and recovery procedures not documented
**Pattern:** Graduated Severity
**Trigger question:** 4.9

**Severity by answer value:**
- 4.9 is `no` or `unknown` → **concern**
- 4.9 is `partial` → **watch**

**Finding — F4-008**
- Title: Password reset and recovery procedures not documented
- Severity: as above
- Description (concern): There are no documented procedures for password resets or account recovery. When a staff member is locked out — especially during a high-pressure period like the start of school — the absence of a documented process means the IT person must improvise. This creates delays and inconsistent handling.
- Description (watch): Password reset procedures are partially documented. Gaps may exist for specific platforms or account types.
- Confidence: high

**Actions:**
- A4-008a: Document password reset and account recovery procedures for each major platform — who can reset, how they verify identity, and what the recovery path is if the primary method fails
  - Time horizon: next_90_days

---

## Section 4 Composite Rules

### R4-C01 — Privileged access completely uncontrolled
**Pattern:** Composite

**Conditions (all must be true):**
- 4.6 (MFA on privileged accounts) is `no` or `unknown`
- AND 4.7 (reviewed admin list) is `no` or `unknown`
- AND 4.8 (shared accounts minimized) is `no`

**Finding — F4-C01**
- Title: Privileged access is uncontrolled — no MFA, no admin inventory, and shared accounts unreviewed
- Severity: **urgent**
- Description: The school has no MFA on privileged accounts, no current knowledge of who holds admin access, and unreviewed shared accounts. These three gaps together mean that privileged access to core systems is effectively uncontrolled. Any account compromise — or any departing staff member who retains knowledge of shared credentials — represents a complete access risk.
- Confidence: high
- risk_category: security
- affected_entity: privileged account control

**Actions:** Inherit A4-005a, A4-005b, A4-006a, A4-006b, A4-007a. Present as single consolidated urgent finding.

**Report note:** F4-C01 must appear in Key Risks if it fires. Combine with F2-007 (shared credentials undocumented from Section 2) in the Key Risks section — they represent the same underlying control failure from different angles.

**Cross-section aggregation tag:** F4-C01 → Key Risk Group E (primary finding for privileged access)

---

### R4-C02 — Account lifecycle unmanaged at both ends
**Pattern:** Composite

**Conditions (all must be true):**
- 4.3 (onboarding) is `no` or `unknown`
- AND 4.4 (offboarding) is `no` or `unknown`

**Finding — F4-C02**
- Title: Staff account lifecycle unmanaged — no onboarding or offboarding process
- Severity: **urgent**
- Description: There is no documented process for either creating or removing staff accounts. New staff may receive inconsistent or excessive access. Departing staff may retain access indefinitely. Combined, these gaps mean the school has no reliable control over who has access to its systems at any given time.
- Confidence: high
- risk_category: security
- affected_entity: account lifecycle

**Actions:** Inherit A4-002a, A4-003a, A4-003b. Present as single consolidated urgent finding.

---

## Section 4 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F4-C01 fires (privileged access uncontrolled) | urgent |
| F4-C02 fires (account lifecycle unmanaged) | urgent |
| F4-003 fires at urgent (no offboarding process) | urgent |
| F4-005 fires at urgent (no MFA) | urgent |
| F4-006 fires at urgent (no admin list) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 4.4, 4.6, or 4.7 are among the unknowns |

**Unknown override:** Critical questions: 4.4, 4.6, 4.7. Unknown on any raises floor to concern.

---

## Section 4 Judgment Calls

1. **R4-003 (offboarding) is urgent when absent or unknown; R4-002 (onboarding) is only concern.** Offboarding gaps directly enable ongoing unauthorized access. Onboarding gaps cause inconsistency but not active risk to existing systems.

2. **R4-005 (no MFA) is urgent for both `no` and `unknown`.** Unknown MFA state on privileged accounts cannot be assumed safe. Default assumption is absent until confirmed.

3. **R4-006 (no admin list) is urgent when absent or unknown.** You cannot manage access you cannot see. Unknown is as dangerous as absent here.

4. **R4-007 (shared accounts) is concern for `no` but watch for `partially` or `unknown`.** Partial shared account use is common and manageable in small schools. Complete absence of review is a meaningful gap but not immediately operational.

5. **New Key Risk Group E identified.** Privileged access control findings (R4-005, R4-006, F4-C01) and shared credential findings (F2-007) point at the same root risk from different angles. Group E should be formally defined in RA-003 after this section is reviewed.

---

## Report Assembly Updates Required

Add to RA-003 (Key Risk Group definitions):

**Key Risk Group E: Privileged access control gaps** *(newly identified in Section 4)*
- Primary findings: F4-C01, F4-005 (when urgent), F4-006 (when urgent)
- Supporting findings: F2-007 (shared credentials from Section 2), Section 8 security findings (to be added)
- Aggregated severity: urgent if F4-C01, F4-005, or F4-006 fire at urgent; concern otherwise
- Report title: "Privileged access is not adequately controlled"

Add to RA-008 (Composite finding suppression):
- F4-C01 suppresses F4-005, F4-006, F4-007 (actions inherited)
- F4-C02 suppresses F4-002, F4-003 (actions inherited)

---

# Section 5: Endpoints, Printing, and Classroom Technology

## Section 5 Purpose
Understand the school's device inventory, management posture, age profile, printing footprint, and replacement planning. This section favors baseline control and lifecycle clarity over detailed device analytics. Several questions are contextual — they produce no finding themselves but modify the interpretation of others. The key outputs are inventory maturity, lifecycle risk, endpoint management findings, and refresh planning recommendations.

## Section 5 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 5.1 (current device inventory)
- 5.5 (MDM or endpoint management)
- 5.10 (devices beyond supported OS or manufacturer support)

---

### R5-001 — No current device inventory
**Pattern:** Graduated Severity + Escalation Modifier
**Trigger questions:** 5.1, 5.2

**Severity by answer value (5.1):**
- 5.1 is `no` or `unknown` → **concern**
- 5.1 is `partial` → **watch**

**Finding — F5-001**
- Title (concern): No current managed device inventory exists
- Title (watch): Device inventory exists but is incomplete
- Description (concern): There is no current inventory of managed devices. Without a baseline record of what devices exist, who has them, and what state they are in, lifecycle planning, support, and security are all impaired. You cannot protect, update, or replace what you cannot see.
- Description (watch): A device inventory exists but is incomplete. Missing devices or missing fields reduce its usefulness for planning and support.
- Confidence: high

**Actions:**
- A5-001a: Establish or complete a managed device inventory covering all school-owned staff and student devices — include at minimum: device type, model, serial number, assigned user or location, and purchase date or estimated age
  - Time horizon: next_90_days

**Escalation modifier:** If 5.1 is `no` or `unknown` AND 5.2 (inventory field completeness) is also `no` or `unknown`, elevate report prominence — the environment has no device visibility at any level.

**Scheduling note:** Physical device inventory requiring classroom walkthroughs → school calendar Category 2 (winter break) for non-disruptive counts; can also happen during school year if done room by room without disruption.

---

### R5-002 — Inventory fields incomplete
**Pattern:** Graduated Severity
**Trigger question:** 5.2

**Conditions:**
- 5.1 is `yes current` or `partial` (an inventory exists)
- AND 5.2 (inventory includes owner, model, serial, age, status) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 5.2 is `no` or `unknown` → **concern**
- 5.2 is `partial` → **watch**

**Finding — F5-002**
- Title: Device inventory exists but is missing key lifecycle fields
- Severity: as above
- Description: The device inventory does not include all fields needed for lifecycle planning and support. Missing purchase dates make age-based refresh planning impossible. Missing serial numbers impede warranty claims and vendor support. Missing assignment data makes offboarding and recovery harder.
- Confidence: high

**Actions:**
- A5-002a: Enrich the existing inventory to include all missing fields — prioritize purchase date or age, serial number, and assigned user or location
  - Time horizon: next_90_days

**Note:** This rule supplements R5-001 rather than replacing it. If both fire, present as a single inventory maturity finding with a combined action.

---

### R5-003 — Devices not managed through MDM or endpoint management
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 5.5, 5.3, 1.14

**Conditions:**
- Managed staff or student devices are in scope
- AND 5.5 (devices managed through MDM) is `yes some`, `no`, or `unknown`

**Severity by answer value:**
- 5.5 is `no` → **concern**
- 5.5 is `unknown` → **concern**
- 5.5 is `yes some` → **watch** — partial MDM coverage; unmanaged devices create gaps

**Escalation modifier:** If 5.5 is `no` or `unknown` AND 5.3 (1:1 environment) is `yes all relevant grades` or `partial`, escalate to **urgent** — a 1:1 program without MDM means student devices operating at scale with no central management, policy enforcement, or recovery capability.

**Finding — F5-003**
- Title: School-owned devices not fully managed through MDM or endpoint management
- Severity: as above (up to urgent in 1:1 environments)
- Description (concern/urgent): School-owned devices are not managed through a mobile device management or endpoint management platform. Without MDM, the school cannot enforce policies, push software, lock or wipe lost devices, verify OS versions, or efficiently provision and decommission devices. In a 1:1 student device environment, this gap affects every student device simultaneously.
- Description (watch): Some devices are managed through MDM but coverage is incomplete. Unmanaged devices cannot be remotely controlled, configured, or wiped, and may not receive policy enforcement.
- Confidence: high

**Actions:**
- A5-003a: Evaluate and select an MDM or endpoint management platform appropriate for the school's device mix and budget — many options exist at low or no cost for education environments
  - Time horizon: next_90_days
- A5-003b: Enroll all school-owned devices into the MDM platform, prioritizing devices used by students and staff with access to sensitive data
  - Time horizon: next_12_months

**Judgment call note:** The 1:1 escalation to urgent is deliberate. A school running a student device program at scale without MDM has accepted significant operational and security risk. The escalation should be explained in the finding, not just asserted.

---

### R5-004 — Staff device provisioning not standardized
**Pattern:** Graduated Severity + Composite with 5.7
**Trigger questions:** 5.6, 5.7

**Severity logic:**
- 5.6 is `no` or `unknown` AND 5.7 is `no` or `unknown` → **concern** (see also R5-C01)
- 5.6 is `no` or `unknown` AND 5.7 is `partially` or `yes` → **watch**
- 5.6 is `partial` → **watch**

**Finding — F5-004**
- Title: Staff device provisioning not standardized or documented
- Severity: as above
- Description (concern): There is no documented standard for provisioning staff devices, and devices cannot be set up quickly or consistently. Each new device setup depends on whoever is doing it at the time, producing inconsistent configurations, missing software, and variable security posture.
- Description (watch): Staff device provisioning is partially standardized or can be done somewhat consistently but without formal documentation. The process works when the right person is available but is not transferable.
- Confidence: high

**Actions:**
- A5-004a: Document a staff device provisioning standard — required software, security settings, naming convention, and enrollment steps
  - Time horizon: next_90_days
- A5-004b: Where MDM exists, configure a standard deployment profile so devices can be provisioned consistently without manual steps
  - Time horizon: next_90_days

---

### R5-005 — No defined device refresh cycle
**Pattern:** Graduated Severity
**Trigger question:** 5.9

**Severity by answer value:**
- 5.9 is `no` or `unknown` → **concern**
- 5.9 is `informal` → **watch**

**Finding — F5-005**
- Title: No defined device refresh cycle for major device categories
- Severity: as above
- Description (concern): There is no defined refresh cycle for any major device category. Without a planned replacement schedule, devices are replaced reactively when they fail rather than proactively before they become a support burden. This makes budget planning impossible and tends to create large, expensive replacement events rather than manageable annual spend.
- Description (watch): Device refresh happens informally — typically when devices fail or become noticeably slow. This is common in small schools but creates unpredictable budget demands and lifecycle drift.
- Confidence: high

**Actions:**
- A5-005a: Define a target refresh cycle for each major device category — for example: staff laptops every 4–5 years, student devices every 3–4 years, network infrastructure every 5–7 years
  - Time horizon: next_12_months
- A5-005b: Use the device inventory age data to estimate when the next major refresh wave will occur and begin budgeting accordingly
  - Time horizon: next_12_months

**Cross-section aggregation tag:** F5-005 → new Key Risk Group F: "Lifecycle and refresh planning gap" (to be formally defined — will draw from R5-005, R5-006, and Section 6 server lifecycle findings)

---

### R5-006 — Known unsupported devices in use
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 5.10, 5.3, 1.14

**Severity by answer value:**
- 5.10 is `many` → **urgent**
- 5.10 is `some` → **concern**
- 5.10 is `unknown` → **concern** — cannot assess risk without knowing device age profile

**Finding — F5-006**
- Title: Devices beyond supported OS versions or manufacturer support are in active use
- Severity: as above
- Description (urgent): Many devices in the school environment are running unsupported operating systems or have passed manufacturer support end-of-life. Unsupported devices receive no security patches, are incompatible with modern software, and represent an active security and operational liability. In a 1:1 or classroom environment, this affects instruction and student safety tools directly.
- Description (concern): Some devices are running unsupported OS versions or are past manufacturer support. These devices should be identified, quantified, and prioritized for replacement.
- Description (unknown): The age profile of the device fleet is unknown, making it impossible to assess how many devices may be approaching or past end of support. An inventory with age data is the prerequisite for addressing this.
- Confidence: high when `many` or `some`; moderate when `unknown`
- risk_category: lifecycle
- affected_entity: managed device fleet

**Actions:**
- A5-006a: Identify all devices running unsupported OS versions or past manufacturer support end-of-life
  - Time horizon: next_30_days
- A5-006b: Develop a prioritized replacement plan — devices used for student instruction or staff access to sensitive systems should be replaced first
  - Time horizon: next_90_days (plan); next_12_months (execution)

**Escalation modifier:** If 5.10 is `many` AND 5.3 is `yes all relevant grades` (full 1:1 program), elevate finding prominence in Executive Summary — unsupported devices at 1:1 scale is a student-facing operational and safety issue.

**Cross-section aggregation tag:** F5-006 → Key Risk Group F (lifecycle and refresh planning)

---

### R5-007 — Device warranties or support coverage not tracked
**Pattern:** Graduated Severity
**Trigger question:** 5.11

**Conditions:**
- School-owned devices are in scope
- AND 5.11 is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 5.11 is `no` or `unknown` → **watch**
- 5.11 is `partial` → **watch**

**Finding — F5-007**
- Title: Device warranties and support coverage not tracked
- Severity: **watch**
- Description: Device warranties and support coverage are not being tracked. Without this, the school may be paying for support it is not using, missing warranty claims for failed devices, or discovering post-failure that coverage has lapsed.
- Confidence: high

**Actions:**
- A5-007a: Add warranty expiry and support coverage status to the device inventory for all devices where this information is available
  - Time horizon: next_90_days

---

### R5-008 — No spare or loaner device process
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 5.12, 5.3

**Conditions:**
- Student or staff devices are operationally important
- AND 5.12 is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 5.12 is `no` or `unknown` AND 5.3 is `yes all relevant grades` → **concern** — 1:1 program with no spare coverage means a student is without a device until repair is complete
- 5.12 is `no` or `unknown` AND 5.3 is `partial` or `no` → **watch**
- 5.12 is `partial` → **watch**

**Finding — F5-008**
- Title: No spare or loaner device process defined
- Severity: as above
- Description (concern): The school runs a 1:1 or near-1:1 device program but has no defined process for providing spare or loaner devices when a device fails or is being repaired. Students without devices in a 1:1 environment are effectively excluded from instruction until the device is returned.
- Description (watch): There is no defined process for spare or loaner devices. For environments with partial or no 1:1 programs, this is operationally inconvenient rather than critical — but a process and a small spare pool are low-cost improvements worth planning.
- Confidence: high

**Actions:**
- A5-008a: Define a spare and loaner device process — how many spare devices are maintained, who manages them, and how they are issued and returned
  - Time horizon: next_90_days
- A5-008b: Establish a minimum spare device pool appropriate for the school's device program scale
  - Time horizon: next_12_months

---

### R5-009 — No decommissioning or disposal process
**Pattern:** Graduated Severity
**Trigger question:** 5.13

**Conditions:**
- School-owned devices are in scope
- AND 5.13 is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 5.13 is `no` or `unknown` → **concern**
- 5.13 is `partial` → **watch**

**Finding — F5-009**
- Title: No documented device decommissioning or disposal process
- Severity: as above
- Description (concern): There is no documented process for decommissioning or disposing of retired devices. Without a defined process, retired devices may retain school data, credentials, or software licenses. Devices disposed of without data wiping can expose student and staff information. Devices that are not formally decommissioned may remain in the inventory and distort lifecycle planning.
- Description (watch): Decommissioning and disposal happens but is not formally documented. The process depends on whoever handles it at the time, which may not include data wiping or license recovery consistently.
- Confidence: high

**Actions:**
- A5-009a: Document a device decommissioning checklist — data wipe method, account deactivation, license recovery, and disposal or reuse path
  - Time horizon: next_90_days

---

### R5-010 — Peripheral and classroom tech not tracked
**Pattern:** Simple Threshold
**Trigger question:** 5.17

**Conditions:**
- Printers, AV, or specialty classroom devices are in scope
- AND 5.17 is `partial`, `no`, or `unknown`

**Finding — F5-010**
- Title: Printers, specialty devices, and classroom technology not consistently tracked
- Severity: **watch**
- Description: Printers, AV equipment, and classroom technology are not tracked consistently. Without a peripheral inventory, support is reactive, lifecycle planning is absent, and the total cost of the environment is difficult to assess.
- Confidence: moderate — optional question

**Actions:**
- A5-010a: Extend the device inventory or create a separate peripheral register covering printers, AV equipment, interactive displays, and other classroom technology — include model, location, and approximate age
  - Time horizon: next_12_months

---

## Section 5 Composite Rules

### R5-C01 — No device visibility and no management control
**Pattern:** Composite

**Conditions (all must be true):**
- 5.1 (device inventory) is `no` or `unknown`
- AND 5.5 (MDM) is `no` or `unknown`
- AND 5.10 (unsupported devices) is `unknown`

**Finding — F5-C01**
- Title: No device inventory, no endpoint management, and no visibility into device age or support status
- Severity: **urgent**
- Description: The school has no device inventory, no endpoint management platform, and no knowledge of the age or support status of its device fleet. The environment cannot be secured, managed, or planned for — and there is no way to know how significant the risk is without first establishing basic visibility. This is a complete endpoint visibility failure.
- Confidence: high

**Actions:** Inherit A5-001a, A5-003a, A5-006a. Present as single consolidated urgent finding.

---

### R5-C02 — Unsupported devices at scale with no refresh plan
**Pattern:** Composite + Cross-Section Reference

**Conditions (all must be true):**
- 5.10 (unsupported devices) is `many`
- AND 5.9 (refresh cycle defined) is `no` or `unknown`
- AND 5.3 (1:1 environment) is `yes all relevant grades` or `partial`

**Finding — F5-C02**
- Title: Many unsupported devices in a 1:1 program with no refresh plan
- Severity: **urgent**
- Description: The school operates a student device program at scale with many devices beyond supported OS versions or manufacturer support, and has no defined refresh cycle to address this. Students are using devices that receive no security patches and may be incompatible with current instructional platforms. Without a refresh plan, this situation will worsen each year.
- Confidence: high
- risk_category: lifecycle
- affected_entity: student device fleet

**Actions:** Inherit A5-006a, A5-006b, A5-005a, A5-005b. Present as single consolidated urgent finding.

**Report note:** F5-C02 must appear in Key Risks and Executive Summary if it fires. It is a direct student-facing operational risk.

**Cross-section aggregation tag:** F5-C02 → Key Risk Group F (lifecycle and refresh planning — primary finding)

---

## Section 5 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F5-C01 fires (no visibility or management) | urgent |
| F5-C02 fires (unsupported devices at 1:1 scale, no refresh plan) | urgent |
| F5-003 fires at urgent (no MDM in 1:1 environment) | urgent |
| F5-006 fires at urgent (many unsupported devices) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 5.1, 5.5, or 5.10 are among the unknowns |

**Unknown override:** Critical questions: 5.1, 5.5, 5.10. Unknown on any raises floor to concern.

---

## Section 5 Judgment Calls

1. **R5-003 escalates to urgent in a 1:1 environment without MDM.** A student device program at scale without central management is a qualitatively different risk from a small staff fleet without MDM. The escalation is environment-dependent and explained in the finding.

2. **R5-006 (unsupported devices) is urgent when `many`, concern when `some`, concern when `unknown`.** Unknown is treated as concern rather than watch because device age is a factual question — if the IT person does not know the answer, the inventory gap is the root cause and should be surfaced as concern.

3. **R5-009 (no decommissioning process) is concern, not watch, when fully absent.** Data remaining on retired devices is an active privacy risk, not a planning gap. Partial or undocumented processes are watch because some handling is better than none.

4. **Questions 5.3, 5.4, 5.14, 5.15, 5.16, 5.18, 5.19 generate no findings.** They are contextual inputs that modify other rules or feed the environment overview and appendix. This is intentional — not every question needs a finding.

5. **New Key Risk Group F identified.** Lifecycle and refresh planning findings (R5-005, R5-006, F5-C02) and Section 6 server lifecycle findings will aggregate here. Add to RA-003 after Section 6 is reviewed.

---

## Report Assembly Updates Required

Add to RA-003 (Key Risk Group definitions):

**Key Risk Group F: Lifecycle and refresh planning gap** *(newly identified in Section 5)*
- Primary findings: F5-C02, F5-006 (when urgent)
- Supporting findings: F5-005, Section 6 server lifecycle findings (to be added)
- Aggregated severity: urgent if F5-C02 fires; concern otherwise
- Report title: "Device lifecycle and refresh planning gap"

Add to RA-001 (Executive Summary mandatory findings):
- F5-C02 — Many unsupported devices in 1:1 program with no refresh plan

Add to RA-008 (Composite finding suppression):
- F5-C01 suppresses F5-001, F5-003 (actions inherited)
- F5-C02 suppresses F5-006, F5-005 (actions inherited)

Add to RA-005 (Finding clusters):
| Inventory and lifecycle gap | F5-001, F5-002, F5-006 | Section 5 |
| Provisioning and management gap | F5-003, F5-004 | Section 5 |

---

# Section 6: Core Systems, Servers, Vendors, and Contracts

## Section 6 Purpose
Capture the systems the school depends on, the server environment if present, and whether vendor relationships and renewal risks are visible. This section splits naturally into two clusters: vendor and systems visibility (6.1–6.12) and server infrastructure (6.13–6.19). The goal is to identify operational dependencies without building a full CMDB. Key outputs are vendor visibility, renewal risk, concentration risk indicators, and server lifecycle findings.

## Section 6 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 6.3 (core systems list exists)
- 6.8 (contract renewal dates tracked)
- 6.16 (server admin access documented — if servers exist)

---

### R6-001 — No core systems list exists
**Pattern:** Graduated Severity + Escalation Modifier
**Trigger questions:** 6.3, 6.4

**Severity by answer value (6.3):**
- 6.3 is `no` or `unknown` → **concern**
- 6.3 is `partial` → **watch**

**Finding — F6-001**
- Title (concern): No list of core systems used by the school
- Title (watch): Core systems list exists but is incomplete
- Description (concern): There is no list of the core systems the school depends on. Without knowing what systems exist, it is impossible to plan for renewals, document ownership, track vendor relationships, or respond to an outage affecting a critical platform. Discovery of critical systems should not happen during an incident.
- Description (watch): A partial list of core systems exists. The missing entries represent undocumented dependencies — systems that the school relies on but has no formal record of.
- Confidence: high
- risk_category: visibility
- affected_entity: core systems

**Actions:**
- A6-001a: Create or complete a core systems register listing every platform the school depends on — include at minimum: system name, purpose, primary users, vendor, and estimated renewal date
  - Time horizon: next_90_days

**Escalation modifier:** If 6.3 is `no` or `unknown` AND 6.4 (list field completeness) is also `no` or `unknown`, elevate report prominence — the school has no systems visibility at any level.

**Cross-section aggregation tag:** F6-001 → Key Risk Group A (No accountable IT ownership — a school that cannot list its own systems cannot manage them)

---

### R6-002 — Core systems list missing key fields
**Pattern:** Graduated Severity
**Trigger question:** 6.4

**Conditions:**
- 6.3 is `yes current` or `partial` (a list exists)
- AND 6.4 (list includes purpose, owner, vendor, renewal date, admin access) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.4 is `no` or `unknown` → **concern**
- 6.4 is `partial` → **watch**

**Finding — F6-002**
- Title: Core systems list exists but is missing key operational fields
- Severity: as above
- Description: The core systems list does not include all fields needed for operational management. Missing renewal dates create surprise expiry risk. Missing admin access methods create recovery gaps. Missing ownership means no one is accountable when something goes wrong.
- Confidence: high

**Actions:**
- A6-002a: Enrich the core systems register to include for each system: purpose, named owner, vendor contact, renewal date, and admin access method or location of credentials
  - Time horizon: next_90_days

**Note:** Supplements R6-001. If both fire, present as a single systems visibility finding with combined actions.

---

### R6-003 — Subscription governance not tracked
**Pattern:** Graduated Severity
**Trigger question:** 6.6

**Conditions:**
- Major software subscriptions exist
- AND 6.6 (cost, purpose, renewal, user groups tracked) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.6 is `no` or `unknown` → **concern**
- 6.6 is `partial` → **watch**

**Finding — F6-003**
- Title: Software subscription governance not tracked
- Severity: as above
- Description (concern): The school has software subscriptions but is not tracking cost, purpose, renewal timing, or primary user groups. Untracked subscriptions auto-renew without review, accumulate over time, and may include tools that are no longer used or no longer appropriate for student data handling.
- Description (watch): Some subscription information is tracked but coverage is incomplete. The gaps represent unmonitored spend and unreviewed tools.
- Confidence: moderate — optional question

**Actions:**
- A6-003a: Create a subscription register covering all major software subscriptions — include cost, purpose, renewal date, primary user group, and whether student data is involved
  - Time horizon: next_90_days

**Cross-section aggregation tag:** F6-003 → Key Risk Group C (Vendor visibility and continuity)

---

### R6-004 — FERPA/COPPA review status not known for student-data systems
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 6.7, 2.12

**Conditions:**
- Student-data systems or educational apps are in use
- AND 6.7 (FERPA/COPPA review status known) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.7 is `no` or `unknown` AND 2.12 (software approval process) is unclear → **concern**
- 6.7 is `partial` AND 2.12 is unclear → **concern**
- 6.7 is `no` or `unknown` AND 2.12 is documented → **watch**
- 6.7 is `partial` AND 2.12 is documented → **watch**

**Finding — F6-004**
- Title: FERPA/COPPA compliance review status not known for student-data systems
- Severity: as above
- Description: Student-data systems and educational apps are in use but the school does not have documented evidence of FERPA or COPPA review for most of them. Schools are responsible for ensuring that third-party tools handling student data meet regulatory requirements. Without a review process or documented status, the school cannot demonstrate compliance and may be using tools that expose student data inappropriately.
- Confidence: moderate

**Actions:**
- A6-004a: Identify all systems and apps that handle student data and document whether a FERPA/COPPA review has been performed for each
  - Time horizon: next_90_days
- A6-004b: For systems without documented review, complete a review or consult with legal counsel to determine compliance posture
  - Time horizon: next_12_months

**Cross-section aggregation tag:** F6-004 → Key Risk Group D (Student data governance — primary finding)

---

### R6-005 — Contract renewal dates not tracked
**Pattern:** Graduated Severity
**Trigger question:** 6.8

**Severity by answer value:**
- 6.8 is `no` or `unknown` → **concern**
- 6.8 is `partial` → **watch**

**Finding — F6-005**
- Title: Contract renewal dates not tracked
- Severity: as above
- Description (concern): Contract and subscription renewal dates are not tracked in a calendar or system. Untracked renewals lead to surprise auto-renewals, missed cancellation windows, unexpected budget impact, and service gaps when contracts lapse without notice. In a small school where IT manages dozens of vendor relationships, this creates recurring unforced errors.
- Description (watch): Some renewal dates are tracked but coverage is incomplete. The untracked renewals represent blind spots in the school's vendor calendar.
- Confidence: high

**Actions:**
- A6-005a: Add all known contract and subscription renewal dates to a central calendar — set reminders at least 60 days before each renewal to allow time for review and renegotiation
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F6-005 → Key Risk Group C (Vendor visibility and continuity)

---

### R6-006 — Vendor support escalation paths not documented
**Pattern:** Graduated Severity
**Trigger question:** 6.9

**Conditions:**
- Third-party vendors support critical systems
- AND 6.9 (vendor escalation paths documented) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.9 is `no` or `unknown` → **concern**
- 6.9 is `partial` → **watch**

**Finding — F6-006**
- Title: Vendor support escalation paths not documented
- Severity: as above
- Description (concern): There is no documented escalation path for vendors who support critical systems. When a critical system fails, the time spent finding a support contact or contract reference is time the school cannot afford. Undocumented escalation paths also mean that only certain people know how to reach certain vendors — a key-person dependency in disguise.
- Description (watch): Some vendor escalation paths are documented but coverage is incomplete. The gaps affect the school's ability to respond quickly when those systems have problems.
- Confidence: high

**Actions:**
- A6-006a: Document the support escalation path for every vendor supporting a critical system — include support contact, contract or account number, SLA, and emergency escalation method
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F6-006 → Key Risk Group C (Vendor visibility and continuity)

---

### R6-007 — Single-vendor or single-person dependencies identified
**Pattern:** Simple Threshold + Constraint Annotation
**Trigger question:** 6.10

**Conditions:**
- 6.10 (single-vendor or single-person dependencies) is `yes`

**Finding — F6-007**
- Title: Single-vendor or single-person dependencies create operational risk
- Severity: **concern**
- Description: The school has identified single-vendor or single-person dependencies that create operational risk. If the vendor fails, is acquired, or becomes unresponsive — or if the key person leaves — the school loses the ability to manage or support the affected system. Dependencies of this type are often invisible until they become a crisis.
- Confidence: high — notes field identifies the specific dependencies
- risk_category: continuity
- affected_entity: as specified in notes

**Actions:**
- A6-007a: Document each identified dependency — the system affected, the vendor or person involved, and what would happen if they became unavailable
  - Time horizon: next_30_days
- A6-007b: For each dependency, develop a mitigation plan — alternate vendor, cross-training, documentation, or escrow of credentials and configurations
  - Time horizon: next_90_days

**Report behavior:** Notes from 6.10 must be quoted in the finding description. Each specific dependency should be listed by name in the report rather than referred to generically.

**Cross-section aggregation tag:** F6-007 → Key Risk Group B (Single-person dependency) when the dependency involves a person; Key Risk Group C (Vendor visibility) when the dependency involves a vendor.

---

### R6-008 — Unused paid tools or services identified
**Pattern:** Simple Threshold
**Trigger question:** 6.11

**Conditions:**
- 6.11 (tools being paid for but not actively used) is `yes`

**Finding — F6-008**
- Title: School is paying for tools or services that are not actively used
- Severity: **watch**
- Description: The school has identified tools or services it is paying for but not using. This represents recoverable budget that could be redirected to active needs. Unused tools may also represent data or access risks if accounts remain active without active oversight.
- Confidence: high — notes field identifies specific tools
- risk_category: planning
- affected_entity: as specified in notes

**Actions:**
- A6-008a: Review and cancel or consolidate identified unused subscriptions before the next renewal date
  - Time horizon: next_30_days

**Judgment call note:** Watch and never urgent. This is an optimization opportunity, not a risk finding. It should not be presented as a negative finding — frame it as recoverable budget and a clean-up opportunity.

---

### R6-009 — Server inventory incomplete or absent
**Pattern:** Graduated Severity + Escalation Modifier
**Trigger questions:** 6.14, 6.15

**Conditions:**
- Server infrastructure exists (6.13 > 0)
- AND 6.14 (server inventory with model, serial, role, location, OS, support status) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.14 is `no` or `unknown` → **urgent**
- 6.14 is `partial` → **concern**

**Finding — F6-009**
- Title: Server inventory incomplete or absent
- Severity: as above
- Description (urgent): Servers are in use but there is no inventory documenting their model, serial number, role, location, operating system, or support status. Without this, lifecycle planning, vendor support, incident response, and replacement are all severely impaired. An undocumented server environment is effectively unsupportable by anyone other than the person who built it.
- Description (concern): A partial server inventory exists but is missing key fields. The gaps reduce the school's ability to plan for lifecycle events and respond to failures.
- Confidence: high

**Actions:**
- A6-009a: Create or complete a server inventory including for each server: model, serial number, role and purpose, physical or virtual location, operating system and version, support/warranty status, and admin access method
  - Time horizon: next_30_days

**Escalation modifier:** If 6.14 is `no` or `unknown` AND 6.15 (server purpose documented) is also `no` or `unknown`, severity remains **urgent** and the finding description should emphasize that the environment cannot be understood or supported by anyone other than the person currently managing it.

**Cross-section aggregation tag:** F6-009 (when urgent) → Key Risk Group B (single-person dependency — an undocumented server environment concentrates knowledge in whoever set it up)

---

### R6-010 — Server admin access not documented or available
**Pattern:** Graduated Severity
**Trigger question:** 6.16

**Conditions:**
- Server infrastructure exists
- AND 6.16 (server admin access methods documented and available) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.16 is `no` or `unknown` → **urgent**
- 6.16 is `partial` → **concern**

**Finding — F6-010**
- Title: Server administrative access not documented or not available to the school
- Severity: as above
- Description (urgent): Administrative access methods for servers are not documented or are not available to the school. If the primary IT person is unavailable, no one can access the servers to diagnose problems, perform maintenance, or recover from a failure. This is a single-person dependency at the infrastructure level.
- Description (concern): Server admin access is partially documented. Some servers can be accessed without the primary IT person, but gaps remain that create dependency risk.
- Confidence: high
- risk_category: continuity
- affected_entity: server infrastructure

**Actions:**
- A6-010a: Document the admin access method for every server — local console access, remote access tool, credentials location, and recovery path if primary access fails
  - Time horizon: immediate
- A6-010b: Ensure at least one other authorized person can access each server without involving the primary IT person
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F6-010 → Key Risk Group B (single-person dependency creates recovery and continuity risk)

---

### R6-011 — No defined server patching cycle
**Pattern:** Graduated Severity
**Trigger question:** 6.17

**Conditions:**
- Server infrastructure exists
- AND 6.17 (defined server patching or update cycle) is `informal`, `no`, or `unknown`

**Severity by answer value:**
- 6.17 is `no` or `unknown` → **concern**
- 6.17 is `informal` → **watch**

**Finding — F6-011**
- Title: No defined server patching or update cycle
- Severity: as above
- Description (concern): There is no defined cycle for patching or updating servers. Unpatched servers accumulate vulnerabilities over time and are among the most common entry points for ransomware and unauthorized access in school environments.
- Description (watch): Server patching happens informally. This typically means it occurs when the IT person remembers or notices an issue, rather than on a defined cadence. Informal patching is better than none, but creates gaps between updates that grow unpredictably.
- Confidence: high

**Actions:**
- A6-011a: Define and document a server patching cycle — at minimum monthly for security patches, quarterly for feature updates, with a test-before-production approach where feasible
  - Time horizon: next_30_days

**Scheduling note:** Server patching requiring restarts or extended maintenance windows → school calendar Category 3 (spring break) or Category 4 (summer) depending on server criticality and downtime tolerance.

---

### R6-012 — Server warranties or support not tracked
**Pattern:** Graduated Severity
**Trigger question:** 6.18

**Conditions:**
- Physical or vendor-supported server infrastructure exists
- AND 6.18 (server warranties or support coverage known) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 6.18 is `no` or `unknown` → **concern**
- 6.18 is `partial` → **watch**

**Finding — F6-012**
- Title: Server warranty and support coverage not tracked
- Severity: as above
- Description (concern): Server warranty and support coverage is not tracked. A server that fails outside of warranty with no support contract may require full replacement at unplanned cost. Without knowing coverage status, the school cannot plan for this risk or make informed decisions about extended support or hardware refresh timing.
- Description (watch): Some server warranty and support information is tracked but coverage is incomplete.
- Confidence: high

**Actions:**
- A6-012a: Document the warranty and support status for every server — expiry date, support tier, vendor contact, and whether extended support is available and worth purchasing
  - Time horizon: next_30_days

**Cross-section aggregation tag:** F6-012 → Key Risk Group F (Lifecycle and refresh planning gap)

---

### R6-013 — No server hardware refresh or lifecycle plan
**Pattern:** Graduated Severity
**Trigger question:** 6.19

**Conditions:**
- Server infrastructure exists
- AND 6.19 (hardware refresh or lifecycle plan for servers) is `informal`, `no`, or `unknown`

**Severity by answer value:**
- 6.19 is `no` or `unknown` → **concern**
- 6.19 is `informal` → **watch**

**Finding — F6-013**
- Title: No hardware refresh or lifecycle plan for servers
- Severity: as above
- Description (concern): There is no defined lifecycle or refresh plan for server hardware. Servers that age beyond manufacturer support receive no security patches and increasingly fail to run current software. Without a plan, server replacement happens reactively after failure — at the worst possible time, with no budget prepared.
- Description (watch): Server refresh planning happens informally. This typically means replacement is considered when a server fails or becomes obviously inadequate, rather than planned in advance.
- Confidence: high

**Actions:**
- A6-013a: Define a server lifecycle target — typically 5–7 years for physical servers — and map current servers against that target to identify which are approaching end of useful life
  - Time horizon: next_90_days
- A6-013b: Incorporate server refresh into the IT budget planning cycle
  - Time horizon: next_12_months

**Cross-section aggregation tag:** F6-013 → Key Risk Group F (Lifecycle and refresh planning gap)

---

## Section 6 Composite Rules

### R6-C01 — No vendor or systems visibility at any level
**Pattern:** Composite

**Conditions (all must be true):**
- 6.3 (core systems list) is `no` or `unknown`
- AND 6.8 (renewal dates tracked) is `no` or `unknown`
- AND 6.9 (vendor escalation paths) is `no` or `unknown`

**Finding — F6-C01**
- Title: No vendor or systems visibility — systems, renewals, and escalation paths all undocumented
- Severity: **urgent**
- Description: The school has no list of its core systems, no tracking of contract renewal dates, and no documented vendor escalation paths. The school is operationally dependent on systems and vendors it cannot fully identify, cannot plan renewals for, and cannot escalate to when something fails. Discovery of critical dependencies should not happen during an incident.
- Confidence: high
- risk_category: visibility
- affected_entity: all systems and vendors

**Actions:** Inherit A6-001a, A6-005a, A6-006a. Present as single consolidated urgent finding.

**Cross-section aggregation tag:** F6-C01 → Key Risk Group A (No accountable IT ownership) and Key Risk Group C (Vendor visibility and continuity)

---

### R6-C02 — Server environment completely undocumented
**Pattern:** Composite

**Conditions (all must be true):**
- Server infrastructure exists (6.13 > 0)
- AND 6.14 (server inventory) is `no` or `unknown`
- AND 6.15 (server purpose documented) is `no` or `unknown`
- AND 6.16 (server admin access documented) is `no` or `unknown`

**Finding — F6-C02**
- Title: Server environment completely undocumented — no inventory, no purpose records, no admin access documentation
- Severity: **urgent**
- Description: The school has servers in use but no inventory, no documentation of what each server does, and no documented admin access methods. This environment cannot be supported by anyone other than the person who built it. In a failure scenario, recovery would require rebuilding from scratch with no reference material. This is the server equivalent of a complete documentation failure.
- Confidence: high
- risk_category: continuity
- affected_entity: server infrastructure

**Actions:** Inherit A6-009a, A6-010a, A6-010b. Present as single consolidated urgent finding.

**Cross-section aggregation tag:** F6-C02 → Key Risk Group B (single-person dependency) and Key Risk Group F (lifecycle and refresh planning)

---

## Section 6 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F6-C01 fires (no vendor or systems visibility) | urgent |
| F6-C02 fires (server environment completely undocumented) | urgent |
| F6-009 fires at urgent (no server inventory) | urgent |
| F6-010 fires at urgent (no server admin access) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 6.3, 6.8, or 6.16 are among the unknowns |

**Unknown override:** Critical questions: 6.3, 6.8, 6.16 (if servers exist). Unknown on any raises floor to concern.

---

## Section 6 Judgment Calls

1. **F6-009 (server inventory absent) is urgent when fully absent.** An undocumented server environment is effectively unsupportable by anyone other than the person who built it. This is the same logic as R3-010 (no admin access to network) — it represents a fundamental loss of institutional control over critical infrastructure.

2. **F6-010 (server admin access undocumented) is urgent when absent or unknown.** Identical reasoning to R7-012 and R3-010 — access you cannot document is access only one person has, which is a continuity crisis waiting to happen.

3. **F6-007 (single-vendor/person dependency) is concern and uses constraint annotation.** The notes from 6.10 are quoted directly in the report. The finding frames dependencies as manageable risks rather than failures — the school identified them, which is the first step to mitigating them.

4. **F6-008 (unused paid tools) is watch and never urgent.** This is an optimization opportunity, not a risk. The report should frame it as recoverable budget, not a failure.

5. **Questions 6.1, 6.2, 6.5, 6.11, 6.12, 6.13 generate no standalone findings.** They are contextual inputs that feed the environment overview, appendix, and other rules. This is intentional.

6. **Section 6 is the completion point for Key Risk Groups C and D.** With F6-004 (FERPA/COPPA), F6-005 and F6-006 (renewal and escalation), and F6-007 (dependencies) now defined, Groups C and D can be fully specified. See RA updates below.

---

## Report Assembly Updates Required

Update RA-003 — finalize Key Risk Groups C and D:

**Key Risk Group C: Vendor visibility and continuity** *(now complete)*
- Primary findings: F2-004, F6-005, F6-006, F6-C01
- Supporting findings: F6-003, F6-007 (vendor dependencies)
- Aggregated severity: urgent if F6-C01 fires; concern otherwise
- Report title: "Vendor relationships and renewal visibility"

**Key Risk Group D: Student data governance** *(now complete)*
- Primary findings: F2-011, F6-004
- Supporting findings: F6-003 (if student data subscriptions are untracked)
- Aggregated severity: concern (no urgent path in this group currently)
- Report title: "Student data governance and software approval"

Update RA-001 — add mandatory Executive Summary findings:
- F6-C01 — No vendor or systems visibility at any level
- F6-C02 — Server environment completely undocumented

Update RA-003 — add to Key Risk Group F supporting findings:
- F6-012, F6-013 now confirmed as Group F supporting findings

Update RA-005 — add finding clusters:
| Vendor and systems visibility gap | F6-001, F6-002, F6-005, F6-006 | Section 6 |
| Server documentation and access gap | F6-009, F6-010, F6-011 | Section 6 |

Update RA-006 — add notes passthrough:
| F6-007 | 6.10 (single-vendor/person dependencies) | Each specific dependency quoted by name in finding |

Update RA-008 — add composite suppression:
- F6-C01 suppresses F6-001, F6-005, F6-006 (actions inherited)
- F6-C02 suppresses F6-009, F6-010 (actions inherited)

---

# Section 8: Security Operations, Filtering, and Safeguards

## Section 8 Purpose
Capture practical security maturity without requiring a full formal audit. This section identifies obvious control gaps and visibility gaps without pretending to be a comprehensive security assessment. The emphasis is on baseline hygiene, operational response capability, and student-facing protections. Key outputs are baseline security posture, urgent control gaps, and practical risk reduction actions.

## Section 8 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 8.1 (endpoint protection deployed)
- 8.5 (web filter in place)
- 8.8 (incident response process documented)

---

### R8-001 — Endpoint protection not fully deployed
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 8.1, 1.14, 5.3

**Conditions:**
- Endpoints are in scope
- AND 8.1 (endpoint protection deployed on supported devices) is `yes some`, `no`, or `unknown`

**Severity by answer value:**
- 8.2 is `no` → **urgent**
- 8.2 is `unknown` → **urgent**
- 8.2 is `yes some` → **concern**

**Finding — F8-001**
- Title (urgent): Endpoint protection not deployed across managed devices
- Title (concern): Endpoint protection deployed on some but not all managed devices
- Description (urgent): Endpoint protection or antivirus is not deployed on managed devices, or deployment status is unknown. Unprotected endpoints are a primary attack surface for malware, ransomware, and credential theft. In a school environment, student and staff devices accessing the internet without endpoint protection represent both a security risk and a safeguarding concern.
- Description (concern): Endpoint protection is deployed on some managed devices but not all. Unprotected devices remain exposed regardless of how well other devices are protected — one compromised endpoint can affect the entire network.
- Confidence: high
- risk_category: security
- affected_entity: managed device fleet

**Actions:**
- A8-001a: Identify which devices do not have endpoint protection deployed and deploy coverage immediately
  - Time horizon: immediate
- A8-001b: Verify that endpoint protection is active and reporting on all managed devices, and establish a process to confirm new devices are enrolled before use
  - Time horizon: next_30_days

**Escalation modifier:** If 8.1 is `no` or `unknown` AND 5.3 is `yes all relevant grades` (1:1 student program), elevate finding prominence — unprotected student devices at scale is both a security and safeguarding issue that should be noted explicitly.

**Cross-section aggregation tag:** F8-001 → Key Risk Group E (Privileged access control gaps — security posture supporting finding)

---

### R8-002 — Patching not managed on a defined cadence
**Pattern:** Graduated Severity
**Trigger question:** 8.3

**Conditions:**
- Endpoints or servers are in scope
- AND 8.3 (patching managed on defined cadence) is `informal`, `no`, or `unknown`

**Severity by answer value:**
- 8.3 is `no` or `unknown` → **concern**
- 8.3 is `informal` → **watch**

**Finding — F8-002**
- Title: Endpoint and server patching not managed on a defined cadence
- Severity: as above
- Description (concern): There is no defined cadence for patching endpoints and servers. Unpatched systems accumulate known vulnerabilities over time and are among the most common causes of successful attacks in school environments. Ransomware campaigns specifically target unpatched systems because the attack path is published and automated.
- Description (watch): Patching happens informally — typically when the IT person is aware of a specific issue rather than on a scheduled basis. This creates unpredictable gaps between patch cycles.
- Confidence: high

**Actions:**
- A8-002a: Define and document a patching cadence — at minimum monthly security patches for endpoints and servers, with critical patches applied within 72 hours of release where feasible
  - Time horizon: next_30_days
- A8-002b: Where MDM or endpoint management is in place, configure automated patch deployment to reduce manual effort
  - Time horizon: next_90_days

---

### R8-003 — Network and security device firmware not regularly reviewed
**Pattern:** Graduated Severity
**Trigger question:** 8.4

**Conditions:**
- Network or security infrastructure exists
- AND 8.4 (critical network/security devices reviewed for firmware currency) is `irregularly`, `no`, or `unknown`

**Severity by answer value:**
- 8.4 is `no` or `unknown` → **concern**
- 8.4 is `irregularly` → **watch**

**Finding — F8-003**
- Title: Network and security device firmware not regularly reviewed for currency
- Severity: as above
- Description (concern): Critical network and security devices — firewalls, switches, wireless controllers — are not being reviewed for firmware currency. Outdated firmware on security devices is functionally equivalent to leaving a known vulnerability unpatched. Attackers specifically target network infrastructure because compromising a firewall or switch provides access to all traffic passing through it.
- Description (watch): Firmware is reviewed irregularly. The gaps between reviews represent periods where known vulnerabilities may be present on devices that protect the entire network.
- Confidence: high

**Actions:**
- A8-003a: Review the current firmware version on all critical network and security devices and compare against vendor-recommended versions
  - Time horizon: next_30_days
- A8-003b: Establish a twice-yearly firmware review cadence as a recurring calendar item
  - Time horizon: next_30_days

**Scheduling note:** Firmware updates for firewalls and core switches → school calendar Category 3 (spring break) where updates require downtime.

**Cross-reference note:** Pairs with R3-005 (firewall details not known). If both fire, the finding should note that firmware cannot be reviewed without first documenting the current version.

---

### R8-004 — No web filter or content filter in place
**Pattern:** Graduated Severity + Cross-Section Reference
**Trigger questions:** 8.5, 5.3

**Conditions:**
- Internet access is provided to students or staff (always true in v1)
- AND 8.5 (web filter in place) is `limited or partial`, `no`, or `unknown`

**Severity by answer value:**
- 8.5 is `no` AND 5.3 is `yes all relevant grades` or `partial` → **urgent** — students accessing the internet without filtering is both a safeguarding and a compliance concern
- 8.5 is `no` AND student devices not in scope → **concern**
- 8.5 is `unknown` → **concern**
- 8.5 is `limited or partial` → **concern**

**Finding — F8-004**
- Title: Web or content filtering absent or inadequate
- Severity: as above
- Description (urgent): There is no web or content filter protecting student internet access. Schools have legal and ethical obligations to protect students from harmful online content. The absence of filtering in a student device environment may also conflict with E-rate compliance requirements and CIPA obligations.
- Description (concern): Web filtering is absent, unknown, or only partially implemented. Gaps in filtering coverage leave users — particularly students — exposed to harmful content and phishing sites.
- Confidence: high
- risk_category: security
- affected_entity: student and staff internet access

**Actions:**
- A8-004a: Implement a web filter or content filter covering all student internet access as an immediate priority — many education-specific filtering solutions are available at low or no cost
  - Time horizon: immediate (if student devices in scope with no filter)
- A8-004b: Extend filtering coverage to staff devices and document the filtering scope and any exception policies
  - Time horizon: next_30_days

**Judgment call note:** No filtering on student devices is urgent because of the safeguarding dimension — this is not purely a security finding. CIPA compliance for E-rate recipients adds a regulatory obligation. Unknown is concern rather than urgent because the filter may exist but simply be undocumented.

---

### R8-005 — Student safety monitoring controls not documented
**Pattern:** Simple Threshold
**Trigger question:** 8.7

**Conditions:**
- Filtering or student safety controls exist or are expected (8.5 or 8.6 indicates controls)
- AND 8.7 (controls documented well enough to understand coverage and gaps) is `partial`, `no`, or `unknown`

**Finding — F8-005**
- Title: Student safety and filtering controls not documented
- Severity: **watch**
- Description: The school has web filtering or student safety monitoring in place but the controls are not documented well enough to understand coverage and gaps. Without documentation, it is unclear which students are covered, what categories are filtered, and how exceptions are managed. This makes it difficult to demonstrate appropriate safeguarding to parents, leadership, or regulators.
- Confidence: moderate — optional question

**Actions:**
- A8-005a: Document the current filtering and student safety control configuration — what is filtered, who is covered, what the exception process is, and who is responsible for reviewing and maintaining the controls
  - Time horizon: next_90_days

---

### R8-006 — No incident response process for security events
**Pattern:** Graduated Severity
**Trigger question:** 8.8

**Conditions:**
- 8.8 (documented process for responding to suspicious activity, malware, or account compromise) is `partial`, `no`, or `unknown`

**Severity by answer value:**
- 8.8 is `no` or `unknown` → **concern**
- 8.8 is `partial` → **watch**

**Finding — F8-006**
- Title: No documented process for responding to security incidents
- Severity: as above
- Description (concern): There is no documented process for responding to malware, suspicious activity, or account compromise. When a security event occurs, the absence of a defined response process means the IT person must improvise under pressure — which typically results in slower response, inconsistent containment, and higher impact. For small schools, a simple one-page response guide covering the most common scenarios is sufficient.
- Description (watch): A partial incident response process exists. Key scenarios or steps may be missing, leaving gaps that could be critical during an actual event.
- Confidence: high

**Actions:**
- A8-006a: Create a basic security incident response reference covering at minimum: how to identify a compromise, who to notify, how to contain the affected system, how to communicate with staff and leadership, and when to involve external help
  - Time horizon: next_90_days

**Cross-reference note:** Pairs with R7-011 (no disaster response reference). If both fire, present together as a combined operational response readiness finding — the school has no documented playbook for either security incidents or IT outages.

---

### R8-007 — Logs and alerts not regularly reviewed
**Pattern:** Graduated Severity
**Trigger question:** 8.9

**Conditions:**
- Logs or alerts are available from core systems
- AND 8.9 (logs or alerts reviewed by someone) is `sometimes`, `no`, or `unknown`

**Severity by answer value:**
- 8.9 is `no` or `unknown` → **watch**
- 8.9 is `sometimes` → **watch**

**Finding — F8-007**
- Title: System logs and alerts not regularly reviewed
- Severity: **watch**
- Description: Logs and alerts from key systems are not being reviewed regularly. Without regular review, security events — failed logins, unusual access patterns, system errors — go unnoticed until they become significant incidents. Even basic periodic review of authentication logs and firewall alerts meaningfully improves detection capability.
- Confidence: moderate — optional question

**Actions:**
- A8-007a: Establish a regular log review practice — at minimum monthly review of authentication logs, failed login attempts, and any security alerts generated by the firewall or endpoint protection platform
  - Time horizon: next_90_days

---


### R8-001b — Endpoint protection alerts not monitored
**Pattern:** Simple Threshold
**Trigger question:** 8.2b
**Note:** This rule was added in v0.1.7 intake engine revision. Not in original schema.

**Conditions:**
- 8.1 (endpoint protection deployed) is not `No` or `Unknown`
- AND 8.2b (someone monitoring EP alerts and trends) is `Sometimes`, `No`, or `Endpoint protection does not notify us centrally`

**Severity by answer value:**
- 8.2b is `No` → **concern**
- 8.2b is `Sometimes` → **watch**
- 8.2b is `Endpoint protection does not notify us centrally` → **concern** — the tool cannot alert even if someone wanted to review

**Finding — F8-001b**
- Title: Endpoint protection alerts not consistently monitored
- Severity: as above
- Description (concern): Endpoint protection is deployed but no one is consistently reviewing its alerts and trends. Unmonitored alerts are functionally equivalent to no detection — a threat that triggers an alert but goes unreviewed produces no response. Endpoint protection that does not provide centralized notifications cannot support any alert-review practice.
- Description (watch): Alerts are reviewed occasionally. The irregular cadence means threats may persist between reviews without detection.
- Confidence: high

**Actions:**
- A8-001b-a: Establish a regular alert review cadence — at minimum weekly review of endpoint protection alerts and trend reports
  - Time horizon: next_30_days
- A8-001b-b: If the current platform does not support centralized alerting, evaluate platforms that do
  - Time horizon: next_90_days

### R8-008 — Known unresolved security concerns
**Pattern:** Simple Threshold + Constraint Annotation
**Trigger question:** 8.11

**Conditions:**
- 8.11 (known unresolved security concerns today) is `yes`

**Finding — F8-008**
- Title: Known unresolved security concerns identified
- Severity: **concern**
- Description: The IT person has identified active, unresolved security concerns. These are confirmed issues, not hypothetical risks, and should be treated as immediate priorities regardless of where they fall in the broader assessment findings.
- Confidence: high — notes field identifies specific concerns
- risk_category: security
- affected_entity: as specified in notes

**Actions:**
- A8-008a: Document each identified security concern with a description, estimated risk level, and a specific action and owner
  - Time horizon: immediate
- A8-008b: Address each confirmed concern according to its severity — do not allow known security issues to remain unowned
  - Time horizon: next_30_days

**Report behavior:** Notes from 8.11 must be quoted directly in the finding description. Known active security concerns must appear in the Executive Summary and Key Risks section.

**Escalation modifier:** If 8.11 is `yes` AND 8.1 is `no` or `unknown` (no endpoint protection), escalate to **urgent** — active security concerns in an unprotected environment represent compounded risk.

---

## Section 8 Composite Rules

### R8-C01 — Baseline security hygiene completely absent
**Pattern:** Composite

**Conditions (all must be true):**
- 8.1 (endpoint protection deployed) is `no` or `unknown`
- AND 8.3 (patching cadence) is `no` or `unknown`
- AND 8.5 (web filter) is `no` or `unknown`

**Finding — F8-C01**
- Title: Baseline security hygiene absent — no endpoint protection, no patching cadence, no web filtering
- Severity: **urgent**
- Description: The school has no endpoint protection, no defined patching cadence, and no web filtering. These three controls represent the most fundamental baseline of security hygiene. Their simultaneous absence means the school's devices, users, and students are exposed to common threats with no systematic defense. This is not a gap in maturity — it is an absence of basic protection.
- Confidence: high
- risk_category: security
- affected_entity: entire IT environment

**Actions:** Inherit A8-001a, A8-002a, A8-004a. Present as single consolidated urgent finding.

**Report note:** F8-C01 must appear in Key Risks and Executive Summary if it fires. Cross-reference with F4-C01 (privileged access uncontrolled) if that also fires — the combination represents a school with no security controls at any level.

**Cross-section aggregation tag:** F8-C01 → Key Risk Group E (Privileged access and security posture — expands the group to include baseline hygiene)

---

## Section 8 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F8-C01 fires (baseline hygiene absent) | urgent |
| F8-001 fires at urgent (no endpoint protection — 8.1) | urgent |
| F8-004 fires at urgent (no filtering on student devices) | urgent |
| F8-008 fires AND escalated (known concerns + no endpoint protection) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 8.1, 8.5, or 8.8 are among the unknowns |

**Unknown override:** Critical questions: 8.2, 8.5, 8.8. Unknown on any raises floor to concern.

---

## Section 8 Judgment Calls

1. **R8-004 (no web filter on student devices) is urgent — safeguarding dimension.** This is the only finding in the module where a legal and ethical obligation to students independently elevates severity beyond the technical risk. Unknown is concern rather than urgent because the filter may exist but be undocumented.

2. **R8-001 (no endpoint protection) is urgent for both `no` and `unknown`.** Same reasoning as MFA and admin lists in Section 4 — unknown protection status cannot be assumed safe.

3. **R8-007 (logs not reviewed) and R8-005 (controls not documented) are watch, not concern.** These are maturity improvements. The absence of log review is a detection gap, not a direct exposure. The absence of documentation is a visibility gap, not a control failure.

4. **R8-008 (known active security concerns) quotes notes directly.** The IT person has specifically flagged these — they should appear by name in the report, not be paraphrased into generic language.

5. **Question 8.6 (student safety monitoring) and 8.10 (cyber insurance) generate no standalone findings.** They are contextual inputs to the appendix and may influence roadmap recommendations in future versions, but do not create findings in v1.

---

## Report Assembly Updates Required

Add to RA-001 (mandatory Executive Summary findings):
- F8-C01 — Baseline security hygiene completely absent
- F8-008 — Known unresolved security concerns (always surfaces in Executive Summary when it fires)

Add to RA-003 — update Key Risk Group E:
**Key Risk Group E: Privileged access and security posture** *(expanded from Section 8)*
- Primary findings: F4-C01, F4-005 (when urgent), F4-006 (when urgent), F8-C01
- Supporting findings: F2-007, F8-001, F8-004 (when urgent)
- Aggregated severity: urgent if any primary finding fires at urgent; concern otherwise
- Report title: "Privileged access and baseline security posture"

Add to RA-005 (finding clusters):
| Security hygiene gap | F8-001, F8-002, F8-003 | Section 8 |
| Student protection gap | F8-004, F8-005 | Section 8 |

Add to RA-006 (notes passthrough):
| F8-008 | 8.11 (known security concerns) | Quoted directly in finding description and Executive Summary |

Add to RA-008 (composite suppression):
- F8-C01 suppresses F8-001, F8-002, F8-004 (actions inherited)

---

# Section 9: Documentation and Operational Readiness

## Section 9 Purpose
Measure whether the environment is understandable and supportable by more than one person. This section is foundational to the whole framework — poor documentation here amplifies the severity of findings elsewhere because it reduces confidence, recoverability, and transferability. Key outputs are documentation maturity, operational resilience findings, and suggested documentation tasks.

## Section 9 Critical Questions for Unknown Override
If any of the following are unknown, section floor rises to **concern**:
- 9.1 (central documentation location)
- 9.5 (environment understandable by a third party)
- 9.6 (knowledge concentration)

---

### R9-001 — No central documentation location
**Pattern:** Graduated Severity
**Trigger question:** 9.1

**Severity by answer value:**
- 9.1 is `no` or `unknown` → **concern**
- 9.1 is `yes but inconsistent` → **watch**

**Finding — F9-001**
- Title (concern): No central location for IT documentation
- Title (watch): Central documentation location exists but is used inconsistently
- Description (concern): There is no central location where IT documentation is stored. Documentation that exists is scattered across personal drives, email threads, sticky notes, or individual memory. This makes it effectively inaccessible to anyone other than the person who created it — and often inaccessible even to that person under pressure.
- Description (watch): A central documentation location exists but is not used consistently. Some documentation lives there while other items remain in personal storage or undocumented entirely. The value of a central location depends on consistent use.
- Confidence: high

**Actions:**
- A9-001a: Designate a single authoritative location for all IT documentation — a wiki, shared drive folder, or IT documentation platform — and communicate it to all stakeholders
  - Time horizon: next_30_days
- A9-001b: Migrate existing documentation to the central location and establish a policy that new documentation is always created there
  - Time horizon: next_90_days

---

### R9-002 — Documentation not kept current
**Pattern:** Graduated Severity
**Trigger question:** 9.2

**Conditions:**
- Documentation exists or is expected
- AND 9.2 (network, systems, and vendor documents kept current) is `partly`, `no`, or `unknown`

**Severity by answer value:**
- 9.2 is `no` or `unknown` → **concern**
- 9.2 is `partly` → **watch**

**Finding — F9-002**
- Title: IT documentation not kept reasonably current
- Severity: as above
- Description (concern): Network, systems, and vendor documentation exists but is not being kept current. Outdated documentation can be worse than no documentation — it may misdirect troubleshooting, cause misconfiguration during changes, or give false confidence about the state of the environment.
- Description (watch): Most documentation is reasonably current but some areas lag. The outdated sections represent blind spots that may matter precisely when they are most needed.
- Confidence: high

**Actions:**
- A9-002a: Conduct a documentation audit — identify what exists, what is outdated, and what is missing entirely — and prioritize updates starting with network diagrams, server records, and vendor contacts
  - Time horizon: next_90_days
- A9-002b: Establish a documentation review cadence — at minimum an annual review of all major documentation, with updates triggered by any significant change
  - Time horizon: next_90_days

---

### R9-003 — Standard operating procedures not documented
**Pattern:** Graduated Severity
**Trigger question:** 9.3

**Severity by answer value:**
- 9.3 is `no` or `unknown` → **concern**
- 9.3 is `partial` → **watch**

**Finding — F9-003**
- Title: Standard operating procedures not documented for recurring IT tasks
- Severity: as above
- Description (concern): There are no documented standard operating procedures for common recurring IT tasks. Without SOPs, every task depends on the IT person's memory or improvisation. New staff, vendors, or coverage personnel cannot perform these tasks reliably. Common tasks that lack SOPs include: new device setup, account onboarding and offboarding, printer troubleshooting, classroom tech reset procedures, and end-of-year cleanup.
- Description (watch): Some SOPs exist but coverage is incomplete. The missing procedures represent tasks that cannot be delegated or covered reliably.
- Confidence: high

**Actions:**
- A9-003a: Identify the five most frequently performed IT tasks that currently rely on memory or informal knowledge, and document a simple step-by-step SOP for each
  - Time horizon: next_90_days

---

### R9-004 — No change documentation process
**Pattern:** Graduated Severity
**Trigger question:** 9.4

**Severity by answer value:**
- 9.4 is `no` or `unknown` → **concern**
- 9.4 is `informal` → **watch**

**Finding — F9-004**
- Title: No process for documenting changes after projects or incidents
- Severity: as above
- Description (concern): There is no known process for documenting changes to the IT environment after projects, updates, or incidents. Each undocumented change widens the gap between the documented environment and the actual environment. Over time, this gap makes troubleshooting unreliable and planning inaccurate.
- Description (watch): Changes are sometimes documented informally. The result is a partially documented environment where some changes are captured and others are not — often with no reliable way to know which is which.
- Confidence: high

**Actions:**
- A9-004a: Establish a simple change documentation habit — after any significant change to the environment, update the relevant documentation before the change is considered complete
  - Time horizon: next_30_days

---

### R9-005 — Environment not understandable by a third party
**Pattern:** Graduated Severity
**Trigger question:** 9.5

**Severity by answer value:**
- 9.5 is `no` → **urgent**
- 9.5 is `unknown` → **concern**
- 9.5 is `partially` → **concern**

**Finding — F9-005**
- Title: IT environment not understandable or supportable from existing documentation
- Severity: as above
- Description (urgent): A qualified third party could not understand or support the IT environment from existing documentation. This means that if the primary IT person were suddenly unavailable, recovery, troubleshooting, and ongoing support would require starting from scratch. The school is one departure or illness away from an environment no one can manage.
- Description (concern): The environment is only partially understandable from existing documentation. A third party could handle some situations but would be unable to support or recover key areas without significant investigation.
- Confidence: high
- risk_category: continuity
- affected_entity: entire IT environment

**Actions:**
- A9-005a: Identify the areas where documentation is weakest — typically network topology, server configuration, vendor access, and admin credential locations — and prioritize documentation of these areas
  - Time horizon: next_90_days
- A9-005b: Use the findings from this assessment as a starting point: every finding that references missing documentation is also a documentation task

**Cross-section aggregation tag:** F9-005 → Key Risk Group B (Single-person dependency creates recovery and continuity risk — documentation gap is a key driver of this risk)

---

### R9-006 — Knowledge concentration in one person
**Pattern:** Simple Threshold + Notes Passthrough
**Trigger question:** 9.6

**Conditions:**
- 9.6 (major knowledge areas live only in one person's head) is `yes`

**Finding — F9-006**
- Title: Critical IT knowledge concentrated in a single person
- Severity: **concern**
- Description: Major IT knowledge areas exist only in one person's head with no documentation or backup coverage. This is a knowledge single-point-of-failure. If that person leaves, becomes ill, or is simply unavailable for an extended period, the school loses access to that knowledge entirely. The notes field identifies the specific areas of concentration.
- Confidence: high — notes field identifies specific knowledge areas
- risk_category: continuity
- affected_entity: as specified in notes

**Actions:**
- A9-006a: Identify each area of knowledge concentration and develop a documentation or cross-training plan for each
  - Time horizon: next_90_days
- A9-006b: Prioritize documentation of the highest-risk knowledge areas — those that would cause the most operational disruption if suddenly unavailable
  - Time horizon: next_30_days

**Report behavior:** Notes from 9.6 must be quoted in the finding description. The specific knowledge areas should be listed by name, not referred to generically.

**Cross-section aggregation tag:** F9-006 → Key Risk Group B (Single-person dependency — knowledge concentration is the documentation layer of this risk)

---

## Section 9 Composite Rules

### R9-C01 — Documentation completely absent and environment non-transferable
**Pattern:** Composite

**Conditions (all must be true):**
- 9.1 (central documentation location) is `no` or `unknown`
- AND 9.2 (documentation kept current) is `no` or `unknown`
- AND 9.5 (environment understandable by third party) is `no` or `unknown`

**Finding — F9-C01**
- Title: No documentation exists and environment is non-transferable
- Severity: **urgent**
- Description: There is no central documentation location, existing documentation is not kept current, and the environment cannot be understood from documentation by anyone other than the current IT person. The school's entire IT environment exists only in one person's memory. This is the most significant single-point-of-failure in the assessment — it means every other finding in this report is harder to address because there is no documented baseline to work from.
- Confidence: high
- risk_category: continuity
- affected_entity: entire IT environment

**Actions:** Inherit A9-001a, A9-001b, A9-002a, A9-005a. Present as single consolidated urgent finding.

**Report note:** F9-C01 must appear in Key Risks and Executive Summary if it fires. It should be cross-referenced with all Key Risk Group B findings — documentation absence is what makes single-person dependency a crisis rather than a risk.

**Cross-section aggregation tag:** F9-C01 → Key Risk Group B (primary amplifier finding)

---

## Section 9 Domain Score Logic

| Condition | Domain Status |
|---|---|
| F9-C01 fires (no documentation, environment non-transferable) | urgent |
| F9-005 fires at urgent (environment completely non-transferable) | urgent |
| Two or more concern-level findings fire | concern |
| One concern-level finding fires | concern |
| Only watch-level findings fire | watch |
| No findings fire | healthy |
| More than one-third of questions unknown | watch minimum; escalates to concern if 9.1, 9.5, or 9.6 are among the unknowns |

**Unknown override:** Critical questions: 9.1, 9.5, 9.6. Unknown on any raises floor to concern.

**Section 9 amplification rule:** Section 9 findings amplify findings in other sections. When F9-C01 or F9-005 fire, the confidence level of findings in Sections 3, 6, and 7 that depend on documentation should be reduced, and their descriptions should note that the absence of documentation makes them harder to resolve. This is a report assembly behavior, not a scoring change.

---

## Section 9 Judgment Calls

1. **F9-005 (environment non-transferable) is urgent when `no`, concern when `partially` or `unknown`.** `no` is urgent because it is a confirmed statement that the environment cannot be managed without the current IT person. This is a direct operational crisis condition.

2. **R9-006 (knowledge concentration) is always concern when `yes`.** The IT person has confirmed that knowledge lives only in their head. This is always material regardless of how well other areas are documented.

3. **Section 9 amplifies other sections rather than standing alone.** The section's most important design behavior is the amplification rule — a poorly documented environment makes every other finding harder to resolve. This should be visible in the report rather than implicit.

4. **Questions 9.1 through 9.6 all generate findings.** Unlike some sections with many contextual-only questions, every Section 9 question contributes to a finding. This reflects the section's foundational importance to the whole assessment.

---

## Report Assembly Updates Required

Add to RA-001 (mandatory Executive Summary findings):
- F9-C01 — No documentation and environment non-transferable

Add to RA-003 — update Key Risk Group B (now complete):
**Key Risk Group B: Single-person dependency creates recovery and continuity risk** *(complete)*
- Primary findings: F2-C02, F2-008
- Supporting findings: F7-012, F3-C02, F6-009 (when urgent), F6-010, F6-C02, F9-005, F9-006, F9-C01
- Aggregated severity: urgent if F2-C02, F7-012, F3-C02, F6-C02, F9-C01, or F9-005 fires at urgent; concern otherwise
- Report title: "Single-person dependency creates recovery and continuity risk"

Add to RA-005 (finding clusters):
| Documentation maturity gap | F9-001, F9-002, F9-003, F9-004 | Section 9 |

Add to RA-006 (notes passthrough):
| F9-006 | 9.6 (knowledge concentration areas) | Specific knowledge areas quoted by name in finding description |

Add to RA-008 (composite suppression):
- F9-C01 suppresses F9-001, F9-002, F9-005 (actions inherited)

Add new RA-011 — Section 9 amplification behavior:

## RA-011 — Section 9 documentation amplification

When F9-C01 or F9-005 fire, the report assembler must apply a documentation amplification flag to findings in the following sections that reference missing documentation as part of their finding description:
- Section 3: F3-001, F3-002, F3-008, F3-009, F3-012
- Section 6: F6-001, F6-002, F6-009, F6-010
- Section 7: F7-003, F7-010, F7-011

The amplification flag adds a sentence to each affected finding: *"This finding is harder to resolve because the environment currently lacks a central documentation system — addressing Section 9 findings first will make this and other documentation gaps easier to close systematically."*

The amplification flag does not change finding severity or scoring. It is a report narrative modifier only.

---

# Section 10: Near-Term Priorities and Planning Inputs

## Section 10 Purpose
Section 10 generates no findings and no scores. It is a calibration and context section. Its answers are used by the report assembler to sequence and annotate the action plan, tune the roadmap, and record data quality information for the appendix. Every question feeds report assembly behavior rather than the deterministic rule engine.

---

### R10-001 — Known IT priorities noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.1

**Conditions:**
- 10.1 (list of known IT problems or projects) is answered with one or more entries

**Report behavior:**
- Each item listed in 10.1 is compared against the findings and actions generated by the assessment
- Items that match an existing finding or action are tagged with a "user-confirmed priority" marker in the action plan — this elevates their display prominence without changing their deterministic severity
- Items that do not match any finding or action are listed in a separate "IT person priorities not yet supported by assessment data" appendix note — they are acknowledged but not elevated
- Items that contradict assessment findings (e.g. IT person does not consider something a priority that the engine scored urgent) are noted without suppressing the urgent finding

**No finding generated.** This is a pure report assembly input.

---

### R10-002 — Planned projects noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.2

**Report behavior:**
- Each item in 10.2 is passed to the roadmap section and the annual follow-up calendar
- Where a planned project overlaps with a recommended action, the action plan notes that this item is already in planning — it remains in the action plan but is marked "in progress / planned"
- Where a planned project does not appear in the assessment findings, it is listed in the appendix as additional context

**No finding generated.**

---

### R10-003 — Known deadlines and compliance events noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.3

**Report behavior:**
- Each item in 10.3 is passed to the annual follow-up calendar
- Where a deadline relates to a finding (e.g. an upcoming E-rate filing relates to filtering findings), the action plan annotates the relevant action with the deadline date
- Deadlines within 30 days of the report date are flagged as time-sensitive in the action plan

**No finding generated.**

---

### R10-004 — Changes before next school year noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.4

**Report behavior:**
- Content from 10.4 is passed to the roadmap section's summer and pre-year planning notes
- Where a stated change (e.g. new grade level launching, new campus opening) creates new IT requirements, those requirements are noted in the roadmap as anticipated work items — they do not generate findings but do appear as planning actions

**No finding generated.**

---

### R10-005 — Leadership expecting a plan
**Pattern:** Constraint Annotation
**Trigger question:** 10.5

**Report behavior:**
- If 10.5 is `yes`, the report assembler increases the prominence of the roadmap section and adds an introductory note: *"Leadership is expecting a budget, refresh, or improvement plan from IT. The roadmap section of this report is designed to support that conversation."*
- The notes field from 10.5 (e.g. "board wants refresh plan by May") is appended to the roadmap section introduction
- No finding is generated and no scoring is changed

**No finding generated.**

---

### R10-006 — Known obstacles and constraints noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.6

**Report behavior:**
- Content from 10.6 is passed to the action plan as a general constraint annotation — similar to F2-006 but broader in scope
- The obstacles are listed in the action plan introduction: *"The following constraints were noted and may affect the feasibility or timing of recommended actions: [10.6 content]"*
- Individual actions that are directly affected by the stated obstacles are tagged with a constraint marker referencing 10.6

**No finding generated.**

---

### R10-007 — Overall data confidence assessed
**Pattern:** Graduated Severity (report behavior only — no finding)
**Trigger question:** 10.7

**Report behavior by answer value:**
- 10.7 is `high` → no caveat; report proceeds normally
- 10.7 is `moderate` → Executive Summary includes a single sentence: *"The IT person indicated that most answers in this assessment are based on recall or staff reports rather than documented verification. Findings should be verified before action is taken."*
- 10.7 is `low` → Executive Summary and each section summary include a data quality caveat. Sections with high unknown rates are additionally flagged as "Research Needed" regardless of whether they crossed the one-third unknown threshold automatically
- 10.7 is `mixed` → Executive Summary includes a caveat; sections flagged in 10.8 receive per-section data quality annotations

**No finding generated.** This is a report confidence modifier only. It does not change scores or finding severities.

---

### R10-008 — Specific uncertain sections noted
**Pattern:** Constraint Annotation
**Trigger question:** 10.8

**Conditions:**
- 10.8 is answered with one or more sections or topic areas
- AND 10.7 is `moderate`, `low`, or `mixed`

**Report behavior:**
- Each section or topic flagged in 10.8 receives a "respondent-flagged uncertainty" annotation in its findings page: *"The IT person indicated that data in this area was particularly uncertain. Findings should be verified before action is taken."*
- This annotation does not change finding severity or scoring
- The full list of flagged sections appears in the appendix data quality note

**No finding generated.**

---

## Section 10 Domain Score Logic

Section 10 does not receive a domain score. It has no findings and no severity outputs. Its contribution to the report is entirely through report assembly behavior.

---

## Section 10 Judgment Calls

1. **Section 10 generates zero findings — confirmed.** Every question is a calibration or context input. The section's value is in making the action plan and roadmap more relevant and actionable, not in adding to the finding count.

2. **R10-007 (data confidence) is a report modifier, not a scoring modifier.** Low confidence widens the Research Needed flag and adds caveats but does not change finding severities. The deterministic findings stand — what changes is how confidently they are presented.

3. **User-confirmed priorities that don't match findings are acknowledged but not elevated.** The IT person may have priorities the assessment didn't surface as findings. These are recorded honestly rather than suppressed or automatically promoted.

4. **User priorities that contradict urgent findings are noted without suppressing the finding.** If the IT person doesn't consider something important that the engine scored urgent, the report notes the discrepancy — it does not remove the urgent finding.

---

## Report Assembly Updates Required

Add new RA-012 — Section 10 action plan priority annotation:

## RA-012 — Section 10 action plan priority annotation

When 10.1 (known IT priorities) contains items that match existing findings or actions:
- The matching action in the action plan is tagged with: *"User-confirmed priority"*
- This tag increases the item's display prominence in the action plan (e.g. listed first within its time horizon bucket)
- It does not change the action's time horizon or severity

When 10.1 contains items that do not match any finding:
- They are listed in the appendix under: *"IT person priorities not yet confirmed by assessment data"*
- They are not elevated into the action plan

When 10.5 is `yes`:
- The roadmap section receives an introductory note referencing leadership expectations
- The notes content from 10.5 is appended to the roadmap introduction

When 10.7 is `moderate`, `low`, or `mixed`:
- Executive Summary receives a data quality caveat as specified in R10-007
- Sections flagged in 10.8 receive per-section uncertainty annotations

When 10.6 is answered:
- The action plan introduction includes the stated obstacles
- Individual actions affected by the stated obstacles are tagged with a constraint marker

---

# Sections To Be Added
The following sections are pending rule schema development.

- Section 1: School Identity, Profile, and Context *(minimal rule impact — primarily context and display; will be added as a brief contextual section with no findings)*

---

---

# Scoring Weights
To be defined after a minimum of three section schemas are complete. Weights will be assigned based on which rules fire most consequentially and which findings have the highest impact on overall domain status. See design document for scoring visibility requirements.
