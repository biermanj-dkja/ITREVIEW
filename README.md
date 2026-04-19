# School IT Documentation Engine
## Intake Engine — v0.1

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.

---

## What this is

The intake engine presents structured questionnaires to school IT staff,
captures answers with save/resume support, and displays scored results
section by section. This version covers Sections 1 and 2 of Module 1
(School Identity and Governance/Staffing/Ownership).

---

## Requirements

- Python 3.10 or higher
- pip

---

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

### 4. Open in your browser

```
http://localhost:5000
```

You will see a persistent banner confirming:
**"This tool runs entirely on your computer. No data is sent to the internet."**

---

## First run walkthrough

1. Click **Set Up School Profile** and enter your school name and website URL
2. Click **+ New Assessment** to start a new assessment session
3. Work through Section 1 (School Identity) and Section 2 (Governance)
4. Each question shows its **point value** so you know its relative importance
5. Use **Skip this question** or **I don't know the answer** controls as needed
6. Click **Complete Section** to see your section score and severity label
7. Your progress is saved automatically — close the browser and resume anytime

---

## Project structure

```
school_it_engine/
├── app.py              # Flask application and routes
├── database.py         # SQLite operations (sessions, answers, profile)
├── engine.py           # Module loader, condition evaluator, scoring
├── requirements.txt    # Python dependencies
├── modules/
│   └── module_1.yaml   # Question definitions for Module 1
├── templates/
│   ├── base.html       # Base layout with nav and privacy banner
│   ├── home.html       # Session list and start screen
│   ├── setup.html      # School profile setup
│   ├── section.html    # Section questionnaire (main UI)
│   ├── section_complete.html  # Score reveal screen
│   └── summary.html    # Assessment summary
└── data/
    └── assessments.db  # SQLite database (created on first run)
```

---

## Data and privacy

All data is stored in `data/assessments.db` — a local SQLite file on your
machine. Nothing is transmitted over the network. The application only
listens on `localhost` (127.0.0.1) and is not accessible from other devices
on your network.

To back up your assessment data, copy `data/assessments.db` to a safe location.
To start fresh, delete `data/assessments.db` and restart the application.

---

## Current scope (v0.1)

- ✅ School profile setup
- ✅ Assessment session creation and management
- ✅ Save and resume across sessions
- ✅ Section 1: School Identity, Profile, and Context (16 questions)
- ✅ Section 2: Governance, Budget, Staffing, and Ownership (12 questions)
- ✅ Conditional question logic (one level of branching)
- ✅ All answer types: text, count, yes/no, single select, multi-select, list
- ✅ Skip and unknown answer controls
- ✅ Point values displayed during answering
- ✅ Section score revealed on completion (points / max + severity label)
- ✅ Summary screen for completed sections

## Not yet implemented

- Sections 3–10 question definitions
- Deterministic rule engine (findings and actions)
- DOCX report generation
- Charts and visuals
- Section 1 has no scored questions — it is context only

---

## Adding sections

To add more sections, extend `modules/module_1.yaml` following the existing
pattern. Each question needs:

- `question_id` — e.g. `"3.1"`
- `prompt` — the question text
- `answer_type` — one of: `short_text`, `long_text`, `count`, `yes_no_unknown`,
  `single_select`, `multi_select`, `list_of_items`
- `points` — integer 0–5
- `skippable` — `true` (all questions are skippable by default in v0.1)
- `condition` — `null` or a condition object (one level only)
- `options` — list of strings (required for `single_select` and `multi_select`)

---

## Known issues / next steps

- Section 2 max score shown as 36 in the scoring weights document — correct
  value is 32 (the YAML is correct; the document has a typo to fix)
- The rule engine (deterministic findings and actions) is not yet built
- DOCX report generation is not yet built
- Sections 3–10 YAML definitions are not yet written
