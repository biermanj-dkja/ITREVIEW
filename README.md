# School IT Documentation Engine
## v0.8.7.2

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
## Known limitations in this version

- Follow-up questions appear and disappear live as you answer — no Save Progress required for question visibility. Questions with a **Save Progress ↓** button still need a server round-trip for actions that generate new content (e.g. the system worksheets in Module 2 DG1).
- Module 2 per-system worksheets are generated after saving Section DG1; if you add systems to the inventory later, return to DG1 and save again to regenerate.
- Logo/crest file upload is not yet implemented.
- Module 1 Sections 1 and 10 generate no findings (context only by design).
- Archived (deprecated) sessions are accessible via the Archived tab on the home page. They can be restored, exported, or permanently deleted from there.
- Composite findings absorb their component findings — absorbed findings are listed in Appendix A of the Module 1 report for traceability.