"""
trace.py  —  Rule evaluation trace writer

Writes a sidecar JSON file alongside report generation when the env var
FLASK_DEBUG_TRACE=1 is set. One trace file per report download, written to
data/traces/<session_id>_<module>_<timestamp>.json

The trace is the authoritative debugging record for a report run. It captures:
  - Every answer: raw value, normalized value, and status
  - Every finding that fired: id/key, title, severity, source
  - Every finding that was suppressed (Module 1) or skipped (no condition met)
  - Score calculation: per-section/system/vendor breakdown and weighted overall
  - Floor cap detail when triggered
  - Key risk groups (Module 1 only)

Usage (from app.py after report generation):
    from trace import write_trace_m1, write_trace_dg, write_trace_vr
    write_trace_m1(session_id, answers, report_obj)
    write_trace_dg(session_id, answers, dg_report_obj, system_names, gen_ids)
    write_trace_vr(session_id, answers, vr_report_obj, vendor_names, gen_ids)

Each function checks the env var internally — safe to call unconditionally.
"""

import os
import json
import datetime
from datetime import timezone as _tz
from pathlib import Path

# ── Env var gate ──────────────────────────────────────────────────

def _trace_enabled():
    return os.environ.get("FLASK_DEBUG_TRACE", "0").strip() == "1"


# ── Output path ───────────────────────────────────────────────────

def _trace_path(session_id: str, module: str) -> Path:
    ts = datetime.datetime.now(_tz.utc).strftime("%Y%m%dT%H%M%S")
    base = Path(__file__).resolve().parent / "data" / "traces"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{session_id[:8]}_{module}_{ts}.json"


# ── Answer normalizer snapshot ────────────────────────────────────
# Captures what the rules engine sees for every answered question,
# including the raw value, the normalized token, and the DB status.

def _snapshot_answers(answers: dict, module_prefix: str = "") -> dict:
    """
    Returns {qid: {raw, normalized, status}} for every question in answers.
    module_prefix filters to a specific section when set (e.g. "DG_SYS_1_").
    """
    from rules_engine import norm  # Module 1 normalizer; covers all three modules
    snapshot = {}
    for qid, data in answers.items():
        if module_prefix and not qid.startswith(module_prefix):
            continue
        raw = data.get("raw_answer")
        status = data.get("answer_status", "unanswered")
        if status == "unknown":
            normalized = "unknown"
        elif status in ("unanswered", "skipped"):
            normalized = None
        else:
            normalized = norm(raw) if not isinstance(raw, list) else raw
        snapshot[qid] = {
            "raw":        raw,
            "normalized": normalized,
            "status":     status,
        }
    return snapshot


# ── Module 1 trace ────────────────────────────────────────────────

def write_trace_m1(session_id: str, answers: dict, report) -> None:
    """
    Write a Module 1 trace file.
    report  —  FindingsReport from rules_engine.evaluate_all()
    """
    if not _trace_enabled():
        return

    fired = []
    for f in report.findings:
        fired.append({
            "finding_id":   f.finding_id,
            "rule_id":      f.rule_id,
            "section_id":   f.section_id,
            "title":        f.title,
            "severity":     f.severity,
            "risk_category": f.risk_category,
            "affected_entity": f.affected_entity,
            "aggregation_groups": f.aggregation_groups,
            "amplification_flag": f.amplification_flag,
            "constraint_flagged": f.finding_id in (report.constraint_flags or []),
            "actions": [
                {
                    "action_id":    a.action_id,
                    "time_horizon": a.time_horizon,
                    "effort":       a.effort,
                    "constraint_flag": a.constraint_flag,
                }
                for a in f.actions
            ],
        })

    suppressed = []
    for f in report.suppressed_findings:
        suppressed.append({
            "finding_id":  f.finding_id,
            "rule_id":     f.rule_id,
            "section_id":  f.section_id,
            "title":       f.title,
            "severity":    f.severity,
            "suppressed_by": f.suppressed_by,
        })

    by_sev = {
        "urgent":  [f["finding_id"] for f in fired if f["severity"] == "urgent"],
        "concern": [f["finding_id"] for f in fired if f["severity"] == "concern"],
        "watch":   [f["finding_id"] for f in fired if f["severity"] == "watch"],
    }

    trace = {
        "meta": {
            "session_id":    session_id,
            "module":        "module_1",
            "generated_at":  datetime.datetime.now(_tz.utc).isoformat() + "Z",
        },
        "normalized_answers":  _snapshot_answers(answers),
        "score_summary": {
            "sections_evaluated":  report.section_ids_evaluated,
            "finding_count":       len(report.findings),
            "suppressed_count":    len(report.suppressed_findings),
            "by_severity":         by_sev,
            "data_confidence":     report.data_confidence,
            "uncertain_sections":  report.uncertain_sections,
            "constraint_flags":    report.constraint_flags,
        },
        "findings_fired":      fired,
        "findings_suppressed": suppressed,
        "key_risk_groups":     report.key_risk_groups,
        "floor_cap":           None,  # Module 1 has no floor cap
    }

    _write(session_id, "m1", trace)


