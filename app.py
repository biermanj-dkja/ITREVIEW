import uuid
import json
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import (
    init_db, save_answer, get_answers, get_answer, create_session,
    get_session, mark_section_complete, get_all_sessions,
    save_school_profile, get_school_profile
)
from engine import (
    load_module, get_section, get_visible_questions,
    calculate_section_score, get_section_severity_label, CRITICAL_QUESTIONS
)

# Resolve the directory this file lives in.
# This ensures templates and modules are found correctly on Windows
# regardless of what directory Python is invoked from.
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
)
app.secret_key = "school-it-engine-dev-key-change-in-production"

# Custom Jinja2 filters
import json as _json
app.jinja_env.filters["from_json"] = _json.loads

MODULE_ID = "module_1"


@app.before_request
def setup():
    init_db()


# HOME / SESSION MANAGEMENT

@app.route("/")
def home():
    profile = get_school_profile()
    sessions = get_all_sessions()
    return render_template("home.html", profile=profile, sessions=sessions)


@app.route("/setup", methods=["GET", "POST"])
def setup_profile():
    if request.method == "POST":
        school_name = request.form.get("school_name", "").strip()
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
    session_id = str(uuid.uuid4())
    create_session(session_id, MODULE_ID, profile["school_name"])
    return redirect(url_for("section", session_id=session_id, section_id="1"))


@app.route("/resume/<session_id>")
def resume(session_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))
    complete = json.loads(sess["sections_complete"])
    module = load_module(MODULE_ID)
    for s in module["sections"]:
        if s["section_id"] not in complete:
            return redirect(url_for("section", session_id=session_id, section_id=s["section_id"]))
    return redirect(url_for("summary", session_id=session_id))


# SECTION INTAKE

@app.route("/session/<session_id>/section/<section_id>", methods=["GET", "POST"])
def section(session_id, section_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    module = load_module(MODULE_ID)
    sec = get_section(module, section_id)
    if not sec:
        flash("Section not found.", "error")
        return redirect(url_for("home"))

    answers = get_answers(session_id)
    profile = get_school_profile()

    if request.method == "GET":
        for q in sec["questions"]:
            qid = q["question_id"]
            if q.get("prefill") and qid not in answers and profile:
                prefill_value = profile.get(q["prefill"])
                if prefill_value:
                    save_answer(session_id, qid, prefill_value, status="answered")
        answers = get_answers(session_id)

    visible_questions = get_visible_questions(sec, answers)

    if request.method == "POST":
        action = request.form.get("action", "save")

        for q in visible_questions:
            qid = q["question_id"]
            atype = q["answer_type"]
            field_key = f"q_{qid.replace('.', '_')}"

            skipped = request.form.get(f"{field_key}_skip") == "1"
            unknown = request.form.get(f"{field_key}_unknown") == "1"

            if skipped:
                save_answer(session_id, qid, None, status="skipped")
                continue

            if unknown:
                save_answer(session_id, qid, "unknown", status="unknown")
                continue

            if atype == "multi_select":
                raw = request.form.getlist(field_key)
                status = "answered" if raw else "unanswered"
            elif atype == "yes_no_unknown":
                raw = request.form.get(field_key)
                status = "answered" if raw else "unanswered"
            else:
                raw = request.form.get(field_key, "").strip()
                status = "answered" if raw else "unanswered"

            notes = request.form.get(f"{field_key}_notes", "").strip() or None

            if atype == "list_of_items" and isinstance(raw, str):
                items = [line.strip() for line in raw.splitlines() if line.strip()]
                raw = items if items else None
                status = "answered" if raw else "unanswered"

            save_answer(session_id, qid, raw, notes=notes, status=status)

        if action == "complete":
            answers = get_answers(session_id)
            earned, max_pts, answered_count, total_q = calculate_section_score(sec, answers)

            critical_set = CRITICAL_QUESTIONS.get(section_id, set())
            unknown_count = sum(
                1 for q in visible_questions
                if answers.get(q["question_id"], {}).get("answer_status") == "unknown"
            )
            critical_unknowns = sum(
                1 for qid in critical_set
                if answers.get(qid, {}).get("answer_status") == "unknown"
            )

            severity = get_section_severity_label(earned, max_pts, unknown_count, critical_unknowns)
            mark_section_complete(session_id, section_id)

            return redirect(url_for(
                "section_complete",
                session_id=session_id,
                section_id=section_id,
                earned=earned,
                max_pts=max_pts,
                severity=severity
            ))

        return redirect(url_for("section", session_id=session_id, section_id=section_id))

    complete = json.loads(sess["sections_complete"])
    total_sections = len(module["sections"])
    complete_count = len(complete)

    return render_template(
        "section.html",
        session_id=session_id,
        section=sec,
        questions=visible_questions,
        answers=answers,
        module=module,
        complete=complete,
        total_sections=total_sections,
        complete_count=complete_count,
        profile=profile,
    )


@app.route("/session/<session_id>/section/<section_id>/complete")
def section_complete(session_id, section_id):
    earned = int(float(request.args.get("earned", 0)))
    max_pts = int(float(request.args.get("max_pts", 0)))
    severity = request.args.get("severity", "unknown")

    module = load_module(MODULE_ID)
    sec = get_section(module, section_id)
    sess = get_session(session_id)
    complete = json.loads(sess["sections_complete"])

    next_section = None
    sections = module["sections"]
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
        next_section=next_section,
        complete=complete,
        module=module,
    )


# SUMMARY

@app.route("/session/<session_id>/summary")
def summary(session_id):
    sess = get_session(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for("home"))

    module = load_module(MODULE_ID)
    answers = get_answers(session_id)
    complete = json.loads(sess["sections_complete"])

    section_results = []
    for sec in module["sections"]:
        sid = sec["section_id"]
        if sid not in complete:
            continue
        earned, max_pts, answered_count, total_q = calculate_section_score(sec, answers)
        visible = get_visible_questions(sec, answers)
        critical_set = CRITICAL_QUESTIONS.get(sid, set())
        unknown_count = sum(
            1 for q in visible
            if answers.get(q["question_id"], {}).get("answer_status") == "unknown"
        )
        critical_unknowns = sum(
            1 for qid in critical_set
            if answers.get(qid, {}).get("answer_status") == "unknown"
        )
        severity = get_section_severity_label(earned, max_pts, unknown_count, critical_unknowns)
        pct = round((earned / max_pts * 100) if max_pts > 0 else 0)
        section_results.append({
            "section": sec,
            "earned": earned,
            "max_pts": max_pts,
            "pct": pct,
            "severity": severity,
            "answered_count": answered_count,
        })

    return render_template(
        "summary.html",
        session_id=session_id,
        sess=sess,
        section_results=section_results,
        module=module,
    )


if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 60)
    print("  School IT Documentation Engine")
    print("  Running at: http://localhost:5000")
    print("  This tool runs entirely on your computer.")
    print("  No data is sent to the internet.")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
