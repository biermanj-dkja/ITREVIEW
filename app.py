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
    delete_session, save_session_meta, get_session_meta
)
from rules_engine import evaluate_all, evaluate_section, findings_to_dict
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

MODULE_ID = "module_1"


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


@app.before_request
def setup():
    init_db()


# ── HOME / SESSION MANAGEMENT ──────────────────────────────────────

@app.route("/")
def home():
    profile  = get_school_profile()
    sessions = get_all_sessions()
    # Annotate each session with is_complete — module-aware
    for sess in sessions:
        complete = json.loads(sess.get("sections_complete", "[]"))
        mid = sess.get("module_id", MODULE_ID)
        if mid == "module_2":
            # Module 2 is complete when DG1 and DG2 are done,
            # plus at least one system worksheet (DG_SYS_*).
            # We consider it complete when DG1 and DG2 are in complete
            # AND at least one DG_SYS_* section is complete.
            dg1_done = "DG1" in complete
            dg2_done = "DG2" in complete
            sys_done = any(s.startswith("DG_SYS_") for s in complete)
            sess["is_complete"] = dg1_done and dg2_done and sys_done
        else:
            sess["is_complete"] = len(complete) >= 10
    return render_template("home.html", profile=profile, sessions=sessions)


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
            # Special: prefill today's date for DG1.2
            if qid == "DG1.2" and qid not in answers:
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
        answers = get_answers(session_id)

    visible_questions = get_visible_questions(sec, answers)

    if request.method == "POST":
        action = request.form.get("action", "save")

        for q in visible_questions:
            qid      = q["question_id"]
            atype    = q["answer_type"]
            field_key = f"q_{qid.replace('.', '_')}"

            skipped = request.form.get(f"{field_key}_skip")    == "1"
            unknown = request.form.get(f"{field_key}_unknown") == "1"

            if skipped:
                save_answer(session_id, qid, None, status="skipped")
                continue
            if unknown:
                save_answer(session_id, qid, "unknown", status="unknown")
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

            save_answer(session_id, qid, raw, notes=notes, status=status)

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
    )



# ── DELETE SESSION ──────────────────────────────────────────────

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
    return render_template("findings.html",
        session_id=session_id,
        sess=sess,
        report=data,
        section_label=None,
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
    return render_template("findings.html",
        session_id=session_id,
        sess=sess,
        report=data,
        section_label=section_label,
    )



# ── REPORT DOWNLOAD ─────────────────────────────────────────────

@app.route("/session/<session_id>/report-setup", methods=["GET", "POST"])
def report_setup(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        if not start_date:
            flash("Please enter a start date.", "error")
            return redirect(url_for("report_setup", session_id=session_id))
        return redirect(url_for("download_report", session_id=session_id, start_date=start_date))
    from datetime import date
    today = date.today().isoformat()
    return render_template("report_setup.html", session_id=session_id, today=today)


@app.route("/session/<session_id>/report.docx")
def download_report(session_id):
    sess = get_session(session_id)
    if not sess:
        return redirect(url_for("home"))

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
        docx_bytes = generate_report(report_data, answers, profile, section_results,
                                     start_date=start_date)
    except Exception as e:
        flash(f"Report generation failed: {e}", "error")
        return redirect(url_for("summary", session_id=session_id))

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    filename = f"{school}_IT_Report.docx"

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

    return render_template(
        "summary.html",
        session_id=session_id,
        sess=sess,
        section_results=section_results,
        module=module,
        flagged=flagged,
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

    answers  = get_answers(session_id)
    module, gen_ids = _load_expanded_module("module_2", session_id)
    system_names = module.get("_system_names", [])
    dg = evaluate_dg(answers, system_names, gen_ids)

    return render_template(
        "dg_report.html",
        session_id=session_id,
        sess=sess,
        dg=dg,
        module=module,
    )


@app.route("/session/<session_id>/dg_report.docx")
def download_dg_report(session_id):
    """Generate and download the Data Governance DOCX report."""
    from rules_engine_dg import evaluate_dg
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    answers  = get_answers(session_id)
    profile  = get_school_profile()
    module, gen_ids = _load_expanded_module("module_2", session_id)
    system_names = module.get("_system_names", [])
    dg = evaluate_dg(answers, system_names, gen_ids)

    try:
        docx_bytes = generate_dg_report(dg, answers, profile, system_names, gen_ids)
    except Exception as e:
        flash(f"Report generation failed: {e}", "error")
        return redirect(url_for("dg_report", session_id=session_id))

    school = (profile.get("school_name") if profile else "School").replace(" ", "_")
    filename = f"{school}_Data_Governance_Report.docx"

    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )

if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 60)
    print("  School IT Documentation Engine v0.5.1")
    print("  Running at: http://localhost:5000")
    print("  This tool runs entirely on your computer.")
    print("  No data is sent to the internet.")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
