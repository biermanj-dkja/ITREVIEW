# Changelog
## School IT Documentation Engine

Full version history for all releases. See [README.md](README.md) for current usage instructions.

---

## Version History

**v0.8.7** is a polish and UX correctness release.

### Dead `is_answered` variable removed (`templates/section.html`)

`is_answered` was defined on line 26 of the `render_question` macro but never referenced anywhere else in the template. The card class was already set by a separate inline ternary on the next line. The variable contained a redundant boolean expression with a misplaced `or` that made it hard to reason about. Since it had no effect on anything, it has been removed entirely along with the misleading comment above it.

### Home page Archived tab no longer overrides active sessions (`templates/home.html`)

The tab default logic had a special case that honoured a stored `'archived'` preference unconditionally — even when the user had active in-progress sessions. A user who last visited the Archived tab would always land there on their next visit, hiding their active work. The logic now only restores the Archived tab when there are no active sessions. If active sessions exist, the user always lands on Saved regardless of their stored preference. The `has_archived` boolean is now passed from Jinja2 to JavaScript the same way `has_sessions` is.

### Manage page now shows session navigation (`app.py`, `templates/manage_session.html`)

The Manage Assessment page (Archive / Export / Delete) had no way to navigate back to the session itself — only a "← Back to Home" link. Users who arrived here from the `⋯ Manage` button had to use the browser back button or the nav bar to return to their work. A session card has been added at the top of the page showing the school name, module, and completion status. For incomplete sessions it shows a "Continue →" button (links to `/resume/`) and a secondary "Summary" ghost button. For complete sessions it shows "View Summary →". The `manage_session` route now computes `is_complete` using the same logic as the summary and home routes, and passes it to the template.

### Stale-report banner on full findings page (`templates/findings.html`)

When a user runs findings after previously downloading a report, and their answers have changed in between, the findings on screen are current (they recompute live) but the downloaded DOCX is now outdated. A banner has been added that appears only when: (1) the full findings view is shown (not per-section), (2) `last_exported` exists, and (3) `sess.last_modified` is newer than `last_exported`. The banner shows both dates, explains that the findings on screen are current, and provides a direct "⬇ Re-download" button linking to the report setup page. No schema changes or new timestamps were needed — both values were already available in the template.

**Files changed:** `app.py`, `templates/section.html`, `templates/home.html`, `templates/manage_session.html`, `templates/findings.html`, `README.md`, `CHANGELOG.md`

---



### Next-section navigation skips template sections (`app.py`)

In `section_complete`, the "Next →" button was found by a simple `sections[i + 1]` index
walk. If dynamic sections expansion had not yet run (i.e. the user had not entered a
system/vendor list yet), the template section — which has `is_template: True` and is not a
real page — could appear as the next destination. The walk now scans forward and stops at
the first section where `is_template` is absent or false, so it safely skips the raw
template and lands on the next real section.

### Modules 2 and 3 report setup pages now require a start date (`app.py`, `templates/dg_report_setup.html`, `templates/vr_report_setup.html`)

The Data Governance and Vendor Register report setup pages previously treated the
remediation start date as optional — submitting without one skipped the phased timeline
section. Module 1 has always required a date. All three modules now behave consistently:

- The date field defaults to today (pre-filled via `value="{{ today }}"`) so most users can
  simply click Generate without touching the field.
- The `min` attribute prevents selecting a date in the past.
- The `required` attribute blocks HTML5 form submission if the field is cleared.
- The route validates server-side and flashes an error if somehow the field arrives empty.
- Labels and help text updated to match the Module 1 pattern (removed "(optional)" qualifier
  and "Leave blank to skip the timeline" instructions).

### Performance and stub notes added to FUTURE_IDEAS.md

Two items from a recent internal review have been documented for future consideration:
the home-page YAML-load performance issue (scales linearly with session count) and the
`save_session_meta`/`get_session_meta` stub functions (currently no-ops; silent data loss
if called expecting persistence).

**Files changed:** `app.py`, `templates/dg_report_setup.html`, `templates/vr_report_setup.html`, `FUTURE_IDEAS.md`, `README.md`, `CHANGELOG.md`

---

 addressing five issues identified in a fourth internal code review.

### `delete_session` now removes all associated rows (`database.py`)

`delete_session()` previously only deleted rows from `answer_record` and `assessment_session`. Rows in `answer_history` (the amendment log) and `finding_context` (reviewer context notes) were orphaned in the database after a permanent delete. These tables had no cascade constraint because SQLite foreign keys are off by default. The function now deletes from all four tables before committing. No user-visible data was lost by this bug — the orphan rows were invisible — but the database grew unboundedly with deleted session debris.

### `findings_full` now evaluates only completed sections (`app.py`)

The full findings route was calling `evaluate_all(…, completed_sections=None)`, which evaluates rules for every section regardless of whether it was completed. An assessment with only sections 2–4 complete would fire rules for sections 5–9 against unanswered questions, generating spurious findings (e.g. "No endpoint protection" when Section 8 was never answered). The route now reads `sections_complete` from the session and passes the list to `evaluate_all`, so only rules for completed sections are evaluated. This matches the behaviour already in place for `download_report`.

### `unarchive_session` route moved to `database.py` (`app.py`, `database.py`)

The `unarchive_session_route` was using `__import__("database").get_db()` and writing SQL directly in `app.py`, bypassing the database layer. A new `unarchive_session(session_id)` function has been added to `database.py` and the route now calls it. This follows the same pattern as `deprecate_session`.

### `import_session` route DB bypasses replaced with `database.py` functions (`app.py`, `database.py`)

Two `__import__("database")` blocks in the `import_session` route were writing SQL directly. Two new functions have been added to `database.py`:

- `restore_session_state(session_id, sections_complete, sections_flagged, status, last_modified)` — restores session header fields while preserving the original `last_modified` from the export.
- `restore_answer_history(session_id, history_records)` — bulk-inserts amendment history records using `INSERT OR IGNORE` for safe re-import. Returns the count of rows written.

The route now calls these functions, removing the last direct-SQL bypasses from `app.py`.

### Missing CSS utility classes added (`templates/base.html`)

The templates used `.mb-12`, `.mb-16`, `.mb-24`, and `.mt-0` in several places, but `base.html` only defined `.mb-4` and `.mb-8`. These classes were silently no-ops — spacing was not applied where expected. The four missing classes have been added to the shared CSS in `base.html`.

**Files changed:** `app.py`, `database.py`, `templates/base.html`, `README.md`, `CHANGELOG.md`

---

**v0.8.4** is a UX correctness release fixing four issues identified in a third external code review.

### Module-specific summary page copy (`templates/summary.html`)

