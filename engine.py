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
    """
    Evaluate a one-level condition against the current answer set.
    Returns True if the question should be shown.
    None means always show.
    """
    if condition is None:
        return True

    ctype = condition.get("type")
    qid = condition.get("question_id")
    answer_data = answers.get(qid)
    current_value = answer_data["raw_answer"] if answer_data else None

    # Normalise booleans that may have leaked through YAML parsing
    if isinstance(current_value, bool):
        current_value = "yes" if current_value else "no"

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


def get_gate_status(section, answers):
    """
    Find any gate question in this section and determine whether it is
    currently firing negatively (i.e. its answer is in gate_negative_values).

    Returns (gate_question_id, is_negative) or (None, False) if no gate.
    """
    for q in section["questions"]:
        if not q.get("is_gate"):
            continue
        qid = q["question_id"]
        answer_data = answers.get(qid)
        if not answer_data:
            continue
        raw = answer_data.get("raw_answer")
        if isinstance(raw, bool):
            raw = "yes" if raw else "no"
        negative_values = q.get("gate_negative_values", [])
        # Normalise comparison — gate_negative_values are stored as strings
        if raw in negative_values:
            return qid, True
    return None, False


def get_visible_questions(section, answers):
    """
    Return questions whose conditions are satisfied.
    If a gate question has fired negatively, all questions that depend
    on the gate (i.e. any non-gate question that is not the gate itself)
    are hidden. Gate-dependent questions are identified as those whose
    condition references the gate question, OR any question that appears
    after the gate with no condition of its own (within the same section).
    The gate question itself is always visible.
    """
    gate_qid, gate_fired = get_gate_status(section, answers)

    visible = []
    for q in section["questions"]:
        qid = q["question_id"]

        # Gate question is always shown
        if q.get("is_gate"):
            visible.append(q)
            continue

        # If gate has fired negatively, hide all non-gate questions
        # whose condition references the gate OR that have no condition
        # (they were implicitly dependent on backups/EP existing)
        if gate_fired:
            cond = q.get("condition")
            if cond is None:
                # Unconditional questions in a gated section are hidden
                # when the gate fires — they assume the gated thing exists
                continue
            if cond.get("question_id") == gate_qid:
                # Explicitly depends on the gate question
                continue
            # Questions conditional on something else are evaluated normally
            if evaluate_condition(cond, answers):
                visible.append(q)
            continue

        # Normal evaluation
        if evaluate_condition(q.get("condition"), answers):
            visible.append(q)

    return visible


def get_gated_hidden_questions(section, answers):
    """
    Return question_ids of questions hidden because a gate fired negatively.
    These questions stay in the denominator at 0 points.
    """
    gate_qid, gate_fired = get_gate_status(section, answers)
    if not gate_fired:
        return set()

    hidden = set()
    for q in section["questions"]:
        if q.get("is_gate"):
            continue
        cond = q.get("condition")
        if cond is None:
            hidden.add(q["question_id"])
        elif cond.get("question_id") == gate_qid:
            hidden.add(q["question_id"])
    return hidden


def calculate_section_score(section, answers):
    """
    Returns (earned, max_points, answered_count, skipped_count, total_visible).

    Scoring rules:
    - Skipped questions are REMOVED from the denominator (max_points not incremented)
    - Unknown answers stay in denominator and earn 0 points
    - Gate-hidden questions stay in denominator at 0 points (penalised for not having the thing)
    - Context-only questions (0 points) never affect the denominator
    """
    visible = get_visible_questions(section, answers)
    gated_hidden = get_gated_hidden_questions(section, answers)

    max_points = 0
    earned = 0.0
    answered_count = 0
    skipped_count = 0

    # Score visible questions
    for q in visible:
        points = q.get("points", 0)
        qid = q["question_id"]
        answer_data = answers.get(qid)
        answer_status = answer_data["answer_status"] if answer_data else "unanswered"
        raw = answer_data["raw_answer"] if answer_data else None
        notes = (answer_data.get("notes") or "") if answer_data else ""
        atype = q["answer_type"]

        if answer_status in ("answered", "unknown"):
            answered_count += 1
        elif answer_status == "skipped":
            skipped_count += 1

        if points == 0:
            continue

        # Skipped: remove from denominator
        if answer_status == "skipped":
            continue

        # Unanswered: keep in denominator, earn 0
        max_points += points

        if answer_status == "unknown":
            continue  # 0 earned

        if answer_status == "unanswered":
            continue  # 0 earned

        # Score by type
        if atype == "yes_no_unknown":
            if raw == "yes":
                earned += points

        elif atype == "single_select":
            earned += _score_single_select(qid, raw, points, notes)

        elif atype in ("short_text", "long_text"):
            if raw and str(raw).strip():
                earned += points

        elif atype == "count":
            earned += score_count_question(qid, raw, points)

        elif atype in ("list_of_items", "multi_select"):
            if raw and len(raw) > 0:
                earned += points

    # Add gated-hidden questions to denominator at 0 points
    for q in section["questions"]:
        if q["question_id"] in gated_hidden:
            points = q.get("points", 0)
            if points > 0:
                max_points += points
            # 0 added to earned — full penalty

    total_visible = len([q for q in visible if q.get("points", 0) > 0])
    return earned, max_points, answered_count, skipped_count, total_visible


