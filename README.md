# School IT Documentation Engine
## Intake Engine — v0.1

A locally-run assessment tool for small private school IT environments.
This tool runs entirely on your computer. No data is sent to the internet.

---

## Requirements

- Python 3.10 or higher
- pip

---

## Setup

### 1. Create a virtual environment (recommended)

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
   follow-up questions only appear after saving
7. Click **Complete Section** to see your section score and severity label
8. Your progress is saved automatically — close the browser and resume anytime

---

## Project structure

```
school_it_engine/
├── app.py              # Flask application and routes
├── database.py         # SQLite operations
├── engine.py           # Module loader, scoring, gate logic
├── requirements.txt    # Python dependencies
├── modules/
│   └── module_1.yaml   # Question definitions for Module 1
├── templates/          # HTML templates
└── data/
    └── assessments.db  # SQLite database (created on first run)
```

---

## Data and privacy

All data is stored in `data/assessments.db` on your machine.
Nothing is transmitted over the network.

To back up your data: copy `data/assessments.db` to a safe location.
To start completely fresh: delete `data/assessments.db` and restart.

---

## Known limitations in this version

- Follow-up questions appear only after hitting Save Progress (not live)
- Logo/crest file upload is not yet implemented
- DOCX report generation is not yet implemented
- The rule engine (findings and action items) is not yet implemented
