# Building a Standalone Executable
## School IT Engine — Tester Distribution Guide

This guide explains how to package the School IT Engine into a single
double-clickable file that testers can run without installing Python,
without a terminal, and without any technical knowledge.

The tool used is **PyInstaller**. It bundles your Python code, all
dependencies (Flask, PyYAML, python-docx, etc.), and the Python
interpreter itself into one self-contained package.

You do the build once on each platform you want to support. The output
is not cross-platform — a Windows build only runs on Windows, a Mac
build only runs on Mac.

---

## Before you start — one-time setup

You need Python installed on your build machine. This is only for
building; testers do not need Python at all.

If you already have Python set up for the engine, you are ready. If not,
install it from https://python.org and follow the README.

---

## Step 1 — Install PyInstaller

Open a terminal (or command prompt) in the project folder, activate your
virtual environment if you use one, then run:

```bash
pip install pyinstaller
```

Verify it installed:

```bash
pyinstaller --version
```

You should see a version number like `6.x.x`.

---

## Step 2 — Create a launcher script

PyInstaller needs a single entry-point file. The engine's `app.py` uses
`app.run()` directly, which works fine in development but needs a small
wrapper for a packaged executable so the browser opens automatically.

Create a new file called **`launcher.py`** in the root of the project
folder (same folder as `app.py`) with this content:

```python
import sys
import os
import threading
import webbrowser
import time

# When running as a PyInstaller bundle, sys._MEIPASS is the temp
# folder where all bundled files are unpacked. We need to tell the
# app where to find its templates, modules, and data folder.
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    # Put the database in the same folder as the executable,
    # not in the temp unpacking folder (which is deleted on exit).
    exe_dir = os.path.dirname(sys.executable)
    os.environ['SCHOOL_IT_DATA_DIR'] = os.path.join(exe_dir, 'data')
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from app import app, init_db_path

PORT = 5000

def open_browser():
    time.sleep(1.5)  # Give Flask a moment to start
    webbrowser.open(f'http://127.0.0.1:{PORT}')

if __name__ == '__main__':
    init_db_path()
    print("=" * 50)
    print("  School IT Engine")
    print(f"  Running at: http://127.0.0.1:{PORT}")
    print("  Close this window to stop the application.")
    print("=" * 50)
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)
```

---

## Step 3 — Patch app.py and database.py for the data directory

The launcher sets an environment variable `SCHOOL_IT_DATA_DIR` so the
database is written next to the executable rather than inside the
temporary unpacking folder (which is deleted every time the app closes).

**In `database.py`**, change the `DB_PATH` line from:

```python
DB_PATH = BASE_DIR / "data" / "assessments.db"
```

to:

```python
import os
_data_dir = os.environ.get('SCHOOL_IT_DATA_DIR')
if _data_dir:
    DB_PATH = Path(_data_dir) / "assessments.db"
else:
    DB_PATH = BASE_DIR / "data" / "assessments.db"
```

**In `app.py`**, add this function near the top (after imports):

```python
def init_db_path():
    """Called by launcher to ensure the data directory exists."""
    from database import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
```

---

## Step 4 — Run PyInstaller

### Windows

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "SchoolITEngine" ^
  --add-data "templates;templates" ^
  --add-data "modules;modules" ^
  --add-data "static;static" ^
  launcher.py
```

> **Note:** If you don't have a `static` folder, remove that line.

### macOS (Intel or Apple Silicon)

```bash
pyinstaller \
  --onefile \
  --windowed \
  --name "SchoolITEngine" \
  --add-data "templates:templates" \
  --add-data "modules:modules" \
  launcher.py
```

> **macOS note:** The separator in `--add-data` is a **colon** on Mac/Linux
> and a **semicolon** on Windows. Easy to mix up.

### What `--windowed` does

On Windows it suppresses the black command-prompt window. On Mac it
bundles as a `.app` package. If you want testers to see a terminal window
(useful during testing to see error messages), replace `--windowed` with
`--console`.

**Recommendation for beta testing:** Use `--console` for your first round
so testers can copy and paste any error messages they see.

---

## Step 5 — Find your output

PyInstaller creates a `dist/` folder in your project directory.

- **Windows:** `dist/SchoolITEngine.exe`
- **macOS:** `dist/SchoolITEngine` (single binary) or `dist/SchoolITEngine.app` (app bundle)

The `build/` folder and the `.spec` file are intermediate files — testers
don't need them.

---

## Step 6 — Test the build before distributing

Before sending to testers, run the built executable yourself:

1. Navigate to `dist/`
2. Double-click `SchoolITEngine.exe` (or `.app` on Mac)
3. A terminal/console window should appear (if using `--console`)
4. Your browser should open to `http://127.0.0.1:5000` automatically
5. Work through a full assessment and download a report
6. Close the window — confirm the app stops

