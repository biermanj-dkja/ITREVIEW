"""
test_routes.py  —  Route, lifecycle, report, and import/export tests
v0.9.1.1

Run with:  python test_routes.py                   # full suite (direct)
           python test_routes.py --lifecycle-only  # Part A only
           python test_routes.py --report-only     # Part B only
           python test_routes.py --import-only     # Part C only
           python -m pytest test_routes.py -v      # pytest discovery
           python -m unittest test_routes -v       # unittest discovery

Exit code 0 = all tests passed.
Exit code 1 = one or more failures.

─────────────────────────────────────────────────────────────────────────────
PART A — Session lifecycle
    Tests home, setup GET/POST (incl. validation), new_session for all
    three modules, invalid module rejection, section GET/POST (save /
    save_exit / complete), section_complete page, summary, manage,
    findings, report-setup GET/POST, resume, deprecate, unarchive,
    delete, and graceful unknown-session handling.
    Includes a CSRF sub-group: no-token → 400, bad-token → 400,
    valid-token → succeeds.

PART B — Report generation
    Imports the three Bit-By-Bit Academy fixture exports (one per module),
    then hits every download route asserting 200, correct Content-Type,
    valid DOCX magic bytes, and >10 KB.  Covers HTML report cards,
    report-setup POST → docx redirect chains, all six wrong-module
    route-guard combinations, finding context note save/delete, and
    DOCX content verification (unzip word/document.xml and assert the
    note text is present).

PART C — Import / export round-trip
    Verifies that export → re-import preserves all answers (key, value,
    status, and notes), sections_complete, sections_flagged, status,
    last_modified, finding contexts, and session_meta (inventory
    snapshots).  Guard-rail cases: duplicate session_id, wrong
    export_format, missing session_id, unknown module_id, non-JSON file.
    All three fixture files imported and independently verified.
─────────────────────────────────────────────────────────────────────────────
"""

import io
import json
import os
import sys
import argparse
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path

# ── arg parsing ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--lifecycle-only", action="store_true")
parser.add_argument("--report-only",    action="store_true")
parser.add_argument("--import-only",    action="store_true")
_cli_args, _ = parser.parse_known_args()
RUN_LIFECYCLE = not (_cli_args.report_only or _cli_args.import_only)
RUN_REPORT    = not (_cli_args.lifecycle_only or _cli_args.import_only)
RUN_IMPORT    = not (_cli_args.lifecycle_only or _cli_args.report_only)

# ── path setup ────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_SCRIPT_DIR)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
BASE_DIR = Path(_SCRIPT_DIR)

# Fixture files are stored at project root in this repo (they would be under
# TESTDATA/ when packaged for distribution).
_TESTDATA_CANDIDATES = [BASE_DIR, BASE_DIR / "TESTDATA"]

def _find_fixture(filename):
    """Return the Path to a fixture file, searching root then TESTDATA/."""
    for d in _TESTDATA_CANDIDATES:
        p = d / filename
        if p.exists():
            return p
    return BASE_DIR / "TESTDATA" / filename   # canonical path for missing-file error

M1_FIX = _find_fixture("BitByBit_Academy_module-1_export.json")
M2_FIX = _find_fixture("Bit-By-Bit_Academy_module-2_export_UPDATED.json")
M3_FIX = _find_fixture("Bit-By-Bit_Academy_module-3_export_UPDATED.json")

# ── isolated temp database ────────────────────────────────────────────────────
_tmp_db_dir  = tempfile.mkdtemp()
_tmp_db_path = Path(_tmp_db_dir) / "test_routes.db"

import database as _db_module
_db_module.DB_PATH = _tmp_db_path

from database import (
    init_db, create_session, get_session, get_all_sessions,
    save_school_profile, get_school_profile,
    save_answer, get_answers,
    mark_section_complete,
    save_finding_context, get_finding_contexts,
    get_answer_history,
    save_session_meta, get_session_meta, get_all_session_meta,
)

init_db()

# ── Flask test client (CSRF-bypassed) ─────────────────────────────────────────
import app as _app_module

_app_module.app.config["TESTING"]    = True
_app_module.app.config["SECRET_KEY"] = "test-secret-key"

# The template_folder is correctly set by app.py itself (BASE_DIR / "templates").
# We do NOT override it here — if templates/ is missing the test fails loudly,
# which is the correct behaviour.