The Findings panel below the section table contained Module 1-specific copy ("You can also generate findings for a single section… use the Section Findings link…") that was shown to all modules. Module 2 and 3 sessions have no section findings links — this text was misleading. The panel now shows module-appropriate text: Module 1 gets the original findings engine description; Module 2 and 3 get a short sentence directing users to their respective report cards.

### "Begin assessment" link fixed for Modules 2 and 3 (`templates/summary.html`)

The empty-state card shown when no sections are complete had a hardcoded link to `/section/1`. Module 2 starts at `DG1` and Module 3 starts at `VR1`, so this link produced a 404 for those modules. The link now uses `module.sections[0].section_id` and always goes to the correct first section.

### Breadcrumb labels corrected throughout (`app.py`)

Two routes — `section_complete()` and `manage_session()` — used a two-branch if/else that defaulted Module 3 to "Data Governance" in the breadcrumb. A `_module_label(mid)` helper has been added and used everywhere breadcrumb labels are set, so all three modules now show their correct name ("IT Assessment", "Data Governance Audit", "Vendor Register") in every breadcrumb context.

### Export/import now preserves finding context notes and answer history (`app.py`)

Session JSON exports now include two additional keys:

- `finding_context` — all reviewer context notes attached to findings (e.g. "Resolved June 2025 — MFA enforced")
- `answer_history` — the full amendment log (previous values, new values, timestamps for all revised answers)

These were previously silently dropped on export, meaning a re-imported session would lose all reviewer annotations and change history. The import route now restores both. The flash message on successful import now lists what was restored (e.g. "164 answers, 3 finding notes, 12 amendment records restored"). Both fields are optional in the JSON — older export files without them import cleanly with no change to existing behaviour.

**Files changed:** `app.py`, `templates/summary.html`, `CHANGELOG.md`, `README.md`

---

**v0.8.3** is a polish and documentation release addressing issues identified in a second external code review.

### Report-card and setup route guards (`app.py`)

Five routes that render or set up module-specific report cards were accessible by any session regardless of module type: `dg_report`, `dg-report-setup`, `vr_report`, `vr-report-setup`, and `report-setup`. Each route now checks `sess.module_id` and redirects with a flash message if the session type does not match. This closes the last gap in the module mismatch guard coverage added in v0.8.2.

### BUILD_EXECUTABLE.md updated (`BUILD_EXECUTABLE.md`)

Steps 2 and 3 previously instructed the builder to manually create `launcher.py` and patch `database.py`. Both files have been in the repository since v0.8.2. The steps are rewritten as confirmation checks, with the full file contents retained as collapsible troubleshooting reference rather than active instructions.

### Test data answer counts corrected (`TESTDATA/README-TESTDATA.md`)

The table listed 160 answers for Module 2 and 312 for Module 3. The actual file counts are 164 and 314 respectively.

### README split into README.md and CHANGELOG.md

The README had grown to ~1,100 lines, most of which was version history. The changelog has been moved to a separate `CHANGELOG.md` file. `README.md` now covers what the tool is, how to run it, what each module does, and known limitations. Full version history lives here in `CHANGELOG.md`.

**Files changed:** `app.py`, `BUILD_EXECUTABLE.md`, `TESTDATA/README-TESTDATA.md`, `README.md`, `CHANGELOG.md` (new)

---

**v0.8.2** is a correctness and beta-readiness release addressing eight issues identified in an external code review.

### Module 3 section ordering fixed (`dynamic_engine.py`)

Per-vendor worksheets in Module 3 were being inserted in the wrong position — after VR2 instead of between VR1 and VR2. Root cause: `expand_dynamic_sections()` hardcoded `DG1` as the split point, which worked for Module 2 but placed all Module 3 worksheets at the end. Fixed by replacing the split logic with position-aware insertion: clones now replace the template section at its exact original position in the YAML order. This fix covers both Module 2 and Module 3 without any module-specific branching.

**Impact:** Navigation, resume behaviour, sidebar ordering, and summary ordering for Module 3 are now correct.

### Completion logic requires all generated sections (`app.py`)

Modules 2 and 3 were considered complete when DG1/VR1, DG2/VR2, and *any one* generated worksheet were marked complete. A school with 13 vendors and only 1 completed vendor worksheet could be treated as finished. All four completion checks (home page, summary page, DG DOCX download, VR DOCX download) now require every generated section ID to be present in `sections_complete`. An assessment with worksheets outstanding correctly shows as incomplete and marks the DOCX as DRAFT.

### Section count shown for dynamic modules (`app.py`)

The home page previously showed no section total for Modules 2 and 3 (the count was set to `None`). It now computes the correct total once the vendor/system list is entered: `2 + len(gen_ids)` (the two fixed sections plus all generated worksheets). A session with 13 vendors shows "5 of 15 sections complete" rather than a blank.

### Findings links restricted to Module 1 (`summary.html`)

The per-section Findings link in the summary table was hidden only for Module 2, meaning Module 3 sessions showed Findings links that routed to the Module 1 findings engine. The condition is now `== 'module_1'` so only IT Assessment sessions show section findings links.

### Report route module guards (`app.py`)

`/report.docx`, `/dg_report.docx`, and `/vr_report.docx` now verify that the session's `module_id` matches the report generator before proceeding. A mismatched request flashes an error and redirects to the session summary rather than attempting to generate a report against the wrong data.

### Executable packaging made reproducible (`database.py`, `launcher.py`)

`database.py` now honours the `SCHOOL_IT_DATA_DIR` environment variable when present, writing the SQLite database next to the executable rather than inside the PyInstaller temp folder (which is deleted on exit). `launcher.py` — the PyInstaller entry point described in `BUILD_EXECUTABLE.md` — is now committed to the repository. These two changes make the packaging guide reproducible without manual patching steps.

### Test data filenames corrected (`README-TESTDATA.md`)

The test data README listed `BitByBit_Academy_module-2_export.json` and `BitByBit_Academy_module-3_export.json`. The actual files are `Bit-By-Bit_Academy_module-2_export_UPDATED.json` and `Bit-By-Bit_Academy_module-3_export_UPDATED.json`. Filenames updated.

### Module 3 roadmap clarified (`FUTURE_IDEAS.md`)

The "pre-release requirements for Module 3" heading previously implied two cross-module features (M2→M3 prefill and coverage gap flag) were blocking v1.0. They are now reclassified as post-v1.0 deferred items with a documented rationale. Module 3 generates correct, complete standalone reports; the cross-module features add convenience but do not affect report accuracy.

**Files changed:** `dynamic_engine.py`, `app.py`, `summary.html`, `database.py`, `launcher.py` (new), `README-TESTDATA.md`, `FUTURE_IDEAS.md`, `README.md`