def get_skip_percentage(section, answers):
    """
    Return the percentage of scoreable visible questions that were skipped.
    Used for SC3 completion warning logic.
    """
    visible = get_visible_questions(section, answers)
    scoreable = [q for q in visible if q.get("points", 0) > 0]
    if not scoreable:
        return 0.0
    skipped = sum(
        1 for q in scoreable
        if answers.get(q["question_id"], {}).get("answer_status") == "skipped"
    )
    return (skipped / len(scoreable)) * 100


def questions_have_unknown_option(q):
    """
    Return True if a question has an Unknown option in its options list.
    Used by the template to suppress the 'I don't know' tick box.
    """
    if q.get("answer_type") not in ("single_select",):
        return False
    options = q.get("options", [])
    return any(
        str(opt).strip().lower() in ("unknown", '"unknown"')
        for opt in options
    )


def _score_single_select(question_id, raw, points, notes):
    """Graduated scoring for maturity-spectrum questions."""
    if isinstance(raw, bool):
        raw = "Yes" if raw else "No"

    graduated = {
        # Section 2
        "2.6": {
            "Yes — formal annual budget": 1.0,
            "Yes — but informal or ad hoc": 0.5,
            "No": 0.0, "Unknown": 0.0,
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
            "No": 0.0, "Unknown": 0.0,
        },
        "2.12": {
            "IT director or technology coordinator": 1.0,
            "Ed tech director or academic technology lead": 1.0,
            "Principal or head of school": 0.5,
            "No single person — decisions are made ad hoc": 0.0,
        },
        # Section 3
        "3.2": {
            "Yes — current and accurate": 1.0,
            "Yes — but outdated": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "3.13_count": {},  # handled separately via count type
        "3.15": {
            "Yes — load balancing and automatic failover to a secondary connection": 1.0,
            "Yes — automatic failover to a secondary connection": 1.0,
            "Yes — manual failover (requires someone to switch it)": 0.5,
            "No — single connection with no backup": 0.0,
            "Unknown": 0.0,
        },
        # Section 4
        "4.3": {
            "Yes — documented and followed consistently": 1.0,
            "Informal — process exists but is either not documented or not always followed or both": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "4.4": {
            "Yes — documented and followed consistently": 1.0,
            "Informal — process exists but is either not documented or not always followed or both": 0.4,
            "No": 0.0, "Unknown": 0.0,
        },
        "4.5": {
            "Yes — documented and followed consistently": 1.0,
            "Informal — process exists but is either not documented or not always followed or both": 0.5,
            "No": 0.0, "Unknown": 0.0,
            "Not applicable — school does not manage student accounts": 1.0,
        },
        "4.6": {
            "Yes — all privileged accounts have MFA": 1.0,
            "Partial — some privileged accounts have MFA": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "4.6b": {
            "Yes — required for all staff": 1.0,
            "Partial — encouraged but not enforced for all staff": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "4.7": {
            "Yes — reviewed within the last 12 months": 1.0,
            "Yes — but outdated (not reviewed in over 12 months)": 0.4,
            "No": 0.0, "Unknown": 0.0,
        },
        "4.8": {
            "Yes — shared accounts are minimal and documented": 1.0,
            "Partially — some shared accounts exist without formal justification": 0.5,
            "No — shared accounts are common and not tracked": 0.0,
            "Unknown": 0.0,
        },
        # Section 5
        "5.1": {
            "Yes — current and reasonably complete": 1.0,
            "Partial — exists but incomplete or outdated": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "5.5": {
            "Yes — most devices managed": 1.0,
            "Partial — some devices managed": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "5.9": {
            "Yes — documented refresh cycle": 1.0,
            "Informal — refresh cycle defined but not followed": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "5.10": {
            "None known — all devices are within supported life": 1.0,
            "Some — a small number of unsupported devices in use": 0.5,
            "Many — a significant portion of the fleet is unsupported": 0.0,
            "Unknown": 0.0,
        },
        # Section 6
        "6.3": {
            "Yes — current list in use": 1.0,
            "Partial — incomplete or informal list": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "6.8": {
            "Yes — tracked in a calendar or system with reminders": 1.0,
            "Partial — some renewals tracked, others not": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "6.9": {
            "Yes — documented for all critical vendors": 1.0,
            "Partial — documented for some vendors": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        # Section 7
        "7.1": {
            "Yes — confirmed and verified": 1.0,
            "Maybe or assumed — believed to be in place but not verified": 0.4,
            "No": 0.0, "Unknown": 0.0,
        },
        "7.7": {
            "Yes — reviewed regularly (at least weekly)": 1.0,
            "Irregularly — checked occasionally but not on a schedule": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "7.7b": {
            "Both — onsite and offsite copies maintained": 1.0,
            "Offsite only — stored in cloud or remote location": 0.67,
            "Onsite only — stored at the school": 0.33,
            "Inconsistent — some backups are both, some are only one location": 0.33,
            "Unknown": 0.0,
        },
        "7.8": {
            "Yes — tested and documented within the last 12 months": 1.0,
            "More than 12 months ago": 0.4,
            "No — never tested": 0.0,
            "Unknown": 0.0,
        },
        "7.12": {
            "Yes — securely stored and accessible to authorized backup person": 1.0,
            "Partially — some credentials accessible, others not": 0.4,
            "No": 0.0, "Unknown": 0.0,
        },
        # Section 8
        "8.1": {
            "Yes — deployed on most managed devices": 1.0,
            "Partial — deployed on some devices": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "8.2b": {
            "Yes — alerts and trends are reviewed regularly": 1.0,
            "Sometimes — reviewed occasionally but not consistently": 0.5,
            "No": 0.0,
            "Endpoint protection does not notify us centrally": 0.0,
        },
        "8.3": {
            "Yes — documented patching schedule with defined response windows": 1.0,
            "Informal — patching happens but not on a defined schedule": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "8.4": {
            "Yes — reviewed regularly (at least twice per year)": 1.0,
            "Irregularly — reviewed occasionally": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "8.5": {
            "Yes — for students and staff": 1.0,
            "Yes — for students only": 0.75,
            "Limited or partial coverage": 0.4,
            "No": 0.0, "Unknown": 0.0,
        },
        "8.8": {
            "Yes — documented process exists": 1.0,
            "Partial — informal notes or partial documentation": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "8.10b": {
            "Yes": 1.0,
            "No": 0.0,
        },
        "8.10c": {
            "Yes — our response steps match the policy requirements": 1.0,
            "Partial — some of our steps match their requirements": 0.5,
            "No": 0.0,
            "I don't know": 0.0,
        },
        # Section 9
        "9.1": {
            "Yes — well used and reasonably complete": 1.0,
            "Yes — but used inconsistently": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "9.2": {
            "Yes — most documentation is current": 1.0,
            "Partly — some is current, some is outdated": 0.5,
            "No — documentation is generally outdated": 0.0,
            "Unknown": 0.0,
        },
        "9.3": {
            "Yes — SOPs exist for most recurring tasks": 1.0,
            "Partial — some tasks are documented": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "9.4": {
            "Yes — changes are documented as part of the process": 1.0,
            "Informal — sometimes documented, sometimes not": 0.5,
            "No": 0.0, "Unknown": 0.0,
        },
        "9.5": {
            "Yes — documentation is sufficient for a qualified person to get oriented": 1.0,
            "Partially — they could understand some areas but not others": 0.4,
            "No — the environment is not understandable from documentation alone": 0.0,
            "Unknown": 0.0,
        },
    }

    if question_id in graduated:
        multiplier = graduated[question_id].get(raw, 0.0)
        return points * multiplier

    if raw and str(raw) not in ("Unknown", "False", "false", ""):
        return points
    return 0


def score_count_question(question_id, raw, points):
    """Special scoring for count-type questions with threshold rules."""
    if question_id == "3.13":
        try:
            n = int(float(str(raw)))
            return points if n >= 2 else 0
        except (ValueError, TypeError):
            return 0
    # Default: any non-empty count earns full points
    if raw is not None and str(raw).strip():
        return points
    return 0


def get_section_severity_label(earned, max_points, unknown_count, critical_unknowns):
    """Return severity label with unknown floor overrides."""
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


# Critical questions per section — unknowns raise floor to concern
CRITICAL_QUESTIONS = {
    "2": {"2.2", "2.8", "2.9"},
    "3": {"3.7", "3.12", "3.15", "3.18"},
    "4": {"4.4", "4.6", "4.7"},
    "5": {"5.1", "5.5", "5.10"},
    "6": {"6.3", "6.8", "6.16"},
    "7": {"7.1", "7.8", "7.12"},
    "8": {"8.1", "8.5", "8.8"},
    "9": {"9.1", "9.5", "9.6"},
}
