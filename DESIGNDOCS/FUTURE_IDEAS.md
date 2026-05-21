# Future Ideas

Ideas captured during development. Not prioritised — reference for future roadmap conversations.

---

## Reporting & Visualisation

- **Graphical calendar view** — visual Gantt-style calendar for the phased remediation timeline,
  rendered in the browser or embedded in the DOCX. Deferred from v0.4 timeline implementation.
- **Executive / board report variant** — shorter, less technical version of the DOCX focused
  on key risks, scores, and the Phase 1 summary. No per-finding detail.
- **Anonymous benchmarking** — opt-in submission of score data (no PII, no school name) to
  build an aggregate benchmark database. Allow schools to see how they compare to similar
  institutions by size or type.
- **Score change delta report** — when a re-assessment is run, produce a diff view showing
  which findings were resolved, which worsened, and how section scores shifted. Requires
  re-assessment tracking (see Operations).

## UI / UX

- **Dark mode toggle** — the UI is already dark-themed; add a light mode option for users who prefer it.
- **Logo upload** — allow school to upload a logo that appears on the DOCX cover page.
- **JS dynamic conditionals** ✓ *Implemented in v0.5.1* — conditions are evaluated
  client-side on every input change. Questions appear and disappear instantly without
  a page reload. Server remains authoritative on save.
- **Archived sessions tab** ✓ *Implemented in v0.6.0* — deprecated sessions are shown in a
  dedicated "Archived" tab on the home page. Sessions can be viewed, restored to the active
  list, exported, or permanently deleted. Previously they were fully hidden with no UI access.
- **Deprecate server-rendered UI** — longer term, replace Flask templates with a modern
  JS frontend (React or HTMX) for a snappier experience.
- **Feature guide / how-to page** — a dedicated in-app page (linked from the home page and
  possibly from a persistent "?" help link) that explains how to use the non-obvious features
  of the app. Priority topics: (1) context notes — what they are, where to find them, and
  why the "download first" gate exists; (2) the amendment log — how to see which answers were
  changed and where the history appears in the DOCX; (3) session export/import — when and why
  to use it; (4) the difference between per-section findings and full assessment findings;
  (5) the phased timeline start date and what happens if you leave it blank. The page should
  be purely static HTML (no database access) and should include short annotated screenshots
  or simple diagrams where helpful. Consider a `/help` route rendering a `help.html` template.

## Scoring & Assessment

- **User-editable score adjustment with mitigating controls** — allow the reviewer to override
  a finding's severity after the fact (e.g. "we fixed this last week, here is the evidence")
  with a required notes field and an audit trail. Different from context notes (v0.6.0), which
  annotate findings without affecting the score. This feature changes the score and requires a
  score_override field with a visible marker in the report. Deferred to v1.5 or later.
- **Module 2, 3…** — expand beyond Module 1 (small private school) to cover other institution
  types: public K-12, higher ed, multi-site districts.
- **Re-assessment tracking** — store multiple assessment snapshots per school and show
  score deltas over time ("you improved Section 7 by 18 points since last review").

## Operations

- **Module 2 phased timeline** ✓ *Implemented in v0.6.0* — the Data Governance DOCX report
  now includes a phased remediation timeline when a start date is supplied on the download
  setup page. The start date field is optional — leaving it blank downloads the report without
  a timeline section. The confusing "leave today's date to skip" instruction has been removed.

- **Rules-in-YAML architecture (target: v0.7.0)** — currently both `rules_engine.py`
  (Module 1, ~1,800 lines) and `rules_engine_dg.py` (Module 2) hardcode all finding logic,
  conditions, severities, actions, and finding IDs in Python, keyed to specific question IDs
  that only exist in their respective modules. This creates two problems: (1) adding a new
  module requires writing a new Python rules engine, not just YAML; (2) the engines can be
  accidentally invoked against the wrong module's answers.

  The target architecture: each module YAML (or a companion `module_N_rules.yaml`) declares
  findings rules as structured data — condition, severity, title, detail, action, effort —
  and a single generic `rules_engine.py` evaluates them against any module's answers. The
  Python engines would be replaced by a generic evaluator and the YAML would be the
  authoritative source of all finding logic.

  Scope estimate: M+ to L. Requires designing a rule DSL expressive enough to cover composite
  findings, suppression chains, cross-question comparisons, and the key-risk grouping logic
  currently in Module 1. Recommend doing Module 1 first as the harder case, then verifying
  Module 2 ports cleanly before retiring the Python engines.