---

**v0.8.1** is a housekeeping release — no feature changes.

- **SyntaxWarning fix (`report_generator.py`):** A docstring inside `_toc()` contained a
  bare `\o` escape sequence. Python 3.12+ raises a `SyntaxWarning` for this; a future
  version will promote it to a `SyntaxError`. Fixed by escaping to `\\o`.

---

**v0.8.0** adds golden fixture tests — automated regression testing for all three scoring engines.

### Golden fixture tests (`test_scoring.py`)

The existing section-level scoring tests (Part A) have been expanded with a full golden
fixture suite (Part B) covering all three modules. Run with:

```bash
python test_scoring.py                # full suite (84 tests)
python test_scoring.py --fixtures-only # Part B only
python test_scoring.py --scoring-only  # Part A only
```

**Three fixture schools per module:**

| Fixture | School | What it tests |
|---------|--------|---------------|
| Strong | Exemplar Academy | A well-run school. Confirms no false positives on healthy answers. |
| Typical | Bit-By-Bit Academy | The existing test data export. Pins the real-world baseline — any rule change that shifts this school's output will be caught immediately. |
| High-Risk | Risk Academy / Risky SIS | Catastrophic gaps across the board. Confirms every major rule fires correctly under worst-case conditions, including floor cap rules. |

**What each fixture asserts:**

- Module 1: exact finding ID sets at each severity tier, total count, suppressed count,
  data confidence level, and key risk group membership
- Module 2: overall grade, floor cap fired/not, per-system grade, finding counts,
  school-wide finding count, and that critical findings appear at the right severity
- Module 3: overall grade, floor cap fired/not, per-vendor grade and score percentage,
  weight multiplier (4× for core + student data), school-wide finding presence

The Bit-By-Bit Academy fixture for Module 1 pins **58 specific finding IDs** — the exact
set of urgent and concern findings. Any rule change that adds, removes, or reclassifies a
finding will produce a named failure rather than silent drift.

Exit code 0 = all tests passed. Exit code 1 = failures listed by name.
The suite is designed to run in under 5 seconds on any machine with the app dependencies
installed.

**Files changed:** `test_scoring.py`

---

**v0.7.8.0** adds rule evaluation tracing — see that entry below for details.

---

### Rule evaluation trace (`trace.py`)

A new optional mode controlled by the environment variable `FLASK_DEBUG_TRACE=1`. When
enabled, each report download writes a sidecar JSON file to `data/traces/` named
`{session_id[:8]}_{module}_{timestamp}.json`. The trace file is the authoritative debugging
record for a report run — it captures everything the rules engine saw and decided, without
requiring manual DOCX inspection.

**What each trace records:**

- **Normalized answers** — every question in the session: raw value, the normalized token
  the rules engine actually tested against (e.g. `"yes"`, `"partial"`, `"unknown"`), and
  the DB status. This makes it immediately clear why a rule fired or didn't.
- **Fired findings** — every finding that was generated, with its ID/key, severity, source
  section/system/vendor, timing, effort, and owner.
- **Suppressed findings** (Module 1) — findings that fired but were absorbed by a composite,
  with the reason recorded.
- **Score breakdown** — per-section (M1), per-system (M2), or per-vendor (M3) earned/max
  scores and area breakdowns, plus the weighted overall grade calculation.
- **Floor cap detail** — when a critical floor rule triggers, the trace records which
  cap applied, which systems/vendors triggered it, and the finding to resolve.
- **Key risk groups** (Module 1) — the full group membership and severity aggregation
  that drives the Key Risks section of the report.
- **Renewal risk register** (Module 3) — the full register with risk levels and reasons.

To enable tracing, set the env var before starting the app:

```bash
FLASK_DEBUG_TRACE=1 python app.py
```

Trace write failures never abort report generation — if the write fails for any reason,
a warning is printed to the console and the DOCX download proceeds normally.

**Files changed:** `trace.py` (new), `app.py`

---

**v0.7.7.1** is a bug fix and parity release. No scoring changes.

### Bug fixes

- **Import restores original `last_modified`** — the session import route previously
  stamped `last_modified` with the current UTC time, discarding the original value from
  the export file. This caused the dual-date logic on report covers to show only one date
  (since both dates matched). The import now restores the original `last_modified` from
  the export, falling back to the current time only when the field is absent.
- **Module 3 breadcrumb label** — section pages for Module 3 (Vendor Register) were
  labelled "Data Governance" in the breadcrumb. Now correctly labelled "Vendor Register".
- **Context note entry UI — Modules 2 and 3** — the "Add context note" UI was only
  available on the Module 1 full findings page. Modules 2 and 3 report card pages
  (`dg_report.html`, `vr_report.html`) now show the same context note entry UI on every
  finding, gated on `last_exported` as in Module 1.
- **Module 3 DOCX context notes not rendering** — `_finding_box()` in
  `report_generator_vr.py` accepted `finding_contexts` but never looked up or rendered
  the note. Now fixed — context notes appear in the DOCX alongside Module 3 findings.
- **School-wide findings (M3) missing context note support** — `_school_wide_findings()`
  was passing an empty dict to `_finding_box()`. Now correctly forwards `finding_contexts`
  and the `VR2` section ID.

### UX improvement

- **Context note UI more visible** — on the Module 1 full findings page, the "Add context
  note" control was a faint collapsed `<details>` arrow that was easy to miss. It is now
  an open, always-visible dashed card with a heading and explanatory text. Existing notes
  display prominently with a green left border; the edit/remove form stays collapsed behind
  a `<details>` toggle so it does not clutter findings that already have notes.

**Files changed:** `app.py`, `dg_report.html`, `vr_report.html`, `report_generator_vr.py`,
`findings.html`

---

**v0.7.7.0** adds criticality-weighted scoring to the Module 3 (Vendor Register) overall grade.

Previously, the Module 3 overall grade was a simple average across all vendors — a school
with a well-governed SIS and a poorly-governed one had the same overall grade regardless of
which was which. This mirrored an early design limitation that Module 2 had already resolved
in v0.7.2.

The overall grade is now a **criticality-weighted average** using four multiplier tiers:

| Tier | Condition | Weight |
|------|-----------|--------|
| 4× | Core/critical category AND holds student data | Highest — e.g. SIS, identity provider with records |
| 3× | Core/critical category OR holds student data (but not both) | High — e.g. firewall; gradebook app |
| 2× | Holds confidential staff data only | Elevated — e.g. HR system, payroll processor |
| 1× | Everything else | Baseline — e.g. classroom tools, communication apps |

"Core/critical category" is determined by the `core_vendor_categories` list in `module_3.yaml`,
the same list used by the VR-S4 escalation path finding since v0.7.3.0.

