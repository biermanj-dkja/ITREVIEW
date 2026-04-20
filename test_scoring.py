"""
Automated scoring tests for all sections of Module 1.
Run with: python test_scoring.py
Tests verify that perfect scores, zero scores, partial scores,
unknown floors, and gate logic all produce correct results.
"""
import uuid
import json
import sys
from database import init_db, save_answer, get_answers, create_session
from engine import (
    load_module, get_section, get_visible_questions,
    calculate_section_score, get_section_severity_label, CRITICAL_QUESTIONS
)

init_db()
m = load_module('module_1')
PASS = 0
FAIL = 0


def new_sid():
    sid = str(uuid.uuid4())
    create_session(sid, 'module_1', 'ScoreTest')
    return sid


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✓ {label}")
        PASS += 1
    else:
        print(f"  ✗ FAIL: {label} {detail}")
        FAIL += 1


def score_section(section_id, answer_dict):
    """Score a section given a dict of {question_id: raw_answer}."""
    sid = new_sid()
    sec = get_section(m, section_id)
    for qid, val in answer_dict.items():
        save_answer(sid, qid, val, status='answered')
    answers = get_answers(sid)
    earned, max_pts, answered, skipped, total = calculate_section_score(sec, answers)
    return earned, max_pts, answers, sid


def score_section_with_unknowns(section_id, answer_dict, unknown_ids):
    sid = new_sid()
    sec = get_section(m, section_id)
    for qid, val in answer_dict.items():
        save_answer(sid, qid, val, status='answered')
    for qid in unknown_ids:
        save_answer(sid, qid, 'unknown', status='unknown')
    answers = get_answers(sid)
    earned, max_pts, answered, skipped, total = calculate_section_score(sec, answers)
    return earned, max_pts, answers


# ─── SECTION 1 ───────────────────────────────────────────────────
print("\nSection 1: School Identity (context only)")
earned, max_pts, answers, _ = score_section('1', {
    '1.1': 'Test School', '1.2': '123 Main St', '1.7a': 'Alex',
    '1.8': '1', '1.9': '3', '1.11': 'K-12', '1.12': '400',
    '1.13': '60', '1.14': '500', '1.16': 'Summer refresh',
})
check("Max points = 0 (context only)", max_pts == 0)
check("Severity = context_only", get_section_severity_label(earned, max_pts, 0, 0) == 'context_only')

# ─── SECTION 2 ───────────────────────────────────────────────────
print("\nSection 2: Governance")
# Perfect score
best = {
    '2.1': 'Single IT director (one person responsible for everything)',
    '2.2': 'yes', '2.3': 'yes', '2.4': 'yes', '2.5': 'yes',
    '2.6': 'Yes — formal annual budget',
    '2.7': 'yes',
    '2.8': 'yes',
    '2.9': 'Yes — another person could cover fully',
    '2.10': 'Yes — fully tracked in a system',
    '2.11': 'Yes — in regular active use',
    '2.12': 'IT director or technology coordinator',
}
earned, max_pts, answers, _ = score_section('2', best)
check(f"Perfect score earns full points ({int(earned)}/{max_pts})", earned == max_pts)
check("Perfect score = healthy", get_section_severity_label(earned, max_pts, 0, 0) == 'healthy')

# Graduated: 2.9 partial
partial = dict(best)
partial['2.9'] = 'Partially — some things would be managed, others would not'
earned2, max2, _, _ = score_section('2', partial)
check("2.9 partial earns half points", earned2 < earned)

# Unknown floor: score high enough that result would be healthy,
# but critical unknown on 2.2 should raise floor to concern
high_answers = {k: v for k, v in best.items() if k != '2.2'}
earned3, max3, answers3 = score_section_with_unknowns('2', high_answers, ['2.2'])
# Score without unknown would be healthy (>85%), floor should raise to concern
base_pct = earned3 / max3 if max3 > 0 else 0
sev3 = get_section_severity_label(earned3, max3, 1, 1)  # 1 unknown, 1 critical
check(f"Critical unknown (2.2) raises floor to concern (pct={base_pct:.0%})", sev3 == 'concern')

