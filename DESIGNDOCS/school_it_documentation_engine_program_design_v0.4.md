# School IT Documentation Engine - Program Design
## Version 0.4

## Purpose
Create a modular system that guides a school IT leader through a structured questionnaire, captures answers in a consistent schema, and produces a deterministic report with optional narrative enhancement.

This document defines the **platform architecture**, **design principles**, **data structures**, and **report-generation framework**. It is intentionally iterative and will be refined as Module 1 is built and tested.

---

## Product Goal
Build an engine for question-led document and report creation that can:

1. Ask structured questions about an IT environment.
2. Capture and normalize answers.
3. Score or classify findings deterministically.
4. Generate a consistent report with charts and action items.
5. Support multiple modules over time.
6. Optionally add LLM-based narrative rewriting without making AI a core dependency.

---

## Primary Audience

### v1 Target User
The primary operator in v1 is the **school IT director or administrator running the tool for their own school**. The tool is designed so that the IT person gets the data they need to clearly see and understand their own environment.

### Future Audience (post-v1)
Executive, board, and Head of School output is a planned future release. Once the IT-facing report is working well enough to be genuinely useful, a subsequent release will focus on simplifying and beautifying the output for non-technical power-holders.

### Out of Scope for v1
- IT consultants or MSPs running the tool on behalf of multiple clients
- Multi-school or multi-tenant usage

---

## Core Design Principles

### 1. Module-first, framework-aware
The first release should be built around one real module and one real report. The framework should stay as thin as possible until repeated patterns emerge.

### 2. Deterministic by default
All scoring, findings, recommendation selection, and report structure should work without an LLM.

### 3. AI is optional
Any LLM usage should be limited to narrative variation or report polishing, never required for core output.

### 4. Privacy-sensitive by design
The system must support environments where no questionnaire data is sent to an external AI service. The local web UI must make this clear to the user at all times (see Technical Design section).

### 5. Evidence-friendly
Questions should allow for a confidence or evidence state such as documented, observed, reported, estimated, or unknown.

### 6. Action-oriented reporting
The report should not only describe the environment. It should identify concerns, priorities, and near-term actions.

### 7. School-specific context
The framework should account for realities of small schools: limited staffing, shared roles, budget constraints, seasonal timing, campus events, student device fleets, vendor-heavy ecosystems, and compliance/safeguarding concerns.

---

## Platform Scope

### In scope
- Questionnaire module definition
- Answer schema
- Deterministic scoring logic
- Finding generation
- Action recommendation rules
- Report assembly
- Charts and summary visuals
- Optional narrative rewriting layer
- Module expansion over time
- Save and resume across multiple sessions

### Out of scope for v1
- Deep live integrations into network tools
- Automated scanning as a core dependency
- Asset discovery pipelines
- Full CMDB replacement
- Advanced benchmarking across organizations
- Executive or board-facing report output
- Multi-school or MSP/consultant usage

---

## System Layers

### Layer 1: Module Definition
Each module defines:
- sections
- questions
- answer types
- validation rules
- scoring rules
- finding rules
- action rules
- chart mappings
- report mappings

### Layer 2: Intake Experience
The user interface or form flow that:
- presents questions
- captures responses
- handles skips and unknowns
- records evidence/confidence
- supports save and resume across multiple sessions (see Assessment Session in the data model)

### Layer 3: Normalization
Transforms raw responses into a standard internal structure.

### Layer 4: Deterministic Analysis
Evaluates responses against rules to produce:
- domain status
- findings
- priorities
- risks
- next actions

### Layer 5: Report Assembly
Builds a consistent output with:
- executive summary
- environment overview
- findings by domain
- charts
- action plan
- roadmap
- appendix/detail sections

### Layer 6: Optional Narrative Enhancement
An optional pass that rewrites selected narrative blocks for tone, clarity, or variation. In v1 this is most relevant for preparing content for a future executive-facing output.

---

## Proposed Data Model

### School Profile
Collected once before any module is run. Shared across all modules for a given installation.
- school_name
- school_website_url

Note: The school website URL is included specifically to prevent any ambiguity when referencing or filing assessment records. Additional profile fields (enrollment size, campus count, etc.) are captured within Module 1, Section 1.