The per-vendor scorecard in the DOCX now shows the weight multiplier next to each vendor's
grade line when it is above 1×, so the reader can see which vendors are driving the grade.
The executive summary adds a one-sentence explanation of the weighting method.

The `weight_multiplier` field is stored on `VendorResult` so it is available for future
reporting uses (e.g. a weighted breakdown table) without re-computation.

**Files changed:** `rules_engine_vr.py`, `report_generator_vr.py`, `app.py`

---

**v0.7.6.0** adds critical floor rules to Modules 2 and 3, and creates `rules_engine_vr.py`
as a fully standalone module.

### Critical floor rules

A critical floor caps the overall module grade at D regardless of the weighted average.
This prevents a strong score on routine or low-risk items from obscuring a genuinely
dangerous gap. Three floor conditions are defined for each module; any one is sufficient
to trigger the cap.

**Module 2 (Data Governance) floor conditions:**

- **DG-FLOOR-1:** Any system holding sensitive data has confirmed active accounts belonging
  to former staff — an active breach risk
- **DG-FLOOR-2:** Any sensitive-data system has both MFA and backup controls absent
  simultaneously — no authentication protection and no recovery path
- **DG-FLOOR-3:** Any sensitive-data system has no DPA and no breach notification clause —
  both contractual compliance controls absent at once

**Module 3 (Vendor Register) floor conditions:**

- **VR-FLOOR-1:** Any student-data vendor has both no signed DPA and no FERPA/COPPA
  review — a direct FERPA compliance failure
- **VR-FLOOR-2:** Three or more core or student-data vendors have undocumented admin
  credentials — severe operational continuity risk across multiple critical systems
- **VR-FLOOR-3:** Any core/critical-category vendor scores below 30% — near-complete
  absence of governance for a system the school depends on daily

When a floor fires, both the rules engine and the DOCX report make the cap explicit.
A red callout box appears in the executive summary naming the affected systems/vendors
and the finding to resolve to remove the cap.

### `rules_engine_vr.py` — full standalone implementation

This file previously existed only in local development. It is now fully documented and
included in the repository. It contains all Module 3 finding logic, scoring, the renewal
risk register builder, the school-wide governance findings (VR2 section), and the
`evaluate_vr()` entry point.

**Files changed:** `rules_engine_vr.py` (new), `rules_engine_dg.py`, `report_generator_dg.py`,
`report_generator_vr.py`, `app.py`

---

**v0.7.5.1** was a synchronisation and cleanup release — no new features.

- **YAML path fix (`report_generator.py`):** The schema-driven appendix label lookup
  was looking for `module_1.yaml` in the project root; the file lives in `modules/`.
  Path corrected to `modules/module_1.yaml`. Labels now load from YAML as intended;
  the hardcoded fallback dict is no longer exercised in normal use.

- **Export version metadata (`app.py`):** The session export JSON was embedding a
  hardcoded `engine_version: "0.5.3"` field that had not been updated since v0.5.
  Replaced with `app_version` pulling from `app.config['VERSION']` — one source of
  truth, always current.

- **README Known Limitations (`README.md`):** Removed the stale "composite finding
  suppression is not yet enabled" bullet. RA-003 has been active since v0.7.5.0.
  Replaced with an accurate description of current behaviour.

- **Module 3 schema doc (`module_3_rule_schema_and_scoring_v0_1.md`):** The scoring
  table listed `V.COST.amount` as 3 points. The resolved design decision (v0.7.2) set
  it to 0 points (conditional escalator only). Table updated to reflect this.

- **Test data Florida language (`Bit-By-Bit_Academy_module-2_export_UPDATED.json`):**
  A raw answer for `DG_SYS_1_SYS.5.2` contained Florida-specific retention law
  references, inconsistent with Bit-By-Bit Academy being a California fictional school.
  Replaced with generic jurisdiction-neutral language.

- **FUTURE_IDEAS.md:** Stale "deferred" sections for items that are now implemented
  (RA-003, dual dates, notes passthrough, score contribution table, VR-S4 YAML move)
  replaced with a clean resolved-decisions log. Tier 1 and Tier 2 status updated.

**Files changed:** `report_generator.py`, `app.py`, `README.md`,
`module_3_rule_schema_and_scoring_v0_1.md`,
`Bit-By-Bit_Academy_module-2_export_UPDATED.json`, `FUTURE_IDEAS.md`

---

**v0.7.5.0** completes RA-003 — the Key Risks section is now fully deterministic.

Three sub-items were outstanding. All three are done.

### Mandatory F2-C01 ordering (RA-002)

The group containing finding F2-C01 ("No accountable IT ownership") now always appears
first in the Key Risks section when it fires, regardless of how other groups are sorted
by severity. Previously groups were sorted by severity only, which could push the
ownership finding below others. A dedicated sort key in `_key_risks()` enforces this.

### Composite severity aggregation narrative (RA-003)

When a Key Risk group is escalated to Urgent by one of its defined trigger findings,
the group box now shows a plain-language line explaining why:

> *Rated Urgent because: No backup IT coverage exists (F2-C02)*

Multiple triggers are listed separated by semicolons. The trigger finding IDs and
titles are recorded in `build_key_risk_groups()` in `rules_engine.py` via a new
`urgent_trigger_fired` list on each group dict, and rendered in `report_generator.py`.

### Assessment Overview — accurate suppression count

The Assessment Overview sentence previously ended with an italic disclaimer:
*"Note: composite finding suppression is not yet enabled in this version."*
This was false — suppression has been active since v0.5. The sentence now reads
accurately: *"X component findings absorbed into composite findings (see Appendix A
for traceability)"* — or simply ends with a period when nothing was suppressed.

**Files changed:** `rules_engine.py`, `report_generator.py`, `app.py`,
`FUTURE_IDEAS.md`, `README.md`

---

**v0.7.4.0** delivers two Tier 2 framework improvements: targeted notes passthrough
for Modules 2 and 3, and schema-driven appendix labels for Module 1.

### Notes passthrough — Module 2 (DG2.10) and Module 3 (VR2.10)

The free-text "biggest unresolved concern" fields in both modules are now quoted
prominently in the report rather than only appearing in the appendix.

- **Module 2** (`report_generator_dg.py`): If the respondent answered DG2.10
  ("biggest unresolved data governance concern"), a highlighted callout box
  appears at the end of the Executive Summary, quoting the answer verbatim.
- **Module 3** (`report_generator_vr.py`): If the respondent answered VR2.10
  ("biggest unresolved vendor concern"), a highlighted callout box appears
  immediately after the Renewal Risk Register table, where it sits alongside
  the renewal data it most directly informs.

