# School IT Documentation Engine
## v0.5.0.1

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.

---

## What's in this version

**v0.5.0.1** fixes question ID naming consistency across Module 2 — all per-system worksheet questions now use the same numeric scheme as Module 1 (e.g. SYS.1.1, SYS.2.3) rather than the previous lettered scheme (SYS.A1, SYS.B3).

**v0.5.0** adds the Data Governance and Data Flow Audit (Module 2), a
dynamic section engine, and a per-system report card. See the
[Modules](#modules) section below for what each module covers.

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

The engine runs two independent assessment modules. Each produces its own
findings and report. You start a separate session for each one.

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

## First run walkthrough

1. Click **Set Up School Profile** and enter your school name and website
2. From the home screen, choose:
   - **+ IT Assessment** to start a Module 1 session
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
├── report_generator.py     # DOCX report builder using python-docx (pure Python)
├── test_scoring.py         # Automated scoring tests
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── BUILD_EXECUTABLE.md     # Instructions for packaging as a standalone .exe / .app
├── modules/
│   ├── module_1.yaml       # IT State of the System — questions, scoring, gate logic
│   └── module_2.yaml       # Data Governance Audit — discovery, per-system template, governance
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

## Known limitations in this version

- Follow-up questions appear only after hitting Save Progress — conditional
  question visibility is evaluated server-side on each save or page load.
  Questions will not appear or disappear instantly as you type; hit
  Save Progress to reveal any follow-ups. JavaScript live-update of
  conditional questions is planned for a future version.
- Module 2 per-system worksheets are generated after saving Section DG1;
  if you add systems to the inventory later, save again to regenerate
- Logo/crest file upload is not yet implemented
- Deprecate assessment UI is not yet implemented (the database field exists)
- Module 2 does not yet produce a downloadable DOCX — the report card is
  browser-only in this version (DOCX export is planned)
- Module 1 Sections 1 and 10 generate no findings (context only by design)
