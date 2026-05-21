"""
test_scoring.py  —  Automated scoring and golden fixture tests
v0.8.0

Run with:  python test_scoring.py
           python test_scoring.py --fixtures-only
           python test_scoring.py --scoring-only

Exit code 0 = all tests passed.
Exit code 1 = one or more failures.

─────────────────────────────────────────────────────────────────────────────
PART A — Section scoring mechanics (Module 1)
    Tests that individual question answers produce correct point values,
    gate logic works, and unknown-floor rules escalate severity correctly.

PART B — Golden fixture tests (all three modules)
    Three fixture schools per module: Strong, Typical (Bit-By-Bit Academy),
    and High-Risk. Each fixture asserts:
      - Which finding IDs (M1) or finding keys (M2/M3) fired
      - Which fired at each severity tier
      - Overall grade (M2/M3) or finding count (M1)
      - Floor cap fired or not (M2/M3)
      - Data confidence / school-wide finding count

    The expected values below were recorded from a known-good run and are the
    authoritative baseline. Any deviation means a rule changed — intentional
    or not.
─────────────────────────────────────────────────────────────────────────────
"""

import uuid
import json
import sys
import os
import argparse

# ── arg parsing ──────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--fixtures-only", action="store_true")
parser.add_argument("--scoring-only",  action="store_true")
args, _ = parser.parse_known_args()
RUN_SCORING  = not args.fixtures_only
RUN_FIXTURES = not args.scoring_only

# ── imports ───────────────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, save_answer, get_answers, create_session
from engine import (
    load_module, get_section, get_visible_questions,
    calculate_section_score, get_section_severity_label, CRITICAL_QUESTIONS
)
from rules_engine import evaluate_all, findings_to_dict
from rules_engine_dg import evaluate_dg
from rules_engine_vr import evaluate_vr
from dynamic_engine import expand_dynamic_sections
import yaml

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TESTDATA_DIR = os.path.join(BASE_DIR, "TESTDATA")
MODULES_DIR  = os.path.join(BASE_DIR, "modules")

init_db()
m1 = load_module("module_1")

PASS = 0
FAIL = 0
FAILURES = []


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✓ {label}")
        PASS += 1
    else:
        msg = f"  ✗ FAIL: {label}"
        if detail:
            msg += f"  ({detail})"
        print(msg)
        FAILURES.append(f"{label} — {detail}" if detail else label)
        FAIL += 1


def new_sid(module="module_1", school="ScoreTest"):
    sid = str(uuid.uuid4())
    create_session(sid, module, school)
    return sid


def score_section(section_id, answer_dict):
    sid = new_sid()
    sec = get_section(m1, section_id)
    for qid, val in answer_dict.items():
        save_answer(sid, qid, val, status="answered")
    answers = get_answers(sid)
    earned, max_pts, answered, skipped, total = calculate_section_score(sec, answers)
    return earned, max_pts, answers, sid


def score_section_with_unknowns(section_id, answer_dict, unknown_ids):
    sid = new_sid()
    sec = get_section(m1, section_id)
    for qid, val in answer_dict.items():
        save_answer(sid, qid, val, status="answered")
    for qid in unknown_ids:
        save_answer(sid, qid, "unknown", status="unknown")
    answers = get_answers(sid)
    earned, max_pts, answered, skipped, total = calculate_section_score(sec, answers)
    return earned, max_pts, answers


def wrap(raw_dict):
    """Wrap a plain {qid: value} dict into the format rules engines expect."""
    return {qid: {"raw_answer": val, "answer_status": "answered"}
            for qid, val in raw_dict.items()}


# ═════════════════════════════════════════════════════════════════════════════
# PART A — SECTION SCORING MECHANICS
# ═════════════════════════════════════════════════════════════════════════════