### Assessment Session
Tracks the state of a single in-progress or completed assessment. Enables save and resume.
- session_id
- module_id
- school_name
- created_on
- last_modified
- status (in_progress / complete / archived)
- sections_complete[]
- sections_skipped[]
- overall_completion_percentage

### Module
- module_id
- module_name
- version
- target_audience
- description
- sections[]
- scoring_profile
- report_template_id

### Section
- section_id
- title
- description
- order
- domain_tags[]
- questions[]

### Question
- question_id
- prompt
- help_text
- answer_type
- required
- options[]
- validation_rules[]
- evidence_mode
- deterministic_rules[]
- output_tags[]

### Answer Record
- session_id
- question_id
- raw_answer
- normalized_answer
- answer_status
- evidence_status
- notes
- attachments_or_links
- answered_by
- answered_on
- last_modified

### Finding
- finding_id
- domain
- severity
- title
- description
- supporting_question_ids[]
- confidence
- status

### Recommendation
- recommendation_id
- domain
- priority
- title
- rationale
- suggested_owner
- time_horizon
- source_rule_ids[]

### Report Object
- report_id
- session_id
- organization_profile
- module_results[]
- domain_scores[]
- findings[]
- recommendations[]
- charts[]
- summary_blocks[]
- appendix_data[]

---

## Standard Answer Types
- yes_no
- yes_no_unknown
- single_select
- multi_select
- short_text
- long_text
- number
- percentage
- date
- date_unknown
- count
- list_of_items
- maturity_scale
- risk_scale
- evidence_state

---

## Standard Evidence / Confidence States
- documented
- observed
- reported_by_staff
- estimated
- unknown

These should influence confidence in findings and may also affect recommendations.

---

## Deterministic Output Framework

### Output categories
1. **State**: what is true about the environment
2. **Concern**: what appears incomplete, risky, or unclear
3. **Priority**: what should be addressed soon
4. **Action**: what should be done next
5. **Timeline item**: when the next relevant follow-up should occur

### Example rule pattern
If:
- firewall documentation = no or unknown
- and firmware status = unknown
Then:
- create finding: perimeter security documentation gap
- severity: medium or high depending on other conditions
- action: document firewall platform, firmware, support status, and backup config location
- time horizon: 30 days

### Rule types
- threshold rule
- completeness rule
- dependency rule
- contradiction rule
- lifecycle rule
- recency rule
- ownership rule
- scheduling rule

---

## Recommended Severity Scale
- healthy
- watch
- concern
- urgent
- unknown

Note: **unknown** should remain visible as its own class rather than being silently converted to healthy or concern.

---

## Scoring Visibility

Scores are visible to the user at all times. This applies at three levels:

### Question-level scoring
Each answered question displays its individual score or status as soon as it is answered. The user should never have to wonder how a response was interpreted.

### Section-level scoring
Each section displays a running and final score as questions are completed. Section scores reflect the combined result of individual question scores plus any adjustments triggered by unknown answer thresholds (see Unknown Answer Handling Rules).

### Total score
A total overall score is displayed on the assessment summary screen and included prominently in the report. The total is an aggregate of all section scores, weighted as defined in the module's scoring profile.

### Score display format
The specific visual format (numeric, percentage, severity label, color band, or combination) is to be defined during UI design. All three levels must be present. The scoring must be fully deterministic and traceable — the user should be able to understand why they received the score they did.

### Future: Anonymous benchmarking
A future version (not v1) may allow users to optionally submit their scores to a central database to compare anonymously against other schools. This is noted here for architectural awareness — the data model should not actively prevent it, but no infrastructure for it will be built in v1.

---

## Unknown Answer Handling Rules

Unknown answers are a first-class output state and must be handled consistently across all modules. The following rules apply deterministically:

### Section-level unknown thresholds
- **Any unknown answer in a section** → section receives at minimum a **watch** status, regardless of other answers.
- **More than one-third of questions in a section answered as unknown** → section is flagged as **"Insufficient Data"** and escalated to a **warning** status. A specific finding of type *"Research Needed"* is generated automatically.

### Confidence propagation
- Findings drawn from sections with unknown answers are assigned reduced confidence.
- The report must display data coverage clearly so the IT person can see where gaps exist.

### Hiding unknowns is explicitly prohibited
Unknown answers must never be silently converted to healthy, concern, or any other status. They must appear in the report as their own visible category.

---

## Recommended Priority Scale for Actions
- now
- next_30_days
- next_90_days
- next_12_months
- strategic_future

