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

## Consultant / MSP Mode

- **Multi-school profiles** — allow a single installation to hold multiple school profiles,
  with sessions tagged to a school_id. A consultant managing several engagements could switch
  contexts without running separate instances. Significant architecture change to `database.py`,
  `app.py`, and all routes. Explicitly out of scope before v1.0.

---

*Last updated: v0.6.0*
