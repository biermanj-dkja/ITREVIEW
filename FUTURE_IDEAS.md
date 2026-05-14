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

## UI / UX

- **Dark mode toggle** — the UI is already dark-themed; add a light mode option for users who prefer it.
- **Logo upload** — allow school to upload a logo that appears on the DOCX cover page.
- **JS dynamic conditionals** ✓ *Implemented in v0.5.1* — conditions are evaluated
  client-side on every input change. Questions appear and disappear instantly without
  a page reload. Server remains authoritative on save.
- **Deprecate server-rendered UI** — longer term, replace Flask templates with a modern
  JS frontend (React or HTMX) for a snappier experience.

## Scoring & Assessment

- **User-editable score adjustment** — allow the reviewer to override a finding's severity
  after the fact (e.g. "we fixed this last week") with an audit trail.
- **Module 2, 3…** — expand beyond Module 1 (small private school) to cover other institution
  types: public K-12, higher ed, multi-site districts.
- **Re-assessment tracking** — store multiple assessment snapshots per school and show
  score deltas over time ("you improved Section 7 by 18 points since last review").

## Operations

- **Module 2 phased timeline** — extend the phased remediation timeline (currently
  Module 1 only) to the Data Governance DOCX report, using effort ratings already
  assigned to all DG findings.

- **Rules-in-YAML architecture (0.6.0)** — currently both `rules_engine.py` (Module 1,
  ~1,800 lines) and `rules_engine_dg.py` (Module 2) hardcode all finding logic, conditions,
  severities, actions, and finding IDs in Python, keyed to specific question IDs that only
  exist in their respective modules. This creates two problems: (1) adding a new module
  requires writing a new Python rules engine, not just YAML; (2) the engines can be
  accidentally invoked against the wrong module's answers (as happened with the Module 1
  download button appearing on Module 2 summary pages).

  The target architecture: each module YAML (or a companion `module_N_rules.yaml`) declares
  findings rules as structured data — condition, severity, title, detail, action, effort —
  and a single generic `rules_engine.py` evaluates them against any module's answers. The
  Python engines would be replaced by a generic evaluator and the YAML would be the
  authoritative source of all finding logic.

  Scope estimate: M+ to L. Requires designing a rule DSL expressive enough to cover composite
  findings, suppression chains, cross-question comparisons, and the key-risk grouping logic
  currently in Module 1. Recommend doing Module 1 first as the harder case, then verifying
  Module 2 ports cleanly before retiring the Python engines.

- **Email delivery** — send the DOCX directly to a specified address after generation.
- **Module 2 DOCX report** ✓ *Implemented in v0.5.1* — Data Governance Audit now
  generates a full Word document with per-system findings, action plan, and appendix.

- **PDF export** — generate a PDF version in addition to (or instead of) DOCX for easier
  sharing with non-Word users.
- **Multi-user sessions** — allow multiple people to collaborate on the same assessment
  (e.g. IT director fills sections 2–4, principal fills section 1).

---

## Answer Amendment & Change Log

- **Amendment log** — when a user returns to a completed section and changes an answer, record the previous value to an `answer_history` table (session_id, question_id, old_value, old_status, changed_at). Display the amendment log in the report appendix. No meaningful DB bloat risk — each record is kilobytes at most. Snapshot the full answer record on change rather than field-level diffs. Planned for a pre-v1.0 release.

---

## Finding Context (formerly "Finding Suppression")

- **Finding context notes** — allow the reviewer to attach a contextual note to any finding after the report is generated (e.g. "Remediated 2024-06-01 — new vendor in place"). The finding remains in the report but is rendered with the note and a visual "context added" marker. This is different from suppression: findings are never hidden, only annotated. Requires a `finding_context` table (session_id, finding_id, note, added_at) and a UI on the findings page. Planned for a pre-v1.0 release.

---

## Partial / Interim Report

- **Draft report generation** — allow report download before all sections are complete. Incomplete sections would be flagged with a "Not yet assessed" placeholder in the report, and the cover page would be watermarked DRAFT. Useful for sharing interim progress with a head of school or consultant. Planned for a pre-v1.0 release.

---

## Completion Certificate / Cover Letter

- **One-page summary document** — a single-page PDF or DOCX containing school name, assessment date, overall score, who completed it, and a count of findings by severity. Designed to be handed to a board chair, head of school, or accreditation committee without the full technical report. Not yet prioritised — low implementation effort but unclear demand.

---

## Consultant / MSP Mode

- **Multi-school profiles** — allow a single installation to hold multiple school profiles, with sessions tagged to a school_id. A consultant managing several engagements could switch contexts without running separate instances. Significant architecture change to `database.py`, `app.py`, and all routes. Explicitly out of scope before v1.0.

---

*Last updated: v0.5.3*
