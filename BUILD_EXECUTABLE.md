# Building a Standalone Executable
## School IT Engine v0.8.3 — Tester Distribution Guide

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

## Before you start

You need Python installed on your build machine. This is only for
building; testers do not need Python at all.

If you already have Python set up for the engine (i.e. you can run
`python app.py` successfully), you are ready to go.

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

## Step 2 — Confirm launcher.py is present

`launcher.py` is the PyInstaller entry point. It is included in the
repository — you do not need to create it. Confirm it exists in the
project root alongside `app.py`:

```
school_it_engine/
├── app.py
├── launcher.py   ← should be here
├── database.py
└── ...
```

If it is missing for any reason, the full file content is shown below
for reference. Do not modify it unless you are changing the port number.

<details>
<summary>launcher.py — full content for reference / troubleshooting</summary>

```python
import sys
import os
import threading
import webbrowser
import time

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    exe_dir = os.path.dirname(sys.executable)
    os.environ['SCHOOL_IT_DATA_DIR'] = os.path.join(exe_dir, 'data')
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from app import app, init_db_path

PORT = 5000

def open_browser():
    time.sleep(1.5)
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
</details>

---

## Step 3 — Confirm database.py honours SCHOOL_IT_DATA_DIR

`database.py` is already patched in the repository to write the database
next to the executable rather than inside the PyInstaller temp folder
(which is deleted on every launch). You do not need to edit it.

To verify, open `database.py` and confirm the top of the file reads:

```python
_data_dir = _os.environ.get('SCHOOL_IT_DATA_DIR')
if _data_dir:
    DB_PATH = Path(_data_dir) / "assessments.db"
else:
    DB_PATH = BASE_DIR / "data" / "assessments.db"
```

If it only shows `DB_PATH = BASE_DIR / "data" / "assessments.db"` (the
old single-line form), your copy of the file predates v0.8.2. Replace it
with the current version from the repository before building.

`app.py` also exports an `init_db_path()` function that `launcher.py`
calls on startup to ensure the data directory exists before Flask starts.
This is already present in the current codebase.

---

## Step 4 — Run PyInstaller

Run the command for your platform from inside the project folder,
with your virtual environment active.

### Windows

```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates;templates" --add-data "modules;modules" launcher.py
```

### macOS (Intel or Apple Silicon)

```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates:templates" --add-data "modules:modules" launcher.py
```

> **Separator difference:** `--add-data` uses a **semicolon** on Windows
> and a **colon** on Mac/Linux. This is the most common copy-paste mistake.

### About --console vs --windowed

`--console` keeps a terminal window visible while the app runs. Use this
during beta testing so testers can see and copy any error messages.

Once the build is confirmed stable, switch to `--windowed` for the final
distribution version. On Windows this removes the black terminal window;
on Mac it bundles as a `.app` package.

---

## Step 5 — Find your output

PyInstaller creates a `dist/` folder in your project directory:

- **Windows:** `dist/SchoolITEngine.exe`
- **macOS:** `dist/SchoolITEngine` (binary) or `dist/SchoolITEngine.app`

The `build/` folder and the `.spec` file are intermediate — testers
do not need them.

---

## Step 6 — Test the build before distributing

Before sending to testers, run the executable yourself from the `dist/`
folder:

1. Double-click `SchoolITEngine.exe` (or the `.app` on Mac)
2. The terminal window appears and your browser opens automatically
3. Complete a full session through both a Module 1 and Module 2 assessment
4. Download a report from Module 1
5. Close the terminal window — confirm the app stops

**Check the data folder:** After running, look for `dist/data/assessments.db`.
This file should appear next to the executable (not somewhere in `%TEMP%`
or `/var/folders`). If it is there and survives a restart, the
`SCHOOL_IT_DATA_DIR` support in `database.py` is working correctly.

---

## Step 7 — What to give testers

### Windows testers

Send them `SchoolITEngine.exe`. One file, nothing else required.

Include this note with it:

> **To start:** Double-click SchoolITEngine.exe. A window will open and
> your browser will load the app automatically.
>
> **To stop:** Close the black window when you are done.
>
> **If Windows warns you:** Click **More info**, then **Run anyway**.
> This warning appears because the file does not have a paid code-signing
> certificate — it is safe to dismiss.
>
> **Your data** is saved in a `data` folder that appears next to the .exe
> file after the first run. Do not delete that folder.

### macOS testers

Send them `SchoolITEngine` (the binary) or `SchoolITEngine.app` (the app bundle).

Include this note:

> **To start:** Double-click SchoolITEngine. Your browser will open
> automatically to the app.
>
> **If macOS says it cannot be opened:** Right-click (or Control-click)
> the file and choose **Open**, then click **Open** in the dialog.
> You only need to do this the first time.
>
> **To stop:** Close the terminal window that appeared when you launched.
>
> **Your data** is saved in a `data` folder next to the app file.

---

## Common problems and fixes

### "Failed to execute script" on launch

Almost always a file that PyInstaller did not bundle. Switch to `--console`
temporarily and read the error in the terminal window. The fix is usually
one more `--add-data` flag.

Common things to check:

```bash
# The templates folder (always required)
--add-data "templates:templates"      # Mac
--add-data "templates;templates"      # Windows