# ── Module 2 (DG) trace ───────────────────────────────────────────

def write_trace_dg(session_id: str, answers: dict, dg_report,
                   system_names: list, generated_section_ids: list) -> None:
    """
    Write a Module 2 Data Governance trace file.
    dg_report  —  DGReport from rules_engine_dg.evaluate_dg()
    """
    if not _trace_enabled():
        return

    per_system = []
    all_fired = []

    for result in dg_report.per_system_results:
        findings = []
        for f in result.findings:
            fid_key = f"{result.section_id}:{f.area[:3].upper()}"
            entry = {
                "key":       fid_key,
                "area":      f.area,
                "severity":  f.severity,
                "title":     f.title,
                "timing":    f.timing,
                "effort":    f.effort,
                "owner":     f.owner,
            }
            findings.append(entry)
            all_fired.append({**entry, "system_name": result.system_name,
                              "section_id": result.section_id})

        # Per-system answer snapshot (only questions for this system)
        sys_answers = _snapshot_answers(answers, module_prefix=f"{result.section_id}_")

        per_system.append({
            "system_name":  result.system_name,
            "section_id":   result.section_id,
            "score_pct":    result.score_pct,
            "grade":        result.grade_label,
            "severity":     result.severity,
            "earned":       result.earned,
            "max_pts":      result.max_pts,
            "data_held":    result.data_held,
            "area_scores":  {k: {"earned": v[0], "max": v[1]}
                             for k, v in result.area_scores.items()},
            "findings_fired": findings,
            "strengths":    result.strengths,
            "answers":      sys_answers,
        })

    school_wide_fired = []
    for f in dg_report.school_wide_results:
        school_wide_fired.append({
            "key":      f"DG2:{f.area[:3].upper()}",
            "area":     f.area,
            "severity": f.severity,
            "title":    f.title,
            "timing":   f.timing,
            "effort":   f.effort,
            "owner":    f.owner,
        })

    floor = None
    if dg_report.floor_cap:
        fc = dg_report.floor_cap
        floor = {
            "cap_grade":       fc.cap_grade,
            "reason":          fc.reason,
            "trigger_systems": fc.trigger_systems,
            "trigger_finding": fc.trigger_finding,
        }

    by_sev = {
        "critical": [e["key"] for e in all_fired if e["severity"] == "critical"],
        "high":     [e["key"] for e in all_fired if e["severity"] == "high"],
        "medium":   [e["key"] for e in all_fired if e["severity"] == "medium"],
        "low":      [e["key"] for e in all_fired if e["severity"] == "low"],
    }

    trace = {
        "meta": {
            "session_id":   session_id,
            "module":       "module_2",
            "generated_at": datetime.datetime.now(_tz.utc).isoformat() + "Z",
        },
        "normalized_answers": _snapshot_answers(answers),
        "score_summary": {
            "overall_grade":       dg_report.summary.overall_grade,
            "total_systems":       dg_report.summary.total_systems,
            "systems_scored":      dg_report.summary.systems_scored,
            "systems_urgent":      dg_report.summary.systems_urgent,
            "systems_concern":     dg_report.summary.systems_concern,
            "systems_watch":       dg_report.summary.systems_watch,
            "systems_healthy":     dg_report.summary.systems_healthy,
            "critical_findings":   dg_report.summary.critical_finding_count,
            "high_findings":       dg_report.summary.high_finding_count,
            "floor_cap_applied":   floor is not None,
            "by_severity":         by_sev,
        },
        "per_system":              per_system,
        "school_wide_fired":       school_wide_fired,
        "findings_fired":          all_fired,
        "findings_suppressed":     [],   # DG has no suppression chain
        "floor_cap":               floor,
        "key_risk_groups":         {},   # Not applicable for Module 2
    }

    _write(session_id, "dg", trace)


# ── Module 3 (VR) trace ───────────────────────────────────────────

