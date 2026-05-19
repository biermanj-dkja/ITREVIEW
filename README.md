# School IT Documentation Engine
## v0.7.3.1

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.
The format of this tool is structured interview → written documentation → prioritized action plan.

---
If you're the IT director — or the person who ended up being the IT director — at a small private school, you already know the situation. You're managing devices, vendors, accounts, backups, and security for an entire institution, often without a team, a budget line for assessments, or a consultant you can actually afford. When someone asks "how are we doing on IT?", the honest answer is usually somewhere between "better than last year" and "I'm not totally sure."
This tool is built for that gap. It walks you through a structured assessment of your school's IT environment — network, devices, identity management, backups, security, data governance — and produces a prioritized findings report and a phased action plan as a Word document you can share with your head of school or board. The whole thing runs locally on your computer. Nothing is sent anywhere.
---

## Requirements

- Python 3.10 or higher

See [Pre-Setup](#pre-setup) below if Python is not already on your machine.
Node.js is **not required** — the DOCX report is generated entirely within Python.

---

## Pre-Setup

This step installs Python on your machine. You only need to do it once.

### 1. Install Python

1. Go to **https://www.python.org/downloads**
2. Click the yellow **Download Python** button — it will offer the correct
   version for your operating system automatically
3. Run the installer
4. **Windows users:** On the first screen of the installer, check the box
   that says **"Add Python to PATH"** before clicking Install Now.
   If you miss this step, Python will not be recognised as a command in
   your terminal.
5. **Close and reopen your terminal** after installation
6. Verify the installation worked:

```bash
python --version
```

This should print a version number of 3.10 or higher. On some Mac systems
the command is `python3 --version` instead.

---

## Setup

These steps set up the project itself. Run them once when you first install
the tool, and again if you move it to a new machine.

### 1. Create a virtual environment

A virtual environment keeps the tool's Python dependencies separate from
the rest of your machine.

```bash
python -m venv venv
```

Activate it:

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your terminal prompt
when the virtual environment is active.

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

### 4. Open in your browser

```
http://127.0.0.1:5000
```

**Note for Mac users:** If `localhost` does not work in your browser,
use `http://127.0.0.1:5000` instead — they point to the same place.

You will see a persistent banner confirming:
**"This tool runs entirely on your computer. No data is sent to the internet."**

---

## Stopping the application

Press `Ctrl+C` in the terminal window where the app is running.

To exit the virtual environment when you are done:

```bash
deactivate
```

---

## Modules

The engine runs three independent assessment modules. Each produces its own
findings and report. You start a separate session for each one.

**Recommended order:** Start with the **IT Assessment (Module 1)** to get a broad picture of your environment, then the **Vendor Register (Module 3)** to build your complete system and subscription inventory, then use that inventory as your starting point for the **Data Governance Audit (Module 2)**. If you already know your environment well, any module works as a standalone starting point.

### Module 1 — IT State of the System

A full-coverage assessment of the school's IT environment across nine
scored sections. Produces a prioritised findings report and a downloadable
Word document with an executive summary, action plan, and appendix.

| Section | Title | Est. time |
|---------|-------|-----------|
| 1 | School Identity, Profile, and Context | 3 min |
| 2 | IT Staffing and Governance | 5 min |
| 3 | Network and Infrastructure | 5 min |
| 4 | Identity and Access Management | 5 min |
| 5 | Device Management and Endpoint Health | 5 min |
| 6 | Software, Licensing, and Vendor Management | 5 min |
| 7 | Backup and Recovery | 5 min |
| 8 | Security Controls and Incident Response | 5 min |
| 9 | Documentation and Knowledge Management | 5 min |

**Total: approximately 45-60 minutes** for a complete assessment.

Section scores are rated: **Healthy / Watch / Concern / Urgent**
based on the percentage of available points earned and the number of
unknown answers in critical questions.

---

### Module 2 — Data Governance and Data Flow Audit

A structured audit of every system the school uses — mapping where data
lives, how it flows between systems, who has access, what vendor agreements
govern it, and how it is retained and deleted. Designed to be worked
through collaboratively across IT, department heads, HR, and the business
office.

**How it works:**

1. **Discovery (Section DG1)** — you list every system, platform, and
   service the school uses or has used. This takes 15-20 minutes.
2. **Dynamic worksheet generation** — the engine reads your list and
   automatically creates one per-system worksheet for each entry. If you
   identify 14 systems, 14 worksheets are generated. They appear in the
   navigation sidebar immediately after saving.
3. **Per-system worksheets** — each worksheet covers five areas:

   | Area | What it covers |
   |------|----------------|
   | 1 — Access Control | User roster, MFA, SSO, audit logs, former staff accounts |
   | 2 — Backup & Recovery | Backup ownership, frequency, restore testing, offsite storage |
   | 3 — Data Flows | Inbound and outbound data, automated integrations, encryption |
   | 4 — Vendor & Contract | DPA status, breach notification clauses, deletion on contract end |
   | 5 — Retention & Disposal | Data types held, retention periods, deletion process, decommissioning |

   Each worksheet takes approximately 30 minutes for the IT director's
   portion. Department heads, HR, and the business office contribute
   their sections in parallel — the worksheet is designed to be passed
   between people, with role badges marking who answers what.

4. **School-Wide Governance (Section DG2)** — completed after all
   per-system worksheets are returned. Covers policy, breach response
   plan, software approval process, offboarding, vendor review, and
   staff training.

5. **Data Governance Report Card** — each system receives a letter grade
   (A-F) and a severity rating, with a prioritised list of findings and
   recommended actions. A school-wide summary shows overall governance
   posture.

**Estimated time — baseline with 5 systems discovered in DG1:**

| Phase | Who | Time |
|-------|-----|------|
| DG1 — System Inventory | IT director | 20 min |
| Per-system worksheets × 5 (IT portion) | IT director | 2 hr 30 min |
| Per-system worksheets × 5 (Dept / HR / Business Office) | Multiple people, in parallel | 1–2 hr total |
| DG2 — School-Wide Governance | IT director + leadership | 30 min |
| **Total (IT director)** | | **~3 hr 20 min** |
| **Total (all contributors, elapsed)** | | **~4–5 hr over several days** |

Time scales directly with systems found. Each additional system in DG1 adds
approximately 30 minutes of IT director time and 10–20 minutes across other
contributors. A school with 14 systems should budget 7–8 hours of IT time
spread over several days, plus a two-hour cross-team session for DG2.

---

### Module 3 — Software, Licensing, and Vendor Register

A structured register of every software subscription, licensed application,
and vendor contract the school holds. Maps renewal dates, costs, student-data
obligations, and support contacts into a single managed document. Designed to
be completed jointly by IT and the Business Office.

**How it works:**

1. **Discovery (Section VR1)** — you list every vendor, subscription, and
   licensed tool the school holds, one per line. This takes 10–15 minutes.
2. **Dynamic worksheet generation** — the engine creates one per-vendor
   worksheet for each entry. They appear in the navigation sidebar
   immediately after saving.
3. **Per-vendor worksheets** — each worksheet covers six areas:

   | Area | What it covers |
   |------|----------------|
   | Identification | Category, status, named owner, primary department |
   | Cost & Billing | Annual cost, billing cycle, budget inclusion |
   | Renewal & Contract | Renewal date, auto-renew flag, cancellation notice, signed contract |
   | Support & Access | Support contact, escalation path, admin credentials |
   | Student Data & Compliance | Student/staff data flag, FERPA/COPPA review, DPA status |
   | Usage & Value | Active use, value assessment, notes |

4. **School-Wide Vendor Governance (Section VR2)** — completed after all
   per-vendor worksheets are done. Covers software approval process, contract
   signing authority, spend thresholds, shared password management, renewal
   tracking, offboarding, DPA register, and annual vendor review.

5. **Vendor Register Report Card** — each vendor receives a letter grade
   (A–F) and a severity rating. A renewal risk register lists all vendors
   sorted by renewal risk level. School-wide governance gaps are surfaced
   separately from per-vendor findings.

**Estimated time:**

| Phase | Who | Time |
|-------|-----|------|
| VR1 — Vendor Inventory | IT director + Business Office | 15 min |
| Per-vendor worksheets (10 vendors) | IT + Business Office | ~1 hr 40 min |
| VR2 — School-Wide Governance | IT director + Business Office | 20 min |
| **Total (10 vendors)** | | **~2 hr 15 min** |

Time scales with vendor count. Each additional vendor adds approximately
10 minutes. A school with 25 vendors should budget around 4–5 hours total,
spread across IT and the Business Office in parallel.

---

## First run walkthrough

1. Click **Set Up School Profile** and enter your school name and website
2. From the home screen, select the **New Assessment** tab, then choose:
   - **+ IT Assessment** to start a Module 1 session
   - **+ Vendor Register** to start a Module 3 session
   - **+ Data Governance Audit** to start a Module 2 session
3. Work through each section using the sidebar to navigate
4. Each question shows its **point value** so you know its relative importance
5. Use **Skip this question** or **I don't know the answer** controls as needed
6. **Important:** Hit **Save Progress** after answering questions — some
   follow-up questions only appear after saving. Questions with a
   **Save Progress to reveal follow-up questions** button next to them
   are the ones that trigger additional questions when answered.
   In Module 2, saving the system inventory in Section DG1 generates
   your per-system worksheets.
7. Click **Complete Section** to see your section score and severity label
8. Your progress is saved when you hit Save Progress or Complete Section —
   close the browser after saving and resume anytime
9. Once all sections are complete, the session shows **Inspect** on the
   home page

---

## Generating findings and reports

### Module 1

From the **Summary** screen:

- **Generate Full Findings** — runs the rules engine against your saved
  answers and displays a prioritised list of gaps and recommended actions.
  You can also generate findings for a single section using the
  **Findings** link next to any completed section.
  Findings are generated on demand — re-run any time after updating answers.

- **Download Report (.docx)** — generates and downloads a complete Word
  document containing the cover page, executive summary, key risks,
  section-by-section findings, action plan, and appendix.
  No additional software required — generated entirely within Python.

### Module 2

From the **Summary** screen:

- **View Data Governance Report Card** — shows a per-system grade grid
  (A-F) with score bars, severity labels, and a full prioritised findings
  list covering all systems and school-wide governance gaps.

- **Download Report (.docx)** — generates and downloads a complete Word
  document from the report card screen. Contains: cover page, executive
  summary with system grade table, per-system findings with effort ratings,
  school-wide governance findings, a consolidated action plan grouped by
  area, and a raw answer appendix per system.

### Module 3

From the **Summary** screen:

- **View Vendor Register Report Card** — shows per-vendor grades (A–F),
  a renewal risk register sorted by risk level, vendor category breakdown,
  and school-wide governance findings from Section VR2.

- **Download Report (.docx)** — generates and downloads a complete Word
  document containing: cover page, executive summary, renewal risk register
  table, per-vendor findings, school-wide governance findings, action plan
  grouped by timing bucket, and a raw answer appendix per vendor.

---

## Effort ratings

Findings generated by the engine include an effort rating for each
recommended action. These are t-shirt-size estimates for a single
IT person with normal school access:

| Rating | Estimate | Example |
|--------|----------|---------|
| **S** | Half a day (~4 hours) | Enable MFA on one system, revoke a former staff account |
| **S+** | One day (~8 hours) | Document a process, run a backup restore test |
| **M** | Three days | Implement a password manager, draft a security policy |
| **M+** | Five days | Deploy endpoint protection across a fleet, full access audit |
| **L** | Ten days (~two weeks) | Replace a core system, implement SSO, migrate to a new platform |

Effort ratings reflect implementation time only, not procurement or
decision-making. Some L-rated items involve vendor lead times or budget
approvals that extend the calendar time considerably.

---

## Project structure

```
school_it_engine/
├── app.py                  # Flask application and all routes
├── launcher.py             # Entry point for packaged executables (see BUILD_EXECUTABLE.md)
├── database.py             # SQLite operations (sessions, answers, profile)
├── engine.py               # Module loader, scoring, gate logic, severity labels
├── dynamic_engine.py       # Dynamic section generator for Module 2 per-system worksheets
├── rules_engine.py         # Deterministic findings engine for Module 1
├── rules_engine_dg.py      # Findings engine for Module 2 (data governance)
├── rules_engine_vr.py      # Findings engine for Module 3 (vendor register)
├── report_generator.py     # DOCX report builder for Module 1
├── report_generator_dg.py  # DOCX report builder for Module 2 (data governance)
├── report_generator_vr.py  # DOCX report builder for Module 3 (vendor register)
├── test_scoring.py         # Automated scoring tests
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── BUILD_EXECUTABLE.md     # Instructions for packaging as a standalone .exe / .app
├── modules/
│   ├── module_1.yaml       # IT State of the System — questions, scoring, gate logic
│   ├── module_2.yaml       # Data Governance Audit — discovery, per-system template, governance
│   └── module_3.yaml       # Vendor Register — discovery, per-vendor template, governance
├── templates/
│   ├── base.html           # Base layout, navigation, privacy banner
│   ├── home.html           # Assessment list, new session, resume, inspect, delete
│   ├── setup.html          # School profile setup
│   ├── section.html        # Question answering interface
│   ├── section_complete.html  # Section score reveal
│   ├── summary.html        # Assessment overview, scores, report and findings links
│   ├── findings.html       # Module 1 findings display (full or single-section)
│   ├── dg_report.html      # Module 2 data governance report card
│   └── report_setup.html   # Report download options
└── data/
    └── assessments.db      # SQLite database (created on first run)
```

---

## Data and privacy

All data is stored in `data/assessments.db` on your machine.
Nothing is transmitted over the network.

To back up your data: copy `data/assessments.db` to a safe location.
To start completely fresh: delete `data/assessments.db` and restart.

---

## Distributing to testers without Python

See **`BUILD_EXECUTABLE.md`** in this folder for step-by-step instructions
on packaging the engine as a standalone double-clickable executable
(.exe on Windows, .app on macOS) using PyInstaller.
Testers receive a single file and do not need Python, a terminal,
or any technical setup.

---


## What's in this version

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

## Known limitations in this version

- Follow-up questions appear and disappear live as you answer — no Save Progress required for question visibility. Questions with a **Save Progress ↓** button still need a server round-trip for actions that generate new content (e.g. the system worksheets in Module 2 DG1).
- Module 2 per-system worksheets are generated after saving Section DG1; if you add systems to the inventory later, return to DG1 and save again to regenerate.
- Logo/crest file upload is not yet implemented.
- Module 1 Sections 1 and 10 generate no findings (context only by design).
- Archived (deprecated) sessions are accessible via the Archived tab on the home page. They can be restored, exported, or permanently deleted from there.
- Composite finding suppression is not yet enabled — all findings are listed individually. Full RA-003 implementation is tracked in the roadmap.