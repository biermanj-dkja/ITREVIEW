import uuid
import json
import io
import os
import hmac
import hashlib
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from database import (
    init_db, save_answer, get_answers, get_answer, create_session,
    get_session, mark_section_complete, get_all_sessions,
    save_school_profile, get_school_profile, flag_session_incomplete,
    delete_session, save_session_meta, get_session_meta,
    set_last_exported, get_last_exported,
    get_answer_history, get_amended_question_ids,
    save_finding_context, delete_finding_context, get_finding_contexts,
    deprecate_session, unarchive_session,
    restore_session_state, restore_answer_history
)
from rules_engine import evaluate_all, evaluate_section, findings_to_dict
from trace import write_trace_m1, write_trace_dg, write_trace_vr
from report_generator import generate_report
from engine import (
    load_module, get_section, get_visible_questions,
    calculate_section_score, get_section_severity_label,
    get_skip_percentage, questions_have_unknown_option,
    CRITICAL_QUESTIONS
)
from dynamic_engine import expand_dynamic_sections
from report_generator_dg import generate_dg_report

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
# Secret key: read from environment variable if set, otherwise generate a
# fresh random key each startup.  A random key is fine for this localhost-only
# tool (sessions do not need to survive a restart).  Set SECRET_KEY in the
# environment for a stable key if you are running the tool on a shared machine.
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config['VERSION'] = '0.8.9.0'

import json as _json
app.jinja_env.filters["from_json"] = _json.loads
app.jinja_env.filters["tojson"]    = _json.dumps   # serialize condition dicts for JS data attrs

def yaml_safe_str(val):
    if val is True:  return "Yes"
    if val is False: return "No"
    return val
app.jinja_env.filters["yaml_safe"] = yaml_safe_str
app.jinja_env.globals["yaml_safe"]  = yaml_safe_str
app.jinja_env.globals["questions_have_unknown_option"] = questions_have_unknown_option

@app.context_processor
def inject_globals():
    from flask import request as _req
    # Show the full privacy banner only on home and setup pages
    show_banner = _req.endpoint in ('home', 'setup')
    return dict(
        app_version=app.config['VERSION'],
        show_privacy_banner=show_banner,
        session_breadcrumb=None,  # overridden by individual views when inside a session
    )


# ── CSRF protection ──────────────────────────────────────────────────────────
# Lightweight double-submit cookie pattern.  A per-session token is stored in
# the Flask session (server-side, signed by secret_key) and emitted as a
# hidden field by the csrf_token() Jinja helper.  Every POST request checks
# that the submitted token matches the session token.
#
# Exempt routes: none — all POST handlers are protected.  File upload and
# JSON endpoints are included because the session cookie is present on all
# same-origin requests.

from flask import session as _flask_session

def _get_csrf_token():
    """Return the CSRF token for the current session, creating one if absent."""
    if "_csrf_token" not in _flask_session:
        secret = app.secret_key
        if isinstance(secret, str):
            secret = secret.encode()
        _flask_session["_csrf_token"] = hmac.new(
            secret, uuid.uuid4().bytes, hashlib.sha256
        ).hexdigest()
    return _flask_session["_csrf_token"]


def _check_csrf():
    """Abort with 400 if the CSRF token is missing or wrong."""
    token = _flask_session.get("_csrf_token")
    submitted = (request.form.get("_csrf_token")
                 or request.headers.get("X-CSRF-Token"))
    if not token or not submitted or not hmac.compare_digest(token, submitted):
        from flask import abort
        abort(400, "CSRF token missing or invalid. Please reload the page and try again.")


