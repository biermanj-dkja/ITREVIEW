"""
dynamic_engine.py  —  Dynamic section generator for School IT Engine v0.5.0

When a module declares  dynamic_sections.enabled: true,  this engine:

1.  Reads the inventory answer from the question nominated in
    dynamic_sections.inventory_question_id  (a list_of_items answer).
2.  Clones the template section (dynamic_sections.template_section_id)
    once for each system, substituting {system_name}, {system_index},
    and {system_total} throughout all prompt/help_text strings and the
    section title/description.
3.  Rewrites all question_id values in each clone so they are unique:
        SYS.A1  →  DG_SYS_3_SYS.A1   (for system 3)
    This keeps the normal answer-storage and scoring paths unchanged.
4.  Returns an augmented module dict with:
    -   The template section removed
    -   Generated per-system sections inserted between DG1 and DG2
    -   A top-level  generated_system_sections  list for the UI to use
        when building the sidebar

The function is pure — it does not modify the original module dict.
"""

import copy
import re


def _substitute(text, system_name, system_index, system_total):
    """Replace template placeholders in a string."""
    if not isinstance(text, str):
        return text
    text = text.replace("{system_name}", system_name)
    text = text.replace("{system_index}", str(system_index))
    text = text.replace("{system_total}", str(system_total))
    return text


def _make_qid(original_qid, section_prefix):
    """
    Rewrite a template question_id so it is unique per system.

    SYS.A1  →  DG_SYS_3_SYS.A1
    """
    return f"{section_prefix}_{original_qid}"


def _rewrite_condition(condition, section_prefix):
    """
    Rewrite the question_id inside a condition dict so it points to
    the cloned question in the same system section.
    """
    if condition is None:
        return None
    c = copy.deepcopy(condition)
    if "question_id" in c:
        c["question_id"] = _make_qid(c["question_id"], section_prefix)
    return c


def clone_section_for_system(template_section, system_name, system_index,
                              system_total, section_id_prefix):
    """
    Return a fully-substituted, question-id-rewritten copy of
    template_section for one system.
    """
    section = copy.deepcopy(template_section)
    section_prefix = f"{section_id_prefix}{system_index}"

    # Section-level fields
    section["section_id"] = section_prefix
    section["title"] = _substitute(
        section.get("title", "System Worksheet — {system_name}"),
        system_name, system_index, system_total
    )
    section["description"] = _substitute(
        section.get("description", ""),
        system_name, system_index, system_total
    )
    section["order"] = section.get("order", 100) + system_index
    section["is_template"] = False
    section["system_name"] = system_name
    section["system_index"] = system_index

    # Rewrite every question
    new_questions = []
    for q in section.get("questions", []):
        q = copy.deepcopy(q)
        old_qid = q["question_id"]
        q["question_id"] = _make_qid(old_qid, section_prefix)
        q["prompt"] = _substitute(
            q.get("prompt", ""), system_name, system_index, system_total
        )
        q["help_text"] = _substitute(
            q.get("help_text", ""), system_name, system_index, system_total
        )
        q["condition"] = _rewrite_condition(q.get("condition"), section_prefix)

        # Pre-fill the system name confirmation question
        if old_qid == "SYS.ID.name":
            q["prefill_value"] = system_name

        new_questions.append(q)

    section["questions"] = new_questions
    return section


def expand_dynamic_sections(module, answers):
    """
    Given a loaded module dict and the current answers dict,
    return an augmented module dict with per-system sections generated.

    If dynamic_sections is not enabled, or no inventory answer exists yet,
    returns the module unchanged (template section stripped but no clones).

    Parameters
    ----------
    module  : dict   — as returned by engine.load_module()
    answers : dict   — as returned by database.get_answers()

    Returns
    -------
    dict   — augmented module (deep copy, original unmodified)
    list   — list of generated section_ids (empty if none yet)
    """
    ds = module.get("dynamic_sections", {})
    if not ds.get("enabled"):
        return module, []

    template_id = ds.get("template_section_id", "DG_SYS_TEMPLATE")
    inventory_qid = ds.get("inventory_question_id", "DG1.3")
    prefix = ds.get("generated_section_id_prefix", "DG_SYS_")
    max_systems = ds.get("max_systems", 40)

    # Pull inventory list from answers
    inv_answer = answers.get(inventory_qid, {})
    raw = inv_answer.get("raw_answer") if inv_answer else None

    # raw is stored as a JSON list (list_of_items type)
    system_names = []
    if isinstance(raw, list):
        system_names = [str(s).strip() for s in raw if str(s).strip()]
    elif isinstance(raw, str) and raw.strip():
        # Fallback: newline-separated plain text
        system_names = [s.strip() for s in raw.splitlines() if s.strip()]

    system_names = system_names[:max_systems]

    # Find and remove the template section; collect all others
    template_section = None
    other_sections = []
    for sec in module.get("sections", []):
        if sec["section_id"] == template_id:
            template_section = sec
        else:
            other_sections.append(copy.deepcopy(sec))

    if template_section is None:
        # No template found — return as-is
        mod = copy.deepcopy(module)
        return mod, []

    # Split other_sections into before/after the template insertion point.
    # By convention DG_SYS_* sections go between DG1 and DG2.
    before = [s for s in other_sections if s["section_id"] == "DG1"]
    after  = [s for s in other_sections if s["section_id"] != "DG1"]

    # Generate clones
    system_total = len(system_names)
    generated_ids = []
    clones = []
    for i, name in enumerate(system_names, start=1):
        clone = clone_section_for_system(
            template_section, name, i, system_total, prefix
        )
        clones.append(clone)
        generated_ids.append(clone["section_id"])

    # Assemble augmented module
    mod = copy.deepcopy(module)
    mod["sections"] = before + clones + after
    mod["_generated_system_sections"] = generated_ids
    mod["_system_names"] = system_names

    return mod, generated_ids


def get_system_section_ids(module, answers):
    """
    Convenience wrapper: return only the generated section IDs.
    Used by routes that need to know the system section list without
    reassembling the whole module.
    """
    _, ids = expand_dynamic_sections(module, answers)
    return ids


def get_system_name_for_section(module_or_section, section_id):
    """
    Given an expanded module dict, return the system name for a
    generated section_id such as DG_SYS_3.
    Returns None for non-generated sections.
    """
    if isinstance(module_or_section, dict) and "sections" in module_or_section:
        for sec in module_or_section["sections"]:
            if sec["section_id"] == section_id:
                return sec.get("system_name")
    return None


def strip_section_prefix(question_id, section_id):
    """
    Given a generated question_id like  DG_SYS_3_SYS.A1
    and the section_id  DG_SYS_3,
    return the original template question_id  SYS.A1.

    Used by the rules engine to match findings rules written against
    template question IDs.
    """
    prefix = f"{section_id}_"
    if question_id.startswith(prefix):
        return question_id[len(prefix):]
    return question_id