Both callouts are suppressed when the question was skipped or left blank —
they only appear when the respondent actually wrote something.

### Schema-driven appendix labels — Module 1 (report_generator.py)

The Module 1 DOCX appendix (Appendix C — Full Response Log) previously used a
hardcoded `QUESTION_PROMPTS` dict to display a short label next to each question ID.
Adding or renumbering a question in `module_1.yaml` would silently leave the
appendix showing a blank label for the new question.

The appendix now reads question prompts directly from `module_1.yaml` at import time
via a new `get_question_label()` helper. The helper:
- Builds a lookup from `module_1.yaml` on startup (once, not per-report)
- Falls back to the hardcoded `QUESTION_PROMPTS` dict for any question not found in YAML
- Logs a warning on fallback, making label drift visible in server output
- Is exported so other modules can reuse it if needed

The hardcoded dict is retained as a fallback safety net and will be removed in a
future cleanup pass once the YAML-driven path has been validated.

**Files changed:** `report_generator.py`, `report_generator_dg.py`,
`report_generator_vr.py`, `app.py`, `README.md`

---

**v0.7.3.1** adds a score contribution table to the Module 1 DOCX executive summary.

A new "Score Breakdown by Section" table now appears immediately after the overall
score box, showing exactly how each section contributes to the overall weighted score:

| Column | Contents |
|--------|----------|
| Section | Section number and title |
| Weight | The section's weight in the overall score (e.g. 15%) |
| Section Score | The raw percentage earned in that section |
| Weighted Contribution | Section Score × Weight — what it actually adds to the total |

Sections 1 and 10 appear in the table as "Context only — not scored" so they are
not silently omitted, making clear to the reader that the overall score is built
from Sections 2–9 only. A totals row confirms the 100% weight sum and the final
overall percentage. No scoring logic, rules engine, or other files were changed.

**Files changed:** `report_generator.py`, `app.py`, `README.md`

---

**v0.7.3.0** moves the VR-S4 core vendor category list from hardcoded Python to `module_3.yaml`.

Previously, the list of vendor categories that trigger the VR-S4 escalation path finding
(no escalation contact documented for a core system) was a hardcoded set inside
`rules_engine_vr.py`. Adding or adjusting a category required editing Python source.