---

## School Calendar Scheduling Rules

Actions that are disruptive to school operations must be scheduled according to the school calendar. The following rules apply deterministically when assigning time horizons to action items.

### Category 1: Non-disruptive — Schedule during the school year
Actions that can be completed without disrupting classes or requiring after-hours access may be assigned to any time during the active school year. Examples: documentation tasks, software audits, vendor calls, policy drafting, staff training that doesn't affect production systems.

### Category 2: Short disruptive, no tech support risk — Winter break
Actions that are disruptive to classroom operations but are unlikely to require vendor or external tech support if something goes wrong. These can be completed in a week or less and are appropriate for winter break. Examples: giving printers new IP addresses, conducting classroom inventory, renaming computers, testing speakers and AV equipment, reorganizing storage or cabling.

### Category 3: Short disruptive, tech support risk — Spring break
Actions that are disruptive and carry a meaningful risk of requiring vendor or external tech support if something goes wrong. These should not be scheduled over winter break when support availability may be reduced. Examples: updating firewall firmware, updating switch firmware, installing a new server, replacing major network components.

### Category 4: Multi-week disruptive — Summer only
Actions that cannot be completed while school is in session and require more than one week of focused work. Examples: major infrastructure replacements, full network redesigns, large-scale device refreshes, campus rewiring.

### Implementation notes
- The scheduling rule type should be added to the rule type list and applied as an output tag on action items.
- The report's action plan and roadmap must reflect these categories clearly, so the IT person can see not just what to do but when it is realistic to do it.
- Effort and cost band estimation is deferred to v1.5 or later.

---

## Report Structure for v1

The v1 report is written for the **IT person**, not for executive leadership. Tone should be direct, factual, and practical. Beautification and simplification for power-holders is a post-v1 goal.

### 1. Summary
High-level synopsis of the environment, major strengths, major concerns, and most important next steps — written for the IT reader.

### 2. Organization Context
School name, website, and profile data captured in Module 1, Section 1 (size, campuses, device model, support model, notable constraints).

### 3. Environment Overview
High-level overview of infrastructure, systems, identity, endpoints, and support posture.

### 4. Findings by Domain
Section-by-section results with consistent formatting. Includes data coverage indicators so gaps in unknown answers are visible.

### 5. Key Risks and Gaps
Top concerns requiring attention, including any sections flagged as Insufficient Data.

### 6. Action Plan
30-day, 60-day, and 90-day actions with suggested owners.

### 7. 12-Month Roadmap
Broader improvement opportunities.

### 8. Appendix
Full question responses, evidence notes, detailed observations, and unknown answer log.

---

## Suggested Chart Types for v1
- response completeness by domain
- concern level by domain
- known vs unknown data coverage
- lifecycle status summary
- action count by time horizon
- action count by school calendar window (school year / winter / spring / summer)

Charts should be simple, readable, and printable.

---

## Module Design Conventions
Each future module should include:
- purpose
- target use case
- assumptions
- section list
- question catalog
- deterministic rules
- report mappings
- glossary
- version notes

---

## Optional LLM Integration Model

### Default position
LLM use is off by default.

### Approved use cases
- rewrite summary narrative
- vary wording of narrative sections
- improve readability
- adapt tone for a future executive-facing output (post-v1)

### Not required for
- scoring
- finding detection
- recommendation generation
- chart creation
- timeline generation

### Privacy control modes
- no_ai
- local_ai
- cloud_ai_summary_only
- cloud_ai_full_section

---

## Technical Design

### Confirmed stack direction
- **Runtime**: Python backend
- **Frontend**: Local web UI served to `localhost` in the browser
- **Storage**: SQLite database (supports save/resume across sessions reliably)
- **Report output**: DOCX (v1 primary output)
- **Question/rule definitions**: JSON or YAML
- **Report rendering**: Python-based DOCX generation (e.g., python-docx)

### Data privacy — local web UI
The tool runs entirely on the user's own machine. No data is transmitted to any external server. To prevent concern among privacy-sensitive users, the following design requirements apply:

- A persistent, clearly visible banner must appear on every page stating: *"This tool runs entirely on your computer. No data is sent to the internet."*
- The localhost address must be visible in the browser URL bar at all times.
- Network activity (if any) must be limited strictly to localhost.
- AI features, if enabled, must require explicit user opt-in and must clearly disclose what data would leave the machine.