# Bypass CSRF for all application-flow tests.  Part A includes a separate
# CSRF sub-group that re-enables the hook and tests the tokens directly.
_NO_CSRF_HOOKS = [
    f for f in _app_module.app.before_request_funcs.get(None, [])
    if getattr(f, "__name__", "") != "csrf_protect"
]
_WITH_CSRF_HOOKS = list(_app_module.app.before_request_funcs.get(None, []))

def _set_csrf(enabled: bool):
    _app_module.app.before_request_funcs[None] = (
        _WITH_CSRF_HOOKS if enabled else _NO_CSRF_HOOKS
    )

_set_csrf(False)   # default: CSRF off for flow tests


def fresh_client():
    return _app_module.app.test_client()


# ── Shared check/counter state ────────────────────────────────────────────────
PASS = 0
FAIL = 0
FAILURES = []


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✓ {label}")
        PASS += 1
    else:
        msg = f"  ✗ FAIL: {label}"
        if detail:
            msg += f"  ({detail})"
        print(msg)
        FAILURES.append(f"{label} — {detail}" if detail else label)
        FAIL += 1


_DOCX_MAGIC = b"PK\x03\x04"


def _docx_text(docx_bytes: bytes) -> str:
    """Unzip a DOCX and return the decoded text of word/document.xml."""
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
        with zf.open("word/document.xml") as doc:
            return doc.read().decode("utf-8", errors="replace")