The list is now defined under `core_vendor_categories` in `module_3.yaml` and loaded at
evaluation time. To add a new core category, edit the YAML — no Python changes needed.
Behavior and matching logic are unchanged (case-insensitive substring match against the
vendor's category field). The Known Limitations note about this feature is removed.

**Files changed:** `app.py`, `rules_engine_vr.py`, `module_3.yaml`

---

**v0.7.2.0** adds dual date display to all three report covers and footers.

Reports now show both the date the assessment was conducted and the date the report
was generated, so a DOCX produced weeks or months after the session was completed
is not mistaken for a current snapshot.

- **Cover page** — when the two dates differ, the cover shows:
  `Assessment conducted: YYYY-MM-DD` and `Report generated: YYYY-MM-DD` as separate
  lines. When the report is downloaded the same day the session was last saved, only
  a single date is shown (no redundant duplication).
- **Footer** — similarly shows `Assessed: X · Generated: Y` when dates differ, or
  the single date when they match. Module 3 (Vendor Register) also updates its
  header line, which previously included the date.
- The assessment date is derived from `session.last_modified` — the timestamp of the
  most recent answer save in the session. This is the closest available proxy for
  "when the assessment was conducted."

**Files changed:** `app.py`, `report_generator.py`, `report_generator_dg.py`,
`report_generator_vr.py`

---

**v0.7.1.3** is a housekeeping release. One code change, one documentation update.

- **`rules_engine_dg.py`** — removed the legacy double-underscore fallback from `_get()`
  and `_answered()`. The fallback (`answers.get(f"{section_id}__{template_qid}")`) was
  added in v0.7.1 as an emergency patch for sessions exported with an older key format
  (`DG_SYS_1__SYS.1.3`). On review, `dynamic_engine.py` has always written the canonical
  single-underscore format (`DG_SYS_1_SYS.1.3`), the test JSONs were regenerated in
  v0.7.1, and no user data in the old format exists. The fallback was dead code. Removed
  and the comment updated to document the canonical format.
- **`FUTURE_IDEAS.md`** — roadmap section added covering the agreed v0.8 → v1.0 plan,
  including the double-underscore issue resolution and explicit decisions about what is
  and is not being built before v1.0.

No scoring changes. No report changes. No YAML changes.

---

**v0.7.1.2** is a documentation and design-record release. No code changes from v0.7.1.1.
Version string updated to reflect that v0.7.1 and v0.7.1.1 were sequential patch releases.
All design documents are now current as of this release.

---

**v0.7.1.1** adds four new Module 3 finding rules, resolves all open Module 3 design questions,
fixes the Module 2 overall grade calculation, and documents the Module 2 scoring calibration
as an intentional design decision.

### New Module 3 finding rules (`rules_engine_vr.py`)

- **VR-R6 — Cancellation notice window unknown** — fires when a vendor auto-renews and the
  required cancellation notice period is Unknown or not specified in the contract. Medium
  severity, near-term. Schools caught in an auto-renewal without knowing the notice window
  have no reliable way to cancel before committing to another term.

- **VR-S4 — No escalation path for core system vendor** — fires when a vendor's category
  is in the core/critical list (SIS, LMS, Identity Provider, Firewall, VoIP, etc.) and the
  escalation path beyond standard support is not documented. Medium severity, near-term.
  Non-critical vendors produce no finding for this question.

- **VR-R6 cost escalation modifier** — `V.COST.amount` is now used as a conditional severity
  escalator. If a vendor is unbudgeted and the annual cost is $5,000 or more, the existing
  budget finding escalates from Medium/near-term to High/immediate, with the dollar amount
  appended to the finding detail.

- **VR2.3 — No spend threshold policy** — new school-wide finding. If no IT procurement spend
  threshold policy exists, a Medium/Concern finding fires about shadow IT risk. An informal
  policy (understood but not written down) fires a Low finding.

### Module 3 YAML (`module_3.yaml`)

- `V.COST.amount` point value corrected to 0. It was previously assigned 3 points in the YAML
  but was never included in scoring — the point value was misleading. It is now correctly
  documented as financial metadata used to populate the vendor register and as a conditional
  severity modifier.

### Module 2 overall grade — sensitivity-weighted average (`rules_engine_dg.py`)

The Module 2 overall report grade is now a **sensitivity-weighted average** rather than a
simple average of per-system scores. Systems holding higher-sensitivity data carry more
weight, preventing strong scores on low-risk tools from masking failures in the school's
primary data systems.

Multipliers are derived from the data categories recorded in SYS.5.1:
- **3×** — student health records, staff HR records, financial and payment data
- **2×** — student academic records, behavioral records, admissions data, auth credentials
- **1×** — everything else (content filters, logging tools, etc.)

For a typical assessment where the SIS holds health and academic records and scores poorly,
the weighted grade will be substantially lower than the simple average — accurately reflecting
the school's real risk posture rather than averaging it away.

### Module 2 scoring calibration — documented as intentional

The Module 2 scoring model is intentionally calibrated toward governance rigor. A well-managed
system with partial MFA, vendor-managed backups, and no formal DPA review will score in the
Watch/C range. This is correct: Module 2 is a data governance audit, not an operational health
check. This decision is now formally recorded in `FUTURE_IDEAS.md`.

### Report generator (`report_generator.py`)

The "0 findings absorbed into composites (see appendix)" placeholder text has been replaced
with: "Note: composite finding suppression is not yet enabled in this version — all findings
are listed individually." This reads as a versioned design decision rather than a broken counter.

### Documentation

- `module_2_rule_schema_and_scoring_v0_1.md` — updated to document the sensitivity-weighted
  average and mark the simple-average gap as resolved.
- `module_3_rule_schema_and_scoring_v0_1.md` — known gaps table updated to mark all four
  resolved items.
- `FUTURE_IDEAS.md` — M3-Q1 and M3-Q2 open question sections replaced with a resolved
  decision log; Module 2 scoring calibration entry added.

---

**v0.7.1** is an assessment quality and correctness release. It fixes the most significant
report accuracy issues identified in a structured review of the Module 1 and Module 2 outputs
against the design documentation and rule schema.

### Module 2 per-system findings — critical bug fixed (`rules_engine_dg.py`)

Every system was previously scoring 0% / F / urgent with zero findings and the message
"all assessed controls appear to be in place" — a direct contradiction. Root cause: a key
format mismatch between how question IDs were stored in sessions exported from an earlier
build (double-underscore separator: `DG_SYS_1__SYS.1.3`) and how the rules engine looked
them up (single-underscore: `DG_SYS_1_SYS.1.3`). Every answer lookup silently returned
None, producing zero scores and zero findings simultaneously.

Fixed in `_get()` and `_answered()` with a fallback that tries both formats. Per-system
results now correctly evaluate worksheet answers:
- Veracross: 29% / 6 findings / urgent
- Google Workspace: 68% / 4 findings / watch
- Seesaw: 25% / 4 findings / urgent
- Lightspeed Filter: 65% / 2 findings / watch
- Bark for Schools: 65% / 1 finding / watch

### State-specific legal citations removed (`rules_engine_dg.py`, `module_2.yaml`)

All references to Florida FIPA, Florida SDPA, and "Florida law" have been removed from both
the rules engine finding text and the YAML help text. Replaced with generic federal and
applicable-law language (FERPA, COPPA, general best practice). The tool is now legally
accurate for schools in any jurisdiction.

### Module 1 appendix label drift fixed (`report_generator.py`)

The appendix label dictionary was written against an older version of `module_1.yaml` before
the buildings sub-question was inserted at positions 1.9/1.10. This shifted all subsequent
labels by one, causing the appendix to show the right values under wrong headings (e.g. staff
count displayed under "Number of student devices"). Labels for questions 1.8–1.16 now match
the current YAML exactly.

### Overall weighted score added to Module 1 executive summary (`report_generator.py`)

The overall weighted score is now displayed in the executive summary as a coloured score box
showing the numeric percentage, severity band, and a plain-language explanation of how it was
calculated. Sections 2–9 are weighted using the section weight table from the scoring framework
document. Sections 1 and 10 are excluded (context and calibration inputs respectively).

### Severity legend added to Module 2 report (`report_generator_dg.py`)

A legend box has been added at the top of the Per-System Findings section explaining the two
severity scales used in the report: System Status (Urgent/Concern/Watch/Healthy, derived from
score percentage) and Finding Severity (Critical/High/Medium/Low, per individual control gap).
These are two distinct dimensions; the legend makes the distinction explicit for readers.

### Key Risk Groups — RA-003 status documented (`rules_engine.py`)

A clearly labelled comment block has been added above `build_key_risk_groups()` documenting
what is and is not implemented (Option A only: correct titles and finding IDs; severity
aggregation and mandatory ordering not yet implemented). Full RA-003 implementation is tracked
in `FUTURE_IDEAS.md`.

### Design documentation (`FUTURE_IDEAS.md`)

Four deferred items added with full context, current state, and implementation effort estimates:
RA-003 full implementation, Notes Passthrough (R9-006/R3-026), Per-Section Data Quality
Annotations (R10-007), and Report Date dual display.

### New design documents

Three new reference documents added covering all three modules:
- `module_2_rule_schema_and_scoring_v0_1.md` — complete rule schema and scoring weights for
  the Data Governance Audit, derived from the source code.
- `module_3_rule_schema_and_scoring_v0_1.md` — complete rule schema and scoring weights for
  the Vendor Register, derived from the source code.
- `module_1_scoring_weights_v0_1.md` — v0.2 addendum appended, documenting escalation rules
  and composite behaviours added after the original document was written, plus a known gaps
  table for the score display features not yet implemented.

---

adds Module 3 — Software, Licensing, and Vendor Register — and a recommended module order note.

- **Module 3 — Vendor Register** — a structured register of every software subscription, licensed application, and vendor contract the school holds. Uses the same dynamic worksheet pattern as Module 2: list your vendors in the discovery section (VR1), get one worksheet per vendor, complete a school-wide governance section (VR2). Produces a renewal risk register, per-vendor grade cards (A–F), school-wide governance findings, and a DOCX report with action plan.
- **Recommended module order** — the home page and README now include a short guidance note: start with Module 1 (broad IT orientation), then Module 3 (build your complete vendor inventory), then Module 2 (data governance audit using that inventory as your starting point).
- **Version bump** — app version updated to 0.7.0.

---

**v0.6.0** is the first pre-v1.0 feature milestone, completing five features formally committed as pre-release requirements:

- **Archived Sessions tab** — a third tab on the home page shows all archived assessments. They can be viewed, restored to the active list, exported, or permanently deleted. Previously archived sessions were hidden with no way to access them short of re-importing a backup.
- **Module 2 phased timeline** — the Data Governance DOCX now fully supports the phased remediation timeline. The start date field is now optional: leave it blank to skip the timeline. The previous confusing "leave today's date to skip" instruction has been removed.
- **Answer amendment log** — when a user returns to a completed section and changes an answer, the previous value is recorded to a new `answer_history` table. Revised questions show an italic "edited" badge on the section page. A new Appendix D in both Module 1 and Module 2 DOCX reports lists all amendments (question ID, previous value, revised value, timestamp).
- **Finding context notes** — after downloading a report at least once, an "Add context note" control appears under each finding on the Findings page. Notes appear inline in subsequent DOCX downloads. They do not affect scores or severity — they annotate findings for the reader (e.g. "Resolved June 2025 — MFA enforced").
- **Draft report treatment** — when not all sections are complete, both Module 1 and Module 2 DOCX reports carry a "DRAFT — ASSESSMENT INCOMPLETE" marker on the cover page and a red callout box in the Executive Summary listing incomplete sections. The download button always remains visible but shows an italic note when incomplete.

---

**v0.5.3.2** is a UI/UX overhaul pass informed by Material Design principles. No scoring logic, rules engine, or report generator was changed — all changes are in templates and `app.py` routing.

### Home page
- **Tabbed layout** — the home page now has two clearly separated tabs: "New Assessment" (module launcher cards) and "Saved Assessments" (session list). The app defaults to Saved Assessments when sessions exist, New Assessment when none do. The selected tab persists across page reloads via localStorage.
- **Session management page** — Archive and Delete have been moved off the home page session cards and into a dedicated `/session/<id>/manage` page. The card now shows a single "⋯ Manage" button. The manage page presents Archive, Export, and Delete as distinct actions with clear descriptions; Delete uses an inline two-step confirmation rather than a browser `window.confirm()` dialog.
- **Human-readable session labels** — sessions are now identified as "#1 · Started 2025-05-14" rather than a truncated UUID. The label is stable across the session's lifetime and numbered in creation order.
- **Progress bar colours** — in-session section progress bars now use the accent colour throughout and only turn green at 100% completion. Previously the bar started red at 0%, which falsely implied an error state.

### Navigation and wayfinding
- **In-session breadcrumb** — when inside a session (section or summary), the nav bar shows `› IT Assessment › Section 3: Network` so the user always knows where they are. On summary pages, only the module name is shown.
- **Privacy banner scoped to home and setup** — the full "This tool runs entirely on your computer" banner now appears only on the Home and Setup pages where trust matters most. All other pages show a compact `🔒 local` indicator in the nav instead. This prevents banner blindness while preserving the privacy message where it is actually reassuring.

### Section form
- **Unsaved-changes guard** — a `● unsaved changes` indicator appears near the Save button when any answer has been modified since the last save. Clicking a sidebar section link while dirty prompts a confirmation. The browser also fires a standard beforeunload warning.
- **Skip / Unknown micro-copy** — the two checkboxes at the bottom of each question card are now labelled "Skip for now" (with tooltip: temporarily excluded, no scoring impact) vs "I don't know ⚠" (with tooltip: scores zero, may surface a finding). The warning icon on the unknown label signals the difference without adding visual clutter.
- **Point chip tooltips** — hovering a point chip (e.g. `3 pts`, `context`) now shows a tooltip explaining what the value means and how it affects the section score.

### Summary page
- **Section score table severity borders** — each row in the section scores table now has a 3px left border in the section's severity colour (healthy / watch / concern / urgent), making severity scannable without reading the badge text.
- **Findings CTA hierarchy** — "Generate Full Findings" is now a full-width primary button. "Download Report (.docx)" is a secondary button below it with a "view findings first" hint. Previously both were equal-weight side-by-side.

### Section complete page
- **Richer score narrative** — each severity band now shows the actual percentage earned and a 1–2 sentence explanation of what the score means and what to expect next, rather than a single generic status line.

### Accessibility
- **Flash messages** — all flash message divs now carry `role="alert"` and `aria-live="polite"` so screen readers announce them. A ✕ dismiss button is added to each alert.

**v0.5.3** adds three new features to the assessment experience:

- **Section progress bar** — a live counter and progress bar now appear at the top of every section form, showing how many questions have been addressed (answered, unknown, or skipped) vs the total visible in the current section. The bar updates instantly as you work — no save required.
- **Unknowns summary panel** — the Assessment Summary page now includes a dedicated panel listing every question marked *I don't know* across all sections, grouped by section. Each entry links directly back to that section so you can revisit it without hunting through the form. The panel only appears when there are unknowns to review.
- **Export / Import** — a new Export JSON button on the Summary page downloads a complete snapshot of the session (all answers, section status, session metadata, and school profile). Sessions can be restored via the new Import button on the home page. Use this to back up work before switching machines or to hand a session off to someone else.

**v0.5.2.2** is a significant overhaul of the Module 1 report (`report_generator.py`), making it easier to navigate, more honest about what's working, and more actionable. All changes are in `report_generator.py` only — no YAML, rules engine, or other files were modified.

### Table of Contents
- The report now opens with a native Word TOC field on page 2 (after the cover). When the document opens in Word or LibreOffice, right-click the placeholder text and choose "Update Field" to generate the live table of contents with page numbers.
- Headings are now registered as proper Word Heading styles (Heading 1, Heading 2, Heading 3) with `outlineLevel` set in the style definition. This is what allows the TOC field to collect them. The visual appearance is unchanged.

### Executive Summary overhaul
- **Overall health verdict** — a single plain-language sentence appears at the top of the executive summary, giving the reader an honest one-line assessment before any tables. The sentence adapts based on the number and severity of findings.
- **Data confidence callout in the body** — when confidence is moderate or low, a highlighted amber box now appears in the executive summary body. Previously the caveat was only in 7pt footer text that most readers never see.
- **"What's Working" column in the Section Scores table** — the scores table now has a fifth column showing a plain-language status per section (✓ Healthy / Mostly good / Needs work). Sections scoring 85%+ show a green ✓ so the reader can immediately see what's performing well alongside what needs attention. Previously the report only communicated problems.

### Bullet Action Plan removed — Phased Timeline is the single source
- The old "Action Plan" section (actions as bullet points grouped by horizon then section) has been removed entirely. It duplicated the Phased Remediation Timeline that immediately followed it. The timeline is richer (includes effort, severity, dates, and now a Section column) and serves as the only action-planning section.
- The timeline table now has a Section column (§2, §3, etc.) so readers can trace each action back to the relevant section of the report without needing the finding ID.

### Section-by-Section Findings improvements
- **Healthy section markers** — sections that were scored but produced no findings now appear with a green "✓ No findings" box rather than being silently skipped. This confirms to the reader that the section was assessed and is in good shape.
- **Finding ID explained** — the introduction paragraph now notes that finding IDs (e.g. F3-004) are used for cross-referencing in the action plan.
- **Visually distinct box types** — three box types now use clearly different colours:
  - IT person notes (passthrough) → blue (`D6EAF8`)
  - Plain-language / scoring notes → amber (`FEF9E7`)
  - Recommended actions → pale green (`EAFAF1`) with a "Recommended actions:" header in green
  - Previously all three used the same blue and were easy to skim past.
- **Action arrows** — each action line now opens with `→` (or `⚠` for constrained actions) to make them visually distinct from the description text above.

### Key Risks section improvements
- **Primary finding labelled** — each risk group now identifies its primary finding (highest severity, largest effort) with a "← Start here" label. Previously the group just listed finding IDs with no indication of where to begin.
- **Updated intro text** — the section intro now explains the "Start here" label explicitly.

### Appendix improvements
- **Unknown Answer Log promoted and reframed** — the Unknown Answer Log is now Section B (before the full response log, not after). It opens with a highlighted amber callout box explaining that each unknown answer is a gap in IT situational awareness — something the school doesn't currently know about its own environment. Previously it was a small unlabelled list buried after the response log.
- **Question prompts in the Full Response Log** — the response log table now has a "Question" column showing the human-readable prompt for each question ID (e.g. `3.4 | AP location documented? | answered | No`). Previously the log showed only `3.4 | answered | No`, which was unreadable without the YAML schema.

**v0.5.2.1** upgraded the Module 2 (Data Governance) report — see that entry for details.

### Rules engine (`rules_engine_dg.py`)
- **Data categories in finding detail text** — every high/critical finding now states which data types the affected system holds (e.g. "This system holds student health records and financial data"), drawn from SYS.5.1 answers. Findings about unprotected systems now communicate real stakes rather than abstract risk.
- **New findings for audit log gaps** — SYS.1.5 answers of "logs exist but not reviewed" and "no audit logging" now generate low and medium findings respectively. Previously these answers docked points silently with no explanation.
- **New finding for vendor security review** — SYS.4.4 "No — not reviewed" now generates a low finding pointing to SOC 2. Previously this answer docked points with no finding.
- **New findings for retention/deletion gaps** — "Deletion occurs but is not documented" and "No deletion process" now generate low and medium findings respectively.
- **New findings for school-wide gaps** — DG2.3 (no data register), DG2.6 (staff training), DG2.8 (vendor review process) now generate findings. The DG2.3 partial case ("exists but outdated") also now surfaces a low finding.
- **Owner role on every finding** — each finding now carries a suggested responsible role (IT Director, Business Office, HR / IT Director, Head of School) so the action plan can be assigned immediately.
- **Timing buckets** — every finding is tagged `immediate` (do within 30 days), `near_term` (do within 90 days), or `planned` (schedule this year), derived from severity.
- **Per-area score breakdown** — `score_system_section()` now returns area-level earned/max scores for Access Control, Backup & Recovery, Data Flows, Vendor & Contract, and Retention & Disposal.
- **Strength detection** — systems with few or no findings now get a list of specific things that are working well (MFA required, backups tested, DPA on file, etc.) rather than a generic "all good" message.
- **Top priorities** — `DGSummary` now includes a list of the 5 highest-priority findings across all systems and school-wide, for the executive summary.
- **Data-at-risk summary** — a plain-language sentence is generated when concern/urgent systems hold sensitive data categories.
- **Getting Started checklist** — for schools grading C or below with significant school-wide gaps, a new `GettingStarted` object is populated with a five-step checklist and a 15-minute monthly governance ritual, based on the Magic EdTech K-12 data governance framework.

### Report generator (`report_generator_dg.py`)
- **Top Priorities table in executive summary** — up to 5 critical/high findings shown with owner and timing, so leadership can act from page 2 without reading the full report.
- **Data-at-risk callout in executive summary** — flags which sensitive data categories are held by at-risk systems.
- **Per-area score bars** — each per-system section now shows a compact area-by-area breakdown table with a visual bar, making it clear whether weaknesses are in access control, backups, contracts, or elsewhere.
- **Strengths box for passing systems** — systems with no findings now show a green "what's working" box listing specific passing controls, replacing the generic "all clear" message.
- **Action plan restructured into timing buckets** — the action plan is now divided into three sections (Immediate / Near-Term / Planned) with color-coded headers, making it straightforward to prioritise.
- **Owner column in action plan and findings** — every action now shows the suggested responsible role.
- **Timing shown in per-system finding boxes** — each finding's action box now displays Owner · Timing · Effort.
- **Getting Started section** — new report section (shown for grade C and below) with a five-step governance checklist and 15-minute monthly meeting agenda, inspired by the Magic EdTech K-12 governance framework.
- **Appendix now includes question prompt text** — the raw answer log table has a new "Question" column showing the human-readable prompt for each question ID, so the appendix is readable without the YAML schema.
- **Respondent role** — the cover page now pulls `DG1.1b` (respondent role) if present alongside the existing `DG1.1` (respondent name).

**v0.5.2** fixes a collection of Module 2 issues found in first-run testing:
- Sidebar section IDs now show as "1", "Sys 1", "Sys 2", "2" instead of "DG1", "DG_SYS_1", "DG2"
- DG1.2 (inventory date) now autofills with today's date
- DG1.4 (system count) now autofills from the length of the DG1.3 list after saving
- Per-system worksheet description now notes the multi-session time expectation
- SYS.1.1a reworded to plain English: "Do any active accounts belong to people who no longer work at the school?"
- SYS.2.3 and SYS.2.4 (restore test, offsite storage) are now conditional on the school managing the backup — these questions are not answerable when a vendor manages it
- SYS.2.5 splits into two questions: the original RTO question for school-managed backups, and a new continuity-plan question for vendor-managed systems
- SYS.4.2 and SYS.4.3 are now correctly labelled as conditional in the UI
- SYS.3.1 data source count is now checked against total inventory; a school-wide warning finding is raised if any worksheet lists more sources than systems
- Home page "Inspect" vs "Resume" now correctly reflects Module 2 completion (was hardcoded to Module 1's 10-section count)
- Module 2 report card and DOCX no longer surface Module 1 findings links in the summary

**v0.5.1** adds two major features:
- **Module 2 DOCX report** — the Data Governance Audit now generates a full downloadable Word document with cover page, per-system grade cards, findings, action plan with effort ratings, and a raw answer appendix.
- **Live conditional questions** — follow-up questions now appear and disappear instantly as you answer, without requiring a Save Progress round-trip. The server still validates on save; the browser now evaluates conditions client-side for immediate feedback.

**v0.5.0.1** fixes question ID naming consistency across Module 2.

**v0.5.0** adds the Data Governance and Data Flow Audit (Module 2), a
dynamic section engine, and a per-system report card. See the
[Modules](#modules) section below for what each module covers.

---

---