### Implementation posture
- Structured question definitions in JSON or YAML
- Deterministic rules expressed in JSON logic or equivalent code
- Report templates in DOCX-compatible format
- Output object fully assembled before rendering begins

---

## Rule Patterns

This section documents formal rule patterns identified during schema development. Each pattern represents a reusable structure that should be applied consistently across all sections and modules.

---

### Pattern 1: Simple Threshold Rule
The most common pattern. A single question answer triggers a finding at a fixed severity.

```
IF question X = [value]
THEN generate finding F at severity [S]
```

Example: If 7.2 (backups in place) = `no` → generate F7-001 at urgent.

---

### Pattern 2: Escalation Modifier Rule
A base finding fires at one severity, but a second condition escalates it higher. The base finding and the escalated finding share the same finding ID — only the severity changes.

```
IF question X = [value A]
THEN generate finding F at severity [S1]

IF question X = [value A]
AND question Y = [value B]
THEN escalate finding F to severity [S2]
```

Example: R7-002 fires at concern when 7.2 = `maybe or assumed`. If 7.8 (restore test) is also `no` or `unknown`, F7-002 escalates to urgent.

**Implementation note:** The rule engine must evaluate base findings before escalation modifiers. Escalation modifiers never generate a new finding ID — they modify the severity of an existing one.

---

### Pattern 3: Graduated Severity Rule
A single question has multiple answer options that each produce a different severity outcome. This pattern is necessary when the answer space is not binary and different values represent meaningfully different risk levels. The finding ID is the same across all severities — only the severity and description vary by answer value.

```
IF question X = [value A] → finding F at severity [S1]
IF question X = [value B] → finding F at severity [S2]
IF question X = [value C] → no finding (healthy or suppressed)
```

Example: R2-005 (IT budget):
- 2.6 = `no` or `unknown` → F2-005 at concern
- 2.6 = `informal` → F2-005-W at watch
- 2.6 = `yes annual` → no finding; healthy signal

**When to use this pattern:** Use graduated severity when the answer options represent a maturity spectrum rather than a simple present/absent binary. Common triggers: maturity-scale questions, process-maturity options (documented / informal / no / unknown), and coverage-level questions (full / partial / none / unknown).

**Implementation note:** The rule engine must evaluate all graduated branches and select the appropriate severity. Only one branch should fire per question per evaluation pass. The finding description should be written separately for each severity branch to reflect the specific situation accurately.

---

### Pattern 4: Composite Rule
Two or more conditions across multiple questions must all be true to fire the finding. Composite rules capture risks that are greater than the sum of their parts.

```
IF question X = [value]
AND question Y = [value]
AND question Z = [value]
THEN generate finding F at severity [S]
```

Example: R7-C01 fires only when 7.2, 7.7, and 7.8 are all in failing states simultaneously.

**Implementation note:** Composite rules should be evaluated after all individual rules have fired. If a composite rule fires, its finding should be presented in the report instead of (or consolidated with) the individual findings it subsumes. The composite finding references the individual finding IDs it replaces.

---

### Pattern 5: Cross-Section Reference Rule
A finding in one section references the answer to a question in a different section to determine severity or applicability. This pattern is necessary when risk context from one domain directly affects interpretation in another.

```
IF question X in Section A = [value]
AND question Y in Section B = [value]
THEN generate finding F at severity [S]
```

Example: R7-005 (staff device backup gap) references 4.1 (identity platform) and 4.10 (auto file sync) from Section 4 to determine whether the severity is concern or watch.

**Implementation note:** Cross-section references must be resolved after all sections are answered and normalized. The rule engine must have access to the full normalized answer set before evaluating cross-section rules. Cross-section references should be explicitly documented in each rule that uses them.

---

### Pattern 6: Constraint Annotation Rule
A question answer does not generate a finding in the traditional sense but instead attaches a modifier to the report's action plan. Actions that are affected by the constraint are annotated rather than suppressed.

```
IF question X = [value indicating constraint]
THEN annotate relevant actions with constraint flag
AND pass notes from question X to action plan annotations
```

Example: R2-006 — when 2.7 (budget or staffing constraints) is `yes`, relevant actions in the action plan are tagged with a visible constraint marker. The actions are not removed. The constraint notes from 2.7 are included in the annotation.

