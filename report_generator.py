"""
Report Generator for Module 1 — School IT State of the System Report
Produces a DOCX file from a FindingsReport and session answers.

Usage (from app.py):
    from report_generator import generate_report
    docx_bytes = generate_report(report_data, answers, profile)
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import date

# Path to the Node.js report script (same directory as this file)
_SCRIPT_DIR = Path(__file__).resolve().parent
_NODE_SCRIPT = _SCRIPT_DIR / "report_script.js"


def _get_answer_text(answers, qid):
    """Return raw answer text for a question, or empty string."""
    data = answers.get(qid)
    if not data:
        return ""
    raw = data.get("raw_answer")
    if isinstance(raw, list):
        return ", ".join(str(x) for x in raw)
    return str(raw) if raw else ""


def _severity_label(sev):
    labels = {
        "urgent": "Urgent",
        "concern": "Concern",
        "watch": "Watch",
        "healthy": "Healthy",
        "context_only": "Context Only",
    }
    return labels.get(sev, sev.title())


def _time_horizon_label(horizon):
    labels = {
        "immediate": "Immediate",
        "next_30_days": "Within 30 days",
        "next_90_days": "Within 90 days",
        "next_12_months": "Within 12 months",
        "strategic_future": "Strategic / Future",
    }
    return labels.get(horizon, horizon)


def _schedule_label(cat):
    labels = {1: "During school year", 2: "Winter break preferred",
               3: "Spring break preferred", 4: "Summer preferred"}
    return labels.get(cat, "")


def build_report_payload(report_data, answers, profile, section_results=None):
    """
    Assemble a JSON payload describing the full report.
    The Node.js script reads this and produces the DOCX.
    """

    # ── School identity from Section 1 answers ──────────────────
    school_name     = _get_answer_text(answers, "1.1") or (profile.get("school_name") if profile else "")
    school_mission  = _get_answer_text(answers, "1.5")
    respondent_name = _get_answer_text(answers, "1.7a")
    respondent_role = _get_answer_text(answers, "1.7b")
    school_address  = _get_answer_text(answers, "1.2")
    school_website  = _get_answer_text(answers, "1.4") or (profile.get("school_website") if profile else "")
    grades_served   = _get_answer_text(answers, "1.11")
    enrollment      = _get_answer_text(answers, "1.12")
    staff_count     = _get_answer_text(answers, "1.13")
    device_count    = _get_answer_text(answers, "1.14")

    # ── Data confidence (from Section 10) ───────────────────────
    confidence      = report_data.get("data_confidence", "high")
    uncertain_secs  = report_data.get("uncertain_sections", [])

    confidence_caveat = ""
    if confidence == "moderate":
        confidence_caveat = (
            "The IT person indicated that most answers in this assessment are based on "
            "recall or staff reports rather than documented verification. Findings should "
            "be verified before action is taken."
        )
    elif confidence == "low":
        confidence_caveat = (
            "Many answers were estimated or unknown. Treat all findings as provisional "
            "until confirmed against actual system state."
        )
    elif confidence == "mixed":
        uncertain_str = ", ".join(f"Section {s}" for s in uncertain_secs) if uncertain_secs else "certain sections"
        confidence_caveat = (
            f"Data confidence varies by section. The following areas were flagged as "
            f"particularly uncertain: {uncertain_str}. Findings in those areas should "
            f"be verified before action is taken."
        )

    # ── Findings organised by severity ──────────────────────────
    findings    = report_data.get("findings", [])
    suppressed  = report_data.get("suppressed_findings", [])
    by_severity = report_data.get("by_severity", {})

    urgent_ids  = set(by_severity.get("urgent",  []))
    concern_ids = set(by_severity.get("concern", []))
    watch_ids   = set(by_severity.get("watch",   []))

    # ── Section names map ────────────────────────────────────────
    section_names = {
        "2": "Governance, Budget, Staffing, and Ownership",
        "3": "Sites, Buildings, Network, and Internet",
        "4": "Identity, Accounts, and Access",
        "5": "Endpoints, Printing, and Classroom Technology",
        "6": "Core Systems, Servers, Vendors, and Contracts",
        "7": "Data Protection, Backup, and Recovery",
        "8": "Security Operations, Filtering, and Safeguards",
        "9": "Documentation and Operational Readiness",
    }

    # ── Section scores (if available) ───────────────────────────
    scores = []
    if section_results:
        for r in section_results:
            scores.append({
                "section_id":   r["section"]["section_id"],
                "title":        r["section"]["title"],
                "earned":       r["earned"],
                "max_pts":      r["max_pts"],
                "pct":          r["pct"],
                "severity":     r["severity"],
                "answered":     r["answered_count"],
                "skipped":      r["skipped_count"],
            })

    # ── Key risk groups ──────────────────────────────────────────
    key_risks = []
    for group_id, group in report_data.get("key_risk_groups", {}).items():
        key_risks.append({
            "group_id": group_id,
            "title":    group["title"],
            "severity": group["severity"],
            "finding_ids": group["finding_ids"],
        })
    # Sort: urgent first, then concern, then watch
    sev_order = {"urgent": 0, "concern": 1, "watch": 2, "healthy": 3}
    key_risks.sort(key=lambda g: sev_order.get(g["severity"], 9))

    # ── Findings serialised with all fields ──────────────────────
    def serialise_finding(f):
        return {
            "finding_id":        f["finding_id"],
            "rule_id":           f["rule_id"],
            "section_id":        f["section_id"],
            "section_name":      section_names.get(f["section_id"], f"Section {f['section_id']}"),
            "title":             f["title"],
            "severity":          f["severity"],
            "severity_label":    _severity_label(f["severity"]),
            "description":       f["description"],
            "notes_passthrough": f.get("notes_passthrough") or "",
            "plain_language_note": f.get("plain_language_note") or "",
            "amplification_flag": f.get("amplification_flag", False),
            "aggregation_groups": f.get("aggregation_groups", []),
            "actions": [
                {
                    "action_id":       a["action_id"],
                    "description":     a["description"],
                    "time_horizon":    a["time_horizon"],
                    "horizon_label":   _time_horizon_label(a["time_horizon"]),
                    "schedule_category": a.get("schedule_category"),
                    "schedule_label":  _schedule_label(a.get("schedule_category")),
                    "constraint_flag": a.get("constraint_flag", False),
                    "user_confirmed":  a.get("user_confirmed", False),
                }
                for a in f.get("actions", [])
            ],
        }

    serialised_findings = [serialise_finding(f) for f in findings]

    # ── Findings grouped by section for section-by-section pages ─
    sections_with_findings = {}
    for f in serialised_findings:
        sid = f["section_id"]
        if sid not in sections_with_findings:
            sections_with_findings[sid] = {
                "section_id":   sid,
                "section_name": f["section_name"],
                "findings":     [],
            }
        sections_with_findings[sid]["findings"].append(f)

    # Sort findings within each section by severity then finding_id
    for sid in sections_with_findings:
        sections_with_findings[sid]["findings"].sort(
            key=lambda f: (sev_order.get(f["severity"], 9), f["finding_id"])
        )

    # ── Action plan bucketed by time horizon ────────────────────
    horizon_order = ["immediate", "next_30_days", "next_90_days",
                     "next_12_months", "strategic_future"]
    action_buckets = {h: [] for h in horizon_order}

    for f in serialised_findings:
        for act in f["actions"]:
            action_buckets[act["time_horizon"]].append({
                "finding_id":    f["finding_id"],
                "finding_title": f["title"],
                "section_id":    f["section_id"],
                "section_name":  f["section_name"],
                "severity":      f["severity"],
                "action_id":     act["action_id"],
                "description":   act["description"],
                "horizon_label": act["horizon_label"],
                "schedule_label":act["schedule_label"],
                "constraint_flag": act["constraint_flag"],
                "user_confirmed":  act["user_confirmed"],
            })

    # ── Appendix: unknown answers log ───────────────────────────
    unknown_log = []
    for qid, data in answers.items():
        if data.get("answer_status") == "unknown":
            unknown_log.append({
                "question_id": qid,
                "section_id":  qid.split(".")[0],
            })
    unknown_log.sort(key=lambda x: (x["section_id"], x["question_id"]))

    # ── Appendix: full response log ─────────────────────────────
    response_log = []
    for qid, data in sorted(answers.items()):
        response_log.append({
            "question_id": qid,
            "section_id":  qid.split(".")[0],
            "status":      data.get("answer_status", "unanswered"),
            "answer":      str(data.get("raw_answer", "")) if data.get("raw_answer") else "",
        })

    # ── Assemble full payload ────────────────────────────────────
    payload = {
        "meta": {
            "report_date":       date.today().isoformat(),
            "school_name":       school_name,
            "school_mission":    school_mission,
            "school_address":    school_address,
            "school_website":    school_website,
            "respondent_name":   respondent_name,
            "respondent_role":   respondent_role,
            "grades_served":     grades_served,
            "enrollment":        enrollment,
            "staff_count":       staff_count,
            "device_count":      device_count,
            "confidence":        confidence,
            "confidence_caveat": confidence_caveat,
            "uncertain_sections": uncertain_secs,
        },
        "summary": {
            "finding_count":   len(findings),
            "urgent_count":    len(urgent_ids),
            "concern_count":   len(concern_ids),
            "watch_count":     len(watch_ids),
            "suppressed_count": len(suppressed),
        },
        "scores":                    scores,
        "key_risks":                 key_risks,
        "findings":                  serialised_findings,
        "sections_with_findings":    list(sections_with_findings.values()),
        "action_buckets":            action_buckets,
        "horizon_order":             horizon_order,
        "horizon_labels": {
            "immediate":        "Immediate",
            "next_30_days":     "Within 30 Days",
            "next_90_days":     "Within 90 Days",
            "next_12_months":   "Within 12 Months",
            "strategic_future": "Strategic / Future",
        },
        "suppressed_findings":  [serialise_finding(f) for f in suppressed],
        "unknown_log":          unknown_log,
        "response_log":         response_log,
    }

    return payload


def generate_report(report_data, answers, profile, section_results=None):
    """
    Generate a DOCX report and return it as bytes.
    Raises RuntimeError on failure.
    """
    payload = build_report_payload(report_data, answers, profile, section_results)

    with tempfile.TemporaryDirectory() as tmp:
        payload_path = os.path.join(tmp, "payload.json")
        output_path  = os.path.join(tmp, "report.docx")

        with open(payload_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

        result = subprocess.run(
            ["node", str(_NODE_SCRIPT), payload_path, output_path],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Report generation failed:\n{result.stderr}\n{result.stdout}"
            )

        with open(output_path, "rb") as f:
            return f.read()