@app.before_request
def csrf_protect():
    """Validate CSRF token on every state-changing (POST/PUT/PATCH/DELETE) request."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        _check_csrf()


# Make csrf_token() available in every template without an explicit import.
app.jinja_env.globals["csrf_token"] = _get_csrf_token


MODULE_ID = "module_1"
VALID_MODULE_IDS = {"module_1", "module_2", "module_3"}


def _module_label(mid):
    """Return a human-readable label for a module_id. Used in breadcrumbs and flash messages."""
    if mid == "module_1":
        return "IT Assessment"
    if mid == "module_2":
        return "Data Governance Audit"
    if mid == "module_3":
        return "Vendor Register"
    return "Assessment"


def init_db_path():
    """Called by launcher.py to ensure the data directory exists before Flask starts."""
    from database import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_expanded_module(module_id, session_id):
    """
    Load a module and, if it has dynamic sections enabled, expand them
    using the answers already saved for this session.
    Returns (expanded_module, generated_section_ids).
    """
    module = load_module(module_id)
    if not module.get("dynamic_sections", {}).get("enabled"):
        return module, []
    answers = get_answers(session_id)
    return expand_dynamic_sections(module, answers)


def _get_module_id_for_session(session_id):
    """Return the module_id stored for a given session."""
    sess = get_session(session_id)
    return sess["module_id"] if sess else MODULE_ID


def _get_latest_module1_answers():
    """
    Return answers dict for the most recently modified Module 1 session,
    or {} if none exists. Used to prefill Module 2 with known school context.
    """
    sessions = get_all_sessions()
    for sess in sorted(sessions, key=lambda s: s["last_modified"], reverse=True):
        if sess.get("module_id", MODULE_ID) == "module_1":
            return get_answers(sess["session_id"])
    return {}


# Maps Module 2 question IDs → Module 1 question IDs that hold the same answer.
# Only used for prefill on first GET; the user can always edit afterward.
_CROSS_MODULE_PREFILL = {
    "DG1.1":  "1.7a",   # Name of person completing inventory  ← Module 1 report author name
    "DG1.1b": "1.7b",   # Role of person completing inventory  ← Module 1 report author role
    "VR1.1":  "1.7a",   # Name of person completing vendor register  ← Module 1 report author name
    "VR1.1b": "1.7b",   # Role of person completing vendor register  ← Module 1 report author role
}




# ── HOME / SESSION MANAGEMENT ──────────────────────────────────────

@app.route("/")
def home():
    profile  = get_school_profile()
    sessions = get_all_sessions()
    # Annotate each session with is_complete, total_sections, and a human label
    # Sort by created_at ascending so we can assign stable numbers
    visible = [s for s in sessions if s.get("status") != "deprecated"]
    archived = [s for s in sessions if s.get("status") == "deprecated"]
    visible_sorted = sorted(visible, key=lambda s: s.get("created_on", s.get("last_modified", "")))
    label_counter = {}
    for i, sess in enumerate(visible_sorted, 1):
        mid = sess.get("module_id", MODULE_ID)
        label_counter[sess["session_id"]] = i

    for sess in sessions:
        complete = json.loads(sess.get("sections_complete", "[]"))
        mid = sess.get("module_id", MODULE_ID)
        if mid == "module_2":
            dg1_done = "DG1" in complete
            dg2_done = "DG2" in complete
            _, gen_ids = _load_expanded_module(mid, sess["session_id"])
            all_sys_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
            sess["is_complete"] = dg1_done and dg2_done and all_sys_done
            sess["total_sections"] = 2 + len(gen_ids) if gen_ids else None
        elif mid == "module_3":
            vr1_done = "VR1" in complete
            vr2_done = "VR2" in complete
            _, gen_ids = _load_expanded_module(mid, sess["session_id"])
            all_vendor_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
            sess["is_complete"] = vr1_done and vr2_done and all_vendor_done
            sess["total_sections"] = 2 + len(gen_ids) if gen_ids else None
        else:
            sess["is_complete"] = len(complete) >= 10
            sess["total_sections"] = 10
        # Human label: "Assessment #N · Started YYYY-MM-DD"
        n = label_counter.get(sess["session_id"], "")
        started = sess.get("created_on", sess.get("last_modified", ""))[:10]
        sess["human_label"] = f"#{n} · Started {started}" if n else f"Started {started}"
    return render_template("home.html", profile=profile, sessions=sessions,
                           archived_sessions=archived)


@app.route("/setup", methods=["GET", "POST"])
def setup_profile():
    if request.method == "POST":
        school_name    = request.form.get("school_name", "").strip()
        school_website = request.form.get("school_website", "").strip()
        if not school_name or not school_website:
            flash("School name and website are required.", "error")
            return redirect(url_for("setup_profile"))
        save_school_profile(school_name, school_website)
        flash("School profile saved.", "success")
        return redirect(url_for("home"))
    profile = get_school_profile()
    return render_template("setup.html", profile=profile)


@app.route("/new_session")
def new_session():
    profile = get_school_profile()
    if not profile:
        flash("Please set up your school profile first.", "error")
        return redirect(url_for("setup_profile"))
    module_id = request.args.get("module_id", MODULE_ID)
    if module_id not in VALID_MODULE_IDS:
        flash("Unknown module type.", "error")
        return redirect(url_for("home"))
    session_id = str(uuid.uuid4())
    create_session(session_id, module_id, profile["school_name"])
    module = load_module(module_id)
    first_sec = next(
        (s["section_id"] for s in module["sections"] if not s.get("is_template")),
        module["sections"][0]["section_id"]
    )
    return redirect(url_for("section", session_id=session_id, section_id=first_sec))


@app.route("/resume/<session_id>")
def resume(session_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))
    complete = json.loads(sess["sections_complete"])
    mid = sess.get("module_id", MODULE_ID)
    module, _ = _load_expanded_module(mid, session_id)
    for s in module["sections"]:
        if s.get("is_template"):
            continue
        if s["section_id"] not in complete:
            return redirect(url_for("section", session_id=session_id,
                                    section_id=s["section_id"]))
    return redirect(url_for("summary", session_id=session_id))


# ── SECTION INTAKE ─────────────────────────────────────────────────

@app.route("/session/<session_id>/section/<section_id>", methods=["GET", "POST"])
def section(session_id, section_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    mid = _get_module_id_for_session(session_id)
    module, gen_ids = _load_expanded_module(mid, session_id)
    sec    = get_section(module, section_id)
    if not sec:
        flash("Section not found.", "error")
        return redirect(url_for("home"))

    answers = get_answers(session_id)
    profile = get_school_profile()

    # Compute inv_qid early — needed in both GET (snapshot comparison) and POST
    # (snapshot write) code paths.
    _ds = module.get("dynamic_sections", {})
    inv_qid = _ds.get("inventory_question_id") if _ds.get("enabled") else None

    # Prefill on first GET
    if request.method == "GET":
        from datetime import date as _date
        # Cross-module prefill: populate Module 2 questions from Module 1 answers
        # only when entering a Module 2 session for the first time on a question.
        m1_answers = None  # lazy-load once if needed
        for q in sec["questions"]:
            qid = q["question_id"]
            # Standard profile prefill
            if q.get("prefill") and qid not in answers and profile:
                prefill_value = profile.get(q["prefill"])
                if prefill_value:
                    save_answer(session_id, qid, prefill_value, status="answered")
            # Dynamic template prefill (e.g. system name confirmation)
            if q.get("prefill_value") and qid not in answers:
                save_answer(session_id, qid, q["prefill_value"], status="answered")
            # Special: prefill today's date for DG1.2 and VR1.2
            if qid in ("DG1.2", "VR1.2") and qid not in answers:
                save_answer(session_id, qid, _date.today().isoformat(), status="answered")
            # Special: autofill DG1.4 (system count) from DG1.3 list length
            if qid == "DG1.4":
                inv = answers.get("DG1.3", {})
                raw = inv.get("raw_answer") if inv else None
                if isinstance(raw, list) and raw:
                    save_answer(session_id, qid, len(raw), status="answered")
                elif isinstance(raw, str) and raw.strip():
                    count = len([s for s in raw.splitlines() if s.strip()])
                    if count:
                        save_answer(session_id, qid, count, status="answered")
            # Special: autofill VR1.4 (vendor count) from VR1.3 list length
            if qid == "VR1.4":
                inv = answers.get("VR1.3", {})
                raw = inv.get("raw_answer") if inv else None
                if isinstance(raw, list) and raw:
                    save_answer(session_id, qid, len(raw), status="answered")
                elif isinstance(raw, str) and raw.strip():
                    count = len([s for s in raw.splitlines() if s.strip()])
                    if count:
                        save_answer(session_id, qid, count, status="answered")
            # Cross-module prefill: pull matching answers from latest Module 1 session
            if qid in _CROSS_MODULE_PREFILL and qid not in answers:
                if m1_answers is None:
                    m1_answers = _get_latest_module1_answers()
                m1_qid = _CROSS_MODULE_PREFILL[qid]
                m1_rec = m1_answers.get(m1_qid, {})
                m1_val = m1_rec.get("raw_answer") if isinstance(m1_rec, dict) else None
                if m1_val and m1_rec.get("answer_status") == "answered":
                    save_answer(session_id, qid, m1_val, status="answered")
        answers = get_answers(session_id)

    visible_questions = get_visible_questions(sec, answers)

    if request.method == "POST":
        action = request.form.get("action", "save")

        # Determine if this section was already marked complete — if so, saves are revisions
        already_complete = section_id in json.loads(sess.get("sections_complete", "[]"))

        def _process_questions(question_list):
            """Save answers for the given list of questions from the current POST body."""
            for q in question_list:
                qid      = q["question_id"]
                atype    = q["answer_type"]
                field_key = f"q_{qid.replace('.', '_')}"

                skipped = request.form.get(f"{field_key}_skip")    == "1"
                unknown = request.form.get(f"{field_key}_unknown") == "1"

                if skipped:
                    save_answer(session_id, qid, None, status="skipped",
                                record_history=already_complete)
                    continue
                if unknown:
                    save_answer(session_id, qid, "unknown", status="unknown",
                                record_history=already_complete)
                    continue

                if atype == "multi_select":
                    raw    = request.form.getlist(field_key)
                    status = "answered" if raw else "unanswered"
                elif atype == "yes_no_unknown":
                    raw = request.form.get(field_key)
                    if raw == "unknown":
                        save_answer(session_id, qid, "unknown", status="unknown",
                                    record_history=already_complete)
                        continue
                    status = "answered" if raw else "unanswered"
                else:
                    raw    = request.form.get(field_key, "").strip()
                    status = "answered" if raw else "unanswered"

                notes = request.form.get(f"{field_key}_notes", "").strip() or None

                if atype == "list_of_items" and isinstance(raw, str):
                    items = [line.strip() for line in raw.splitlines() if line.strip()]
                    raw   = items if items else None
                    status = "answered" if raw else "unanswered"

                save_answer(session_id, qid, raw, notes=notes, status=status,
                            record_history=already_complete)

        # First pass: save answers for all questions visible BEFORE this POST.
        # This covers most questions and — crucially — saves gate/trigger answers
        # that may reveal new conditional questions.
        _process_questions(visible_questions)

        # Second pass: re-evaluate visibility with the freshly-saved answers so
        # that any questions newly revealed by this submit are also saved.
        # This prevents answers typed into newly-appeared conditional questions
        # from being silently dropped when the user submits in a single round-trip.
        updated_answers = get_answers(session_id)
        new_visible = get_visible_questions(sec, updated_answers)
        first_pass_qids = {q["question_id"] for q in visible_questions}
        newly_visible = [q for q in new_visible if q["question_id"] not in first_pass_qids]
        if newly_visible:
            _process_questions(newly_visible)

        # P2-H1: After saving answers, update the inventory snapshot if this
        # section contains the inventory question.  The snapshot records the
        # exact ordered list at the time worksheets were (re)generated, so
        # future GETs can detect reorder/rename/replacement, not just count changes.
        if inv_qid:
            saved_inv = get_answers(session_id).get(inv_qid, {})
            saved_raw = saved_inv.get("raw_answer") if saved_inv else None
            saved_list = [str(s).strip() for s in (saved_raw or []) if str(s).strip()] \
                         if isinstance(saved_raw, list) else []
            if saved_list:
                snapshot_key = f"inv_snapshot:{inv_qid}"
                # Re-expand so we know if worksheets now exist after this save
                _, post_gen_ids = _load_expanded_module(mid, session_id)
                if post_gen_ids:
                    existing_snapshot = get_session_meta(session_id, snapshot_key)
                    # Write the snapshot the first time, and re-write it only when
                    # the worksheet count has just changed (i.e. items were added/removed
                    # and saved).  Rewrites on same-count edits are intentionally NOT
                    # done here — those are exactly the cases we want to warn about.
                    if existing_snapshot is None or len(existing_snapshot) != len(post_gen_ids):
                        save_session_meta(session_id, snapshot_key, saved_list)

        # P2-H4: Save & Exit — save answers then return to home
        if action == "save_exit":
            return redirect(url_for("home"))

        if action == "complete":
            answers = get_answers(session_id)
            earned, max_pts, answered_count, skipped_count, total_q = \
                calculate_section_score(sec, answers)

            # SC3 — skip percentage check
            skip_pct = get_skip_percentage(sec, answers)
            if skip_pct > 20:
                # Flag but allow — section not marked complete, flagged at summary
                flag_session_incomplete(session_id, section_id)
                flash(
                    f"Section {section_id} has {skip_pct:.0f}% skipped questions "
                    f"— there is not enough information here to score your environment. "
                    f"Your progress has been saved. Please come back and complete this section "
                    f"before finishing the assessment.",
                    "error"
                )
                return redirect(url_for("section", session_id=session_id,
                                        section_id=section_id))

            # Count unknowns and critical unknowns
            critical_set     = CRITICAL_QUESTIONS.get(section_id, set())
            unknown_count    = sum(
                1 for q in visible_questions
                if answers.get(q["question_id"], {}).get("answer_status") == "unknown"
            )
            critical_unknowns = sum(
                1 for qid in critical_set
                if answers.get(qid, {}).get("answer_status") == "unknown"
            )

            severity = get_section_severity_label(
                earned, max_pts, unknown_count, critical_unknowns)
            mark_section_complete(session_id, section_id)

            return redirect(url_for(
                "section_complete",
                session_id=session_id,
                section_id=section_id,
                earned=int(float(earned)),
                max_pts=int(float(max_pts)),
                severity=severity,
                skip_pct=round(skip_pct),
            ))

        return redirect(url_for("section", session_id=session_id,
                                section_id=section_id))

    complete       = json.loads(sess["sections_complete"])
    total_sections = len(module["sections"])
    complete_count = len(complete)

    # For JS dynamic conditionals, we render ALL section questions in the DOM.
    # Ones that fail their condition start hidden (display:none + aria-hidden).
    # JS evaluates and toggles them live; server still authoritative on save.
    visible_qids = {q["question_id"] for q in visible_questions}
    all_questions = sec["questions"]  # full list, including gate-hidden ones

    # has_hidden_conditionals: true if any triggers_save questions exist
    # (used to show the server-round-trip hint for worksheet generation)
    has_hidden_conditionals = any(q.get("triggers_save") for q in all_questions)

    # P2-H3: Build a dict of saved values for condition dependencies that live
    # outside the current section.  JS getFieldValue() falls back to this dict
    # when a dependent field is not present in the current section DOM, so
    # cross-section conditions (e.g. 7.4 ← 6.13) behave correctly on first render.
    current_section_qids = {q["question_id"] for q in all_questions}
    condition_values = {}
    for q in all_questions:
        cond = q.get("condition")
        if cond and isinstance(cond, dict):
            dep_qid = cond.get("question_id")
            if dep_qid and dep_qid not in current_section_qids:
                dep_ans = answers.get(dep_qid, {})
                dep_val = dep_ans.get("raw_answer") if dep_ans else None
                if dep_val is not None:
                    condition_values[dep_qid] = dep_val

    # P2-H1 (upgraded): Full inventory snapshot comparison.
    # When dynamic worksheets exist, compare the current inventory list against
    # the snapshot that was saved when worksheets were first generated.
    # Detects insertions/deletions (count change), reorders, renames, and
    # same-count replacements — not just count mismatches.
    inventory_warning_type = None   # None | "count" | "order_or_content" | "both"
    inventory_warning_details = {}  # passed to template for precise copy
    if inv_qid and gen_ids:
        inv_ans = answers.get(inv_qid, {})
        current_inv = inv_ans.get("raw_answer") if inv_ans else None
        current_list = [str(s).strip() for s in (current_inv or []) if str(s).strip()] \
                       if isinstance(current_inv, list) else []

        snapshot_key = f"inv_snapshot:{inv_qid}"
        saved_snapshot = get_session_meta(session_id, snapshot_key)  # list or None

        if saved_snapshot is not None and isinstance(saved_snapshot, list):
            count_changed   = len(current_list) != len(saved_snapshot)
            content_changed = current_list != saved_snapshot
            if count_changed and content_changed:
                inventory_warning_type = "both"
            elif count_changed:
                inventory_warning_type = "count"
            elif content_changed:
                inventory_warning_type = "order_or_content"
            inventory_warning_details = {
                "current": current_list,
                "snapshot": saved_snapshot,
                "current_count": len(current_list),
                "snapshot_count": len(saved_snapshot),
                "gen_count": len(gen_ids),
            }
        elif not saved_snapshot and gen_ids:
            # Worksheets exist but no snapshot recorded yet (pre-upgrade session).
            # Write a snapshot from the current inventory so future edits are detectable.
            if current_list:
                save_session_meta(session_id, snapshot_key, current_list)

    # Backwards-compat alias so section.html can still test a single truthy flag
    inventory_reorder_warning = inventory_warning_type is not None

    module_label = _module_label(mid)
    section_label_bc = f"Section {sec.get('display_id', section_id)}: {sec['title']}"
    breadcrumb = dict(session_id=session_id, module_label=module_label, section_label=section_label_bc)

    amended_qids = get_amended_question_ids(session_id)

    return render_template(
        "section.html",
        session_id=session_id,
        section=sec,
        questions=all_questions,
        visible_qids=visible_qids,
        answers=answers,
        module=module,
        complete=complete,
        total_sections=total_sections,
        complete_count=complete_count,
        profile=profile,
        has_hidden_conditionals=has_hidden_conditionals,
        condition_values=condition_values,
        inventory_reorder_warning=inventory_reorder_warning,
        inventory_warning_type=inventory_warning_type,
        inventory_warning_details=inventory_warning_details,
        inv_qid=inv_qid,
        gen_ids_count=len(gen_ids),
        session_breadcrumb=breadcrumb,
        amended_qids=amended_qids,
    )


@app.route("/session/<session_id>/section/<section_id>/complete")
def section_complete(session_id, section_id):
    earned   = int(float(request.args.get("earned",   0)))
    max_pts  = int(float(request.args.get("max_pts",  0)))
    severity = request.args.get("severity", "unknown")
    skip_pct = int(float(request.args.get("skip_pct", 0)))

    mid = _get_module_id_for_session(session_id)
    module, gen_ids = _load_expanded_module(mid, session_id)
    sec      = get_section(module, section_id)
    sess     = get_session(session_id)
    complete = json.loads(sess["sections_complete"])

    # Find next section — skip any section flagged is_template (un-expanded
    # dynamic modules have the raw template section still in the list, which
    # is not a real destination for navigation).
    next_section = None
    sections     = module["sections"]
    for i, s in enumerate(sections):
        if s["section_id"] == section_id:
            for candidate in sections[i + 1:]:
                if not candidate.get("is_template"):
                    next_section = candidate
                    break
            break

    pct = round((earned / max_pts * 100) if max_pts > 0 else 0)

    mid_bc = _get_module_id_for_session(session_id)
    module_label_bc = _module_label(mid_bc)
    breadcrumb = dict(session_id=session_id, module_label=module_label_bc, section_label=None)

    return render_template(
        "section_complete.html",
        session_id=session_id,
        section=sec,
        earned=earned,
        max_pts=max_pts,
        pct=pct,
        severity=severity,
        skip_pct=skip_pct,
        next_section=next_section,
        complete=complete,
        module=module,
        session_breadcrumb=breadcrumb,
    )



# ── SESSION MANAGE PAGE ─────────────────────────────────────────

@app.route("/session/<session_id>/manage")
def manage_session(session_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))
    mid = sess.get("module_id", MODULE_ID)
    module_label = _module_label(mid)
    breadcrumb = dict(session_id=session_id, module_label=module_label, section_label=None)
    return render_template("manage_session.html",
        sess=sess,
        session_id=session_id,
        module_label=module_label,
        session_breadcrumb=breadcrumb,
    )


# ── DELETE / ARCHIVE SESSION ────────────────────────────────────

@app.route("/session/<session_id>/deprecate", methods=["POST"])
def deprecate_session_route(session_id):
    deprecate_session(session_id)
    flash("Assessment archived. You can view it on the Archived tab.", "success")
    return redirect(url_for("home"))


@app.route("/session/<session_id>/unarchive", methods=["POST"])
def unarchive_session_route(session_id):
    """Restore a deprecated session to in_progress status."""
    unarchive_session(session_id)
    flash("Assessment restored to your active list.", "success")
    return redirect(url_for("home"))


@app.route("/session/<session_id>/delete", methods=["POST"])
def delete_session_route(session_id):
    delete_session(session_id)
    flash("Assessment deleted.", "success")
    return redirect(url_for("home"))



# ── FINDINGS / RULES ENGINE ─────────────────────────────────────

@app.route("/session/<session_id>/findings")
def findings_full(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    answers = get_answers(session_id)
    completed = json.loads(sess.get("sections_complete", "[]"))
    report = evaluate_all(answers, session_id=session_id, completed_sections=completed)
    data = findings_to_dict(report)
    last_exported = get_last_exported(session_id)
    finding_contexts = get_finding_contexts(session_id)
    return render_template("findings.html",
        session_id=session_id,
        sess=sess,
        report=data,
        section_label=None,
        last_exported=last_exported,
        finding_contexts=finding_contexts,
    )


@app.route("/session/<session_id>/findings/<section_id>")
def findings_section(session_id, section_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    answers = get_answers(session_id)
    report = evaluate_section(answers, section_id=section_id, session_id=session_id)
    data = findings_to_dict(report)
    mid = _get_module_id_for_session(session_id)
    m, _ = _load_expanded_module(mid, session_id)
    sec = get_section(m, section_id)
    section_label = sec["title"] if sec else f"Section {section_id}"
    last_exported = get_last_exported(session_id)
    finding_contexts = get_finding_contexts(session_id)
    return render_template("findings.html",
        session_id=session_id,
        sess=sess,
        report=data,
        section_label=section_label,
        last_exported=last_exported,
        finding_contexts=finding_contexts,
    )



# ── FINDING CONTEXT NOTES ────────────────────────────────────────

@app.route("/session/<session_id>/finding-context", methods=["POST"])
def save_finding_context_route(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    finding_id = request.form.get("finding_id", "").strip()
    note = request.form.get("note", "").strip()
    if finding_id and note:
        save_finding_context(session_id, finding_id, note)
        flash("Context note saved.", "success")
    elif finding_id and not note:
        delete_finding_context(session_id, finding_id)
        flash("Context note removed.", "success")

    # Redirect back to the correct report page for this session's module.
    # The return_to hidden field in each template specifies the target;
    # we validate it against known endpoints before using it.
    return_to = request.form.get("return_to", "").strip()
    _VALID_RETURN_ROUTES = {
        "findings_full": lambda: url_for("findings_full", session_id=session_id),
        "dg_report":     lambda: url_for("dg_report",     session_id=session_id),
        "vr_report":     lambda: url_for("vr_report",     session_id=session_id),
    }
    if return_to in _VALID_RETURN_ROUTES:
        return redirect(_VALID_RETURN_ROUTES[return_to]())

    # Fallback: infer from module_id so existing sessions without return_to still work
    mid = sess.get("module_id", "module_1")
    if mid == "module_2":
        return redirect(url_for("dg_report", session_id=session_id))
    if mid == "module_3":
        return redirect(url_for("vr_report", session_id=session_id))
    return redirect(url_for("findings_full", session_id=session_id))


# ── REPORT DOWNLOAD ─────────────────────────────────────────────

@app.route("/session/<session_id>/report-setup", methods=["GET", "POST"])
def report_setup(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if sess.get("module_id", MODULE_ID) != "module_1":
        flash("This report setup is only available for IT Assessment sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        if not start_date:
            flash("Please enter a start date.", "error")
            return redirect(url_for("report_setup", session_id=session_id))
        return redirect(url_for("download_report", session_id=session_id, start_date=start_date))
    from datetime import date
    today = date.today().isoformat()
    last_exported = get_last_exported(session_id)
    return render_template("report_setup.html", session_id=session_id, today=today,
                           last_exported=last_exported)


@app.route("/session/<session_id>/report.docx")
def download_report(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))

    if sess.get("module_id", MODULE_ID) != "module_1":
        flash("This report type is only available for IT Assessment sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))

    start_date = request.args.get("start_date", "").strip() or None

    answers = get_answers(session_id)
    profile = get_school_profile()

    # Build findings
    report = evaluate_all(answers, session_id=session_id)
    report_data = findings_to_dict(report)

    # Build section scores for the report
    mid = _get_module_id_for_session(session_id)
    module, gen_ids = _load_expanded_module(mid, session_id)
    section_results = []
    for sec in module["sections"]:
        sid = sec["section_id"]
        sec_answers = get_answers(session_id)
        earned, max_pts, answered, skipped, total = calculate_section_score(sec, sec_answers)
        severity = get_section_severity_label(earned, max_pts, 0, 0)
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        section_results.append({
            "section": {"section_id": sid, "title": sec["title"]},
            "earned": int(earned),
            "max_pts": max_pts,
            "pct": pct,
            "severity": severity,
            "answered_count": answered,
            "skipped_count": skipped,
        })

    try:
        complete = json.loads(sess.get("sections_complete", "[]"))
        is_complete = len(complete) >= 10
        finding_contexts = get_finding_contexts(session_id)
        amendment_log = get_answer_history(session_id)
        docx_bytes = generate_report(report_data, answers, profile, section_results,
                                     start_date=start_date, is_complete=is_complete,
                                     finding_contexts=finding_contexts,
                                     amendment_log=amendment_log,
                                     assessment_date=sess.get("last_modified", "")[:10])
    except Exception as e:
        flash(f"Report generation failed: {e}", "error")
        return redirect(url_for("summary", session_id=session_id))

    try:
        write_trace_m1(session_id, answers, report)
    except Exception as exc:
        print(f"[TRACE] Trace generation failed (M1): {exc}")

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    filename = f"{school}_IT_Report.docx"

    set_last_exported(session_id)
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )


# ── SUMMARY ────────────────────────────────────────────────────────

@app.route("/session/<session_id>/summary")
def summary(session_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    mid = _get_module_id_for_session(session_id)
    module, gen_ids = _load_expanded_module(mid, session_id)
    answers = get_answers(session_id)
    complete = json.loads(sess["sections_complete"])
    flagged  = json.loads(sess.get("sections_flagged", "[]"))

    section_results = []
    for sec in module["sections"]:
        sid = sec["section_id"]
        if sid not in complete:
            continue
        earned, max_pts, answered_count, skipped_count, total_q = \
            calculate_section_score(sec, answers)
        visible       = get_visible_questions(sec, answers)
        critical_set  = CRITICAL_QUESTIONS.get(sid, set())
        unknown_count = sum(
            1 for q in visible
            if answers.get(q["question_id"], {}).get("answer_status") == "unknown"
        )
        critical_unknowns = sum(
            1 for qid in critical_set
            if answers.get(qid, {}).get("answer_status") == "unknown"
        )
        severity = get_section_severity_label(
            earned, max_pts, unknown_count, critical_unknowns)
        pct = round((earned / max_pts * 100) if max_pts > 0 else 0)
        section_results.append({
            "section":        sec,
            "earned":         int(float(earned)),
            "max_pts":        max_pts,
            "pct":            pct,
            "severity":       severity,
            "answered_count": answered_count,
            "skipped_count":  skipped_count,
            "flagged":        sid in flagged,
        })

    # ── Unknowns summary ──────────────────────────────────────────────
    # Aggregate unknown answers across ALL sections (complete or not) for
    # the unknowns panel on the summary page.
    unknown_summary = []
    total_unknowns  = 0
    for sec in module["sections"]:
        if sec.get("is_template"):
            continue
        sid      = sec["section_id"]
        visible  = get_visible_questions(sec, answers)
        unknowns = [
            {"question_id": q["question_id"], "prompt": q["prompt"]}
            for q in visible
            if answers.get(q["question_id"], {}).get("answer_status") == "unknown"
        ]
        if unknowns:
            unknown_summary.append({
                "section_id":    sid,
                "section_title": sec["title"],
                "unknowns":      unknowns,
            })
            total_unknowns += len(unknowns)

    breadcrumb = dict(session_id=session_id, module_label=_module_label(mid), section_label=None)

    # is_complete: used by summary to conditionally show DRAFT note
    is_complete = sess.get("is_complete", False)
    if mid == "module_2":
        dg1_done = "DG1" in complete
        dg2_done = "DG2" in complete
        all_sys_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
        is_complete = dg1_done and dg2_done and all_sys_done
    elif mid == "module_3":
        vr1_done = "VR1" in complete
        vr2_done = "VR2" in complete
        all_vendor_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
        is_complete = vr1_done and vr2_done and all_vendor_done
    else:
        is_complete = len(complete) >= 10

    return render_template(
        "summary.html",
        session_id=session_id,
        sess=sess,
        section_results=section_results,
        module=module,
        flagged=flagged,
        unknown_summary=unknown_summary,
        total_unknowns=total_unknowns,
        session_breadcrumb=breadcrumb,
        is_complete=is_complete,
    )




# ── DATA GOVERNANCE (module_2) — Report Card & Findings ────────────

@app.route("/session/<session_id>/dg_report")
def dg_report(session_id):
    """Data Governance report card — per-system grades and school-wide findings."""
    from rules_engine_dg import evaluate_dg
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    if sess.get("module_id") != "module_2":
        flash("This report is only available for Data Governance Audit sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))

    answers  = get_answers(session_id)
    module, gen_ids = _load_expanded_module("module_2", session_id)
    system_names = module.get("_system_names", [])
    dg = evaluate_dg(answers, system_names, gen_ids)

    finding_contexts = get_finding_contexts(session_id)
    last_exported = get_last_exported(session_id)
    return render_template(
        "dg_report.html",
        session_id=session_id,
        sess=sess,
        dg=dg,
        module=module,
        finding_contexts=finding_contexts,
        last_exported=last_exported,
    )


@app.route("/session/<session_id>/dg-report-setup", methods=["GET", "POST"])
def dg_report_setup(session_id):
    """Start-date picker for the Data Governance DOCX."""
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if sess.get("module_id") != "module_2":
        flash("This report setup is only available for Data Governance Audit sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        if not start_date:
            flash("Please enter a remediation start date.", "error")
            return redirect(url_for("dg_report_setup", session_id=session_id))
        return redirect(url_for("download_dg_report", session_id=session_id,
                                start_date=start_date))
    from datetime import date
    today = date.today().isoformat()
    last_exported = get_last_exported(session_id)
    return render_template("dg_report_setup.html", session_id=session_id, today=today,
                           last_exported=last_exported)


@app.route("/session/<session_id>/dg_report.docx")
def download_dg_report(session_id):
    """Generate and download the Data Governance DOCX report."""
    from rules_engine_dg import evaluate_dg
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    if sess.get("module_id") != "module_2":
        flash("This report type is only available for Data Governance Audit sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))

    start_date = request.args.get("start_date", "").strip() or None

    answers  = get_answers(session_id)
    profile  = get_school_profile()
    module, gen_ids = _load_expanded_module("module_2", session_id)
    system_names = module.get("_system_names", [])
    dg = evaluate_dg(answers, system_names, gen_ids)

    try:
        complete = json.loads(sess.get("sections_complete", "[]"))
        dg1_done = "DG1" in complete
        dg2_done = "DG2" in complete
        all_sys_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
        is_complete = dg1_done and dg2_done and all_sys_done
        finding_contexts = get_finding_contexts(session_id)
        amendment_log = get_answer_history(session_id)
        docx_bytes = generate_dg_report(dg, answers, profile, system_names, gen_ids,
                                        start_date=start_date, is_complete=is_complete,
                                        finding_contexts=finding_contexts,
                                        amendment_log=amendment_log,
                                        assessment_date=sess.get("last_modified", "")[:10])
    except Exception as e:
        flash(f"Report generation failed: {e}", "error")
        return redirect(url_for("dg_report", session_id=session_id))

    try:
        write_trace_dg(session_id, answers, dg, system_names, gen_ids)
    except Exception as exc:
        print(f"[TRACE] Trace generation failed (DG): {exc}")

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    filename = f"{school}_Data_Governance_Report.docx"

    set_last_exported(session_id)
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )

# ── VENDOR REGISTER (module_3) — Report Card & Download ────────────

@app.route("/session/<session_id>/vr_report")
def vr_report(session_id):
    """Vendor Register report card — per-vendor grades and school-wide findings."""
    from rules_engine_vr import evaluate_vr
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    if sess.get("module_id") != "module_3":
        flash("This report is only available for Vendor Register sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))

    answers = get_answers(session_id)
    module, gen_ids = _load_expanded_module("module_3", session_id)
    vendor_names = module.get("_system_names", [])
    vr = evaluate_vr(answers, vendor_names, gen_ids)

    finding_contexts = get_finding_contexts(session_id)
    last_exported = get_last_exported(session_id)
    return render_template(
        "vr_report.html",
        session_id=session_id,
        sess=sess,
        vr=vr,
        module=module,
        finding_contexts=finding_contexts,
        last_exported=last_exported,
    )


@app.route("/session/<session_id>/vr-report-setup", methods=["GET", "POST"])
def vr_report_setup(session_id):
    """Start-date picker for the Vendor Register DOCX."""
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if sess.get("module_id") != "module_3":
        flash("This report setup is only available for Vendor Register sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        if not start_date:
            flash("Please enter a remediation start date.", "error")
            return redirect(url_for("vr_report_setup", session_id=session_id))
        return redirect(url_for("download_vr_report", session_id=session_id,
                                start_date=start_date))
    from datetime import date
    today = date.today().isoformat()
    last_exported = get_last_exported(session_id)
    return render_template("vr_report_setup.html", session_id=session_id, today=today,
                           last_exported=last_exported)


@app.route("/session/<session_id>/vr_report.docx")
def download_vr_report(session_id):
    """Generate and download the Vendor Register DOCX report."""
    from rules_engine_vr import evaluate_vr
    from report_generator_vr import generate_vr_report
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    if sess.get("module_id") != "module_3":
        flash("This report type is only available for Vendor Register sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))

    start_date = request.args.get("start_date", "").strip() or None

    answers = get_answers(session_id)
    profile = get_school_profile()
    module, gen_ids = _load_expanded_module("module_3", session_id)
    vendor_names = module.get("_system_names", [])
    vr = evaluate_vr(answers, vendor_names, gen_ids)

    try:
        complete = json.loads(sess.get("sections_complete", "[]"))
        vr1_done = "VR1" in complete
        vr2_done = "VR2" in complete
        all_vendor_done = bool(gen_ids) and all(sid in complete for sid in gen_ids)
        is_complete = vr1_done and vr2_done and all_vendor_done
        finding_contexts = get_finding_contexts(session_id)
        amendment_log = get_answer_history(session_id)
        docx_bytes = generate_vr_report(vr, answers, profile, vendor_names, gen_ids,
                                        start_date=start_date, is_complete=is_complete,
                                        finding_contexts=finding_contexts,
                                        amendment_log=amendment_log,
                                        assessment_date=sess.get("last_modified", "")[:10])
    except Exception as e:
        flash(f"Report generation failed: {e}", "error")
        return redirect(url_for("vr_report", session_id=session_id))

    try:
        write_trace_vr(session_id, answers, vr, vendor_names, gen_ids)
    except Exception as exc:
        print(f"[TRACE] Trace generation failed (VR): {exc}")

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    filename = f"{school}_Vendor_Register.docx"

    set_last_exported(session_id)
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )


# ── SESSION EXPORT / IMPORT ─────────────────────────────────────

@app.route("/session/<session_id>/export")
def export_session(session_id):
    """Download a complete session snapshot as a JSON file."""
    from datetime import datetime as _dt, timezone as _tz
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    answers = get_answers(session_id)
    profile = get_school_profile()
    finding_contexts = get_finding_contexts(session_id)
    answer_history   = get_answer_history(session_id)

    export_data = {
        "export_format":    "school_it_engine_session_v1",
        "exported_on":      _dt.now(_tz.utc).isoformat() + "Z",
        "app_version":      app.config['VERSION'],
        "school_profile":   profile,
        "session":          dict(sess),
        "answers":          answers,
        "finding_contexts": finding_contexts,
        "answer_history":   answer_history,
    }

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    module_tag = sess.get("module_id", "session").replace("_", "-")
    filename   = f"{school}_{module_tag}_export.json"

    return send_file(
        io.BytesIO(json.dumps(export_data, indent=2, default=str).encode("utf-8")),
        mimetype="application/json",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/import-session", methods=["GET", "POST"])
def import_session():
    """Import a previously exported session JSON file."""
    if request.method == "GET":
        return render_template("import_session.html")

    # If the form was submitted from setup.html we get a hidden 'from_setup' field
    # so that validation errors bounce back to setup rather than the standalone import page.
    from_setup = request.form.get("from_setup") == "1"
    error_redirect = url_for("setup_profile") if from_setup else url_for("import_session")

    uploaded = request.files.get("session_file")
    if not uploaded or not uploaded.filename.endswith(".json"):
        flash("Please upload a valid .json export file.", "error")
        return redirect(error_redirect)

    try:
        raw = uploaded.read().decode("utf-8")
        data = json.loads(raw)
    except Exception:
        flash("Could not parse the file. Make sure it is a valid session export.", "error")
        return redirect(error_redirect)

    if data.get("export_format") != "school_it_engine_session_v1":
        flash("Unrecognised file format. Only School IT Engine session exports are supported.", "error")
        return redirect(error_redirect)

    sess_data = data.get("session", {})
    answers          = data.get("answers", {})
    profile          = data.get("school_profile")
    finding_contexts = data.get("finding_contexts", {})
    answer_history   = data.get("answer_history", [])

    # Restore or update school profile (only if not already set)
    existing_profile = get_school_profile()
    if not existing_profile and profile:
        save_school_profile(
            profile.get("school_name", "Imported School"),
            profile.get("school_website", ""),
        )

    # Check for existing session with same ID
    session_id = sess_data.get("session_id")
    if not session_id:
        flash("Export file is missing session_id.", "error")
        return redirect(error_redirect)

    existing = get_session(session_id)
    if existing:
        flash(
            f"A session with this ID already exists ({session_id[:8]}…). "
            "Import skipped — no changes were made.",
            "error"
        )
        return redirect(error_redirect)

    # Create the session record
    import_module_id = sess_data.get("module_id", "module_1")
    if import_module_id not in VALID_MODULE_IDS:
        flash(f"Unrecognised module ID '{import_module_id}' in export file.", "error")
        return redirect(error_redirect)
    create_session(
        session_id,
        import_module_id,
        sess_data.get("school_name", "Imported School"),
    )

    # Restore sections_complete, sections_flagged, status, and original last_modified.
    # Preserves the original last_modified from the export so report cover dates
    # reflect when the data was actually collected, not when it was imported.
    # Falls back to now only if the field is absent (legacy exports).
    from datetime import datetime as _dt, timezone as _tz
    now = _dt.now(_tz.utc).isoformat()
    original_last_modified = sess_data.get("last_modified") or now
    restore_session_state(
        session_id,
        sess_data.get("sections_complete", "[]"),
        sess_data.get("sections_flagged", "[]"),
        sess_data.get("status", "in_progress"),
        original_last_modified,
    )

    # Restore answers — touch_session=False so the answer loop does not
    # overwrite last_modified with import time on every row.
    for qid, rec in answers.items():
        save_answer(
            session_id,
            qid,
            rec.get("raw_answer"),
            notes=rec.get("notes"),
            status=rec.get("answer_status", "answered"),
            touch_session=False,
        )

    # Re-stamp the original last_modified now that all answers are written.
    # This is the final word on the timestamp — nothing after this point
    # should update last_modified for an import restore.
    restore_session_state(
        session_id,
        sess_data.get("sections_complete", "[]"),
        sess_data.get("sections_flagged", "[]"),
        sess_data.get("status", "in_progress"),
        original_last_modified,
    )

    # Restore finding context notes (may be absent in exports from older versions)
    contexts_restored = 0
    for finding_id, ctx in finding_contexts.items():
        note = ctx.get("note", "").strip() if isinstance(ctx, dict) else ""
        if note:
            save_finding_context(session_id, finding_id, note)
            contexts_restored += 1

    # Restore answer amendment history (may be absent in exports from older versions)
    history_restored = 0
    if answer_history:
        history_restored = restore_answer_history(session_id, answer_history)

    detail_parts = [f"{len(answers)} answers restored"]
    if contexts_restored:
        detail_parts.append(f"{contexts_restored} finding note{'s' if contexts_restored != 1 else ''} restored")
    if history_restored:
        detail_parts.append(f"{history_restored} amendment record{'s' if history_restored != 1 else ''} restored")

    flash(
        f"Session imported successfully — {', '.join(detail_parts)}. "
        "Review and continue from the assessment below.",
        "success"
    )
    return redirect(url_for("summary", session_id=session_id))


if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 60)
    print(f"  School IT Documentation Engine v{app.config['VERSION']}")
    print("  Running at: http://localhost:5000")
    print("  This tool runs entirely on your computer.")
    print("  No data is sent to the internet.")
    print("=" * 60 + "\n")
    # Debug mode off by default.  Set FLASK_DEBUG=1 in the environment to enable.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=5000)
