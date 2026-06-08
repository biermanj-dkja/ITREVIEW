import uuid
import json
import io
import os
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
    deprecate_session
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
app.secret_key = "school-it-engine-dev-key-change-in-production"
app.config['VERSION'] = '0.8.3'

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

MODULE_ID = "module_1"


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


@app.before_request
def setup():
    init_db()


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

        for q in visible_questions:
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
                raw    = request.form.get(field_key)
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

    module_label = ("IT Assessment" if mid == "module_1"
                    else "Vendor Register" if mid == "module_3"
                    else "Data Governance")
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

    # Find next section and its time estimate
    next_section = None
    sections     = module["sections"]
    for i, s in enumerate(sections):
        if s["section_id"] == section_id and i + 1 < len(sections):
            next_section = sections[i + 1]
            break

    pct = round((earned / max_pts * 100) if max_pts > 0 else 0)

    mid_bc = _get_module_id_for_session(session_id)
    module_label_bc = "IT Assessment" if mid_bc == "module_1" else "Data Governance"
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
    module_label = "IT Assessment" if mid == "module_1" else "Data Governance Audit"
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
    db = __import__("database").get_db()
    from datetime import datetime as _dt
    now = _dt.utcnow().isoformat()
    db.execute(
        "UPDATE assessment_session SET status='in_progress', last_modified=? WHERE session_id=?",
        (now, session_id)
    )
    db.commit()
    db.close()
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
    report = evaluate_all(answers, session_id=session_id, completed_sections=None)
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
    return redirect(url_for("findings_full", session_id=session_id))


# ── REPORT DOWNLOAD ─────────────────────────────────────────────

@app.route("/session/<session_id>/report-setup", methods=["GET", "POST"])
def report_setup(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if sess.get("module_id", MODULE_ID) != "module_1":
        flash("This page is only available for IT Assessment sessions.", "error")
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

    if mid == "module_1":
        module_label = "IT Assessment"
    elif mid == "module_2":
        module_label = "Data Governance"
    else:
        module_label = "Vendor Register"
    breadcrumb = dict(session_id=session_id, module_label=module_label, section_label=None)

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
        flash("This page is only available for Data Governance Audit sessions.", "error")
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
    """Start-date picker for the Data Governance DOCX — identical flow to report_setup."""
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if sess.get("module_id") != "module_2":
        flash("This page is only available for Data Governance Audit sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        # start_date is optional — blank means no timeline section
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
        flash("This page is only available for Vendor Register sessions.", "error")
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
        flash("This page is only available for Vendor Register sessions.", "error")
        return redirect(url_for("summary", session_id=session_id))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
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
    from datetime import datetime as _dt
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    answers = get_answers(session_id)
    profile = get_school_profile()

    export_data = {
        "export_format":  "school_it_engine_session_v1",
        "exported_on":    _dt.utcnow().isoformat() + "Z",
        "app_version":    app.config['VERSION'],
        "school_profile": profile,
        "session":        dict(sess),
        "answers":        answers,
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
    answers   = data.get("answers", {})
    profile   = data.get("school_profile")

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
    create_session(
        session_id,
        sess_data.get("module_id", "module_1"),
        sess_data.get("school_name", "Imported School"),
    )

    # Restore sections_complete, sections_flagged, status, and original last_modified.
    # Preserve the original last_modified from the export so the dual-date logic on
    # report covers reflects when the data was actually collected, not when it was
    # imported.  Fall back to now only if the field is absent (legacy exports).
    db_obj = __import__("database")
    db = db_obj.get_db()
    from datetime import datetime as _dt
    now = _dt.utcnow().isoformat()
    original_last_modified = sess_data.get("last_modified") or now
    db.execute("""
        UPDATE assessment_session
        SET sections_complete=?, sections_flagged=?, status=?, last_modified=?
        WHERE session_id=?
    """, (
        sess_data.get("sections_complete", "[]"),
        sess_data.get("sections_flagged", "[]"),
        sess_data.get("status", "in_progress"),
        original_last_modified,
        session_id,
    ))
    db.commit()
    db.close()

    # Restore answers
    for qid, rec in answers.items():
        save_answer(
            session_id,
            qid,
            rec.get("raw_answer"),
            notes=rec.get("notes"),
            status=rec.get("answer_status", "answered"),
        )

    flash(
        f"Session imported successfully — {len(answers)} answers restored. "
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
    app.run(debug=True, port=5000)