- **Whole-school export / import** — a single "Export School" action that bundles all
  non-deprecated sessions plus the school profile into one JSON file, allowing complete
  migration to a new machine or a full point-in-time backup without touching the SQLite file
  directly.

  Current per-session export (`/session/<id>/export`) produces `export_format:
  school_it_engine_session_v1` and can be re-imported one session at a time. A school-level
  export needs a distinct format key (`school_it_engine_school_v1`) so the import route can
  detect it and iterate.

  Required changes:
  1. **`app.py` — new export route** `/export-school`: calls `get_all_sessions()`, filters
     out deprecated, fetches answers for each via `get_answers()`, and writes a single JSON
     with `{ "export_format": "school_it_engine_school_v1", "school_profile": …,
     "sessions": [ { session, answers }, … ] }`.
  2. **`app.py` — update import route** `/import-session`: detect the new format key and
     loop through the `sessions` array, re-using the existing per-session restore logic for
     each entry. Reject duplicate session IDs the same way the single-session importer does
     (skip with a warning rather than aborting the whole import).
  3. **`home.html` — new button** in the top action bar alongside `⬆ Import`, e.g.
     `⬇ Export School` as a `btn btn-ghost` link. Only render if at least one non-deprecated
     session exists.
  4. **`import_session.html` — update copy** to note that both single-session and whole-school
     export files are accepted.

  No schema changes needed. Scope: S — self-contained to `app.py` and two templates.

- **Email delivery** — send the DOCX directly to a specified address after generation.
- **Module 2 DOCX report** ✓ *Implemented in v0.5.1* — Data Governance Audit now
  generates a full Word document with per-system findings, action plan, and appendix.

- **PDF export** — generate a PDF version in addition to (or instead of) DOCX for easier
  sharing with non-Word users.
- **Multi-user sessions** — allow multiple people to collaborate on the same assessment
  (e.g. IT director fills sections 2–4, principal fills section 1).

---

## Answer Amendment & Change Log

- **Amendment log** ✓ *Implemented in v0.6.0* — when a user returns to a completed section
  and changes an answer, the previous value is written to a new `answer_history` table
  (session_id, question_id, old_raw_answer, old_answer_status, new_raw_answer,
  new_answer_status, changed_at). History is only recorded when the section was already
  marked complete at the time of the save — first-pass saves are not tracked. Revised
  questions show an italic "edited" badge on the section page. Both Module 1 and Module 2
  DOCX reports include an Answer Amendment Log as a new appendix section (Appendix D)
  when any revisions exist.

---

## Finding Context (formerly "Finding Suppression")

