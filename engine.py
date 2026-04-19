import yaml
from pathlib import Path


MODULES_DIR = Path(__file__).parent / "modules"


def load_module(module_id):
    path = MODULES_DIR / f"{module_id}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def get_section(module, section_id):
    for s in module["sections"]:
        if s["section_id"] == section_id:
            return s
    return None


def evaluate_condition(condition, answers):
    """
    Evaluate a one-level condition against the current answer set.
    Returns True if the question should be shown, False if it should be hidden.
    condition is None means always show.
    """
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
            numeric = int(current_value)
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
    """Return only questions whose conditions are satisfied."""
    visible = []
    for q in section["questions"]:
        if evaluate_condition(q.get("condition"), answers):
            visible.append(q)
    return visible


def calculate_section_score(section, answers):
    """
    Calculate raw points earned and max possible points for a section.
    Returns (earned, max_points, answered_count, total_visible_count)
    """
    visible = get_visible_questions(section, answers)
    max_points = 0
    earned = 0
    answered_count = 0

    for q in visible:
        points = q.get("points", 0)
        if points == 0:
            continue  # context-only questions don't contribute

        qid = q["question_id"]
        answer_data = answers.get(qid)

        if not answer_data or answer_data["answer_status"] in ("unanswered", "skipped"):
            max_points += points
            continue

        answer_status = answer_data["answer_status"]
        raw = answer_data["raw_answer"]
        notes = answer_data.get("notes", "")
        atype = q["answer_type"]

        max_points += points
        answered_count += 1

        if answer_status == "unknown":
            # Unknown always earns 0 but still counts as answered
            earned += 0
            continue

        # Full credit answers
        if atype == "yes_no_unknown":
            if raw == "yes":
                earned += points
            elif raw == "no":
                earned += 0
            # unknown handled above

        elif atype == "single_select":
            earned += _score_single_select(qid, raw, points, notes)

        elif atype in ("short_text", "long_text", "list_of_items"):
            # Text answers earn full points if non-empty
            if raw and str(raw).strip():
                earned += points

        elif atype == "count":
            if raw is not None and str(raw).strip():
                earned += points

        elif atype == "multi_select":
            if raw and len(raw) > 0:
                earned += points

    total_visible = len([q for q in visible if q.get("points", 0) > 0])
    return earned, max_points, answered_count, total_visible


def _score_single_select(question_id, raw, points, notes):
    """
    Apply graduated scoring for known questions.
    Falls back to binary (full credit if answered) for unknown questions.
    """
    # Question-specific graduated scoring
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
    }

    if question_id in graduated:
        multiplier = graduated[question_id].get(raw, 0.0)
        return points * multiplier

    # Default: full credit for any non-unknown, non-empty answer
    if raw and raw not in ("Unknown", ""):
        return points
    return 0


def get_section_severity_label(earned, max_points, unknown_count, critical_unknowns):
    """
    Determine the severity label for a section based on score and unknown overrides.
    Returns one of: healthy, watch, concern, urgent, unknown
    """
    if max_points == 0:
        return "healthy"

    pct = earned / max_points

    # Unknown override — any unknown raises floor to watch
    if unknown_count > 0:
        floor = "watch"
    else:
        floor = "healthy"

    # Critical unknown override — critical questions unknown raises floor to concern
    if critical_unknowns > 0:
        floor = "concern"

    # Score-based label
    if pct >= 0.85:
        label = "healthy"
    elif pct >= 0.65:
        label = "watch"
    elif pct >= 0.40:
        label = "concern"
    else:
        label = "urgent"

    # Apply floor — never go below the floor
    severity_order = ["healthy", "watch", "concern", "urgent"]
    label_idx = severity_order.index(label)
    floor_idx = severity_order.index(floor)
    return severity_order[max(label_idx, floor_idx)]


# Critical questions per section for unknown override
CRITICAL_QUESTIONS = {
    "2": {"2.2", "2.8", "2.9"},
}
