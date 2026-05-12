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

*Last updated: v0.5.1*