if RUN_SCORING:
    print("\n" + "═" * 60)
    print("PART A — Section scoring mechanics")
    print("═" * 60)

    # ── Section 1 ─────────────────────────────────────────────────
    print("\nSection 1: School Identity (context only)")
    earned, max_pts, answers, _ = score_section("1", {
        "1.1": "Test School", "1.2": "123 Main St", "1.7a": "Alex",
        "1.8": "1", "1.9": "3", "1.11": "K-12", "1.12": "400",
        "1.13": "60", "1.14": "500", "1.16": "Summer refresh",
    })
    check("Max points = 0 (context only)", max_pts == 0)
    check("Severity = context_only", get_section_severity_label(earned, max_pts, 0, 0) == "context_only")

    # ── Section 2 ─────────────────────────────────────────────────
    print("\nSection 2: Governance")
    best2 = {
        "2.1": "Single IT director (one person responsible for everything)",
        "2.2": "yes", "2.3": "yes", "2.4": "yes", "2.5": "yes",
        "2.6": "Yes — formal annual budget",
        "2.7": "yes",
        "2.8": "yes",
        "2.9": "Yes — another person could cover fully",
        "2.10": "Yes — fully tracked in a system",
        "2.11": "Yes — in regular active use",
        "2.12": "IT director or technology coordinator",
    }
    earned, max_pts, answers, _ = score_section("2", best2)
    check(f"Perfect score earns full points ({int(earned)}/{max_pts})", earned == max_pts)
    check("Perfect score = healthy", get_section_severity_label(earned, max_pts, 0, 0) == "healthy")

    partial2 = dict(best2)
    partial2["2.9"] = "Partially — some things would be managed, others would not"
    earned2, max2, _, _ = score_section("2", partial2)
    check("2.9 partial earns less than perfect", earned2 < earned)

    high_answers = {k: v for k, v in best2.items() if k != "2.2"}
    earned3, max3, answers3 = score_section_with_unknowns("2", high_answers, ["2.2"])
    sev3 = get_section_severity_label(earned3, max3, 1, 1)
    check("Critical unknown (2.2) raises floor to concern", sev3 == "concern")

    # ── Section 3 ─────────────────────────────────────────────────
    print("\nSection 3: Network")
    best3 = {
        "3.1": "Yes — current and reasonably accurate",
        "3.2": "Yes — current and accurate", "3.3": "Yes — current for all locations",
        "3.4": "Yes — all locations are known and documented",
        "3.6": "Yes — current inventory with model and firmware",
        "3.7": "yes",
        "3.9": "Yes — current inventory with model and firmware",
        "3.10": "Yes — current and accurate",
        "3.11": "Yes — fully documented with support status",
        "3.12": "Yes — full admin access to all infrastructure",
        "3.13": "2",
        "3.15": "Yes — load balancing and automatic failover to a secondary connection",
        "3.17": "Yes — fully known and documented",
        "3.18": "Yes — configurations are backed up regularly",
        "3.19": "Yes — coverage is adequate throughout",
        "3.20": "Yes — all segments documented",
        "3.21": "Yes — fully protected",
        "3.22": "Yes — documented and tested",
        "3.23": "Yes — monitored with alerting",
        "3.24": "Yes — regularly scanned",
        "3.26": "no",
    }
    earned3, max3, _, _ = score_section("3", best3)
    check(f"Section 3 perfect score ({int(earned3)}/{max3})", earned3 == max3, f"expected {max3}")

    earned_1conn, _, _, _ = score_section("3", dict(best3, **{"3.13": "1"}))
    check("3.13 with 1 connection scores less than 2+", earned_1conn < earned3)

    # ── Section 4 ─────────────────────────────────────────────────
    print("\nSection 4: Identity")
    best4 = {
        "4.1": "Google Workspace", "4.1b": "yes",
        "4.2": "Yes — cloud-based (Azure AD, Google Directory, etc.)",
        "4.3": "Yes — documented and followed consistently",
        "4.4": "Yes — documented and followed consistently",
        "4.5": "Yes — documented and followed consistently",
        "4.6": "Yes — all privileged accounts have MFA",
        "4.6b": "Yes — required for all staff",
        "4.7": "Yes — reviewed within the last 12 months",
        "4.8": "Yes — shared accounts are minimal and documented",
        "4.9": "Yes — documented for all major platforms",
        "4.10": "Yes — all staff devices sync consistently",
    }
    earned4, max4, _, _ = score_section("4", best4)
    check(f"Section 4 perfect score ({int(earned4)}/{max4})", earned4 == max4)

    inf4 = dict(best4)
    inf4["4.4"] = "Informal — process exists but is either not documented or not always followed or both"
    earned4i, _, _, _ = score_section("4", inf4)
    check("4.4 informal gets partial credit", 0 < earned4i < max4 + 1)

    # ── Section 5 ─────────────────────────────────────────────────
    print("\nSection 5: Endpoints")
    best5 = {
        "5.1": "Yes — current and reasonably complete",
        "5.2": "Yes — all key fields present",
        "5.3": "Yes — all relevant grades are 1:1",
        "5.4": "Yes — all student devices go home",
        "5.5": "Yes — most devices managed",
        "5.6": "Yes — documented hardware standard in use",
        "5.7": "Yes — standardized",
        "5.8": "Yes — defined process or imaging/MDM enrollment in place",
        "5.9": "Yes — documented refresh cycle",
        "5.10": "None known — all devices are within supported life",
        "5.11": "Yes — tracked for all devices",
        "5.12": "Yes — spare pool and process defined",
        "5.13": "Yes — documented process in use",
        "5.17": "Yes — all tracked",
    }
    earned5, max5, _, _ = score_section("5", best5)
    check(f"Section 5 perfect score ({int(earned5)}/{max5})", earned5 == max5)

    bad5 = dict(best5)
    bad5["5.10"] = "Many — a significant portion of the fleet is unsupported"
    earned5b, _, _, _ = score_section("5", bad5)
    check("5.10 many unsupported earns less", earned5b < earned5)

    # ── Section 6 ─────────────────────────────────────────────────
    print("\nSection 6: Systems and Vendors")
    best6 = {
        "6.3": "Yes — current list in use",
        "6.4": "Yes — all key fields present",
        "6.6": "Yes — fully tracked",
        "6.7": "Yes — reviewed for most student-data systems",
        "6.8": "Yes — tracked in a calendar or system with reminders",
        "6.9": "Yes — documented for all critical vendors",
        "6.10": "no", "6.11": "no", "6.13": "0",
    }
    earned6, max6, _, _ = score_section("6", best6)
    check(f"Section 6 no-server score earns points ({int(earned6)}/{max6})", earned6 > 0)

    best6s = dict(best6, **{
        "6.13": "2", "6.14": "Yes — fully documented",
        "6.15": "Yes — all servers have documented purposes",
        "6.16": "Yes — fully documented and accessible",
        "6.17": "Yes — documented patching schedule",
        "6.18": "Yes — known for all servers",
        "6.19": "Yes — documented lifecycle plan",
    })
    earned6s, max6s, _, _ = score_section("6", best6s)
    check("Section 6 with servers has higher max points", max6s > max6)

    # ── Section 7 ─────────────────────────────────────────────────
    print("\nSection 7: Backup and Recovery")
    sec7 = get_section(m1, "7")
    sid7n = new_sid()
    save_answer(sid7n, "7.1", "No", status="answered")
    ans7n = get_answers(sid7n)
    e7n, m7n, _, _, _ = calculate_section_score(sec7, ans7n)
    check(f"Gate=No backup: zero earned, large max ({int(e7n)}/{m7n})", e7n == 0 and m7n > 10)
    check("Gate=No backup: severity = urgent", get_section_severity_label(e7n, m7n, 0, 0) == "urgent")

    best7 = {
        "7.1": "Yes — confirmed and verified",
        "7.3": "Yes — documented scope",
        "7.5": "Yes — staff devices are backed up",
        "7.6": "Yes — critical cloud data is backed up",
        "7.7": "Yes — reviewed regularly (at least weekly)",
        "7.7b": "Both — onsite and offsite copies maintained",
        "7.8": "Yes — tested and documented within the last 12 months",
        "7.9": "Quarterly",
        "7.10": "Yes — recovery priority is documented",
        "7.11": "Yes — written reference exists",
        "7.12": "Yes — securely stored and accessible to authorized backup person",
        "7.13": "1 to 2 weeks",
        "7.14": "Yes",
        "6.13": "0",
    }
    earned7, max7, _, _ = score_section("7", best7)
    check(f"Section 7 perfect score ({int(earned7)}/{max7})", earned7 == max7)
    check("Section 7 perfect = healthy", get_section_severity_label(earned7, max7, 0, 0) == "healthy")

    storage_cases = [
        ("Both — onsite and offsite copies maintained", 3),
        ("Offsite only — stored in cloud or remote location", 2),
        ("Onsite only — stored at the school", 1),
        ("Inconsistent — some backups are both, some are only one location", 1),
    ]
    for opt, expected_pts in storage_cases:
        t = dict(best7, **{"7.7b": opt})
        et, _, _, _ = score_section("7", t)
        actual_pts = 3 - (earned7 - et)
        check(f"7.7b '{opt[:28]}…' = {actual_pts}pts", abs(actual_pts - expected_pts) < 0.5)

    # ── Section 8 ─────────────────────────────────────────────────
    print("\nSection 8: Security")
    sec8 = get_section(m1, "8")
    sid8n = new_sid()
    save_answer(sid8n, "8.1", "No", status="answered")
    save_answer(sid8n, "8.3", "Yes — documented patching schedule with defined response windows", status="answered")
    save_answer(sid8n, "8.5", "Yes — for students and staff", status="answered")
    save_answer(sid8n, "8.8", "Yes — documented process exists", status="answered")
    ans8n = get_answers(sid8n)
    e8n, m8n, _, _, _ = calculate_section_score(sec8, ans8n)
    check(f"Gate=No EP: other questions still score ({int(e8n)}/{m8n})", e8n > 0)

    best8 = {
        "8.1": "Yes — deployed on most managed devices",
        "8.2b": "Yes — alerts and trends are reviewed regularly",
        "8.3": "Yes — documented patching schedule with defined response windows",
        "8.4": "Yes — reviewed regularly (at least twice per year)",
        "8.5": "Yes — for students and staff",
        "8.6": "yes",
        "8.7": "Yes — controls are documented",
        "8.8": "Yes — documented process exists",
        "8.9": "Yes — reviewed regularly",
        "8.10": "Yes", "8.10b": "Yes",
        "8.10c": "Yes — our response steps match the policy requirements",
        "8.11": "no",
    }
    earned8, max8, _, _ = score_section("8", best8)
    check(f"Section 8 perfect score ({int(earned8)}/{max8})", earned8 == max8)

    # ── Section 9 ─────────────────────────────────────────────────
    print("\nSection 9: Documentation")
    best9 = {
        "9.1": "Yes — well used and reasonably complete",
        "9.2": "Yes — most documentation is current",
        "9.3": "Yes — SOPs exist for most recurring tasks",
        "9.4": "Yes — changes are documented as part of the process",
        "9.5": "Yes — documentation is sufficient for a qualified person to get oriented",
        "9.6": "no",
    }
    earned9, max9, _, _ = score_section("9", best9)
    check(f"Section 9 perfect score ({int(earned9)}/{max9})", earned9 == max9)
    check("Perfect documentation = healthy", get_section_severity_label(earned9, max9, 0, 0) == "healthy")

    partial9 = dict(best9)
    partial9["9.5"] = "Partially — they could understand some areas but not others"
    ep9, _, _, _ = score_section("9", partial9)
    check("9.5 partial earns less than perfect", ep9 < earned9)

    # ── Section 10 ────────────────────────────────────────────────
    print("\nSection 10: Planning (context only)")
    best10 = {
        "10.1": "Replace old switches", "10.2": "Network refresh",
        "10.3": "E-rate deadline", "10.4": "New campus planned",
        "10.5": "yes", "10.7": "High — most answers are documented or verified",
    }
    earned10, max10, _, _ = score_section("10", best10)
    check("Section 10 max = 0 (context only)", max10 == 0)
    check("Section 10 severity = context_only", get_section_severity_label(earned10, max10, 0, 0) == "context_only")