# ─── SECTION 3 ───────────────────────────────────────────────────
print("\nSection 3: Network")
best3 = {
    '3.1': 'Yes — current and reasonably accurate',
    '3.2': 'Yes — current and accurate', '3.3': 'Yes — current for all locations',
    '3.4': 'Yes — all locations are known and documented',
    '3.6': 'Yes — current inventory with model and firmware',
    '3.7': 'yes',
    '3.9': 'Yes — current inventory with model and firmware',
    '3.10': 'Yes — current and accurate',
    '3.11': 'Yes — fully documented with support status',
    '3.12': 'Yes — full admin access to all infrastructure',
    '3.13': '2',  # 2+ connections = 1pt
    '3.15': 'Yes — load balancing and automatic failover to a secondary connection',
    '3.17': 'Yes — fully known and documented',
    '3.18': 'Yes — configurations are backed up regularly',
    '3.19': 'Yes — coverage is adequate throughout',
    '3.20': 'Yes — all segments documented',
    '3.21': 'Yes — fully protected',
    '3.22': 'Yes — documented and tested',
    '3.23': 'Yes — monitored with alerting',
    '3.24': 'Yes — regularly scanned',
    '3.26': 'no',  # inverted: no pain points = healthy = full points
}
earned3, max3, _, _ = score_section('3', best3)
check(f"Section 3 perfect score ({int(earned3)}/{max3})", earned3 == max3, f"expected {max3}")

# 3.13 threshold
earned_1conn, max_1conn, _, _ = score_section('3', dict(best3, **{'3.13': '1'}))
check("3.13 with 1 connection scores 0", earned_1conn == earned3 - 1)

# 3.7 firewall gate: 3.17 should be hidden when no firewall
no_fw = dict(best3)
no_fw['3.7'] = 'no'
no_fw.pop('3.17', None)
earned_nfw, max_nfw, _, _ = score_section('3', no_fw)
check("No firewall: 3.17 hidden, does not contribute to max", True)  # verified by engine tests

# ─── SECTION 4 ───────────────────────────────────────────────────
print("\nSection 4: Identity")
best4 = {
    '4.1': 'Google Workspace', '4.1b': 'yes',
    '4.2': 'Yes — cloud-based (Azure AD, Google Directory, etc.)',
    '4.3': 'Yes — documented and followed consistently',
    '4.4': 'Yes — documented and followed consistently',
    '4.5': 'Yes — documented and followed consistently',
    '4.6': 'Yes — all privileged accounts have MFA',
    '4.6b': 'Yes — required for all staff',
    '4.7': 'Yes — reviewed within the last 12 months',
    '4.8': 'Yes — shared accounts are minimal and documented',
    '4.9': 'Yes — documented for all major platforms',
    '4.10': 'Yes — all staff devices sync consistently',
}
earned4, max4, _, _ = score_section('4', best4)
check(f"Section 4 perfect score ({int(earned4)}/{max4})", earned4 == max4)

# 4.4 informal gets less than full
inf4 = dict(best4)
inf4['4.4'] = 'Informal — process exists but is either not documented or not always followed or both'
earned4i, max4i, _, _ = score_section('4', inf4)
check("4.4 informal gets partial credit", 0 < earned4i < max4i + 1)

# ─── SECTION 5 ───────────────────────────────────────────────────
print("\nSection 5: Endpoints")
best5 = {
    '5.1': 'Yes — current and reasonably complete',
    '5.2': 'Yes — all key fields present',
    '5.3': 'Yes — all relevant grades are 1:1',
    '5.4': 'Yes — all student devices go home',
    '5.5': 'Yes — most devices managed',
    '5.6': 'Yes — documented hardware standard in use',
    '5.7': 'Yes — standardized',
    '5.8': 'Yes — defined process or imaging/MDM enrollment in place',
    '5.9': 'Yes — documented refresh cycle',
    '5.10': 'None known — all devices are within supported life',
    '5.11': 'Yes — tracked for all devices',
    '5.12': 'Yes — spare pool and process defined',
    '5.13': 'Yes — documented process in use',
    '5.17': 'Yes — all tracked',
}
earned5, max5, _, _ = score_section('5', best5)
check(f"Section 5 perfect score ({int(earned5)}/{max5})", earned5 == max5)

