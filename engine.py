import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"


def load_module(module_id):
    path = MODULES_DIR / f"{module_id}.yaml"
    with open(str(path), encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_section(module, section_id):
    for s in module["sections"]:
        if s["section_id"] == section_id:
            return s
    return None


def evaluate_condition(condition, answers):
    if condition is None:
        return True

    ctype = condition.get("type")
    qid = condition.get("question_id")
    answer_data = answers.get(qid)
    current_value = answer_data["raw_answer"] if answer_data else None

    if ctype == "value_comparison":
        operator = condition.get("operator")
        threshold = condition.get("value")
        if current_value is None:
            return False
        try:
            numeric = int(float(str(current_value)))
        except (ValueError, TypeError):
            return False
        if operator == "greater_than":
            return numeric > threshold
        if operator == "greater_than_or_equal":
            return numeric >= threshold
        if operator == "equal":
            return numeric == threshold
        if operator == "less_than":
            return numeric < threshold

    if ctype == "answer_is":
        expected = condition.get("value")
        if isinstance(expected, list):
            return current_value in expected
        return current_value == expected

    if ctype == "answer_is_not":
        excluded = condition.get("value")
        if isinstance(excluded, list):
            return current_value not in excluded
        return current_value != excluded

    return True


def get_visible_questions(section, answers):
    return [
        q for q in section["questions"]
        if evaluate_condition(q.get("condition"), answers)
    ]


def calculate_section_score(section, answers):
    """
    Returns (earned, max_points, answered_count, total_visible_scoreable).
    answered_count counts ALL visible questions that received any response
    (answered, unknown, or skipped) — not just scored ones. This gives
    an accurate picture of how much of the section was completed.
    """
    visible = get_visible_questions(section, answers)
    max_points = 0
    earned = 0.0
    answered_count = 0

    for q in visible:
        points = q.get("points", 0)
        qid = q["question_id"]
        answer_data = answers.get(qid)
        answer_status = answer_data["answer_status"] if answer_data else "unanswered"
        raw = answer_data["raw_answer"] if answer_data else None
        notes = (answer_data.get("notes") or "") if answer_data else ""
        atype = q["answer_type"]

        # Count as answered if any response was given (including skip/unknown)
        if answer_status in ("answered", "unknown", "skipped"):
            answered_count += 1

        # Zero-point questions don't affect score
        if points == 0:
            continue

        if answer_status in ("unanswered", "skipped"):
            max_points += points
            continue

        max_points += points

        if answer_status == "unknown":
            earned += 0
            continue

        # Score by answer type
        if atype == "yes_no_unknown":
            if raw == "yes":
                earned += points

        elif atype == "single_select":
            earned += _score_single_select(qid, raw, points, notes)

        elif atype in ("short_text", "long_text"):
            if raw and str(raw).strip():
                earned += points

        elif atype == "count":
            if raw is not None and str(raw).strip():
                earned += points

        elif atype in ("list_of_items", "multi_select"):
            if raw and len(raw) > 0:
                earned += points

    total_visible = len([q for q in visible if q.get("points", 0) > 0])
    return earned, max_points, answered_count, total_visible


def _score_single_select(question_id, raw, points, notes):
    """Graduated scoring for maturity-spectrum questions."""

    # Guard against boolean values serialized oddly
    if isinstance(raw, bool):
        raw = "Yes" if raw else "No"

    graduated = {
        "2.6": {
            "Yes — formal annual budget": 1.0,
            "Yes — but informal or ad hoc": 0.5,
            "No": 0.0,
            "Unknown": 0.0,
        },
        "2.9": {
            "Yes — another person could cover fully": 1.0,
            "Partially — some things would be managed, others would not": 0.5,
            "No — operations would be significantly disrupted": 0.0,
            "Unknown": 0.0,
        },
        "2.10": {
            "Yes — fully tracked in a system": 1.0,
            "Partially — some tasks tracked, others rely on memory": 0.5,
            "No — relies on memory or informal reminders": 0.0,
            "Unknown": 0.0,
        },
        "2.11": {
            "Yes — in regular active use": 1.0,
            "Yes — but limited or inconsistent use": 0.5,
            "No": 0.0,
            "Unknown": 0.0,
        },
        "2.12": {
            "IT director or technology coordinator": 1.0,
            "Ed tech director or academic technology lead": 1.0,
            "Principal or head of school": 0.5,
            "No single person — decisions are made ad hoc": 0.0,
        },
    }

    if question_id in graduated:
        multiplier = graduated[question_id].get(raw, 0.0)
        return points * multiplier

    # Default: full credit for any non-unknown, non-empty answer
    if raw and str(raw) not in ("Unknown", "False", "false", ""):
        return points
    return 0


def get_section_severity_label(earned, max_points, unknown_count, critical_unknowns):
    if max_points == 0:
        return "context_only"

    pct = earned / max_points

    if pct >= 0.85:
        label = "healthy"
    elif pct >= 0.65:
        label = "watch"
    elif pct >= 0.40:
        label = "concern"
    else:
        label = "urgent"

    floor = "healthy"
    if unknown_count > 0:
        floor = "watch"
    if critical_unknowns > 0:
        floor = "concern"

    severity_order = ["healthy", "watch", "concern", "urgent"]
    label_idx = severity_order.index(label)
    floor_idx = severity_order.index(floor)
    return severity_order[max(label_idx, floor_idx)]


CRITICAL_QUESTIONS = {
    "2": {"2.2", "2.8", "2.9"},
}
