"""
Timeline builder for the phased remediation plan.

Given a list of Action dicts (from findings_to_dict) and a start date,
produces Phase 1–4 blocks with estimated date ranges and a re-run note.

Effort day-weights:
    S   → 0.5 days
    S+  → 1   day
    M   → 3   days
    M+  → 5   days
    L   → 10  days

Phase mapping:
    Phase 1 → immediate          (starts on start_date)
    Phase 2 → next_30_days       (starts at max(P1 end, start + 14 days))
    Phase 3 → next_90_days       (starts at max(P2 end, P2 start + 14 days))
    Phase 4 → next_12_months     (starts at max(P3 end, P3 start + 30 days))

Re-run note logic:
    If Phase 1 has > 1 item  → strong declarative note appended after Phase 1
    If Phase 1 has 0 or 1    → gentle iterative suggestion appended after Phase 3
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

EFFORT_DAYS = {
    "S":   0.5,
    "S+":  1.0,
    "M":   3.0,
    "M+":  5.0,
    "L":  10.0,
}

PHASE_HORIZON = {
    1: "immediate",
    2: "next_30_days",
    3: "next_90_days",
    4: "next_12_months",
}

PHASE_LABEL = {
    1: "Phase 1 — Immediate Actions",
    2: "Phase 2 — Within 30 Days",
    3: "Phase 3 — Within 90 Days",
    4: "Phase 4 — Within 12 Months",
}

RERUN_STRONG = (
    "⚡ Re-assessment recommended: with {n} immediate actions addressed, "
    "a follow-up review after Phase 1 completion will confirm risk reduction "
    "and may adjust priorities for subsequent phases."
)

RERUN_GENTLE = (
    "Once Phase 3 is complete, consider scheduling a brief follow-up review "
    "to reassess your IT posture before committing to Phase 4 initiatives."
)


def _days_for_phase(actions: list) -> float:
    """Sum effort day-weights for a list of action dicts."""
    total = 0.0
    for act in actions:
        effort = act.get("effort") or "M"   # default M if missing
        total += EFFORT_DAYS.get(effort, 3.0)
    return max(total, 0.5)   # at least half a day if anything exists


def _end_date(start: date, days: float) -> date:
    """Return end date by rounding up fractional days."""
    return start + timedelta(days=int(days) if days == int(days) else int(days) + 1)


def build_timeline(findings: list, start_date: date) -> dict:
    """
    findings   — list of finding dicts from findings_to_dict()
    start_date — date object for when work begins

    Returns a dict:
    {
      "start_date": date,
      "phases": [
        {
          "phase": 1,
          "label": "Phase 1 — Immediate Actions",
          "horizon": "immediate",
          "start": date,
          "end": date,
          "duration_days": float,
          "actions": [ {action fields + finding_id, finding_title, severity} ],
          "rerun_note": str | None,
        },
        ...
      ],
      "strategic_actions": [ ... ],   # next_12_months are Phase 4; strategic_future excluded
      "total_actions": int,
    }
    """

    # Flatten all actions from all findings, tagged with finding context
    flat_actions = []
    for f in findings:
        for act in f.get("actions", []):
            flat_actions.append({
                **act,
                "finding_id":    f["finding_id"],
                "finding_title": f["title"],
                "severity":      f["severity"],
                "section_id":    f["section_id"],
            })

    # Bucket by phase
    phase_actions = {1: [], 2: [], 3: [], 4: [], 0: []}   # 0 = strategic_future
    for act in flat_actions:
        h = act.get("time_horizon", "")
        if   h == "immediate":        phase_actions[1].append(act)
        elif h == "next_30_days":     phase_actions[2].append(act)
        elif h == "next_90_days":     phase_actions[3].append(act)
        elif h == "next_12_months":   phase_actions[4].append(act)
        else:                         phase_actions[0].append(act)  # strategic_future

    # --- Phase date calculations ---
    # Phase 1
    p1_start = start_date
    p1_days  = _days_for_phase(phase_actions[1]) if phase_actions[1] else 0
    p1_end   = _end_date(p1_start, p1_days) if p1_days else p1_start

    # Phase 2: max(P1 end, start + 14 days)
    p2_start = max(p1_end, start_date + timedelta(days=14))
    p2_days  = _days_for_phase(phase_actions[2]) if phase_actions[2] else 0
    p2_end   = _end_date(p2_start, p2_days) if p2_days else p2_start

    # Phase 3: max(P2 end, P2 start + 14 days)
    p3_start = max(p2_end, p2_start + timedelta(days=14))
    p3_days  = _days_for_phase(phase_actions[3]) if phase_actions[3] else 0
    p3_end   = _end_date(p3_start, p3_days) if p3_days else p3_start

    # Phase 4: max(P3 end, P3 start + 30 days)
    p4_start = max(p3_end, p3_start + timedelta(days=30))
    p4_days  = _days_for_phase(phase_actions[4]) if phase_actions[4] else 0
    p4_end   = _end_date(p4_start, p4_days) if p4_days else p4_start

    phase_dates = {
        1: (p1_start, p1_end, p1_days),
        2: (p2_start, p2_end, p2_days),
        3: (p3_start, p3_end, p3_days),
        4: (p4_start, p4_end, p4_days),
    }

    # Re-run note logic
    p1_count = len(phase_actions[1])
    rerun_after = None   # which phase number gets the note appended
    rerun_text  = None

    if p1_count > 1:
        rerun_after = 1
        rerun_text  = RERUN_STRONG.format(n=p1_count)
    else:
        rerun_after = 3
        rerun_text  = RERUN_GENTLE

    # Build output
    phases = []
    for ph in [1, 2, 3, 4]:
        acts = phase_actions[ph]
        s, e, d = phase_dates[ph]
        phases.append({
            "phase":         ph,
            "label":         PHASE_LABEL[ph],
            "horizon":       PHASE_HORIZON[ph],
            "start":         s,
            "end":           e,
            "duration_days": d,
            "actions":       acts,
            "rerun_note":    rerun_text if ph == rerun_after and rerun_text else None,
        })

    return {
        "start_date":       start_date,
        "phases":           phases,
        "strategic_actions": phase_actions[0],
        "total_actions":    sum(len(v) for v in phase_actions.values()),
    }