# ═════════════════════════════════════════════════════════════════════════════
# PART B — GOLDEN FIXTURE TESTS
# ═════════════════════════════════════════════════════════════════════════════

if RUN_FIXTURES:
    print("\n" + "═" * 60)
    print("PART B — Golden fixture tests")
    print("═" * 60)

    # ─────────────────────────────────────────────────────────────
    # MODULE 1 FIXTURES
    # ─────────────────────────────────────────────────────────────

    def run_m1_fixture(answers_dict):
        sid = new_sid("module_1", answers_dict.get("1.1", "Test"))
        for qid, val in answers_dict.items():
            save_answer(sid, qid, val, status="answered")
        answers = get_answers(sid)
        report = evaluate_all(answers, session_id=sid)
        return findings_to_dict(report)

    # ── M1 Strong ─────────────────────────────────────────────────
    print("\nModule 1 — Strong fixture (Exemplar Academy)")
    M1_STRONG = {
        "1.1": "Exemplar Academy", "1.7a": "Sam Strong",
        "1.8": "1", "1.9": "3", "1.12": "300", "1.13": "45", "1.14": "400",
        "2.2": "yes", "2.3": "yes", "2.4": "yes", "2.5": "yes",
        "2.6": "Yes — formal annual budget", "2.7": "no",
        "2.8": "yes", "2.9": "Yes — another person could cover fully",
        "2.10": "Yes — fully tracked in a system",
        "2.11": "Yes — in regular active use",
        "2.12": "IT director or technology coordinator",
        "3.2": "Yes — current and accurate", "3.3": "Yes — current for all locations",
        "3.6": "Yes — current inventory with model and firmware",
        "3.7": "yes",
        "3.9": "Yes — current inventory with model and firmware",
        "3.10": "Yes — current and accurate",
        "3.11": "Yes — fully documented with support status",
        "3.12": "Yes — full admin access to all infrastructure",
        "3.13": "2",
        "3.15": "Yes — load balancing and automatic failover to a secondary connection",
        "3.17": "Yes — fully known and documented",
        "3.18": "Yes — configurations are backed up regularly",
        "3.19": "Yes — coverage is adequate throughout",
        "3.20": "Yes — all segments documented",
        "3.21": "Yes — fully protected",
        "3.22": "Yes — documented and tested",
        "3.23": "Yes — monitored with alerting",
        "3.24": "Yes — regularly scanned", "3.26": "no",
        "4.1": "Google Workspace", "4.1b": "yes",
        "4.2": "Yes — cloud-based (Azure AD, Google Directory, etc.)",
        "4.3": "Yes — documented and followed consistently",
        "4.4": "Yes — documented and followed consistently",
        "4.5": "Yes — documented and followed consistently",
        "4.6": "Yes — all privileged accounts have MFA",
        "4.6b": "Yes — required for all staff",
        "4.7": "Yes — reviewed within the last 12 months",
        "4.8": "Yes — shared accounts are minimal and documented",
        "4.9": "Yes — documented for all major platforms",
        "4.10": "Yes — all staff devices sync consistently",
        "5.1": "Yes — current and reasonably complete",
        "5.2": "Yes — all key fields present",
        "5.5": "Yes — most devices managed",
        "5.6": "Yes — documented hardware standard in use",
        "5.7": "Yes — standardized",
        "5.8": "Yes — defined process or imaging/MDM enrollment in place",
        "5.9": "Yes — documented refresh cycle",
        "5.10": "None known — all devices are within supported life",
        "5.11": "Yes — tracked for all devices",
        "5.12": "Yes — spare pool and process defined",
        "5.13": "Yes — documented process in use",
        "5.17": "Yes — all tracked",
        "6.3": "Yes — current list in use",
        "6.4": "Yes — all key fields present",
        "6.6": "Yes — fully tracked",
        "6.7": "Yes — reviewed for most student-data systems",
        "6.8": "Yes — tracked in a calendar or system with reminders",
        "6.9": "Yes — documented for all critical vendors",
        "6.10": "no", "6.11": "no", "6.13": "0",
        "7.1": "Yes — confirmed and verified",
        "7.3": "Yes — documented scope",
        "7.5": "Yes — staff devices are backed up",
        "7.6": "Yes — critical cloud data is backed up",
        "7.7": "Yes — reviewed regularly (at least weekly)",
        "7.7b": "Both — onsite and offsite copies maintained",
        "7.8": "Yes — tested and documented within the last 12 months",
        "7.9": "Quarterly",
        "7.10": "Yes — recovery priority is documented",
        "7.11": "Yes — written reference exists",
        "7.12": "Yes — securely stored and accessible to authorized backup person",
        "7.13": "1 to 2 weeks", "7.14": "Yes",
        "8.1": "Yes — deployed on most managed devices",
        "8.2b": "Yes — alerts and trends are reviewed regularly",
        "8.3": "Yes — documented patching schedule with defined response windows",
        "8.4": "Yes — reviewed regularly (at least twice per year)",
        "8.5": "Yes — for students and staff", "8.6": "yes",
        "8.7": "Yes — controls are documented",
        "8.8": "Yes — documented process exists",
        "8.9": "Yes — reviewed regularly",
        "8.10": "Yes", "8.10b": "Yes",
        "8.10c": "Yes — our response steps match the policy requirements",
        "8.11": "no",
        "9.1": "Yes — well used and reasonably complete",
        "9.2": "Yes — most documentation is current",
        "9.3": "Yes — SOPs exist for most recurring tasks",
        "9.4": "Yes — changes are documented as part of the process",
        "9.5": "Yes — documentation is sufficient for a qualified person to get oriented",
        "9.6": "no",
        "10.7": "High — most answers are documented or verified",
    }
    d = run_m1_fixture(M1_STRONG)
    check("No urgent findings", d["by_severity"]["urgent"] == [])
    check("Exactly 1 concern finding (F3-003 — wireless)",
          d["by_severity"]["concern"] == ["F3-003"],
          f"got {d['by_severity']['concern']}")
    check("No watch findings", d["by_severity"]["watch"] == [])
    check("Total = 1 finding", d["finding_count"] == 1, f"got {d['finding_count']}")
    check("Data confidence = high", d["data_confidence"] == "high")
    check("No suppressed findings", len(d["suppressed_findings"]) == 0)

    # ── M1 Typical (Bit-By-Bit Academy) ───────────────────────────
    print("\nModule 1 — Typical fixture (Bit-By-Bit Academy)")
    bba_m1_export = json.load(open(os.path.join(TESTDATA_DIR, "BitByBit_Academy_module-1_export.json")))
    bba_m1_answers_raw = bba_m1_export["answers"]
    report_bba = evaluate_all(bba_m1_answers_raw, session_id="bba-m1-fixture-probe")
    d_bba = findings_to_dict(report_bba)
    # Expected output recorded from known-good run
    EXPECTED_URGENT_M1 = {"F2-007", "F7-004", "F7-008", "F7-012", "F7-C02"}
    EXPECTED_CONCERN_M1 = {
        "F2-003", "F2-004", "F2-008", "F3-011", "F3-012", "F3-017",
        "F4-003", "F4-005", "F5-006", "F6-007", "F6-009", "F6-010",
        "F7-007", "F7-010", "F7-011", "F7-014", "F8-008", "F9-005", "F9-006",
    }
    check("Bit-By-Bit urgent findings match",
          set(d_bba["by_severity"]["urgent"]) == EXPECTED_URGENT_M1,
          f"got {sorted(d_bba['by_severity']['urgent'])}")
    check("Bit-By-Bit concern findings match",
          set(d_bba["by_severity"]["concern"]) == EXPECTED_CONCERN_M1,
          f"got {sorted(d_bba['by_severity']['concern'])}")
    check("Bit-By-Bit total findings = 58",
          d_bba["finding_count"] == 58, f"got {d_bba['finding_count']}")
    check("Bit-By-Bit confidence = moderate", d_bba["data_confidence"] == "moderate")
    check("Bit-By-Bit key risk groups = A,B,C,D,E,F",
          set(d_bba["key_risk_groups"].keys()) == {"A", "B", "C", "D", "E", "F"})
    check("Bit-By-Bit no suppressed findings", len(d_bba["suppressed_findings"]) == 0)

    # ── M1 High-Risk ──────────────────────────────────────────────
    print("\nModule 1 — High-Risk fixture (Risk Academy)")
    M1_HIGH_RISK = {
        "1.1": "Risk Academy", "1.7a": "Pat Peril",
        "1.8": "1", "1.9": "3", "1.12": "200", "1.13": "30", "1.14": "250",
        "2.2": "no", "2.3": "no", "2.4": "no", "2.5": "no",
        "2.6": "No — there is no IT budget", "2.7": "no",
        "2.8": "no", "2.9": "No — no one else could manage IT operations",
        "2.10": "No — recurring tasks are not tracked",
        "2.11": "No — no ticketing or request tracking in use",
        "2.12": "No clear process — staff adopt tools as they see fit",
        "3.2": "No — no network diagram exists",
        "3.3": "No — no site or closet maps exist",
        "3.6": "No — no inventory exists", "3.7": "no",
        "3.9": "No — no inventory exists",
        "3.10": "No — no documentation exists",
        "3.11": "No — no documentation exists",
        "3.12": "No — access to one or more pieces of infrastructure is undocumented",
        "3.13": "1",
        "3.19": "No — significant dead zones in occupied areas",
        "3.20": "No — no network segments or VLAN documentation",
        "3.21": "No — open or limited protection",
        "3.22": "No — no recovery plan documented",
        "3.23": "No — not monitored", "3.24": "No — not scanned", "3.26": "no",
        "4.1": "Google Workspace", "4.1b": "yes",
        "4.2": "No — identity is managed separately per-application",
        "4.3": "No — no documented provisioning process",
        "4.4": "No — no documented offboarding process",
        "4.5": "No — no documented admin process",
        "4.6": "No — MFA is not enabled on privileged accounts",
        "4.6b": "No — not required",
        "4.7": "No — privileged accounts have not been audited",
        "4.8": "No — shared accounts in use and not documented",
        "4.9": "No — admin access is not documented",
        "4.10": "No — devices are not enrolled in directory or MDM",
        "5.1": "No — no device inventory exists",
        "5.2": "No — no inventory exists",
        "5.5": "No — no MDM or device management in use",
        "5.6": "No — no documented hardware standard",
        "5.7": "No — not standardized",
        "5.8": "No — no defined process",
        "5.9": "No — no refresh cycle defined",
        "5.10": "Many — a significant portion of the fleet is unsupported",
        "5.11": "No — warranty status not tracked",
        "5.12": "No — no spare pool or process defined",
        "5.13": "No — no documented process",
        "5.17": "No — not tracked",
        "6.3": "No — no vendor/system list exists",
        "6.4": "No — no list exists",
        "6.6": "No — renewals are not tracked",
        "6.7": "No — not reviewed",
        "6.8": "No — renewals are not tracked",
        "6.9": "No — escalation paths are not documented",
        "6.10": "no", "6.11": "no", "6.13": "0",
        "7.1": "No",
        "8.1": "No",
        "8.3": "No — no patching process or schedule defined",
        "8.4": "No — not reviewed",
        "8.5": "No — no content filtering in place",
        "8.6": "no",
        "8.7": "No — no data protection controls documented",
        "8.8": "No — no documented process",
        "8.9": "No — no incident log maintained",
        "8.10": "No", "8.11": "no",
        "9.1": "No — we do not use a documentation system",
        "9.2": "No — most documentation is missing or outdated",
        "9.3": "No — no SOPs exist",
        "9.4": "No — changes are not documented",
        "9.5": "No — we have no documentation that would help",
        "9.6": "no",
        "10.7": "Low — many answers were estimated or unknown",
    }
    d = run_m1_fixture(M1_HIGH_RISK)
    EXPECTED_URGENT_HR = {"F2-007", "F2-C01", "F3-004", "F3-012", "F5-006", "F7-C01", "F8-001"}
    EXPECTED_CONCERN_HR = {"F2-004", "F3-003", "F3-011", "F4-007"}
    check("High-risk urgent findings match",
          set(d["by_severity"]["urgent"]) == EXPECTED_URGENT_HR,
          f"got {sorted(d['by_severity']['urgent'])}")
    check("High-risk concern findings match",
          set(d["by_severity"]["concern"]) == EXPECTED_CONCERN_HR,
          f"got {sorted(d['by_severity']['concern'])}")
    check("High-risk total = 11", d["finding_count"] == 11, f"got {d['finding_count']}")
    check("High-risk suppressed = 3", len(d["suppressed_findings"]) == 3,
          f"got {len(d['suppressed_findings'])}")
    check("High-risk confidence = low", d["data_confidence"] == "low")
    check("High-risk no watch findings", d["by_severity"]["watch"] == [])

    # ─────────────────────────────────────────────────────────────
    # MODULE 2 FIXTURES
    # ─────────────────────────────────────────────────────────────

    with open(os.path.join(MODULES_DIR, "module_2.yaml")) as f:
        m2_def = yaml.safe_load(f)

    def run_m2_fixture(raw_dict):
        a = wrap(raw_dict)
        me, gi = expand_dynamic_sections(m2_def, a)
        sn = me.get("_system_names", [])
        return evaluate_dg(a, sn, gi), sn, gi

    def _good_sys(prefix):
        return {
            f"{prefix}_SYS.ID.name": "Primary SIS",
            f"{prefix}_SYS.ID.status": "Active — in regular use",
            f"{prefix}_SYS.1.1": "Yes — complete list available",
            f"{prefix}_SYS.1.1a": "no",
            f"{prefix}_SYS.1.2": "Role-based — different roles see different data",
            f"{prefix}_SYS.1.3": "Yes — required for all users",
            f"{prefix}_SYS.1.4": "yes",
            f"{prefix}_SYS.1.4a": "no",
            f"{prefix}_SYS.1.5": "Yes — logs retained 90+ days and reviewed regularly",
            f"{prefix}_SYS.2.1": "Yes — school manages the backup",
            f"{prefix}_SYS.2.3": "Within the last 12 months — documented",
            f"{prefix}_SYS.2.4": "yes",
            f"{prefix}_SYS.3.2a": "Yes — all outbound transfers are encrypted",
            f"{prefix}_SYS.4.1": "Yes — signed DPA on file",
            f"{prefix}_SYS.4.2": "Yes — 72 hours or less",
            f"{prefix}_SYS.4.3": "Yes — deletion required with written confirmation",
            f"{prefix}_SYS.5.1": ["Student academic records (grades, transcripts, reports)"],
            f"{prefix}_SYS.5.3": "Documented secure deletion process with deletion log",
        }

    def _bad_sys(prefix):
        return {
            f"{prefix}_SYS.ID.name": "Primary SIS",
            f"{prefix}_SYS.ID.status": "Active — in regular use",
            f"{prefix}_SYS.1.1": "No — system does not easily provide this",
            f"{prefix}_SYS.1.1a": "yes",
            f"{prefix}_SYS.1.2": "Unknown",
            f"{prefix}_SYS.1.3": "No — not available or not enabled",
            f"{prefix}_SYS.1.4": "no",
            f"{prefix}_SYS.1.4a": "yes",
            f"{prefix}_SYS.1.5": "No — no audit logging",
            f"{prefix}_SYS.2.1": "No — not backed up",
            f"{prefix}_SYS.3.2a": "No — transfers are not encrypted",
            f"{prefix}_SYS.4.1": "No agreement on file",
            f"{prefix}_SYS.4.2": "No breach notification clause",
            f"{prefix}_SYS.4.3": "No — contract is silent on this",
            f"{prefix}_SYS.5.1": ["Student academic records (grades, transcripts, reports)",
                                   "Student health records (medical, counseling, nurse)"],
            f"{prefix}_SYS.5.3": "No deletion process — data accumulates indefinitely",
        }

    _GOOD_DG2 = {
        "DG2.1": "Yes — formal written policy exists and has been reviewed",
        "DG2.2": "Yes — data flows are mapped and documented",
        "DG2.3": "Yes — complete and current",
        "DG2.4": "Yes — data is classified by type and sensitivity",
        "DG2.5": "Yes — IT review required before adoption",
        "DG2.6": "Yes — formal annual training programme",
        "DG2.7": "Yes — documented offboarding checklist covers all systems",
        "DG2.8": "Yes — formal vendor security review process exists",
        "DG2.9": "Yes — documented and reviewed annually",
    }
    _BAD_DG2 = {
        "DG2.1": "No — no formal policy exists",
        "DG2.2": "No — no formal process for documenting data flows",
        "DG2.3": "No — no register exists",
        "DG2.4": "No — no data classification scheme",
        "DG2.5": "No — staff can adopt tools without IT review",
        "DG2.6": "No",
        "DG2.7": "No — no formal offboarding process",
        "DG2.8": "No — vendors are approved without security review",
        "DG2.9": "No",
    }

    # ── M2 Strong ─────────────────────────────────────────────────
    print("\nModule 2 — Strong fixture (one well-governed system)")
    s2 = {"DG1.1": "Sam Strong", "DG1.2": "2025-01-01",
          "DG1.3": ["Primary SIS"], "DG1.4": "1"}
    s2.update(_good_sys("DG_SYS_1"))
    s2.update(_GOOD_DG2)
    dg_s, _, _ = run_m2_fixture(s2)
    check("Strong M2 overall grade = A", dg_s.summary.overall_grade == "A",
          f"got {dg_s.summary.overall_grade}")
    check("Strong M2 no floor cap", dg_s.floor_cap is None)
    check("Strong M2 primary system grade = A",
          dg_s.per_system_results[0].grade_label == "A",
          f"got {dg_s.per_system_results[0].grade_label}")
    check("Strong M2 no per-system findings", dg_s.per_system_results[0].findings == [])
    check("Strong M2 no school-wide findings", dg_s.school_wide_results == [])

    # ── M2 Typical (Bit-By-Bit Academy) ───────────────────────────
    print("\nModule 2 — Typical fixture (Bit-By-Bit Academy)")
    bba_m2_export = json.load(open(os.path.join(TESTDATA_DIR, "Bit-By-Bit_Academy_module-2_export_UPDATED.json")))
    bba_m2_answers = bba_m2_export["answers"]
    me2, gi2 = expand_dynamic_sections(m2_def, bba_m2_answers)
    sn2 = me2.get("_system_names", [])
    dg_bba = evaluate_dg(bba_m2_answers, sn2, gi2)
    # Expected from known-good run
    check("Bit-By-Bit M2 overall grade = F",
          dg_bba.summary.overall_grade == "F",
          f"got {dg_bba.summary.overall_grade}")
    check("Bit-By-Bit M2 floor cap fired", dg_bba.floor_cap is not None)
    check("Bit-By-Bit M2 floor cap grade = D",
          dg_bba.floor_cap.cap_grade == "D" if dg_bba.floor_cap else False)
    check("Bit-By-Bit M2 has 5 systems", dg_bba.summary.total_systems == 5)
    check("Bit-By-Bit M2 Veracross grade = F",
          dg_bba.per_system_results[0].grade_label == "F",
          f"got {dg_bba.per_system_results[0].grade_label}")
    check("Bit-By-Bit M2 has 6 school-wide findings",
          len(dg_bba.school_wide_results) == 6,
          f"got {len(dg_bba.school_wide_results)}")

    # ── M2 High-Risk ──────────────────────────────────────────────
    print("\nModule 2 — High-Risk fixture (one failing system, all DG2 gaps)")
    r2 = {"DG1.1": "Pat Peril", "DG1.2": "2025-01-01",
          "DG1.3": ["Primary SIS"], "DG1.4": "1"}
    r2.update(_bad_sys("DG_SYS_1"))
    r2.update(_BAD_DG2)
    dg_r, _, _ = run_m2_fixture(r2)
    check("High-Risk M2 overall grade = F",
          dg_r.summary.overall_grade == "F",
          f"got {dg_r.summary.overall_grade}")
    check("High-Risk M2 floor cap fired", dg_r.floor_cap is not None)
    check("High-Risk M2 primary system has critical findings",
          any(f.severity == "critical" for f in dg_r.per_system_results[0].findings))
    check("High-Risk M2 primary system has 9 findings",
          len(dg_r.per_system_results[0].findings) == 9,
          f"got {len(dg_r.per_system_results[0].findings)}")
    check("High-Risk M2 has 5 school-wide findings",
          len(dg_r.school_wide_results) == 5,
          f"got {len(dg_r.school_wide_results)}")
    check("High-Risk M2 offboarding finding is critical",
          any(f.severity == "critical" and "offboarding" in f.title.lower()
              for f in dg_r.school_wide_results))

    # ─────────────────────────────────────────────────────────────
    # MODULE 3 FIXTURES
    # ─────────────────────────────────────────────────────────────

    with open(os.path.join(MODULES_DIR, "module_3.yaml")) as f:
        m3_def = yaml.safe_load(f)

    def run_m3_fixture(raw_dict):
        a = wrap(raw_dict)
        me, gi = expand_dynamic_sections(m3_def, a)
        vn = me.get("_system_names", [])
        return evaluate_vr(a, vn, gi)

    def _good_vendor(prefix, name, category="Student Information System"):
        return {
            f"{prefix}_V.ID.name": name,
            f"{prefix}_V.ID.category": category,
            f"{prefix}_V.ID.status": "Active",
            f"{prefix}_V.ID.owner": "IT Director",
            f"{prefix}_V.COST.known": "Yes — confirmed and tracked in a budget or register",
            f"{prefix}_V.COST.cycle": "Annual",
            f"{prefix}_V.COST.budget": "Yes — in the approved budget",
            f"{prefix}_V.RENEW.date": "2026-08-01",
            f"{prefix}_V.RENEW.auto": "No — requires active renewal decision",
            f"{prefix}_V.RENEW.tracked": "Yes — in a calendar or system with a reminder set",
            f"{prefix}_V.RENEW.signed": "Yes — signed contract on file and location is known",
            f"{prefix}_V.SUPPORT.contact": "Yes — full support contact documented and accessible",
            f"{prefix}_V.SUPPORT.escalation": "Yes — documented",
            f"{prefix}_V.SUPPORT.admin": "Yes — credentials in a shared password manager or documented process",
            f"{prefix}_V.DATA.student": "Yes — holds or processes student data",
            f"{prefix}_V.DATA.ferpa": "Yes — DPA or privacy agreement in place and signed",
            f"{prefix}_V.DATA.dpa": "Yes — signed DPA on file, location known",
            f"{prefix}_V.DATA.staff": "No — does not hold staff data",
            f"{prefix}_V.USE.active": "Yes — actively used",
            f"{prefix}_V.USE.value": "Yes — delivering clear value",
        }

    def _bad_vendor(prefix, name, category="Student Information System"):
        return {
            f"{prefix}_V.ID.name": name,
            f"{prefix}_V.ID.category": category,
            f"{prefix}_V.ID.status": "Active",
            f"{prefix}_V.ID.owner": "Unknown",
            f"{prefix}_V.COST.known": "No — cost is not known",
            f"{prefix}_V.COST.cycle": "Unknown",
            f"{prefix}_V.COST.budget": "Unknown",
            f"{prefix}_V.RENEW.date": "Unknown",
            f"{prefix}_V.RENEW.auto": "Yes — auto-renews; cancellation notice required before renewal date",
            f"{prefix}_V.RENEW.tracked": "No — renewal date is not known",
            f"{prefix}_V.RENEW.signed": "No — no signed contract",
            f"{prefix}_V.SUPPORT.contact": "No — support contact not documented",
            f"{prefix}_V.SUPPORT.escalation": "No — not documented",
            f"{prefix}_V.SUPPORT.admin": "No — credentials are not documented",
            f"{prefix}_V.DATA.student": "Yes — holds or processes student data",
            f"{prefix}_V.DATA.ferpa": "No — not reviewed",
            f"{prefix}_V.DATA.dpa": "No — no DPA in place",
            f"{prefix}_V.DATA.staff": "No — does not hold staff data",
            f"{prefix}_V.USE.active": "Yes — actively used",
            f"{prefix}_V.USE.value": "Unknown",
        }

    _GOOD_VR2 = {
        "VR2.1": "IT Director",
        "VR2.2": "Yes — all staff leavers go through a documented vendor offboarding step",
        "VR2.3": "Yes — all staff have a named backup contact for each critical vendor",
        "VR2.4": "Yes — all vendors are reviewed annually",
        "VR2.5": "Yes — school-wide password manager in use for all vendor accounts",
        "VR2.6": "Yes — IT and Business Office review renewal calendar together",
        "VR2.7": "Yes — covered in offboarding checklist",
        "VR2.8": "Yes — central DPA register maintained",
        "VR2.9": "Yes — annual vendor review conducted",
    }
    _BAD_VR2 = {
        "VR2.1": "Unknown",
        "VR2.2": "No — vendor accounts are not reviewed when staff leave",
        "VR2.3": "No — no backup contacts documented",
        "VR2.4": "No — vendors are not reviewed regularly",
        "VR2.5": "No — no password manager in use",
        "VR2.6": "No — IT and Business Office do not share a renewal view",
        "VR2.7": "No — vendor accounts are not part of offboarding",
        "VR2.8": "No — no central DPA register",
        "VR2.9": "No — no annual vendor review",
    }

    # ── M3 Strong ─────────────────────────────────────────────────
    print("\nModule 3 — Strong fixture (one well-governed vendor)")
    s3 = {"VR1.1": "Sam Strong", "VR1.2": "2025-01-01",
          "VR1.3": ["Primary SIS"], "VR1.4": "1"}
    s3.update(_good_vendor("VR_V_1", "Primary SIS"))
    s3.update(_GOOD_VR2)
    vr_s = run_m3_fixture(s3)
    check("Strong M3 overall grade = A",
          vr_s.summary.overall_grade == "A",
          f"got {vr_s.summary.overall_grade}")
    check("Strong M3 no floor cap", vr_s.floor_cap is None)
    check("Strong M3 primary vendor grade = A",
          vr_s.per_vendor_results[0].grade_label == "A",
          f"got {vr_s.per_vendor_results[0].grade_label}")
    check("Strong M3 primary vendor score = 100%",
          vr_s.per_vendor_results[0].score_pct == 100,
          f"got {vr_s.per_vendor_results[0].score_pct}")
    check("Strong M3 no per-vendor findings",
          vr_s.per_vendor_results[0].findings == [])
    check("Strong M3 no school-wide findings",
          vr_s.school_wide_results == [])

    # ── M3 Typical (Bit-By-Bit Academy) ───────────────────────────
    print("\nModule 3 — Typical fixture (Bit-By-Bit Academy)")
    bba_m3_export = json.load(open(os.path.join(TESTDATA_DIR, "Bit-By-Bit_Academy_module-3_export_UPDATED.json")))
    bba_m3_answers = bba_m3_export["answers"]
    me3, gi3 = expand_dynamic_sections(m3_def, bba_m3_answers)
    vn3 = me3.get("_system_names", [])
    vr_bba = evaluate_vr(bba_m3_answers, vn3, gi3)
    # Expected from known-good run
    check("Bit-By-Bit M3 overall grade = D",
          vr_bba.summary.overall_grade == "D",
          f"got {vr_bba.summary.overall_grade}")
    check("Bit-By-Bit M3 floor cap fired", vr_bba.floor_cap is not None)
    check("Bit-By-Bit M3 has 13 vendors",
          vr_bba.summary.total_vendors == 13,
          f"got {vr_bba.summary.total_vendors}")
    check("Bit-By-Bit M3 Seesaw grade = F",
          next((r.grade_label for r in vr_bba.per_vendor_results if "Seesaw" in r.vendor_name), None) == "F")
    check("Bit-By-Bit M3 Comcast grade = A",
          next((r.grade_label for r in vr_bba.per_vendor_results if "Comcast" in r.vendor_name), None) == "A")
    check("Bit-By-Bit M3 has 4 urgent vendors",
          vr_bba.summary.vendors_urgent == 4,
          f"got {vr_bba.summary.vendors_urgent}")
    check("Bit-By-Bit M3 has 8 school-wide findings",
          len(vr_bba.school_wide_results) == 8,
          f"got {len(vr_bba.school_wide_results)}")

    # ── M3 High-Risk ──────────────────────────────────────────────
    print("\nModule 3 — High-Risk fixture (one failing vendor, all VR2 gaps)")
    r3 = {"VR1.1": "Pat Peril", "VR1.2": "2025-01-01",
          "VR1.3": ["Risky SIS"], "VR1.4": "1"}
    r3.update(_bad_vendor("VR_V_1", "Risky SIS"))
    r3.update(_BAD_VR2)
    vr_r = run_m3_fixture(r3)
    check("High-Risk M3 overall grade = F",
          vr_r.summary.overall_grade == "F",
          f"got {vr_r.summary.overall_grade}")
    check("High-Risk M3 floor cap fired", vr_r.floor_cap is not None)
    check("High-Risk M3 primary vendor is urgent",
          vr_r.per_vendor_results[0].severity == "urgent",
          f"got {vr_r.per_vendor_results[0].severity}")
    check("High-Risk M3 primary vendor weight = 4x",
          vr_r.per_vendor_results[0].weight_multiplier == 4,
          f"got {vr_r.per_vendor_results[0].weight_multiplier}")
    check("High-Risk M3 has critical findings",
          any(f.severity == "critical" for f in vr_r.per_vendor_results[0].findings))
    check("High-Risk M3 has school-wide findings",
          len(vr_r.school_wide_results) > 0,
          f"got {len(vr_r.school_wide_results)}")
    check("High-Risk M3 shadow-IT finding fires",
          any("shadow it" in f.title.lower() or "approval process" in f.title.lower()
              for f in vr_r.school_wide_results))


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("All tests passed. ✓")
else:
    print(f"\nFailed tests:")
    for f in FAILURES:
        print(f"  ✗ {f}")
    sys.exit(1)