- **Finding context notes** ✓ *Implemented in v0.6.0* — reviewers can attach a contextual
  note to any finding after the report has been downloaded at least once (e.g. "Resolved
  June 2025 — MFA enforced via Google Admin"). Notes are stored in a `finding_context` table
  (session_id, finding_id, note, added_at) and appear inline in the finding's box in
  subsequent DOCX downloads as a pale green callout. The "Add note" control is gated on
  `last_exported` — it appears on the Findings page only after the first DOCX download, so
  reviewers annotate findings they have already seen in the report.

  Notes do not affect scores, severity, or finding visibility. They are annotation-only.
  Score adjustment via mitigating controls remains deferred to v1.5.

---

## Partial / Interim Report

- **Draft report generation** ✓ *Implemented in v0.6.0* — both Module 1 and Module 2 DOCX
  reports now carry a DRAFT treatment when not all sections are complete: the cover page shows
  "DRAFT — ASSESSMENT INCOMPLETE" and the Executive Summary opens with a red callout box
  listing the specific incomplete sections. The download button on the Summary page is always
  visible but shows a small italic note ("Assessment not yet complete — report will be marked
  DRAFT") when sections remain unfinished.

---

## Completion Certificate / Cover Letter

- **One-page summary document** — a single-page PDF or DOCX containing school name,
  assessment date, overall score, who completed it, and a count of findings by severity.
  Designed to be handed to a board chair, head of school, or accreditation committee without
  the full technical report. Not yet prioritised — low implementation effort but unclear demand.

---

## Module 3 — Software, Licensing, and Vendor Register (target: v0.7.0)

Module 1 Section 6 is intentionally light on subscription and vendor detail, with a dedicated
module noted as planned. Module 2 captures vendor agreements per-system but does not produce a
managed register the business office can use at renewal time. Module 3 fills that gap.

**Concept:** A structured intake for every subscription and vendor contract the school holds.
One dynamic worksheet per vendor (same pattern as Module 2 per-system sections), covering:

- Vendor name, product/service, and category
- Contract owner (named person, not just "IT")
- Annual cost and billing cycle
- Renewal date and auto-renewal flag
- Student-data flag (yes / no / partial)
- FERPA/COPPA review status if student data is involved
- Support contact and escalation path
- Notes (e.g. in active use, under evaluation, being retired)

**Output:** A formatted vendor register DOCX plus a renewal calendar section — open items
sorted by renewal date, flagged by auto-renewal risk and compliance status. Audience is IT
and the business office jointly.

**Entry point:** A `list_of_items` question at the start ("list your vendors/subscriptions,
one per line") generates the dynamic worksheets — same engine pattern as DG1.3 in Module 2.
No file parsing required; a business manager can paste directly from a spreadsheet column.

### Pre-release requirements for Module 3

Before Module 3 reaches full (non-draft) status, two cross-module features must be
implemented:

1. **Module 2 → Module 3 prefill import** — on first entry into a Module 3 session, the
   user is offered the option to seed the vendor list from a completed Module 2 session. The
   engine reads the system inventory collected in DG1.3 (and any vendor fields captured in
   per-system worksheets) and pre-populates the Module 3 vendor list as a starting point.
   The user can then add, remove, and edit before the dynamic worksheets are generated.
   This is an opt-in step, not automatic — the user must explicitly choose which Module 2
   session to draw from.

2. **Cross-module coverage gap flag** — when a service or system appears in Module 2 (the
   system inventory in DG1.3) but has no corresponding entry in Module 3, or vice versa, the
   engine surfaces a coverage gap notice. This appears:
   - On the Module 3 summary page, as a named list of systems in Module 2 with no vendor
     register entry
   - On the Module 2 summary page (retroactively, if Module 3 exists), as a named list of
     vendors in Module 3 with no corresponding system worksheet
   - In both DOCX reports as an appendix note, not a scored finding

   Matching is fuzzy by design — the user confirms or dismisses each suggested pairing.
   Exact string matching is used as the default; an "unmatched" list is shown for manual
   review rather than attempting automated reconciliation.

---

## Module 4 — Incident Response and Business Continuity Readiness

Planned after Module 3 reaches full status. Module 1 Section 8 covers security controls at a
high level but stops short of asking what happens when something goes wrong.

**Concept:** A structured interview covering:
- Written IR plan existence, owner, and last review date
- Communication chain: who is notified, in what order, by whom (IT, leadership, parents, board)
- Recovery runbooks: do they exist, where are they stored, who can access them offline
- Tabletop exercise history: has the plan ever been tested
- Regulatory notification obligations (state breach notification laws, FERPA breach rules)

**Output:** A readiness assessment with a gap list and a phased action plan for building or
improving IR documentation. High value for accreditation and regulatory purposes.

**Note:** This module will produce a higher proportion of "no / not documented" answers than
Modules 1–3. The UX should frame this positively — each gap is an opportunity, not a failure
— and the action plan should give the school a clear path to first-pass documentation quickly.

---

## Module 5 — Annual IT Health Check (Re-assessment Pulse)

Planned after re-assessment tracking infrastructure is in place (see Scoring & Assessment
above). Not a new topic area — a shorter re-run format that revisits the highest-risk findings
from previous Module 1 and Module 2 sessions.

**Concept:** A 15–20 question pulse check that references the school's prior answers and asks
"has this changed?" for the findings that were rated Urgent or Concern. The user can confirm
no change, record an improvement, or flag a regression. 

**Output:** A delta report — what improved, what regressed, what remains open — designed to
be run annually and handed to a head of school or board alongside the original report. Requires
at least one completed Module 1 session to be useful.

**Architectural dependency:** Requires the session comparison infrastructure described under
"Re-assessment tracking" and "Score change delta report" above. Build those first.

---

## Consultant / MSP Mode

- **Multi-school profiles** — allow a single installation to hold multiple school profiles,
  with sessions tagged to a school_id. A consultant managing several engagements could switch
  contexts without running separate instances. Significant architecture change to `database.py`,
  `app.py`, and all routes. Explicitly out of scope before v1.0.

---

*Last updated: v0.7.1.3 — double-underscore fallback removed from rules_engine_dg.py; canonical key format confirmed clean throughout the app. v0.8 roadmap section added.*

---

## Resolved Decisions Log
*(Items previously listed as deferred — now implemented or closed)*

---

### Report Date — Dual Display ✅ Done (v0.7.2.0)

All three report generators show both assessment date (from `session.last_modified`) and
generation date (`date.today()`). When dates match, a single date is shown. Resolved.

---

### RA-003 Full Implementation — Key Risk Group Assembly ✅ Done (v0.7.5.0)

`build_key_risk_groups()` now fully implements RA-003:
- Group titles and contributing finding IDs correct per schema
- Severity aggregated to highest among fired findings
- Mandatory F2-C01 first ordering enforced in `_key_risks()` sort (RA-002)
- "Rated Urgent because: \<title\> (\<fid\>)" narrative rendered in urgent group boxes
- Assessment Overview shows accurate absorbed-findings count linked to Appendix A

---

### Notes Passthrough — Targeted (DG2.10 and VR2.10) ✅ Done (v0.7.4.0)

Two specific high-value passthrough points implemented:
- **Module 2:** `DG2.10` free-text quoted in a callout box at the end of the Executive Summary
- **Module 3:** `VR2.10` free-text quoted in a callout box after the Renewal Risk Register table

Full global notes passthrough (R3-026, R9-006, RA-006) remains future work.

---

### Schema-Driven Appendix Labels — Module 1 ✅ Done (v0.7.4.0, path fixed v0.7.5.1)

`get_question_label()` in `report_generator.py` reads prompts from `modules/module_1.yaml`
at import time and uses them in the Appendix C response log. Hardcoded `QUESTION_PROMPTS`
dict retained as a fallback with a log warning. Path bug fixed in v0.7.5.1.

---

### VR-S4 Core Category List Moved to YAML ✅ Done (v0.7.3.0)

`core_vendor_categories` moved from a hardcoded set in `rules_engine_vr.py` to
`module_3.yaml`. Adding a new core category now requires only a YAML edit.

---

### Critical Floor Rules — Modules 2 and 3 ✅ Done (v0.7.6.0)

`FloorCap` dataclass and `critical_floor_check()` added to `rules_engine_dg.py` and
`rules_engine_vr.py`. Six floor conditions total (three per module). Grade cap applied
after weighted average; red callout box rendered in DOCX exec summary when triggered.
`rules_engine_vr.py` formalised as a fully standalone file in this release.

---

### Module 3 Criticality-Weighted Scoring ✅ Done (v0.7.7.0)

Four-tier multiplier (4×/3×/2×/1×) based on core-category flag and student/staff data
flags. Weight stored on `VendorResult.weight_multiplier`. Shown in per-vendor scorecard
when above baseline. Annual spend tier weighting deferred — requires free-text cost
parsing not yet implemented.

---

### Score Contribution Table in Module 1 DOCX ✅ Done (v0.7.3.1)

"Score Breakdown by Section" table added to the Module 1 executive summary, showing
section weight, section score, and weighted contribution. Sections 1 and 10 shown as
"Context only — not scored."

---

### Per-Section Data Quality Annotations — R10-007

**Current state:** A single global confidence caveat is shown in the Executive Summary.
Per-section annotation (individual findings flagged when the respondent reported low
confidence for that section) is not yet implemented.

**Implementation effort:** S+ (~1 day). Still a future item — not yet scheduled.

---

## Deferred from v0.7.1 Assessment Quality Review

The following items were identified during a structured review of the Module 1 and Module 2 report outputs against the design documents and rule schema. They are intentionally deferred — each is understood, scoped, and documented here for a future sprint.

---

### RA-003 Full Implementation — Key Risk Group Assembly

**Current state (v0.7.1):** `build_key_risk_groups()` in `rules_engine.py` implements RA-003 Option A only. Group titles and contributing finding IDs are correct per the schema. Severity is aggregated to the highest among fired findings.

**What is missing:**
- **Mandatory ordering** — RA-002 requires F2-C01 to be the absolute first entry in the Key Risks section if it fires. Not yet enforced; groups are currently sorted by severity only.
- **Composite severity aggregation** — RA-003 defines specific urgent trigger conditions per group (e.g., Group B is urgent if any of F2-C02, F7-012, F3-C02, F6-C02, F9-C01, or F9-005 fires). The trigger sets are already defined in `urgent_triggers` but the composite aggregation narrative is not rendered as a distinct block.
- **Absorbed findings appendix** — when a composite finding fires and suppresses its component findings, the suppressed findings should appear in a dedicated appendix section ("Findings absorbed into composites") rather than disappearing silently. The suppression count in the Assessment Overview currently reads "0 absorbed" in many cases because composite trigger conditions are not all met on typical assessments; this needs a separate trace pass before implementation.

**Implementation effort:** M+ (5 days). Requires changes to `rules_engine.py`, `report_generator.py`, and a new appendix section function.

---

### Notes Passthrough — User Text Quoted in Finding Descriptions

**Rule references:** R3-026, R9-006, RA-006 (F6-007, F9-006, and others with a notes passthrough requirement in the rule schema).

**What is required:** When a user types notes into a question that has a notes passthrough rule, that text must appear verbatim in the generated finding description — e.g., "IT person noted: 'Only Sarah knows the firewall config.'" This makes the report traceable to the actual assessment conversation rather than relying entirely on static template text.

**Current state:** All finding descriptions use static template text. The `notes_passthrough` field is referenced in the Priority Findings box renderer in `report_generator.py` but is not populated by the rules engine for any rule.

**Implementation effort:** M (3 days). Requires adding a `notes_passthrough` field population step in each affected rule in `rules_engine.py`, keyed to the specific question IDs listed in the rule schema under RA-006.

---

### Per-Section Data Quality Annotations — R10-007

**What is required:** When question 10.8 identifies specific sections where the respondent had low confidence, those sections' findings should each receive an inline uncertainty annotation — a sentence noting that the answers for this section were self-reported as estimated or uncertain.

**Current state:** A single global data confidence caveat is shown in the Executive Summary (the `confidence_caveat` field in report metadata). The per-section annotation step described in R10-007 is not implemented. Individual findings do not carry an evidence or confidence qualifier.

**Implementation effort:** S+ (1 day). The section IDs from question 10.8 are already retrieved in `get_section_10_metadata()`. The annotation would be applied in `report_generator.py` when rendering per-section findings, checking whether the finding's section is in the uncertain list.

---

### Report Date — Dual Display (Assessment Date + Generation Date)

**What is required:** The report currently shows the generation date (today's date when the DOCX is produced). A future version should show both the date the assessment was conducted (derived from the session's `last_modified` or `created_on` timestamp) and the date the report was generated, so a report produced months after the assessment is not mistaken for a current snapshot.

**Current state:** `date.today().isoformat()` is used as `report_date` in `generate_report()` in `report_generator.py`. The session timestamps are available in the database but not passed through to the report builder.

**Implementation effort:** S (½ day). Pass the session's `last_modified` date into `generate_report()` and display both dates on the cover page and in the report footer.

---

## Module 3 — Design Decisions Resolved in v0.7.2

The following items were open questions as of v0.7.1. All four have been resolved and
implemented. They are retained here as a decision log.

---

### M3-Q1 — Three questions with YAML point values (resolved v0.7.2)

- **`V.COST.amount`** → Set to 0 points. Context metadata only. Used as a conditional
  severity escalator: if a vendor is unbudgeted and annual cost ≥ $5,000, the budget
  finding escalates from Medium to High. No direct scoring.
- **`V.RENEW.notice`** → Kept at 2 points. Finding rule VR-R6 added: if auto-renews and
  notice period is Unknown or not specified in contract → Medium finding.
- **`V.SUPPORT.escalation`** → Kept at 2 points. Finding rule VR-S4 added: if vendor
  category matches core/critical categories and escalation path is not documented → Medium
  finding. Non-critical vendors produce no finding for this question.

### M3-Q2 — VR2.3 spend threshold policy (resolved v0.7.2)

Finding rule added. No policy → Medium/Concern school-wide finding about shadow IT risk.
Informal policy → Low finding noting the policy is understood but not written down.

---

## Module 2 — Scoring Calibration (intentional design decision, v0.7.2)

**Decision:** The Module 2 scoring model is intentionally calibrated toward governance rigor
rather than operational maturity. A reasonably well-managed system (e.g. Google Workspace
with MFA partial, backup vendor-managed, no formal DPA review) will score in the 65–70%
range (Watch/C). This is correct and intentional.

**Rationale:** Module 2 is a data governance audit, not an operational health check. The
scoring reflects contractual and compliance posture — not how well the tool works day-to-day.
A school can have a fully functional Google Workspace and still have real governance gaps
(no DPA, backup restore never tested, audit logs not reviewed) that warrant a Watch rating.

**This decision should not be revisited** unless the module's stated purpose changes from
governance rigor to operational maturity scoring.

---

## Roadmap: v0.8 and Path to v1.0

*Agreed plan following the post-v0.7 multi-reviewer audit. Supersedes the two AI-generated
roadmaps produced during that review (both are preserved in the session summary document).
Where this plan diverges from those roadmaps, this document is authoritative.*

---

### What we are not doing, and why

**The double-underscore key normalization refactor is fully resolved as of v0.7.1.3.**

Two external reviewers both pushed hard for centralizing the `DG_SYS_1_SYS.1.3` vs
`DG_SYS_1__SYS.1.3` key format into a canonical normalization layer at ingestion. Here
is the actual situation and what was done:

- `dynamic_engine.py` has always written keys in single-underscore format
  (`DG_SYS_1_SYS.1.3`). One canonical format, consistently, everywhere.
- The only remnant of the old double-underscore format was a two-line `or` fallback in
  `_get()` and `_answered()` in `rules_engine_dg.py`. No separate compatibility layer,
  no migration system — just two `or` chains.
- The test JSONs were regenerated in the correct single-underscore format in v0.7.1.
  No user data in the old format exists.
- In v0.7.1.3 those two fallback lines were removed and the comment updated to document
  the canonical format. Syntax verified clean.

**This issue is fully closed.** No further normalization work is needed unless a new module
introduces a third dynamic worksheet pattern with a different key convention — in which case,
revisit then.

The larger refactor the reviewers recommended (ingestion-layer normalization, validation
reports, per-import debug summaries) is not warranted for a single-machine, single-operator
localhost application. The app has one canonical format and all parts of it use that format.

---

### Tier 1 — Quick Wins, High Credibility

All Tier 1 items are complete.

#### 1. Dual date display on all report covers ✅ Done (v0.7.2.0)

Both assessment date and generation date shown on all three report covers and footers.
Single date shown when both are the same day.

---

#### 2. Section-by-section score contribution table in Module 1 DOCX ✅ Done (v0.7.3.1)

"Score Breakdown by Section" table in the Module 1 executive summary. Sections 1 and 10
shown as "Context only — not scored." Totals row confirms 100% weight sum.

---

#### 3. Move VR-S4 core category list from Python to YAML ✅ Done (v0.7.3.0)

`core_vendor_categories` key added to `module_3.yaml`. Adding a new core vendor category
now requires only a YAML edit, not a Python change.

---

### Tier 2 — Framework Integrity

These should be done before adding any new module or major feature.

#### 4. RA-003 full implementation ✅ Done (v0.7.5.0)

All three sub-items implemented:
- Mandatory `F2-C01` first ordering when it fires — enforced in `_key_risks()` sort
- Composite severity aggregation narrative — "Rated Urgent because: <title> (<fid>)" line rendered in each urgent Key Risk group box
- Assessment Overview suppression count — replaces the previous "not yet enabled" note with an accurate count of absorbed findings, linking to Appendix A

---

#### 5. Notes passthrough — targeted, not global ✅ Done (v0.7.4.0)

- **Module 2:** `DG2.10` quoted in a callout box at the end of the Executive Summary
- **Module 3:** `VR2.10` quoted in a callout box after the Renewal Risk Register table

Full global notes passthrough (R3-026, R9-006, RA-006) remains future work.

---

#### 6. Schema-driven appendix labels in Module 1 ✅ Done (v0.7.4.0, path fixed v0.7.5.1)

`get_question_label()` reads prompts from `modules/module_1.yaml` at import time.
Hardcoded `QUESTION_PROMPTS` dict retained as a fallback with a log warning.

---

### Tier 3 — Scoring Credibility

Important for report trustworthiness, but not urgent for day-to-day use.

#### 7. Critical floor rules for Modules 2 and 3 ✅ Done (v0.7.6.0)

`critical_floor_check()` added to both `rules_engine_dg.py` and `rules_engine_vr.py`.
Three floor conditions per module; any one caps the overall grade at D. Floor cap is
applied after the weighted average and displayed as a red callout box in the DOCX
executive summary. See README v0.7.6.0 entry for full condition list.

---

#### 8. Module 3 sensitivity-weighted scoring ✅ Done (v0.7.7.0)

Four-tier criticality multiplier (1×/2×/3×/4×) replaces the simple average in
`evaluate_vr()`. Weight is pre-computed per vendor and stored on `VendorResult.weight_multiplier`
for reporting use. Per-vendor scorecard in DOCX shows the multiplier when above 1×.
Annual spend tier and auto-renewal weighting factors deferred to a future pass (requires
robust free-text cost parsing).

---

### Tier 4 — Testing and Traceability

Good to have. Do these after the Tier 1–3 items are stable, and before adding a new module.

#### 9. Rule evaluation trace / debug output ✅ Done (v0.7.7.1)

An optional `FLASK_DEBUG_TRACE=1` env var that writes a sidecar JSON file to
`data/traces/` alongside each DOCX report generation. Implemented in `trace.py`
with three entry points: `write_trace_m1()`, `write_trace_dg()`, `write_trace_vr()`.
Called from all three download routes in `app.py` — safe to call unconditionally,
trace write failures never abort report generation.

The trace captures: normalized answers (raw → normalized token → DB status) for
every question; all fired findings with finding ID/key, severity, source section/
system/vendor; suppressed findings (Module 1) with suppression reason; score
calculation detail (per-section/system/vendor earned/max, weighted overall);
floor cap detail when triggered; key risk groups (Module 1); and the renewal risk
register (Module 3). Each file is named `{session_id[:8]}_{module}_{timestamp}.json`.

To enable: set the env var before starting the app:
```
FLASK_DEBUG_TRACE=1 python app.py
```

---

#### 10. Golden test fixtures ✅ Done (v0.8.0)

Three fixture schools per module implemented in `test_scoring.py` (Part B):

- **Strong** — Exemplar Academy / single well-governed system/vendor. Confirms no false
  positives on healthy answers. All three modules produce A grades with no findings and
  no floor caps.
- **Typical** — Bit-By-Bit Academy (existing test data exports). Pins 58 specific Module 1
  finding IDs, Module 2's F grade with floor cap and 6 school-wide findings, and Module 3's
  D grade with 4 urgent vendors and 8 school-wide findings.
- **High-Risk** — Risk Academy / one catastrophically failing system/vendor with all
  school-wide gaps answered worst-case. Confirms floor cap rules fire, critical findings
  appear, and suppression chains work correctly.

The suite runs in under 5 seconds: `python test_scoring.py` (84 tests, all modules).
Assertions are against rules engine output directly — no DOCX inspection required.

---

### What is explicitly deferred past v1.0

- Full rules-in-YAML migration for all modules (valuable long-term; not a v1.0 blocker)
- Module 4 (IR and Business Continuity) and Module 5 (Annual Health Check)
- Executive / board-facing report variant
- PDF export
- Multi-user / shared sessions
- Anonymous benchmarking (requires server infrastructure)
- Full global notes passthrough (R3-026, R9-006, RA-006)
- Re-assessment tracking and score delta reports

---

### Suggested version increments

| Version | Focus |
|---------|-------|
| v0.7.1.x | Bug fixes and doc-only patches ✅ |
| v0.8.0 | Tier 1 quick wins complete ✅ |
| v0.8.5 | Tier 2 framework integrity complete ✅ |
| v0.9.0 | Tier 3 scoring credibility complete ✅ (reached v0.7.7.0) |
| v0.7.8.0 | Tier 4 #9 — rule evaluation trace ✅ |
| v0.8.0 | Tier 4 complete — testing and traceability ✅ |
| v1.0.0 | Final polish, docs aligned, demo-ready |

---