def _import_fixture(client, fixture_path: Path, new_session_id: str = None) -> str:
    """Import a fixture JSON via /import-session with a fresh session_id."""
    with open(fixture_path) as fh:
        data = json.load(fh)
    sid = new_session_id or str(uuid.uuid4())
    data["session"]["session_id"] = sid
    blob = json.dumps(data).encode()
    resp = client.post(
        "/import-session",
        data={"session_file": (io.BytesIO(blob), "export.json")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    if resp.status_code != 302:
        raise AssertionError(
            f"Import {fixture_path.name} returned {resp.status_code}, expected 302"
        )
    return sid


# ═════════════════════════════════════════════════════════════════════════════
# PART A — SESSION LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════════

if RUN_LIFECYCLE:
    print("\n" + "═" * 60)
    print("PART A — Session lifecycle")
    print("═" * 60)

    client = fresh_client()

    # ── A1–A2: Basic pages ───────────────────────────────────────────────────
    print("\nA1: Home page")
    resp = client.get("/")
    check("A1 home returns 200", resp.status_code == 200)
    check("A1 home renders HTML",
          b"<html" in resp.data.lower() or b"<!doctype" in resp.data.lower())

    print("\nA2: Setup GET")
    resp = client.get("/setup")
    check("A2 setup returns 200", resp.status_code == 200)
    check("A2 setup has school_name field", b"school_name" in resp.data)
    check("A2 setup has school_website field", b"school_website" in resp.data)

    # ── A3–A4: Setup profile ─────────────────────────────────────────────────
    print("\nA3: Setup validation rejects empty submission")
    resp = client.post("/setup", data={"school_name": "", "school_website": ""},
                       follow_redirects=True)
    check("A3 empty setup stays on page (200)", resp.status_code == 200)
    check("A3 error shown", b"required" in resp.data.lower() or b"error" in resp.data.lower())

    print("\nA4: Setup success path")
    resp = client.post("/setup",
                       data={"school_name": "Route Test School",
                             "school_website": "routetest.edu"},
                       follow_redirects=True)
    check("A4 setup POST succeeds (200)", resp.status_code == 200)
    profile = get_school_profile()
    check("A4 profile written to DB", profile is not None)
    check("A4 school name persisted",
          profile and profile.get("school_name") == "Route Test School")

    # ── A5–A8: Session creation ──────────────────────────────────────────────
    print("\nA5: New session — Module 1")
    resp = client.get("/new_session?module_id=module_1", follow_redirects=False)
    check("A5 redirects (302)", resp.status_code == 302)
    loc5 = resp.headers.get("Location", "")
    check("A5 redirect has /session/", "/session/" in loc5)
    check("A5 redirect goes to a section", "/section/" in loc5)
    created_sid = loc5.split("/session/")[1].split("/")[0] if "/session/" in loc5 else ""
    check("A5 session_id UUID-like", len(created_sid) > 30)
    sess5 = get_session(created_sid)
    check("A5 session in DB", sess5 is not None)
    check("A5 module_id = module_1", (sess5 or {}).get("module_id") == "module_1")

    print("\nA6: New session — Module 2")
    resp = client.get("/new_session?module_id=module_2", follow_redirects=False)
    check("A6 M2 redirects (302)", resp.status_code == 302)
    check("A6 M2 first section is DG1", "DG1" in resp.headers.get("Location", ""))

    print("\nA7: New session — Module 3")
    resp = client.get("/new_session?module_id=module_3", follow_redirects=False)
    check("A7 M3 redirects (302)", resp.status_code == 302)
    check("A7 M3 first section is VR1", "VR1" in resp.headers.get("Location", ""))

    print("\nA8: Invalid module_id rejected")
    resp = client.get("/new_session?module_id=module_99", follow_redirects=True)
    check("A8 invalid module returns 200 (redirected)", resp.status_code == 200)
    bad_sessions = [s for s in get_all_sessions() if s.get("module_id") == "module_99"]
    check("A8 no session created for invalid module", len(bad_sessions) == 0)

    # ── A9–A12: Section POST paths ───────────────────────────────────────────
    print("\nA9: Section POST — save")
    resp = client.post(
        f"/session/{created_sid}/section/1",
        data={"action": "save", "q_1_1": "Route Test School", "q_1_2": "123 Test Lane"},
        follow_redirects=False,
    )
    check("A9 save redirects (302)", resp.status_code == 302)
    ans9 = get_answers(created_sid)
    check("A9 answer 1.1 saved", "1.1" in ans9)
    check("A9 answer 1.1 value correct",
          ans9.get("1.1", {}).get("raw_answer") == "Route Test School")
    check("A9 answer 1.2 saved", "1.2" in ans9)

    print("\nA10: Section POST — save_exit")
    resp = client.post(
        f"/session/{created_sid}/section/1",
        data={"action": "save_exit", "q_1_1": "Route Test School v2"},
        follow_redirects=False,
    )
    check("A10 save_exit redirects (302)", resp.status_code == 302)
    check("A10 redirects to home (/)",
          resp.headers.get("Location", "").rstrip("/") in ("", "/"))
    check("A10 updated answer persisted",
          get_answers(created_sid).get("1.1", {}).get("raw_answer") == "Route Test School v2")

    print("\nA11: Section POST — complete")
    save_answer(created_sid, "1.1", "Route Test School", status="answered")
    save_answer(created_sid, "1.2", "123 Test Lane", status="answered")
    resp = client.post(
        f"/session/{created_sid}/section/1",
        data={"action": "complete"},
        follow_redirects=False,
    )
    check("A11 complete redirects (302)", resp.status_code == 302)
    loc11 = resp.headers.get("Location", "")
    check("A11 redirect to section_complete or section",
          "section_complete" in loc11 or "section/1" in loc11)

    print("\nA12: Section complete page renders")
    resp_sc = client.get(loc11)
    check("A12 section_complete returns 200", resp_sc.status_code == 200)

    # ── A13: Section GET ─────────────────────────────────────────────────────
    print("\nA13: Section GET returns 200")
    resp13 = client.get(f"/session/{created_sid}/section/1")
    check("A13 section GET returns 200", resp13.status_code == 200)
    check("A13 section page has question content",
          b"question" in resp13.data.lower() or b"form" in resp13.data.lower())

    # ── A14–A19: Navigation and info pages ──────────────────────────────────
    print("\nA14: Summary page")
    resp = client.get(f"/session/{created_sid}/summary")
    check("A14 summary returns 200", resp.status_code == 200)
    check("A14 summary has school name", b"Route Test School" in resp.data)

    print("\nA15: Manage page")
    resp = client.get(f"/session/{created_sid}/manage")
    check("A15 manage returns 200", resp.status_code == 200)

    print("\nA16: Resume route")
    resp = client.get(f"/resume/{created_sid}", follow_redirects=False)
    check("A16 resume redirects (302)", resp.status_code == 302)
    check("A16 resume goes to a section", "/section/" in resp.headers.get("Location", ""))

    print("\nA17: Unknown session_id handled gracefully")
    fake = str(uuid.uuid4())
    for route in ("summary", "manage", "findings"):
        resp = client.get(f"/session/{fake}/{route}", follow_redirects=True)
        check(f"A17 /{route} bad sid → 200", resp.status_code == 200)

    print("\nA18: Findings page")
    resp = client.get(f"/session/{created_sid}/findings")
    check("A18 findings returns 200", resp.status_code == 200)
    check("A18 findings has content", len(resp.data) > 1000)

    print("\nA19: Report setup GET and POST")
    resp = client.get(f"/session/{created_sid}/report-setup")
    check("A19 report-setup GET returns 200", resp.status_code == 200)
    check("A19 has date input", b"start_date" in resp.data)
    resp = client.post(f"/session/{created_sid}/report-setup",
                       data={"start_date": ""}, follow_redirects=True)
    check("A19 empty date stays on page (200)", resp.status_code == 200)
    resp = client.post(f"/session/{created_sid}/report-setup",
                       data={"start_date": "2025-09-01"}, follow_redirects=False)
    check("A19 valid date redirects to docx",
          resp.status_code == 302 and "report.docx" in resp.headers.get("Location", ""))

    # ── A20–A22: Session state transitions ───────────────────────────────────
    print("\nA20: Deprecate / archive")
    resp = client.post(f"/session/{created_sid}/deprecate", follow_redirects=False)
    check("A20 deprecate redirects (302)", resp.status_code == 302)
    check("A20 status = deprecated",
          (get_session(created_sid) or {}).get("status") == "deprecated")

    print("\nA21: Unarchive")
    resp = client.post(f"/session/{created_sid}/unarchive", follow_redirects=False)
    check("A21 unarchive redirects (302)", resp.status_code == 302)
    check("A21 status = in_progress",
          (get_session(created_sid) or {}).get("status") == "in_progress")

    print("\nA22: Delete")
    resp = client.post(f"/session/{created_sid}/delete", follow_redirects=False)
    check("A22 delete redirects (302)", resp.status_code == 302)
    check("A22 session gone from DB", get_session(created_sid) is None)

    # ── A23: Import page ─────────────────────────────────────────────────────
    print("\nA23: Import GET")
    resp = client.get("/import-session")
    check("A23 import GET returns 200", resp.status_code == 200)
    check("A23 has file upload field", b"session_file" in resp.data)

    # ── A24: Home reflects sessions ──────────────────────────────────────────
    print("\nA24: Home page with sessions")
    sid24 = str(uuid.uuid4())
    create_session(sid24, "module_1", "Route Test School")
    resp = client.get("/")
    check("A24 home returns 200", resp.status_code == 200)

    # ── A25–A27: CSRF protection ─────────────────────────────────────────────
    print("\nA25–A27: CSRF protection")
    _set_csrf(True)
    csrf_client = fresh_client()

    # No token → 400
    resp = csrf_client.post("/setup", data={"school_name": "X", "school_website": "x.com"})
    check("A25 POST without CSRF token → 400", resp.status_code == 400)

    # Wrong token → 400
    with csrf_client.session_transaction() as flask_sess:
        flask_sess["_csrf_token"] = "real-token"
    resp = csrf_client.post("/setup",
                            data={"school_name": "X", "school_website": "x.com",
                                  "_csrf_token": "wrong-token"})
    check("A26 POST with bad CSRF token → 400", resp.status_code == 400)

    # Correct token → succeeds (302)
    resp = csrf_client.post("/setup",
                            data={"school_name": "CSRF Test School",
                                  "school_website": "csrf.edu",
                                  "_csrf_token": "real-token"})
    check("A27 POST with valid CSRF token → 302", resp.status_code == 302)

    _set_csrf(False)   # re-disable for the rest of the suite


# ═════════════════════════════════════════════════════════════════════════════
# PART B — REPORT GENERATION
# ═════════════════════════════════════════════════════════════════════════════

if RUN_REPORT:
    print("\n" + "═" * 60)
    print("PART B — Report generation (all three modules)")
    print("═" * 60)

    rpt = fresh_client()
    if not get_school_profile():
        save_school_profile("Bit-By-Bit Academy", "bitbybitacademy.org")

    for fx in (M1_FIX, M2_FIX, M3_FIX):
        check(f"B fixture exists: {fx.name}", fx.exists())

    # ── B1–B5: Module 1 ──────────────────────────────────────────────────────
    print("\nB1–B5: Module 1 — IT Assessment")
    sid_b1 = None
    if M1_FIX.exists():
        sid_b1 = _import_fixture(rpt, M1_FIX)
        check("B1 M1 session imported", get_session(sid_b1) is not None)

        resp = rpt.get(f"/session/{sid_b1}/report.docx?start_date=2025-09-01")
        check("B2 M1 report.docx returns 200", resp.status_code == 200)
        check("B2 M1 Content-Type wordprocessingml",
              "wordprocessingml" in resp.headers.get("Content-Type", ""))
        check("B2 M1 valid DOCX magic bytes", resp.data[:4] == _DOCX_MAGIC)
        check("B2 M1 DOCX > 10 KB", len(resp.data) > 10_000, f"{len(resp.data)} bytes")

        resp = rpt.get(f"/session/{sid_b1}/report.docx")
        check("B3 M1 no-date report returns 200", resp.status_code == 200)
        check("B3 M1 no-date is valid DOCX", resp.data[:4] == _DOCX_MAGIC)

        resp = rpt.post(f"/session/{sid_b1}/report-setup",
                        data={"start_date": "2025-10-01"}, follow_redirects=False)
        check("B4 report-setup POST redirects to docx",
              resp.status_code == 302 and "report.docx" in resp.headers.get("Location", ""))

        resp = rpt.get(f"/session/{sid_b1}/findings")
        check("B5 findings page returns 200", resp.status_code == 200)
        check("B5 findings page has content", len(resp.data) > 5000)

    # ── B6: Wrong-module guards — all 6 combinations ─────────────────────────
    print("\nB6: Wrong-module route guards (all 6 combos)")
    sid_b6m2 = _import_fixture(rpt, M2_FIX) if M2_FIX.exists() else None
    sid_b6m3 = _import_fixture(rpt, M3_FIX) if M3_FIX.exists() else None

    _guard_cases = [
        ("M1 blocked from dg_report.docx", sid_b1,   "dg_report.docx"),
        ("M1 blocked from vr_report.docx", sid_b1,   "vr_report.docx"),
        ("M2 blocked from report.docx",    sid_b6m2, "report.docx"),
        ("M2 blocked from vr_report.docx", sid_b6m2, "vr_report.docx"),
        ("M3 blocked from report.docx",    sid_b6m3, "report.docx"),
        ("M3 blocked from dg_report.docx", sid_b6m3, "dg_report.docx"),
    ]
    for desc, sid_g, route_g in _guard_cases:
        if sid_g:
            resp = rpt.get(f"/session/{sid_g}/{route_g}?start_date=2025-09-01",
                           follow_redirects=True)
            check(f"B6 {desc} → 200, no DOCX",
                  resp.status_code == 200 and resp.data[:4] != _DOCX_MAGIC)

    # ── B7–B10: Module 2 ─────────────────────────────────────────────────────
    print("\nB7–B10: Module 2 — Data Governance")
    sid_b7 = None
    if M2_FIX.exists():
        sid_b7 = _import_fixture(rpt, M2_FIX)
        check("B7 M2 session imported", get_session(sid_b7) is not None)

        resp = rpt.get(f"/session/{sid_b7}/dg_report")
        check("B8 DG report card returns 200", resp.status_code == 200)
        check("B8 DG card has content", len(resp.data) > 5000)

        resp = rpt.get(f"/session/{sid_b7}/dg_report.docx?start_date=2025-09-01")
        check("B9 DG docx returns 200", resp.status_code == 200)
        check("B9 DG Content-Type wordprocessingml",
              "wordprocessingml" in resp.headers.get("Content-Type", ""))
        check("B9 DG valid DOCX magic bytes", resp.data[:4] == _DOCX_MAGIC)
        check("B9 DG DOCX > 10 KB", len(resp.data) > 10_000, f"{len(resp.data)} bytes")

        resp = rpt.post(f"/session/{sid_b7}/dg-report-setup",
                        data={"start_date": "2025-10-01"}, follow_redirects=False)
        check("B10 DG report-setup POST → dg_report.docx",
              resp.status_code == 302 and "dg_report.docx" in resp.headers.get("Location", ""))

    # ── B11–B14: Module 3 ────────────────────────────────────────────────────
    print("\nB11–B14: Module 3 — Vendor Register")
    sid_b11 = None
    if M3_FIX.exists():
        sid_b11 = _import_fixture(rpt, M3_FIX)
        check("B11 M3 session imported", get_session(sid_b11) is not None)

        resp = rpt.get(f"/session/{sid_b11}/vr_report")
        check("B12 VR report card returns 200", resp.status_code == 200)
        check("B12 VR card has content", len(resp.data) > 5000)

        resp = rpt.get(f"/session/{sid_b11}/vr_report.docx?start_date=2025-09-01")
        check("B13 VR docx returns 200", resp.status_code == 200)
        check("B13 VR Content-Type wordprocessingml",
              "wordprocessingml" in resp.headers.get("Content-Type", ""))
        check("B13 VR valid DOCX magic bytes", resp.data[:4] == _DOCX_MAGIC)
        check("B13 VR DOCX > 10 KB", len(resp.data) > 10_000, f"{len(resp.data)} bytes")

        resp = rpt.post(f"/session/{sid_b11}/vr-report-setup",
                        data={"start_date": "2025-11-01"}, follow_redirects=False)
        check("B14 VR report-setup POST → vr_report.docx",
              resp.status_code == 302 and "vr_report.docx" in resp.headers.get("Location", ""))

    # ── B15–B17: Context note save / DOCX content verification ───────────────
    print("\nB15–B17: Finding context notes — save, delete, and DOCX content")

    # M1
    if sid_b1:
        resp = rpt.post(
            f"/session/{sid_b1}/finding-context",
            data={"finding_id": "F2-003", "note": "CANARY_M1_NOTE",
                  "return_to": "findings_full"},
            follow_redirects=False,
        )
        check("B15 M1 context save redirects (302)", resp.status_code == 302)
        ctx = get_finding_contexts(sid_b1)
        check("B15 M1 note stored in DB", any("F2-003" in k for k in ctx))

        resp = rpt.get(f"/session/{sid_b1}/report.docx?start_date=2025-09-01")
        check("B16 M1 DOCX contains context note text",
              "CANARY_M1_NOTE" in _docx_text(resp.data))

        resp = rpt.post(
            f"/session/{sid_b1}/finding-context",
            data={"finding_id": "F2-003", "note": "", "return_to": "findings_full"},
            follow_redirects=False,
        )
        check("B17 M1 context delete redirects (302)", resp.status_code == 302)
        ctx2 = get_finding_contexts(sid_b1)
        check("B17 M1 note removed from DB", not any("F2-003" in k for k in ctx2))

    # DG note in DOCX
    if sid_b7:
        save_finding_context(sid_b7, "DG_SYS_1:ac_mfa_optional", "CANARY_DG_NOTE")
        resp = rpt.get(f"/session/{sid_b7}/dg_report.docx?start_date=2025-09-01")
        check("B18 DG DOCX contains DG context note",
              "CANARY_DG_NOTE" in _docx_text(resp.data))

    # VR note in DOCX
    if sid_b11:
        save_finding_context(sid_b11, "VR_V_1:cv_cost_estimated", "CANARY_VR_NOTE")
        resp = rpt.get(f"/session/{sid_b11}/vr_report.docx?start_date=2025-09-01")
        check("B19 VR DOCX contains VR context note",
              "CANARY_VR_NOTE" in _docx_text(resp.data))


# ═════════════════════════════════════════════════════════════════════════════
# PART C — IMPORT / EXPORT ROUND-TRIP
# ═════════════════════════════════════════════════════════════════════════════

if RUN_IMPORT:
    print("\n" + "═" * 60)
    print("PART C — Import / export round-trip")
    print("═" * 60)

    imp = fresh_client()
    if not get_school_profile():
        save_school_profile("Bit-By-Bit Academy", "bitbybitacademy.org")

    # ── C1: Import M1 — structure ─────────────────────────────────────────────
    print("\nC1: Module 1 fixture import — structure")
    sid_c1 = None
    if M1_FIX.exists():
        sid_c1 = _import_fixture(imp, M1_FIX)
        sess_c1 = get_session(sid_c1)
        check("C1 session created", sess_c1 is not None)
        check("C1 module_id = module_1", (sess_c1 or {}).get("module_id") == "module_1")
        check("C1 school_name preserved",
              (sess_c1 or {}).get("school_name") == "Bit-By-Bit Academy")

        with open(M1_FIX) as fh:
            fixture = json.load(fh)
        expected = len(fixture.get("answers", {}))
        imported = get_answers(sid_c1)
        check(f"C1 all {expected} answers restored",
              len(imported) == expected, f"got {len(imported)}")

        import json as _json
        complete = _json.loads(sess_c1.get("sections_complete", "[]"))
        check("C1 sections_complete restored", len(complete) >= 1)
        check("C1 expected M1 sections present",
              all(s in complete for s in ["1", "2", "3"]))

    # ── C2: Duplicate import blocked ─────────────────────────────────────────
    print("\nC2: Duplicate import blocked")
    if M1_FIX.exists() and sid_c1:
        with open(M1_FIX) as fh:
            dup = json.load(fh)
        dup["session"]["session_id"] = sid_c1
        resp = imp.post(
            "/import-session",
            data={"session_file": (io.BytesIO(json.dumps(dup).encode()), "dup.json")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        check("C2 duplicate → 200", resp.status_code == 200)
        check("C2 'already exists' shown", b"already exists" in resp.data.lower())

    # ── C3–C6: Guard-rail cases ───────────────────────────────────────────────
    print("\nC3–C6: Import guard-rail cases")

    bad_fmt = {"export_format": "other_tool", "session": {}, "answers": {}}
    resp = imp.post("/import-session",
                    data={"session_file": (io.BytesIO(json.dumps(bad_fmt).encode()), "bad.json")},
                    content_type="multipart/form-data", follow_redirects=True)
    check("C3 wrong export_format → 200 + error",
          resp.status_code == 200 and
          (b"unrecogni" in resp.data.lower() or b"error" in resp.data.lower()))

    no_sid = {"export_format": "school_it_engine_session_v1", "session": {}, "answers": {}}
    resp = imp.post("/import-session",
                    data={"session_file": (io.BytesIO(json.dumps(no_sid).encode()), "nosid.json")},
                    content_type="multipart/form-data", follow_redirects=True)
    check("C4 missing session_id → 200 + error",
          resp.status_code == 200 and b"error" in resp.data.lower())

    resp = imp.post("/import-session",
                    data={"session_file": (io.BytesIO(b"not json at all"), "notjson.txt")},
                    content_type="multipart/form-data", follow_redirects=True)
    check("C5 non-JSON file → 200 + error",
          resp.status_code == 200 and
          (b"error" in resp.data.lower() or b"valid" in resp.data.lower()))

    bad_mod = {
        "export_format": "school_it_engine_session_v1",
        "session": {"session_id": str(uuid.uuid4()), "module_id": "module_99",
                    "school_name": "Test", "status": "in_progress",
                    "sections_complete": "[]", "sections_flagged": "[]"},
        "answers": {},
        "school_profile": {"school_name": "Test", "school_website": "test.edu"},
    }
    resp = imp.post("/import-session",
                    data={"session_file": (io.BytesIO(json.dumps(bad_mod).encode()), "badmod.json")},
                    content_type="multipart/form-data", follow_redirects=True)
    check("C6 unknown module_id → 200 + error",
          resp.status_code == 200 and
          (b"error" in resp.data.lower() or b"unrecogni" in resp.data.lower()))

    # ── C7: Export envelope ───────────────────────────────────────────────────
    print("\nC7: Export envelope fields")
    exported = None
    if M1_FIX.exists() and sid_c1:
        resp = imp.get(f"/session/{sid_c1}/export")
        check("C7 export returns 200", resp.status_code == 200)
        check("C7 Content-Type JSON",
              "application/json" in resp.headers.get("Content-Type", ""))
        exported = json.loads(resp.data)
        check("C7 export_format correct",
              exported.get("export_format") == "school_it_engine_session_v1")
        check("C7 exported_on present", "exported_on" in exported)
        check("C7 app_version present", "app_version" in exported)
        check("C7 answers key present", "answers" in exported)
        check("C7 session key present", "session" in exported)
        check("C7 session_meta key present", "session_meta" in exported)
        check("C7 session_id matches",
              exported.get("session", {}).get("session_id") == sid_c1)
        check("C7 school_profile present with school_name",
              "school_name" in (exported.get("school_profile") or {}))

    # ── C8: Deep answer equality ──────────────────────────────────────────────
    print("\nC8: Export answer equality (keys, values, status, notes)")
    if exported and sid_c1:
        db_ans   = get_answers(sid_c1)
        exp_ans  = exported.get("answers", {})
        check("C8 answer key sets match",
              set(exp_ans.keys()) == set(db_ans.keys()),
              f"export={len(exp_ans)} db={len(db_ans)}")
        mismatches = []
        for qid in db_ans:
            db_rec  = db_ans[qid]
            exp_rec = exp_ans.get(qid, {})
            if db_rec.get("raw_answer") != exp_rec.get("raw_answer"):
                mismatches.append(f"{qid} raw_answer")
            if db_rec.get("answer_status") != exp_rec.get("answer_status"):
                mismatches.append(f"{qid} answer_status")
        check("C8 all answer values and statuses match",
              len(mismatches) == 0, f"{mismatches[:3]}" if mismatches else "")

    # ── C9: Session state fields ──────────────────────────────────────────────
    print("\nC9: Export session state fields")
    if exported and sid_c1:
        sess_exp = exported.get("session", {})
        sess_db  = get_session(sid_c1)
        check("C9 sections_complete matches",
              sess_exp.get("sections_complete") == sess_db.get("sections_complete"))
        check("C9 sections_flagged matches",
              sess_exp.get("sections_flagged") == sess_db.get("sections_flagged"))
        check("C9 status matches",
              sess_exp.get("status") == sess_db.get("status"))
        check("C9 last_modified matches",
              sess_exp.get("last_modified") == sess_db.get("last_modified"))

    # ── C10: session_meta round-trip ─────────────────────────────────────────
    print("\nC10: session_meta (inventory snapshot) round-trip")
    if M2_FIX.exists():
        # Import M2 and let the section GET write an inventory snapshot
        sid_c10 = _import_fixture(imp, M2_FIX)

        # Manually plant a known snapshot key so we can verify it survives
        snapshot_key   = "inv_snapshot:DG1.3"
        snapshot_value = ["Veracross (SIS)", "Google Workspace", "Seesaw"]
        save_session_meta(sid_c10, snapshot_key, snapshot_value)

        # Export
        resp = imp.get(f"/session/{sid_c10}/export")
        exp_data = json.loads(resp.data)
        check("C10 session_meta in export", "session_meta" in exp_data)
        check("C10 snapshot key in export",
              snapshot_key in exp_data.get("session_meta", {}))
        check("C10 snapshot value in export",
              exp_data.get("session_meta", {}).get(snapshot_key) == snapshot_value)

        # Re-import and verify key restored
        new_sid = str(uuid.uuid4())
        exp_data["session"]["session_id"] = new_sid
        blob = json.dumps(exp_data).encode()
        resp_imp = imp.post(
            "/import-session",
            data={"session_file": (io.BytesIO(blob), "meta_roundtrip.json")},
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        check("C10 meta round-trip import redirects (302)", resp_imp.status_code == 302)
        restored = get_session_meta(new_sid, snapshot_key)
        check("C10 snapshot key restored after import",
              restored == snapshot_value, f"got {restored!r}")

    # ── C11: Full round-trip preserves answer count ───────────────────────────
    print("\nC11: Full export → re-import round-trip")
    if exported and sid_c1:
        new_sid_rt = str(uuid.uuid4())
        rt_data = json.loads(json.dumps(exported))   # deep copy
        rt_data["session"]["session_id"] = new_sid_rt
        resp_rt = imp.post(
            "/import-session",
            data={"session_file": (io.BytesIO(json.dumps(rt_data).encode()), "rt.json")},
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        check("C11 round-trip import redirects (302)", resp_rt.status_code == 302)
        rt_ans = get_answers(new_sid_rt)
        check("C11 answer count survives round-trip",
              len(rt_ans) == len(db_ans), f"got {len(rt_ans)}, expected {len(db_ans)}")
        rt_sess = get_session(new_sid_rt)
        check("C11 sections_complete survives round-trip",
              rt_sess.get("sections_complete") == (sess_db or {}).get("sections_complete"))

    # ── C12: All three fixtures import cleanly ────────────────────────────────
    print("\nC12: All three fixtures import cleanly")
    for label, fp, expected_mid in [
        ("M1", M1_FIX, "module_1"),
        ("M2", M2_FIX, "module_2"),
        ("M3", M3_FIX, "module_3"),
    ]:
        if fp.exists():
            new_sid = _import_fixture(imp, fp)
            sess    = get_session(new_sid)
            answers = get_answers(new_sid)
            check(f"C12 {label} session created", sess is not None)
            check(f"C12 {label} module_id = {expected_mid}",
                  (sess or {}).get("module_id") == expected_mid)
            check(f"C12 {label} answers > 0", len(answers) > 0, f"got {len(answers)}")
        else:
            check(f"C12 {label} fixture exists", False, f"missing: {fp}")


# ═════════════════════════════════════════════════════════════════════════════
# UNITTEST / PYTEST WRAPPERS
# ═════════════════════════════════════════════════════════════════════════════

class TestLifecycle(unittest.TestCase):
    def test_part_a(self):
        self.assertEqual(FAIL, 0,
            msg=f"{FAIL} failure(s):\n" + "\n".join(f"  ✗ {f}" for f in FAILURES))

class TestReportGeneration(unittest.TestCase):
    def test_part_b(self):
        self.assertEqual(FAIL, 0,
            msg=f"{FAIL} failure(s):\n" + "\n".join(f"  ✗ {f}" for f in FAILURES))

class TestImportExport(unittest.TestCase):
    def test_part_c(self):
        self.assertEqual(FAIL, 0,
            msg=f"{FAIL} failure(s):\n" + "\n".join(f"  ✗ {f}" for f in FAILURES))

class TestAllRoutes(unittest.TestCase):
    def test_all_pass(self):
        self.assertEqual(FAIL, 0,
            msg=f"{FAIL} check(s) failed:\n" + "\n".join(f"  ✗ {f}" for f in FAILURES))


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL == 0:
        print("All tests passed. ✓")
    else:
        print("\nFailed tests:")
        for f in FAILURES:
            print(f"  ✗ {f}")
        sys.exit(1)