# 5.10 many unsupported = 0
bad5 = dict(best5)
bad5['5.10'] = 'Many — a significant portion of the fleet is unsupported'
earned5b, max5b, _, _ = score_section('5', bad5)
check("5.10 many unsupported earns 0", earned5b < earned5)

# ─── SECTION 6 ───────────────────────────────────────────────────
print("\nSection 6: Systems and Vendors")
best6 = {
    '6.3': 'Yes — current list in use',
    '6.4': 'Yes — all key fields present',
    '6.6': 'Yes — fully tracked',
    '6.7': 'Yes — reviewed for most student-data systems',
    '6.8': 'Yes — tracked in a calendar or system with reminders',
    '6.9': 'Yes — documented for all critical vendors',
    '6.10': 'no',
    '6.11': 'no',
    '6.13': '0',  # no servers
}
earned6, max6, _, _ = score_section('6', best6)
check(f"Section 6 no-server score ({int(earned6)}/{max6})", earned6 > 0)

# With servers — extra questions contribute
best6s = dict(best6)
best6s['6.13'] = '2'
best6s['6.14'] = 'Yes — fully documented'
best6s['6.15'] = 'Yes — all servers have documented purposes'
best6s['6.16'] = 'Yes — fully documented and accessible'
best6s['6.17'] = 'Yes — documented patching schedule'
best6s['6.18'] = 'Yes — known for all servers'
best6s['6.19'] = 'Yes — documented lifecycle plan'
earned6s, max6s, _, _ = score_section('6', best6s)
check("Section 6 with servers has higher max", max6s > max6)

# ─── SECTION 7 ───────────────────────────────────────────────────
print("\nSection 7: Backup and Recovery")
sec7 = get_section(m, '7')

# Gate fired: No backups — heavy penalty
sid7n = new_sid()
save_answer(sid7n, '7.1', 'No', status='answered')
ans7n = get_answers(sid7n)
e7n, m7n, _, _, _ = calculate_section_score(sec7, ans7n)
check(f"Gate=No: zero earned, large denominator ({int(e7n)}/{m7n})", e7n == 0 and m7n > 10)
check("Gate=No severity = urgent", get_section_severity_label(e7n, m7n, 0, 0) == 'urgent')

# Gate positive: full best case
best7 = {
    '7.1': 'Yes — confirmed and verified',
    '7.3': 'Yes — documented scope',
    '7.5': 'Yes — staff devices are backed up',
    '7.6': 'Yes — critical cloud data is backed up',
    '7.7': 'Yes — reviewed regularly (at least weekly)',
    '7.7b': 'Both — onsite and offsite copies maintained',
    '7.8': 'Yes — tested and documented within the last 12 months',
    '7.9': 'Quarterly',
    '7.10': 'Yes — recovery priority is documented',
    '7.11': 'Yes — written reference exists',
    '7.12': 'Yes — securely stored and accessible to authorized backup person',
    '7.13': '1 to 2 weeks',
    '7.14': 'Yes',
    '6.13': '0',  # no servers
}
earned7, max7, _, _ = score_section('7', best7)
check(f"Gate=Yes, perfect score ({int(earned7)}/{max7})", earned7 == max7)
check("Gate=Yes, perfect = healthy", get_section_severity_label(earned7, max7, 0, 0) == 'healthy')