**When to use this pattern:** Use when the answer to a question modifies the context of recommendations without creating a new risk finding. Constraint annotation is appropriate for capacity, budget, and timing inputs that the IT person has already acknowledged — the report's job is to make the tension visible, not to alarm.

**Implementation note:** The report assembler must support a constraint_flag field on action items. When set, the action plan renders the flag visibly alongside the action. The constraint text is drawn from the notes field of the triggering question. Constraint flags never suppress actions.

---

When findings from multiple sections point at the same underlying risk, they must be surfaced together in the Key Risks section of the report rather than appearing as isolated domain findings. This prevents the same root problem from being buried across separate sections where it loses its combined weight.

### What triggers aggregation
Findings from different sections should be aggregated when two or more of the following are true:
- They share the same risk category (e.g. both are continuity gaps, both are access control gaps)
- They affect the same system, person, or process
- They share the same recommended owner
- Resolving one finding would directly reduce the severity of another

### How aggregation works in the report
- Individual findings remain in their section for completeness
- An aggregated finding is generated in the Key Risks section that references the contributing section findings by ID
- The aggregated finding severity is the highest severity among the contributing findings
- The aggregated action list consolidates the most important actions from each contributing finding, removing duplicates

### Example
R7-012 (emergency credential access — urgent) + R2-XXX (key-person dependency — concern) + R9-XXX (knowledge concentration — concern) all point at the same root risk: the environment cannot be maintained or recovered if the primary IT person is unavailable. These three findings aggregate into a single Key Risk: "Single-person dependency creates recovery and continuity risk."

### Implementation note
The aggregation engine must be able to tag findings with a shared risk_category and affected_entity so the report assembler can group them. This tagging should be part of the finding definition in each rule schema.

---

## Future To-Do Items

Items noted during design and rule schema development that are intentionally deferred to a later version.

### User-editable mitigating controls and score adjustment
A future version should allow the IT person to add custom mitigating controls in a notes field at the end of each section, and optionally edit their section score to reflect those controls. For example: a school that has no formal backup documentation (which would normally fire a concern finding) but uses a managed backup service that the MSP monitors daily could note this as a mitigating control and adjust the score accordingly. This feature requires a score audit trail so any manual adjustment is visible in the report and appendix alongside the original deterministic score.
- Deferred to: v1.5 or later
- Design impact: the scoring model must leave room for a manual_override field on each section score and each finding, with a required notes field when override is used

---
- Over-engineering the framework before a working module exists
- Mixing scoring logic with prose generation
- Hiding unknown answers
- Asking questions without a clear report purpose
- Producing too many actions with no prioritization
- Allowing recommendations that cannot be traced back to answers
- Triggering data privacy concerns through unclear UI (mitigated by localhost banner requirement)

---

## Decision Log

All decisions are recorded here with version and rationale. Decisions marked **v0.2** were made in the second design review session.