Check that the `data/` folder (containing `assessments.db`) appears
**next to the executable**, not somewhere temporary. If it appears and
persists between runs, the data directory patch worked correctly.

---

## Step 7 — What to give testers

### Windows testers

Send them `SchoolITEngine.exe`. That's it — one file.

Include this note:

> Double-click SchoolITEngine.exe to start. Your browser will open
> automatically. Do not close the black window while using the app —
> it keeps the engine running. Close it when you are done.
>
> Windows may show a "Windows protected your PC" warning the first time.
> Click "More info" then "Run anyway". This appears because the file is
> not signed with a paid code-signing certificate.

### macOS testers

Send them `SchoolITEngine` (the binary) or `SchoolITEngine.app`.

Include this note:

> Double-click SchoolITEngine to start. If macOS says it cannot be opened
> because it is from an unidentified developer, right-click (or
> Control-click) the file and choose Open, then click Open in the dialog.
> You only need to do this once.
>
> Your browser will open automatically to http://127.0.0.1:5000.

---

## Common problems and fixes

### "Failed to execute script" on launch

This is almost always a missing file that PyInstaller didn't bundle.
Switch to `--console` temporarily and look at the error in the terminal.
The fix is usually adding another `--add-data` flag.

Common missed items:

```bash
# If you have a static/ folder with CSS or JS
--add-data "static:static"

# If you reference any files from subdirectories
--add-data "data/seed.json:data"
```

### Flask can't find templates

PyInstaller unpacks files to `sys._MEIPASS` but Flask looks for templates
relative to the app module's location. The `os.chdir(base_dir)` in the
launcher handles this — confirm it's present.

If templates are still missing, explicitly set the template folder in
`app.py`:

```python
import sys
_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_base, 'templates'))
```

### Port 5000 already in use

On macOS Monterey and later, AirPlay Receiver uses port 5000 by default.
Change the port in `launcher.py` to `5001` (or any unused port) if this
affects your testers.

### Antivirus flags the .exe

Common with PyInstaller-built executables because they look similar to
packed malware to heuristic scanners. Solutions in order of effort:

1. Ask testers to add an exception (fine for a small beta group)
2. Rebuild with `--onedir` instead of `--onefile` — a folder of files
   is less suspicious than a single packed binary
3. Purchase a code-signing certificate ($100–200/year) and sign the
   executable — eliminates almost all AV false positives

### App works but data disappears on restart

The `SCHOOL_IT_DATA_DIR` patch in Step 3 is missing or incorrect.
Confirm the database file appears at `dist/data/assessments.db` (next
to the .exe), not somewhere in `%TEMP%` or `/var/folders`.

---

## Using `--onedir` instead of `--onefile`

`--onefile` packs everything into a single executable. It's tidy but
slower to start (it unpacks to a temp folder on each launch) and more
likely to trigger antivirus.

`--onedir` produces a folder containing the executable plus all its
dependencies. Faster to start, less suspicious to AV, but you have to
zip the folder to send it.

To use it, replace `--onefile` with `--onedir` in the PyInstaller command.
The output will be `dist/SchoolITEngine/` — zip that whole folder for
distribution.

---

## Saving the build command as a .spec file

After the first successful build, PyInstaller saves a `SchoolITEngine.spec`
file. Future builds can use:

```bash
pyinstaller SchoolITEngine.spec
```

This is faster and ensures the build is reproducible. Commit the `.spec`
file to version control.

---

## Build on each platform separately

| Platform | Build machine needed | Output |
|---|---|---|
| Windows 10/11 | Windows PC or VM | `SchoolITEngine.exe` |
| macOS Intel | Intel Mac | `SchoolITEngine` |
| macOS Apple Silicon | M1/M2/M3 Mac | `SchoolITEngine` |

You cannot cross-compile. A Mac cannot build a Windows .exe.
If you only have one platform, build for that and ask a colleague
to build the others, or use a CI service (GitHub Actions has free
Windows and macOS runners).

---

## Quick reference — full build command

**Windows:**
```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates;templates" --add-data "modules;modules" launcher.py
```

**macOS / Linux:**
```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates:templates" --add-data "modules:modules" launcher.py
```

Switch `--console` to `--windowed` for the final distribution version
once you've confirmed the build is stable.
