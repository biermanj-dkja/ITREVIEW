# School IT Documentation Engine
## v0.9.0.1

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.
The format of this tool is structured interview → written documentation → prioritized action plan.

---
If you're the IT director — or the person who ended up being the IT director — at a small private school, you already know the situation. You're managing devices, vendors, accounts, backups, and security for an entire institution, often without a team, a budget line for assessments, or a consultant you can actually afford. When someone asks "how are we doing on IT?", the honest answer is usually somewhere between "better than last year" and "I'm not totally sure."
This tool is built for that gap. It walks you through a structured assessment of your school's IT environment — network, devices, identity management, backups, security, data governance — and produces a prioritized findings report and a phased action plan as a Word document you can share with your head of school or board. The whole thing runs locally on your computer. Nothing is sent anywhere.
---

### What's new in v0.9.0.1

**P2-H1 — Inventory reorder warning**
When the number of items in the system/vendor inventory list diverges from the number of generated worksheets (e.g. after inserting or removing an item), a prominent warning banner now appears at the top of that section. Worksheet answers are keyed by position, so reordering the list after worksheets are filled risks misattributing answers to the wrong system or vendor. The warning explains the risk and how to rebuild cleanly.

**P2-H2 — Context-note IDs now use `rule_id` consistently**
DG and VR finding context notes are now keyed as `{scope_id}:{rule_id}` (e.g. `DG_SYS_3:ac_mfa_not_enabled`, `VR2:vg_no_password_manager`) in both the report-card templates and the DOCX generators. The previous area-prefix + loop-index scheme could attach notes to the wrong finding when findings were added, removed, or reordered. The stable `rule_id` slug is always used; the old format is retained as a fallback only when `rule_id` is absent. School-wide DG findings now also render context notes in the DOCX (this path was previously missing).

**P2-H3 — Cross-section conditional questions render correctly on first load**
Question `7.4` ("Do backups cover servers?") depends on question `6.13` (server count) from a different section. Previously the client-side JS couldn't find `6.13` in the current section DOM and would hide `7.4` even when it should be shown. The server now embeds a `CONDITION_VALUES` dict for all cross-section dependencies; `getFieldValue()` falls back to this dict when the field is not present in the current page.

**P2-H4 — "Save & Exit" now saves before navigating home**
The "← Save & Exit" link has been changed to a form submit button (`action=save_exit`). Clicking it now saves the current section's answers before redirecting to the home page — previously it was a plain anchor that silently discarded any unsaved input. Sidebar section-navigation links also now prompt for confirmation if the form has been edited since the last save.

**P2-M1 — Context-note forms no longer require a prior export**
Context notes on findings (DG and VR report cards) are now always visible — the previous `last_exported` gate that hid them until after a first download has been removed. Notes can be added, edited, or removed at any time and will be included in the next DOCX download.

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

**v0.8.9.0** is a security and housekeeping release.

### F1 — CSRF protection for all POST routes (`app.py`, all templates)

Every state-changing POST form now carries a signed `_csrf_token` hidden field. A
`before_request` hook in `app.py` validates the token on every POST, PUT, PATCH, and DELETE
request and returns HTTP 400 on mismatch. The token is generated with `hmac` + `sha256` keyed
to the Flask session secret, stored server-side in the signed session cookie, and exposed to
templates via a `csrf_token()` Jinja global. All 16 POST forms across the 10 HTML templates
have been updated.

### F2 — `datetime.utcnow()` deprecation warnings resolved (`database.py`, `trace.py`, `app.py`)

Python 3.12 deprecated `datetime.utcnow()`. All 15 call sites across the three files have
been replaced with `datetime.now(timezone.utc)`, which produces identical ISO-format strings
and eliminates the deprecation warnings that appeared in pytest output.

### F3 — Stale version strings removed from source file headers (`rules_engine_dg.py`, `rules_engine_vr.py`, `trace.py`, `rules_engine.py`)

Four source files carried inline version numbers (`v0.5.2.1`, `v0.7.7.0`, `v0.7.7.1`,
`Schema version: 0.2`) that had not been updated since their original authoring and were
misleading. These lines have been removed. The application version is authoritative in
`app.config['VERSION']` and `README.md` only.

### F4 — `test_scoring.py` comment corrected (`test_scoring.py`)

The comment above the database isolation block incorrectly stated that `database.py` reads a
`DB_PATH_OVERRIDE` environment variable. That env var does not exist in `database.py` — the
test works by directly patching `database.DB_PATH` before any DB call runs. The comment and
the now-redundant `os.environ` line have both been corrected.

**Files changed:** `app.py`, `database.py`, `trace.py`, `rules_engine.py`, `rules_engine_dg.py`,
`rules_engine_vr.py`, `test_scoring.py`, `home.html`, `section.html`, `setup.html`,
`findings.html`, `dg_report.html`, `vr_report.html`, `report_setup.html`,
`dg_report_setup.html`, `vr_report_setup.html`, `import_session.html`, `manage_session.html`,
`README.md`, `CHANGELOG.md`


## Known limitations in this version

- Follow-up questions appear and disappear live as you answer — no Save Progress required for question visibility. Questions with a **Save Progress ↓** button still need a server round-trip for actions that generate new content (e.g. the system worksheets in Module 2 DG1).
- Module 2 per-system worksheets are generated after saving Section DG1; if you add systems to the inventory later, return to DG1 and save again to regenerate.
- Logo/crest file upload is not yet implemented.
- Module 1 Sections 1 and 10 generate no findings (context only by design).
- Archived (deprecated) sessions are accessible via the Archived tab on the home page. They can be restored, exported, or permanently deleted from there.
- Composite findings absorb their component findings — absorbed findings are listed in Appendix A of the Module 1 report for traceability.