| # | Decision | Version | Notes |
|---|----------|---------|-------|
| 1 | Build the first module before fully generalizing the framework | pre-v0.1 | Avoid over-engineering |
| 2 | Keep all core outputs deterministic | pre-v0.1 | AI must never be required |
| 3 | Use optional AI only as a presentation layer | pre-v0.1 | Privacy and reliability |
| 4 | Focus first on a small private school IT overview workflow | pre-v0.1 | Scope control |
| 5 | Primary operator in v1 is school IT staff, not MSP/consultant | v0.1 | Tool is self-operated by school IT person |
| 6 | v1 report audience is the IT person only | v0.1 | Executive/board output deferred to post-v1 |
| 7 | Primary output format for v1 is DOCX | v0.1 | PDF and screen view deferred |
| 8 | Tool must support save and resume across multiple sessions | v0.1 | Added Assessment Session to data model |
| 9 | Frontend is a local web UI served to localhost | v0.1 | Better UX path than desktop GUI; data privacy concern mitigated by persistent localhost banner |
| 10 | Backend is Python; storage is SQLite | v0.1 | Supports local install, save/resume, low-friction packaging |
| 11 | Any unknown answer in a section sets minimum status to Watch | v0.1 | Unknowns must never be hidden |
| 12 | More than one-third unknowns in a section triggers Insufficient Data + Warning | v0.1 | Generates a Research Needed finding automatically |
| 13 | Minimum school profile = school name + school website URL | v0.1 | URL added to prevent ambiguity; additional profile fields captured in Module 1 Section 1 |
| 14 | One school per installation | v0.1 | Multi-school/MSP use is out of scope for v1 |
| 15 | DOCX section mapping conventions deferred until Module 1 is reviewed | v0.1 | May have enough detail in the module to define this; revisit after module review |
| 16 | Scores are visible to the user at question, section, and total levels | v0.2 | All three levels required; format TBD during UI design |
| 17 | Anonymous benchmarking (comparing scores against other schools) is noted for a future version; no infrastructure built in v1 | v0.2 | Data model should not actively prevent it |
| 18 | Effort and cost band estimation deferred to v1.5 or later | v0.2 | Not needed for the IT person to understand their situation |
| 19 | Actions are scheduled according to school calendar windows: school year, winter break, spring break, or summer | v0.2 | Four categories defined with distinct criteria; scheduling rule type added to rule type list |
| 20 | Cross-section finding aggregation is a formal design pattern | v0.3 | Findings sharing risk category, affected entity, or recommended owner are surfaced together in Key Risks; individual findings remain in their sections |
| 21 | User-editable mitigating controls and score adjustment deferred to v1.5 | v0.3 | Score model must leave room for manual_override field with required notes; audit trail required |
| 22 | Restore test frequency must be proportional to useful backup recovery window, not a fixed calendar interval | v0.3 | Established during Section 7 rule schema review; applies to all sections where restore testing is relevant |
| 23 | Six formal rule patterns documented: simple threshold, escalation modifier, graduated severity, composite, cross-section reference, and constraint annotation | v0.3.1 | Emerged from Section 2 and Section 7 rule schema development; all future rule schemas must use these patterns |
| 24 | Graduated severity pattern is the correct approach when answer options represent a maturity spectrum rather than a binary | v0.3.1 | Established via R2-005 (IT budget formality); applies whenever process_maturity or coverage_level enums are in use |
| 25 | Constraint annotation never suppresses actions — it annotates them with a visible marker and the constraint notes | v0.3.1 | Established via R2-006; report assembler must implement constraint_flag field on action items |
| 26 | Undocumented shared credentials without mitigating controls are frequently a root cause of costly IT failures and should always be marked urgent | v0.3.1 | Confirmed during Section 2 judgment call review; applies to all credential and emergency access questions across sections |
| 27 | Branching logic in v1 is limited to one level — a question can be conditional on one prior answer, but not on a chain of conditions | v0.4 | Start simple; revisit if one-level branching proves insufficient during the build |
| 28 | All questions are marked skippable by default in v1; the skippable status field is built into the question schema so it can be changed per question without code changes; mandatory vs skippable will be tuned after a real run-through | v0.4 | Module format will include a skippable_status field to support future multi-author module creation |
| 29 | Score display format: question level shows point value only (not score) while answering; section score (points earned / max points + severity label) is revealed only after the full section is complete; total score shows weighted percentage + severity label with a section-by-section breakdown | v0.4 | Showing point value during answering gives the IT person a sense of stakes without mid-section anxiety; score revealed at section completion prevents gaming |

---

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | How much branching logic should v1 support? | **Closed** — see Decision #27 |
| 2 | Should scoring be visible to the user or only used internally? | **Closed** — see Decision #16 |
| 3 | Should the action plan include estimated effort and cost bands in v1? | **Closed** — see Decision #18 |
| 4 | How should seasonal school timing influence the default calendar of next steps? | **Closed** — see Decision #19 |
| 5 | What are the DOCX section mapping conventions for module report output? | Open — to be defined during the build |
| 6 | Which questions are mandatory vs skippable? | **Closed** — see Decision #28; all skippable by default, tuned after first real run-through |
| 7 | What is the score display format — number, percentage, color band, severity label, or combination? | **Closed** — see Decision #29 |

*Closed questions are recorded in the Decision Log.*

---

## Next Iteration Goals
1. Resolve score display format (Open Question #7) — short discussion needed before frontend build
2. Build the intake engine for Sections 1 and 2 — exercises save/resume, branching, question flow, and scoring display end to end
3. Define DOCX section mapping conventions during the build as the report template takes shape
4. Run a first real assessment and tune mandatory/skippable status per question based on experience
5. Validate scoring weights against real assessment data — adjust if any section feels miscalibrated in practice
