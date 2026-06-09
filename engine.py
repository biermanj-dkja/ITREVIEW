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

    Gate logic:
    - If a gate question has fired negatively, all directly dependent
      questions are hidden (those with no condition, or whose condition
      references the gate question).
    - CASCADE: questions whose condition references a hidden question are
      also hidden, regardless of their stored answer. This prevents
      sub-conditional questions from bleeding through when their parent
      is hidden by a gate.
    - The gate question itself is always visible.
    """
    gate_qid, gate_fired = get_gate_status(section, answers)

    # Build the set of hidden question IDs (gate-hidden + cascades)
    # We do this in two passes so cascades are resolved correctly.
    hidden_ids = set()

    if gate_fired:
        # Pass 1: identify directly gate-hidden questions.
        # If the gate has gate_hides_unconditional=True, ALL unconditional
        # questions in the section are hidden (e.g. Section 7 — no backups
        # means all backup questions are irrelevant).
        # Otherwise only questions whose condition explicitly references
        # the gate question are hidden (e.g. Section 8 — no EP deployment
        # only hides the EP-specific follow-up questions).
        gate_q = next((q for q in section["questions"] if q.get("is_gate")), None)
        hides_unconditional = gate_q.get("gate_hides_unconditional", False) if gate_q else False

        for q in section["questions"]:
            if q.get("is_gate"):
                continue
            cond = q.get("condition")
            if cond is None:
                if hides_unconditional:
                    hidden_ids.add(q["question_id"])
                # else: unconditional questions remain visible
            elif cond.get("question_id") == gate_qid:
                hidden_ids.add(q["question_id"])

        # Pass 2: cascade — hide questions whose condition references
        # any already-hidden question. Repeat until stable.
        changed = True
        while changed:
            changed = False
            for q in section["questions"]:
                qid = q["question_id"]
                if qid in hidden_ids or q.get("is_gate"):
                    continue
                cond = q.get("condition")
                if cond and cond.get("question_id") in hidden_ids:
                    hidden_ids.add(qid)
                    changed = True

    visible = []
    for q in section["questions"]:
        qid = q["question_id"]

        # Gate question always shown
        if q.get("is_gate"):
            visible.append(q)
            continue

        # Hidden by gate or cascade
        if qid in hidden_ids:
            continue

        # Normal condition evaluation
        if evaluate_condition(q.get("condition"), answers):
            visible.append(q)

    return visible


def get_gated_hidden_questions(section, answers):
    """
    Return question_ids of questions hidden because a gate fired negatively.
    These questions stay in the denominator at 0 points.

    Mirrors the same gate_hides_unconditional logic used by get_visible_questions()
    so the two functions agree on which questions are hidden — preventing double-
    counting visible questions in the denominator (A2 fix).
    """
    gate_qid, gate_fired = get_gate_status(section, answers)
    if not gate_fired:
        return set()

    gate_q = next((q for q in section["questions"] if q.get("is_gate")), None)
    hides_unconditional = gate_q.get("gate_hides_unconditional", False) if gate_q else False

    hidden = set()
    for q in section["questions"]:
        if q.get("is_gate"):
            continue
        cond = q.get("condition")
        if cond is None:
            if hides_unconditional:
                hidden.add(q["question_id"])
            # else: unconditional questions remain visible — do NOT add to hidden
        elif cond.get("question_id") == gate_qid:
            hidden.add(q["question_id"])

    # Cascade: also hide questions whose condition references any already-hidden question
    changed = True
    while changed:
        changed = False
        for q in section["questions"]:
            qid = q["question_id"]
            if qid in hidden or q.get("is_gate"):
                continue
            cond = q.get("condition")
            if cond and cond.get("question_id") in hidden:
                hidden.add(qid)
                changed = True

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
            inverted = q.get("inverted", False)
            if inverted:
                # Inverted: "no" = good = full points, "yes" = problem = partial/zero
                if raw == "no":
                    earned += points
                elif raw == "yes":
                    # Partial credit for knowing about the problem (per design doc)
                    earned += points * 0.5
            else:
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

    # ── Additional explicit maps (A1 fix) ──────────────────────────────────
    # Every scored single_select question must have an entry here.
    # The fallback below scores 0 for any unmapped question so gaps are
    # conservative rather than permissive.
    additional = {
        # Section 2
        "2.1": {
            # Context question — 1 pt, any non-empty answer is informative
            "Internal IT staff (one or more dedicated IT employees)":   1.0,
            "Single IT director (one person responsible for everything)": 1.0,
            "Outsourced MSP (managed service provider handles IT)":     1.0,
            "Hybrid — internal staff plus MSP":                         1.0,
            "Volunteer or ad hoc support (no dedicated IT role)":       1.0,
            "Other":                                                     1.0,
        },
        # Section 3
        "3.1": {
            "Yes — current and reasonably accurate": 1.0,
            "Partial — some buildings or areas covered": 0.5,
            "No": 0.0,
        },
        "3.3": {
            "Yes — current for all locations": 1.0,
            "Partial — some locations documented": 0.5,
            "No": 0.0,
        },
        "3.4": {
            "Yes — all locations are known and documented": 1.0,
            "Partial — most are known, some are not": 0.5,
            "No": 0.0,
        },
        "3.6": {
            "Yes — current inventory with model and firmware": 1.0,
            "Partial — some information documented": 0.5,
            "No": 0.0,
        },
        "3.9": {
            "Yes — current inventory with model and firmware": 1.0,
            "Partial — some information documented": 0.5,
            "No": 0.0,
        },
        "3.10": {
            "Yes — current and accurate": 1.0,
            "Partial — some connections documented": 0.5,
            "No": 0.0,
        },
        "3.11": {
            "Yes — fully documented with support status": 1.0,
            "Partial — some information documented": 0.5,
            "No": 0.0,
        },
        "3.12": {
            "Yes — full admin access to all infrastructure": 1.0,
            "Partial — admin access to some but not all devices": 0.5,
            "No — access is controlled by a vendor or MSP": 0.0,
        },
        "3.17": {
            "Yes — fully known and documented": 1.0,
            "Partial — some information known": 0.5,
            "No": 0.0,
        },
        "3.18": {
            "Yes — configurations are backed up regularly": 1.0,
            "Partial — some devices backed up, others not": 0.5,
            "No": 0.0,
        },
        "3.19": {
            "Yes — coverage is adequate throughout": 1.0,
            "Mixed — some areas have coverage problems": 0.5,
            "No — coverage is a known problem": 0.0,
        },
        "3.20": {
            "Yes — all segments documented": 1.0,
            "Partial — some segments documented": 0.5,
            "No": 0.0,
            "Unknown — not sure if VLANs are in use": 0.0,
        },
        "3.21": {
            "Yes — fully protected": 1.0,
            "Partial — some equipment protected, some not": 0.5,
            "No": 0.0,
        },
        "3.22": {
            "Yes — documented and tested": 1.0,
            "Estimated only — not formally tested": 0.5,
            "No": 0.0,
        },
        "3.23": {
            "Yes — monitored with alerting": 1.0,
            "Partial — some monitored": 0.5,
            "No": 0.0,
        },
        "3.24": {
            "Yes — regularly scanned": 1.0,
            "Occasionally — ad hoc or infrequent": 0.5,
            "No": 0.0,
        },
        # Section 4
        "4.1": {
            # Context question — 1 pt, platform identification only
            "Google Workspace":                                          1.0,
            "Microsoft 365":                                             1.0,
            "Hybrid — Google and Microsoft both in active use":          1.0,
            "Local or on-premises systems only":                         1.0,
            "Other":                                                     1.0,
        },
        "4.2": {
            "Yes — cloud-based (Azure AD, Google Directory, etc.)": 1.0,
            "Yes — on-premises (Windows Active Directory)":         1.0,
            "Yes — hybrid (both cloud and on-premises)":            1.0,
            "No": 0.0,
        },
        "4.9": {
            "Yes — documented for all major platforms": 1.0,
            "Partial — documented for some platforms":  0.5,
            "No": 0.0,
        },
        "4.10": {
            "Yes — all staff devices sync consistently": 1.0,
            "Partial — some devices or some folders only": 0.5,
            "No": 0.0,
        },
        # Section 5
        "5.2": {
            "Yes — all key fields present": 1.0,
            "Partial — some fields missing": 0.5,
            "No": 0.0,
        },
        "5.6": {
            "Yes — documented hardware standard in use": 1.0,
            "Partial — informal preference but not documented": 0.5,
            "No": 0.0,
        },
        "5.7": {
            "Yes — standardized": 1.0,
            "Partially — mostly standardized with some exceptions": 0.5,
            "No": 0.0,
        },
        "5.8": {
            "Yes — defined process or imaging/MDM enrollment in place": 1.0,
            "Partially — possible but inconsistent":                    0.5,
            "No — each setup is manual and varies":                     0.0,
        },
        "5.11": {
            "Yes — tracked for all devices":    1.0,
            "Partial — tracked for some devices": 0.5,
            "No": 0.0,
        },
        "5.12": {
            "Yes — spare pool and process defined":              1.0,
            "Partial — some spares available but no formal process": 0.5,
            "No": 0.0,
        },
        "5.13": {
            "Yes — documented process in use": 1.0,
            "Partial — informal process":      0.5,
            "No": 0.0,
        },
        "5.17": {
            "Yes — all tracked":       1.0,
            "Partial — some tracked":  0.5,
            "No": 0.0,
        },
        # Section 6
        "6.4": {
            "Yes — all key fields present": 1.0,
            "Partial — some fields missing": 0.5,
            "No": 0.0,
        },
        "6.6": {
            "Yes — fully tracked":             1.0,
            "Partial — some information tracked": 0.5,
            "No": 0.0,
        },
        "6.7": {
            "Yes — reviewed for most student-data systems": 1.0,
            "Partial — reviewed for some": 0.5,
            "No": 0.0,
        },
        "6.14": {
            "Yes — fully documented":          1.0,
            "Partial — some information documented": 0.5,
            "No": 0.0,
        },
        "6.15": {
            "Yes — all servers have documented purposes": 1.0,
            "Partial — some documented": 0.5,
            "No": 0.0,
        },
        "6.16": {
            "Yes — fully documented and accessible":       1.0,
            "Partial — some access methods documented":    0.5,
            "No": 0.0,
        },
        "6.17": {
            "Yes — documented patching schedule":                  1.0,
            "Informal — patching happens but on no defined schedule": 0.5,
            "No": 0.0,
        },
        "6.18": {
            "Yes — known for all servers":    1.0,
            "Partial — known for some servers": 0.5,
            "No": 0.0,
        },
        "6.19": {
            "Yes — documented lifecycle plan": 1.0,
            "Informal — planned informally":   0.5,
            "No": 0.0,
        },
        # Section 7
        "7.3": {
            "Yes — documented scope":                            1.0,
            "Partial — some systems documented, others not":     0.5,
            "No": 0.0,
        },
        "7.4": {
            "Yes — all servers backed up":      1.0,
            "Partial — some servers backed up": 0.5,
            "No": 0.0,
            "Not applicable": 1.0,
        },
        "7.5": {
            "Yes — staff devices are backed up":     1.0,
            "Partial — some staff devices backed up": 0.5,
            "No": 0.0,
            "Not applicable — staff work entirely in cloud storage": 1.0,
        },
        "7.6": {
            "Yes — critical cloud data is backed up": 1.0,
            "Partial — some cloud data backed up":    0.5,
            "No": 0.0,
            "Not applicable": 1.0,
        },
        "7.9": {
            # Recovery testing frequency — more frequent = better
            "Quarterly":          1.0,
            "Twice per year":     1.0,
            "Annually":           0.75,
            "Less than annually": 0.25,
            "Never":              0.0,
        },
        "7.10": {
            "Yes — recovery priority is documented":                    1.0,
            "Partial — informally understood but not documented":       0.5,
            "No": 0.0,
        },
        "7.11": {
            "Yes — written reference exists":                    1.0,
            "Partial — informal notes or partial documentation": 0.5,
            "No": 0.0,
        },
        "7.13": {
            # RTO — shorter is better
            "Less than 1 week":    1.0,
            "1 to 2 weeks":        0.75,
            "2 to 4 weeks":        0.5,
            "1 to 3 months":       0.25,
            "More than 3 months":  0.0,
        },
        "7.14": {
            "Yes": 1.0,
            "No":  0.0,
        },
        # Section 8
        "8.7": {
            "Yes — controls are documented":           1.0,
            "Partial — some documentation exists":     0.5,
            "No": 0.0,
        },
        "8.9": {
            "Yes — reviewed regularly":              1.0,
            "Sometimes — reviewed occasionally":     0.5,
            "No": 0.0,
        },
        "8.10": {
            "Yes": 1.0,
            "No":  0.0,
        },
    }

    # Check primary graduated map, then additional map.
    # If found in either, use that multiplier.
    if question_id in graduated:
        multiplier = graduated[question_id].get(raw, 0.0)
        return points * multiplier

    if question_id in additional:
        multiplier = additional[question_id].get(raw, 0.0)
        return points * multiplier

    # Fail-closed: any scored single_select question not in either map scores 0.
    # This prevents bad answers from earning full credit for unmapped questions.
    # If a new question is added to the YAML without a scoring map, it will score
    # conservatively (0) rather than permissively (full points).
    return 0.0


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