# The modules folder (always required — contains the YAML files)
--add-data "modules:modules"          # Mac
--add-data "modules;modules"          # Windows
```

### Flask can't find templates

Confirm that `os.chdir(base_dir)` is present in `launcher.py`. This is
what tells Flask to look for templates in the unpacked bundle rather than
relative to the Python interpreter location.

If templates are still not found, add this to `app.py` where the Flask
app is created:

```python
import sys as _sys, os as _os
_base = getattr(_sys, '_MEIPASS', _os.path.dirname(_os.path.abspath(__file__)))
app = Flask(__name__, template_folder=_os.path.join(_base, 'templates'))
```

### Port 5000 already in use

On macOS Monterey and later, AirPlay Receiver uses port 5000 by default.
If testers see a "port in use" error, change `PORT = 5000` to `PORT = 5001`
in `launcher.py` and rebuild.

### Antivirus flags the .exe

Common with PyInstaller executables — they resemble packed files that
heuristic scanners associate with malware. Options in order of effort:

1. Ask testers to add an exception (fine for a small known group)
2. Rebuild with `--onedir` instead of `--onefile` — a folder of files is
   far less likely to trigger AV than a single packed binary
3. Purchase a code-signing certificate ($100-200/year) and sign the
   executable — eliminates almost all false positives permanently

### App works but data disappears on restart

The `SCHOOL_IT_DATA_DIR` support in `database.py` is missing or not
working correctly. Confirm the `data/assessments.db` file appears at
`dist/data/assessments.db` (next to the .exe), not in `%TEMP%`
or `/var/folders/...`. See Step 3 above to verify your `database.py`
has the correct patch.

### Module 2 worksheets don't appear after saving DG1

The `modules/` folder was not included in the PyInstaller bundle.
Confirm the `--add-data "modules:modules"` (or `modules;modules` on
Windows) flag is in your build command.

---

## Using --onedir instead of --onefile

`--onefile` packs everything into a single executable. Tidy to send but:
- Slower to start (unpacks to a temp folder on every launch)
- More likely to trigger antivirus

`--onedir` produces a folder with the executable plus its dependencies.
Faster to start, less suspicious to AV, but you need to zip the folder
before sending.

To use it, replace `--onefile` with `--onedir`. The output will be
`dist/SchoolITEngine/` — zip that whole folder for distribution.

---

## Saving the build command for next time

After the first successful build, PyInstaller saves a `SchoolITEngine.spec`
file. Future builds can skip retyping the command:

```bash
pyinstaller SchoolITEngine.spec
```

Commit the `.spec` file to version control so builds are reproducible.

---

## Building for multiple platforms

| Platform | Build machine | Output |
|---|---|---|
| Windows 10/11 | Windows PC or VM | `SchoolITEngine.exe` |
| macOS Intel | Intel Mac | `SchoolITEngine` or `.app` |
| macOS Apple Silicon | M-series Mac | `SchoolITEngine` or `.app` |

You cannot cross-compile. A Mac cannot produce a Windows `.exe` and
vice versa. If you need builds for platforms you don't have hardware for,
GitHub Actions provides free Windows and macOS runners — ask for a CI
workflow if you want to set that up.

---

## Quick-reference build commands

**macOS / Linux — beta (console visible):**
```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates:templates" --add-data "modules:modules" launcher.py
```

**macOS / Linux — final distribution (no console):**
```
pyinstaller --onefile --windowed --name "SchoolITEngine" --add-data "templates:templates" --add-data "modules:modules" launcher.py
```

**Windows — beta (console visible):**
```
pyinstaller --onefile --console --name "SchoolITEngine" --add-data "templates;templates" --add-data "modules;modules" launcher.py
```

**Windows — final distribution (no console):**
```
pyinstaller --onefile --windowed --name "SchoolITEngine" --add-data "templates;templates" --add-data "modules;modules" launcher.py
```