def write_trace_vr(session_id: str, answers: dict, vr_report,
                   vendor_names: list, generated_section_ids: list) -> None:
    """
    Write a Module 3 Vendor Register trace file.
    vr_report  —  VRReport from rules_engine_vr.evaluate_vr()
    """
    if not _trace_enabled():
        return

    per_vendor = []
    all_fired = []

    for result in vr_report.per_vendor_results:
        findings = []
        for f in result.findings:
            fid_key = f"{result.section_id}:{f.area[:3].upper()}"
            entry = {
                "key":       fid_key,
                "area":      f.area,
                "severity":  f.severity,
                "title":     f.title,
                "timing":    getattr(f, "timing", "planned"),
                "effort":    f.effort,
                "owner":     f.owner,
            }
            findings.append(entry)
            all_fired.append({**entry, "vendor_name": result.vendor_name,
                              "section_id": result.section_id})

        # Per-vendor answer snapshot
        vendor_answers = _snapshot_answers(answers, module_prefix=f"{result.section_id}_")

        per_vendor.append({
            "vendor_name":       result.vendor_name,
            "section_id":        result.section_id,
            "score_pct":         result.score_pct,
            "grade":             result.grade_label,
            "severity":          result.severity,
            "earned":            result.earned,
            "max_pts":           result.max_pts,
            "category":          result.category,
            "weight_multiplier": result.weight_multiplier,
            "holds_student_data": result.holds_student_data,
            "holds_staff_data":   result.holds_staff_data,
            "renewal_date":      result.renewal_date,
            "auto_renews":       result.auto_renews,
            "area_scores":       {k: {"earned": v[0], "max": v[1]}
                                  for k, v in result.area_scores.items()},
            "findings_fired":    findings,
            "strengths":         result.strengths,
            "answers":           vendor_answers,
        })

    school_wide_fired = []
    for f in vr_report.school_wide_results:
        school_wide_fired.append({
            "key":      f"VR2:{f.area[:3].upper()}",
            "area":     f.area,
            "severity": f.severity,
            "title":    f.title,
            "timing":   getattr(f, "timing", "planned"),
            "effort":   f.effort,
            "owner":    f.owner,
        })

    floor = None
    if vr_report.floor_cap:
        fc = vr_report.floor_cap
        floor = {
            "cap_grade":       fc.cap_grade,
            "reason":          fc.reason,
            "trigger_vendors": fc.trigger_vendors,
            "trigger_finding": fc.trigger_finding,
        }

    by_sev = {
        "critical": [e["key"] for e in all_fired if e["severity"] == "critical"],
        "high":     [e["key"] for e in all_fired if e["severity"] == "high"],
        "medium":   [e["key"] for e in all_fired if e["severity"] == "medium"],
        "low":      [e["key"] for e in all_fired if e["severity"] == "low"],
    }

    # Renewal risk register snapshot
    renewal_register = []
    for r in vr_report.renewal_risk_register:
        renewal_register.append({
            "vendor_name":  r.vendor_name,
            "category":     r.category,
            "renewal_date": r.renewal_date,
            "auto_renews":  r.auto_renews,
            "risk_level":   r.risk_level,
            "risk_reason":  r.risk_reason,
        })

    trace = {
        "meta": {
            "session_id":   session_id,
            "module":       "module_3",
            "generated_at": datetime.datetime.now(_tz.utc).isoformat() + "Z",
        },
        "normalized_answers": _snapshot_answers(answers),
        "score_summary": {
            "overall_grade":          vr_report.summary.overall_grade,
            "total_vendors":          vr_report.summary.total_vendors,
            "vendors_scored":         vr_report.summary.vendors_scored,
            "vendors_urgent":         vr_report.summary.vendors_urgent,
            "vendors_concern":        vr_report.summary.vendors_concern,
            "vendors_watch":          vr_report.summary.vendors_watch,
            "vendors_healthy":        vr_report.summary.vendors_healthy,
            "critical_findings":      vr_report.summary.critical_finding_count,
            "high_findings":          vr_report.summary.high_finding_count,
            "vendors_with_student_data": vr_report.summary.vendors_with_student_data,
            "vendors_missing_dpa":    vr_report.summary.vendors_missing_dpa,
            "floor_cap_applied":      floor is not None,
            "by_severity":            by_sev,
        },
        "per_vendor":              per_vendor,
        "school_wide_fired":       school_wide_fired,
        "findings_fired":          all_fired,
        "findings_suppressed":     [],   # VR has no suppression chain
        "renewal_risk_register":   renewal_register,
        "floor_cap":               floor,
        "key_risk_groups":         {},   # Not applicable for Module 3
    }

    _write(session_id, "vr", trace)


# ── Writer ────────────────────────────────────────────────────────

def _write(session_id: str, module_tag: str, trace: dict) -> None:
    path = _trace_path(session_id, module_tag)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(trace, fh, indent=2, default=str)
        print(f"[TRACE] Written: {path}")
    except Exception as e:
        # Never crash report generation because of a trace write failure
        print(f"[TRACE] Write failed ({path}): {e}")