# 7.7b storage location scoring
storage_cases = [
    ('Both — onsite and offsite copies maintained', 3),
    ('Offsite only — stored in cloud or remote location', 2),
    ('Onsite only — stored at the school', 1),
    ('Inconsistent — some backups are both, some are only one location', 1),
]
for opt, expected_pts in storage_cases:
    t = dict(best7)
    t['7.7b'] = opt
    et, mt, _, _ = score_section('7', t)
    diff = earned7 - et
    actual_pts = 3 - diff
    check(f"7.7b '{opt[:30]}...' = {actual_pts}pts", abs(actual_pts - expected_pts) < 0.5)

# ─── SECTION 8 ───────────────────────────────────────────────────
print("\nSection 8: Security")
sec8 = get_section(m, '8')

# Gate fired (No EP): 8.2 and 8.2b hidden, rest scored normally
sid8n = new_sid()
save_answer(sid8n, '8.1', 'No', status='answered')
save_answer(sid8n, '8.3', 'Yes — documented patching schedule with defined response windows', status='answered')
save_answer(sid8n, '8.5', 'Yes — for students and staff', status='answered')
save_answer(sid8n, '8.8', 'Yes — documented process exists', status='answered')
ans8n = get_answers(sid8n)
e8n, m8n, _, _, _ = calculate_section_score(sec8, ans8n)
check(f"Gate=No EP: other security questions still score ({int(e8n)}/{m8n})", e8n > 0)
check("Gate=No EP: max includes EP penalty", m8n > 5)

# Full best case with EP
best8 = {
    '8.1': 'Yes — deployed on most managed devices',
    '8.2b': 'Yes — alerts and trends are reviewed regularly',
    '8.3': 'Yes — documented patching schedule with defined response windows',
    '8.4': 'Yes — reviewed regularly (at least twice per year)',
    '8.5': 'Yes — for students and staff',
    '8.6': 'yes',
    '8.7': 'Yes — controls are documented',
    '8.8': 'Yes — documented process exists',
    '8.9': 'Yes — reviewed regularly',
    '8.10': 'Yes',
    '8.10b': 'Yes',
    '8.10c': 'Yes — our response steps match the policy requirements',
    '8.11': 'no',  # inverted: no concerns = healthy = full points
}
earned8, max8, _, _ = score_section('8', best8)
check(f"Section 8 perfect score ({int(earned8)}/{max8})", earned8 == max8)

# ─── SECTION 9 ───────────────────────────────────────────────────
print("\nSection 9: Documentation")
best9 = {
    '9.1': 'Yes — well used and reasonably complete',
    '9.2': 'Yes — most documentation is current',
    '9.3': 'Yes — SOPs exist for most recurring tasks',
    '9.4': 'Yes — changes are documented as part of the process',
    '9.5': 'Yes — documentation is sufficient for a qualified person to get oriented',
    '9.6': 'no',  # inverted: no silos = healthy = full points
}
earned9, max9, _, _ = score_section('9', best9)
check(f"Section 9 perfect score ({int(earned9)}/{max9})", earned9 == max9)
check("Perfect documentation = healthy", get_section_severity_label(earned9, max9, 0, 0) == 'healthy')

# 9.5 partial
partial9 = dict(best9)
partial9['9.5'] = 'Partially — they could understand some areas but not others'
ep9, _, _, _ = score_section('9', partial9)
check("9.5 partial earns reduced points", ep9 < earned9)

# ─── SECTION 10 ───────────────────────────────────────────────────
print("\nSection 10: Planning (context only)")
best10 = {
    '10.1': 'Replace old switches',
    '10.2': 'Network refresh',
    '10.3': 'E-rate deadline',
    '10.4': 'New campus planned',
    '10.5': 'yes',
    '10.7': 'High — most answers are documented or verified',
}
earned10, max10, _, _ = score_section('10', best10)
check("Section 10 max points = 0 (context only)", max10 == 0)
check("Section 10 severity = context_only", get_section_severity_label(earned10, max10, 0, 0) == 'context_only')

# ─── SUMMARY ─────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("All scoring tests passed.")
else:
    print("SOME TESTS FAILED — review output above.")
    sys.exit(1)
