# School IT Documentation Engine
## v0.3.0

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.

---

## Requirements

- Python 3.10 or higher
- Node.js 18 or higher (required for DOCX report generation)

Both are free, one-time installs. See Pre-Setup below if either is not
already on your machine.

---

## Pre-Setup

These steps install software on your machine. You only need to do them
once — not every time you use the tool.

### 1. Install Node.js

Node.js is required for DOCX report generation. npm (the Node.js package
manager) comes bundled with it automatically.

1. Go to **https://nodejs.org**
2. Download the **LTS** version (the left button — "Recommended For Most Users")
3. Run the installer with all default settings
4. **Close and reopen your terminal** after installation — the PATH will not
   update in an already-open window
5. Verify the installation worked:

```bash
node --version
npm --version
```

Both commands should print a version number. If either is unrecognised,
close and reopen your terminal and try again.

### 2. Install the docx package for Node.js

```bash
npm install -g docx
```

You only need to do this once per machine.

### 3. Install Python

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

## First run walkthrough

1. Click **Set Up School Profile** and enter your school name and website
2. Click **+ New Assessment** to start a new assessment session
3. Work through each section using the sidebar to navigate
4. Each question shows its **point value** so you know its relative importance
5. Use **Skip this question** or **I don't know the answer** controls as needed
6. **Important:** Hit **Save Progress** after answering questions — some
   follow-up questions only appear after saving. Questions with a
   **Save Progress to reveal follow-up questions** button next to them
   are the ones that trigger additional questions when answered
7. Click **Complete Section** to see your section score and severity label
8. Your progress is saved when you hit Save Progress or Complete Section —
   close the browser after saving and resume anytime
9. Once all sections are complete, the assessment shows **Inspect** on the
   home page. From the summary screen you can generate findings or
   download the full Word report

---

## Generating findings and the report

From the **Summary** screen of any assessment:

- **Generate Full Findings** — runs the rules engine against your saved
  answers and displays a prioritised list of gaps and recommended actions.
  You can also generate findings for a single section using the
  **Findings** link next to any completed section in the score table.
  Findings are generated on demand — re-run any time after updating answers.

- **Download Report (.docx)** — generates and downloads a complete
  Word document containing the cover page, executive summary, key risks,
  section-by-section findings, action plan, and appendix. Requires
  Node.js and the `docx` package (see Pre-Setup above).

---

## Project structure

```
school_it_engine/
├── app.py                  # Flask application and all routes
├── database.py             # SQLite operations (sessions, answers, profile)
├── engine.py               # Module loader, scoring, gate logic, severity labels
├── rules_engine.py         # Deterministic findings engine (all sections)
├── report_generator.py     # Python report assembler (calls report_script.js)
├── report_script.js        # Node.js DOCX builder (requires npm docx package)
├── test_scoring.py         # Automated scoring tests (31 tests)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── modules/
│   └── module_1.yaml       # Question definitions, scoring, gate logic for Module 1
├── templates/
│   ├── base.html           # Base layout, navigation, privacy banner
│   ├── home.html           # Assessment list, new/resume/inspect/delete
│   ├── setup.html          # School profile setup
│   ├── section.html        # Question answering interface
│   ├── section_complete.html  # Section score reveal
│   ├── summary.html        # Assessment overview, scores, findings and report links
│   └── findings.html       # Findings display (full or single-section)
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

## Known limitations in this version

- Follow-up questions appear only after hitting Save Progress (not live —
  JavaScript dynamic loading is planned for a future version)
- Logo/crest file upload is not yet implemented
- Deprecate assessment UI is not yet implemented (the database field exists)
- Section 1 and Section 10 generate no findings (context only by design)
