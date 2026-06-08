"""
launcher.py — Entry point for packaged executables (PyInstaller).

When running as a bundled .exe or .app:
  - sys._MEIPASS is the temp folder where bundled files are unpacked.
  - SCHOOL_IT_DATA_DIR is set to a folder next to the executable so the
    database persists between runs (the temp folder is deleted on exit).

When running normally (python launcher.py or python app.py):
  - base_dir falls back to the project root.
  - SCHOOL_IT_DATA_DIR is not set, so database.py uses data/ as normal.

See BUILD_EXECUTABLE.md for full packaging instructions.
"""

import sys
import os
import threading
import webbrowser
import time

# When running as a PyInstaller bundle, sys._MEIPASS is the temp
# folder where bundled files are unpacked. We tell the app where
# to find its templates, modules, and static files.
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    # Write the database next to the executable, not in the temp
    # folder (which is deleted every time the app closes).
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
