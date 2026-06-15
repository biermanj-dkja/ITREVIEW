"""
rules_engine_vr.py  —  Vendor Register findings engine for module_3

Generates deterministic findings and a report card from the answers
collected in the Software, Licensing, and Vendor Register (module_3).

Architecture
------------
evaluate_vr(answers, vendor_names, generated_section_ids) → VRReport

VRReport contains:
  - per_vendor_results   : list of VendorResult (one per vendor)
  - school_wide_results  : list of VRFinding (VR2 section)
  - summary              : VRSummary (counts, overall grade, risk register)
  - renewal_risk_register: list of RenewalRisk (sorted by urgency)
  - floor_cap            : FloorCap | None  — set when a critical floor rule fires

Each VendorResult has:
  - vendor_name
  - section_id
  - score_pct
  - grade_label     ("A" / "B" / "C" / "D" / "F")
  - severity        ("healthy" / "watch" / "concern" / "urgent")
  - category        : str  — vendor category from V.ID.category
  - findings        : list of VRFinding
  - area_scores     : dict {area_name: (earned, max)}
  - holds_student_data : bool
  - holds_staff_data   : bool
  - renewal_date    : str | None
  - auto_renews     : bool | None
  - annual_cost     : str | None
  - strengths       : list of str

VRFinding fields:
  - area     : str
  - severity : str  ("critical" / "high" / "medium" / "low")
  - effort   : str  ("S" / "S+" / "M" / "M+" / "L")
  - owner    : str
  - timing   : str  ("immediate" / "near_term" / "planned")
  - title    : str
  - detail   : str
  - action   : str
  - vendor_name : str | None

RenewalRisk fields:
  - vendor_name  : str
  - category     : str
  - renewal_date : str
  - auto_renews  : bool
  - notice_days  : str | None
  - risk_level   : str  ("high" / "medium" / "low")
  - risk_reason  : str

FloorCap fields:
  - cap_grade      : str   — the grade ceiling applied ("D" typically)
  - reason         : str   — human-readable explanation
  - trigger_vendors: list of str  — vendors that triggered the floor
  - trigger_finding: str   — the finding title that triggered it

Effort ratings:
  S   = half a day (~4 hours)
  S+  = one day (~8 hours)
  M   = three days
  M+  = five days
  L   = ten days (~two weeks)

Timing buckets:
  immediate  = Do within 30 days  (critical + high findings)
  near_term  = Do within 90 days  (medium findings)
  planned    = Schedule this year  (low findings)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import os
import yaml


# ── Data classes ───────────────────────────────────────────────────

@dataclass
class VRFinding:
    area: str
    severity: str          # critical / high / medium / low
    title: str
    detail: str
    action: str
    effort: str = "M"
    owner: str = "IT Director"
    timing: str = "near_term"
    vendor_name: Optional[str] = None
    rule_id: str = ""            # stable slug used as context-note key in templates


@dataclass
class RenewalRisk:
    vendor_name: str
    category: str
    renewal_date: str
    auto_renews: bool
    notice_days: Optional[str]
    risk_level: str          # high / medium / low
    risk_reason: str


@dataclass
class VendorResult:
    vendor_name: str
    section_id: str
    earned: float
    max_pts: int
    score_pct: int
    grade_label: str
    severity: str
    category: str = "Unknown"
    findings: List[VRFinding] = field(default_factory=list)
    area_scores: Dict[str, Tuple[float, int]] = field(default_factory=dict)
    holds_student_data: bool = False
    holds_staff_data: bool = False
    renewal_date: Optional[str] = None
    auto_renews: Optional[bool] = None
    annual_cost: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    weight_multiplier: int = 1   # criticality weight used in overall grade (1x–4x)


@dataclass
class VRSummary:
    total_vendors: int
    vendors_scored: int
    vendors_urgent: int
    vendors_concern: int
    vendors_watch: int
    vendors_healthy: int
    overall_grade: str
    critical_finding_count: int
    high_finding_count: int
    vendors_with_student_data: int
    vendors_missing_dpa: int
    vendors_auto_renewing_untracked: int
    school_wide_findings: List[VRFinding] = field(default_factory=list)
    top_priorities: List[VRFinding] = field(default_factory=list)
    category_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class VRReport:
    per_vendor_results: List[VendorResult]
    school_wide_results: List[VRFinding]
    summary: VRSummary
    renewal_risk_register: List[RenewalRisk] = field(default_factory=list)
    floor_cap: Optional["FloorCap"] = None


@dataclass
class FloorCap:
    """
    Set when a critical floor rule fires for the module.
    The overall_grade is capped at cap_grade regardless of the
    weighted average. The report shows this cap explicitly.
    """
    cap_grade: str            # "D"
    reason: str
    trigger_vendors: List[str]
    trigger_finding: str


# ── Helpers ────────────────────────────────────────────────────────

def _get(answers, section_id, template_qid):
    """Get the raw answer for a per-vendor template question."""
    full_qid = f"{section_id}_{template_qid}"
    rec = answers.get(full_qid, {})
    if isinstance(rec, dict):
        raw = rec.get("raw_answer")
        if isinstance(raw, bool):
            return "yes" if raw else "no"
        return raw
    return None


def _get_direct(answers, qid):
    """Get the raw answer for a direct (non-template) question."""
    rec = answers.get(qid, {})
    if isinstance(rec, dict):
        raw = rec.get("raw_answer")
        if isinstance(raw, bool):
            return "yes" if raw else "no"
        return raw
    return None


def _grade(pct):
    if pct >= 90: return "A"
    if pct >= 80: return "B"
    if pct >= 65: return "C"
    if pct >= 50: return "D"
    return "F"


def _severity_from_pct(pct):
    if pct >= 80: return "healthy"
    if pct >= 65: return "watch"
    if pct >= 40: return "concern"
    return "urgent"


# ── Per-vendor scoring ─────────────────────────────────────────────

# Areas and their question IDs (template question IDs, without section prefix)
AREA_QUESTIONS = {
    "Ownership & Documentation": ["V.ID.owner", "V.RENEW.signed"],
    "Cost Visibility":           ["V.COST.known", "V.COST.budget"],
    "Renewal Management":        ["V.RENEW.date", "V.RENEW.auto", "V.RENEW.notice", "V.RENEW.tracked"],
    "Support & Access":          ["V.SUPPORT.contact", "V.SUPPORT.escalation", "V.SUPPORT.admin"],
    "Data Compliance":           ["V.DATA.ferpa", "V.DATA.dpa"],
}

QUESTION_WEIGHTS = {
    # Ownership & Documentation
    "V.ID.owner": {
        # any non-empty text answer scores full points; evaluated as present/absent
        "_present": 2, "_absent": 0
    },
    "V.RENEW.signed": {
        "Yes — signed contract on file and location is known": 3,
        "Yes — contract exists but location is unclear":       2,
        "No — no signed contract":                            0,
        "Not applicable — verbal or click-through agreement only": 2,
        "Unknown":                                            0,
    },
    # Cost Visibility
    "V.COST.known": {
        "Yes — confirmed and tracked in a budget or register": 4,
        "Approximate — estimated but not confirmed":           2,
        "No — cost is not known":                             0,
        "Free — no cost":                                     4,
    },
    "V.COST.budget": {
        "Yes — in the approved budget":    3,
        "Partial — partially budgeted":    2,
        "No — not currently budgeted":     0,
        "Unknown":                         0,
    },
    # Renewal Management
    "V.RENEW.date": {
        # any non-empty text scores; absence penalised
        "_present": 5, "_absent": 0
    },
    "V.RENEW.auto": {
        "Yes — auto-renews; cancellation notice required before renewal date": 2,
        "No — requires active renewal decision":                               4,
        "Unknown":                                                             0,
    },
    # V.RENEW.notice: conditional on auto-renew; 2 pts from YAML
    "V.RENEW.notice": {
        "30 days or less":           1,
        "31–60 days":                2,
        "61–90 days":                2,
        "More than 90 days":         2,
        "Not specified in contract": 0,
        "Unknown":                   0,
    },
    "V.RENEW.tracked": {
        "Yes — in a calendar or system with a reminder set": 5,
        "Tracked — but no reminder set":                     3,
        "No — renewal date known but not tracked":           1,
        "No — renewal date is not known":                    0,
        "Unknown":                                           0,
    },
    # Support & Access
    "V.SUPPORT.contact": {
        "Yes — full support contact documented and accessible": 4,
        "Partial — some contact info documented":               2,
        "No — support contact not documented":                  0,
        "Unknown":                                              0,
    },
    # V.SUPPORT.escalation: 2 pts from YAML
    "V.SUPPORT.escalation": {
        "Yes — escalation path documented":  2,
        "No — escalation path not documented": 0,
        "Not applicable — not a critical system": 2,
        "Unknown":                            0,
    },
    "V.SUPPORT.admin": {
        "Yes — credentials in a shared password manager or documented process": 5,
        "Partial — credentials known to IT but not formally documented":         2,
        "No — credentials are not documented":                                   0,
        "Unknown":                                                               0,
    },
    # Data Compliance (only scored when student data is held)
    "V.DATA.ferpa": {
        "Yes — DPA or privacy agreement in place and signed": 6,
        "Yes — reviewed but no formal agreement signed":      3,
        "Partial — under review":                             2,
        "No — not reviewed":                                  0,
        "Unknown":                                            0,
    },
    "V.DATA.dpa": {
        "Yes — signed DPA on file, location known":    5,
        "Yes — DPA exists but location is unclear":    3,
        "No — no DPA in place":                        0,
        "Vendor does not offer a DPA":                 2,
        "Unknown":                                     0,
    },
}


def score_vendor_section(answers, section_id):
    """Score one per-vendor worksheet. Returns (earned, max_pts, area_scores)."""
    earned = 0.0
    max_pts = 0
    area_scores = {area: [0.0, 0] for area in AREA_QUESTIONS}

    holds_student_data = _get(answers, section_id, "V.DATA.student") == \
                         "Yes — holds or processes student data"

    qid_to_area = {}
    for area, qids in AREA_QUESTIONS.items():
        for qid in qids:
            qid_to_area[qid] = area

    for template_qid, weight_map in QUESTION_WEIGHTS.items():
        area = qid_to_area.get(template_qid)

        # Data Compliance questions only count if vendor holds student data
        if area == "Data Compliance" and not holds_student_data:
            continue

        # V.RENEW.notice is only shown (and scored) when the vendor auto-renews
        if template_qid == "V.RENEW.notice":
            auto_val = _get(answers, section_id, "V.RENEW.auto")
            if auto_val != "Yes — auto-renews; cancellation notice required before renewal date":
                continue

        # Text-present/absent questions (owner, renewal date)
        if "_present" in weight_map:
            raw = _get(answers, section_id, template_qid)
            is_present = bool(raw and str(raw).strip() and
                              str(raw).strip().lower() not in ("unknown", "none", ""))
            pts = weight_map["_present"] if is_present else weight_map["_absent"]
            max_q = weight_map["_present"]
        else:
            raw = _get(answers, section_id, template_qid)
            max_q = max(v for k, v in weight_map.items()
                        if not k.startswith("_"))
            if max_q == 0:
                continue
            pts = weight_map.get(str(raw) if raw is not None else "", 0)

        if max_q == 0:
            continue

        max_pts += max_q
        if area:
            area_scores[area][1] += max_q

        earned += pts
        if area:
            area_scores[area][0] += pts

    area_scores_final = {
        a: (v[0], v[1]) for a, v in area_scores.items() if v[1] > 0
    }
    return earned, max_pts, area_scores_final


# ── Strength detection ─────────────────────────────────────────────

def _detect_strengths(answers, section_id):
    g = lambda qid: _get(answers, section_id, qid)
    strengths = []

    if g("V.RENEW.tracked") == "Yes — in a calendar or system with a reminder set":
        strengths.append("Renewal date is tracked with a reminder")
    if g("V.COST.known") == "Yes — confirmed and tracked in a budget or register":
        strengths.append("Annual cost is confirmed and tracked")
    if g("V.COST.budget") == "Yes — in the approved budget":
        strengths.append("Subscription is in the approved budget")
    if g("V.SUPPORT.admin") == "Yes — credentials in a shared password manager or documented process":
        strengths.append("Admin credentials are in a shared password manager")
    if g("V.SUPPORT.contact") == "Yes — full support contact documented and accessible":
        strengths.append("Support contact is fully documented")
    if g("V.RENEW.signed") == "Yes — signed contract on file and location is known":
        strengths.append("Signed contract is on file with known location")
    if g("V.DATA.ferpa") == "Yes — DPA or privacy agreement in place and signed":
        strengths.append("A signed Data Processing Agreement is in place")
    if g("V.DATA.dpa") == "Yes — signed DPA on file, location known":
        strengths.append("Signed DPA is on file with known location")
    return strengths


# ── Per-vendor findings ────────────────────────────────────────────

def findings_for_vendor(answers, section_id, vendor_name, core_categories=None):
    findings = []
    g = lambda qid: _get(answers, section_id, qid)

    holds_student = g("V.DATA.student") == "Yes — holds or processes student data"
    holds_staff   = g("V.DATA.staff")   == "Yes — holds or processes confidential staff data"
    sensitive = holds_student or holds_staff
    data_context = ""
    if holds_student and holds_staff:
        data_context = " This vendor holds student and confidential staff data."
    elif holds_student:
        data_context = " This vendor holds student data."
    elif holds_staff:
        data_context = " This vendor holds confidential staff data."

    # ── Cost visibility ──────────────────────────────────────────
    cost_known = g("V.COST.known")
    if cost_known == "No — cost is not known":
        findings.append(VRFinding(
            area="Cost Visibility", severity="high", effort="S",
            owner="Business Office / IT Director", timing="immediate",
            vendor_name=vendor_name,
            rule_id="cv_cost_unknown",
            title="Annual cost unknown",
            detail=(f"The annual cost for {vendor_name} is not known. Untracked spend "
                    f"cannot be budgeted, reviewed at renewal, or cancelled when value "
                    f"is unclear."),
            action=("Contact the vendor or check billing records to confirm the annual "
                    "cost. Add it to the vendor register and the budget tracker.")
        ))
    elif cost_known == "Approximate — estimated but not confirmed":
        findings.append(VRFinding(
            area="Cost Visibility", severity="medium", effort="S",
            owner="Business Office", timing="near_term",
            vendor_name=vendor_name,
            rule_id="cv_cost_estimated",
            title="Annual cost estimated but not confirmed",
            detail=(f"The cost for {vendor_name} is approximate. An unverified estimate "
                    f"may not match actual billing and can lead to budget surprises at "
                    f"renewal."),
            action=("Verify the exact annual cost against invoice or vendor portal. "
                    "Update the register with the confirmed figure.")
        ))

    budget = g("V.COST.budget")
    if budget == "No — not currently budgeted":
        findings.append(VRFinding(
            area="Cost Visibility", severity="medium" if not sensitive else "high",
            effort="S", owner="Business Office", timing="near_term",
            vendor_name=vendor_name,
            rule_id="cv_not_budgeted",
            title="Subscription not in current budget",
            detail=(f"{vendor_name} is not included in the current approved budget."
                    f"{data_context} Unbudgeted subscriptions are at risk of lapsing "
                    f"or auto-renewing without oversight."),
            action=("Add this subscription to the budget for the current or upcoming year. "
                    "Confirm whether it should continue before the next renewal.")
        ))

    # ── Renewal management ───────────────────────────────────────
    renewal_date = g("V.RENEW.date")
    renewal_absent = (not renewal_date or
                      str(renewal_date).strip().lower() in ("unknown", "none", ""))
    if renewal_absent:
        sev = "high" if sensitive else "medium"
        findings.append(VRFinding(
            area="Renewal Management", severity=sev, effort="S",
            owner="IT Director / Business Office", timing="immediate" if sensitive else "near_term",
            vendor_name=vendor_name,
            rule_id="rm_renewal_date_unknown",
            title="Renewal date not known",
            detail=(f"The renewal or expiry date for {vendor_name} is not recorded."
                    f"{data_context} Without a known renewal date, the contract may "
                    f"auto-renew unexpectedly or lapse without notice."),
            action=("Contact the vendor or review the original contract to find the "
                    "renewal date. Record it in the register and set a calendar reminder "
                    "at least 60 days in advance.")
        ))

    auto_renew = g("V.RENEW.auto")
    renewal_tracked = g("V.RENEW.tracked")
    if (auto_renew == "Yes — auto-renews; cancellation notice required before renewal date"
            and renewal_tracked in ("No — renewal date known but not tracked",
                                    "No — renewal date is not known", "Unknown", None)):
        findings.append(VRFinding(
            area="Renewal Management", severity="high", effort="S",
            owner="IT Director / Business Office", timing="immediate",
            vendor_name=vendor_name,
            rule_id="rm_auto_renew_untracked",
            title="Auto-renewing contract with no tracked reminder",
            detail=(f"{vendor_name} auto-renews and there is no calendar reminder or "
                    f"tracking in place. An unmonitored auto-renewal commits budget "
                    f"without a deliberate decision.{data_context}"),
            action=("Set a calendar reminder at least 60 days before the renewal date "
                    "— or 30 days before the required cancellation notice deadline if "
                    "shorter. Assign a named owner to act on the reminder.")
        ))
    elif renewal_tracked in ("No — renewal date known but not tracked",
                             "Tracked — but no reminder set") and not renewal_absent:
        findings.append(VRFinding(
            area="Renewal Management", severity="low", effort="S",
            owner="IT Director / Business Office", timing="planned",
            vendor_name=vendor_name,
            rule_id="rm_renewal_not_tracked",
            title="Renewal date known but not tracked with a reminder",
            detail=(f"The renewal date for {vendor_name} is known but not entered into "
                    f"a calendar or reminder system. Relying on memory for renewal dates "
                    f"is a common source of missed renewals and surprise auto-renewals."),
            action=("Add the renewal date to a shared calendar with a 60-day reminder. "
                    "Assign a named owner.")
        ))

    signed = g("V.RENEW.signed")
    if signed == "No — no signed contract":
        sev = "medium" if not sensitive else "high"
        findings.append(VRFinding(
            area="Renewal Management", severity=sev, effort="S+",
            owner="Business Office", timing="near_term",
            vendor_name=vendor_name,
            rule_id="rm_no_signed_contract",
            title="No signed contract on file",
            detail=(f"There is no signed contract or order form on file for {vendor_name}."
                    f"{data_context} Without a contract, the school has no documented "
                    f"record of pricing, renewal terms, or vendor obligations."),
            action=("Request a copy of the original contract or order from the vendor. "
                    "If the agreement was click-through, save a PDF of the terms accepted. "
                    "Store it in a shared location with the vendor's other records.")
        ))
    elif signed == "Yes — contract exists but location is unclear":
        findings.append(VRFinding(
            area="Renewal Management", severity="low", effort="S",
            owner="Business Office / IT Director", timing="planned",
            vendor_name=vendor_name,
            rule_id="rm_contract_location_unknown",
            title="Contract exists but its location is not documented",
            detail=(f"A signed contract for {vendor_name} exists, but the location is "
                    f"unclear. A contract that cannot be found quickly is effectively "
                    f"unavailable when needed."),
            action=("Locate the contract and store it in a shared, documented location — "
                    "e.g. a vendor folder in the school's cloud drive. Record the location "
                    "in the vendor register.")
        ))

    # ── Support and access ───────────────────────────────────────
    support = g("V.SUPPORT.contact")
    if support in ("No — support contact not documented", "Unknown"):
        findings.append(VRFinding(
            area="Support & Access", severity="medium", effort="S",
            owner="IT Director", timing="near_term",
            vendor_name=vendor_name,
            rule_id="sa_support_contact_missing",
            title="Support contact not documented",
            detail=(f"The support contact for {vendor_name} is not recorded. If this "
                    f"vendor has an outage or issue, the school does not have a quick "
                    f"way to reach them."),
            action=("Look up the support email, phone number, and portal URL for this "
                    "vendor and add it to the register. Include the account number if "
                    "one exists.")
        ))

    admin = g("V.SUPPORT.admin")
    if admin == "No — credentials are not documented":
        sev = "high" if sensitive else "medium"
        findings.append(VRFinding(
            area="Support & Access", severity=sev, effort="S",
            owner="IT Director", timing="immediate" if sensitive else "near_term",
            vendor_name=vendor_name,
            rule_id="sa_admin_creds_missing",
            title="Admin credentials not documented",
            detail=(f"Admin credentials for {vendor_name} are not documented in a shared "
                    f"location.{data_context} If the person who manages this account leaves "
                    f"the school, access may be lost."),
            action=("Add the admin credentials for this vendor to the school's shared "
                    "password manager. Verify at least two people have access.")
        ))
    elif admin == "Partial — credentials known to IT but not formally documented":
        findings.append(VRFinding(
            area="Support & Access", severity="low", effort="S",
            owner="IT Director", timing="planned",
            vendor_name=vendor_name,
            rule_id="sa_admin_creds_informal",
            title="Admin credentials known but not in a shared password manager",
            detail=(f"Admin credentials for {vendor_name} are known to IT but not stored "
                    f"in a shared password manager. This creates a single-person dependency."),
            action=("Move these credentials to a shared password manager. Confirm a "
                    "backup person has access.")
        ))

    # ── Student data compliance ──────────────────────────────────
    if holds_student:
        ferpa = g("V.DATA.ferpa")
        if ferpa in ("No — not reviewed", "Unknown", None):
            findings.append(VRFinding(
                area="Data Compliance", severity="high", effort="M",
                owner="IT Director / Head of School", timing="immediate",
                vendor_name=vendor_name,
            rule_id="dc_ferpa_not_reviewed",
                title="FERPA/COPPA compliance not reviewed",
                detail=(f"{vendor_name} holds student data and FERPA or COPPA compliance "
                        f"has not been reviewed. Schools are responsible for ensuring "
                        f"third-party vendors meet federal student data requirements. "
                        f"A missing review creates regulatory and reputational risk."),
                action=("Request the vendor's privacy policy, Student Data Privacy Agreement "
                        "template, and any SOC 2 or FERPA compliance documentation. "
                        "Review it and document the outcome before the next renewal.")
            ))
        elif ferpa == "Partial — under review":
            findings.append(VRFinding(
                area="Data Compliance", severity="medium", effort="S+",
                owner="IT Director", timing="near_term",
                vendor_name=vendor_name,
            rule_id="dc_ferpa_review_incomplete",
                title="FERPA/COPPA review in progress but not complete",
                detail=(f"A compliance review is underway for {vendor_name} but has not "
                        f"been completed. Until it is finished and documented, the school "
                        f"cannot confirm this vendor meets its obligations."),
                action=("Complete and document the compliance review. If review reveals "
                        "gaps, flag them before renewing the contract.")
            ))

        dpa = g("V.DATA.dpa")
        if dpa == "No — no DPA in place":
            findings.append(VRFinding(
                area="Data Compliance", severity="critical", effort="M",
                owner="IT Director / Business Office", timing="immediate",
                vendor_name=vendor_name,
            rule_id="dc_no_dpa",
                title="No Data Processing Agreement in place",
                detail=(f"{vendor_name} holds student data but there is no signed Data "
                        f"Processing Agreement (DPA) or Student Data Privacy Agreement. "
                        f"A DPA defines the vendor's obligations around student data use, "
                        f"retention, and breach notification — without one, the school "
                        f"has no contractual protection."),
                action=("Request the vendor's DPA template immediately. Most EdTech vendors "
                        "have a standard DPA — if they do not, this is itself a red flag. "
                        "Sign the DPA before the next renewal and store it in the register.")
            ))
        elif dpa == "Yes — DPA exists but location is unclear":
            findings.append(VRFinding(
                area="Data Compliance", severity="low", effort="S",
                owner="IT Director / Business Office", timing="planned",
                vendor_name=vendor_name,
            rule_id="dc_dpa_location_unknown",
                title="Signed DPA exists but location is not documented",
                detail=(f"A DPA for {vendor_name} is signed but its location is not recorded. "
                        f"A DPA that cannot be quickly produced has limited value in the "
                        f"event of a breach or audit."),
                action=("Locate the signed DPA and store it in a shared, documented "
                        "location. Record its location in the vendor register.")
            ))

    # ── Value and usage ──────────────────────────────────────────
    value = g("V.USE.value")
    use = g("V.USE.active")
    if (use in ("Rarely — barely used", "No — not currently in use") and
            value in ("No — low value, renewal is in question", "Unsure — unclear whether to renew")):
        findings.append(VRFinding(
            area="Value Assessment", severity="low", effort="S",
            owner="IT Director / Department Head", timing="planned",
            vendor_name=vendor_name,
            rule_id="va_low_use_subscription",
            title="Low-use subscription flagged for renewal review",
            detail=(f"{vendor_name} is rarely or not currently in use, and its value has "
                    f"been flagged as unclear or low. Subscriptions in this state are "
                    f"candidates for cancellation at next renewal."),
            action=("Review whether this subscription should be renewed. Consult with "
                    "the primary department user before the renewal date. If the decision "
                    "is to cancel, confirm the cancellation process and any notice requirements.")
        ))

    # ── Cancellation notice window (VR-R6) ───────────────────────
    # Fires when vendor auto-renews and the required cancellation notice period
    # is unknown or not specified — creating financial exposure.
    notice = g("V.RENEW.notice")
    if (auto_renew == "Yes — auto-renews; cancellation notice required before renewal date"
            and notice in ("Unknown", "Not specified in contract", None)):
        findings.append(VRFinding(
            area="Renewal Management", severity="medium", effort="S",
            owner="IT Director / Business Office", timing="near_term",
            vendor_name=vendor_name,
            rule_id="rm_cancellation_window_unknown",
            title="Cancellation notice window unknown for auto-renewing contract",
            detail=(f"{vendor_name} auto-renews and the required cancellation notice "
                    f"period is not documented. Without knowing the notice window, "
                    f"the school cannot reliably cancel before being committed to "
                    f"another term."),
            action=("Check the contract or vendor portal to confirm how many days "
                    "notice are required before the renewal date to cancel. Record "
                    "this in the vendor register and set a calendar reminder accordingly.")
        ))

    # ── Escalation path for core/critical vendors (VR-S4) ────────
    # A missing escalation path is low-risk for utility tools but a material
    # operational gap for core infrastructure vendors (SIS, LMS, identity
    # providers, network infrastructure, communications).
    # The list of core categories is loaded from module_3.yaml — no Python
    # changes needed to add or adjust categories.
    _core = core_categories or []
    escalation = g("V.SUPPORT.escalation")
    vendor_category = g("V.ID.category") or ""
    is_core = any(cat.lower() in vendor_category.lower() for cat in _core)
    if escalation in ("No — escalation path not documented", "Unknown") and is_core:
        findings.append(VRFinding(
            area="Support & Access", severity="medium", effort="S",
            owner="IT Director", timing="near_term",
            vendor_name=vendor_name,
            rule_id="sa_no_escalation_path",
            title="No escalation path documented for core system vendor",
            detail=(f"{vendor_name} is a core system and there is no documented "
                    f"escalation path for when standard support is unresponsive. "
                    f"For critical platforms, knowing who to call next — an account "
                    f"manager, support VP, or emergency line — can be the difference "
                    f"between a 2-hour and a 2-day outage."),
            action=("Ask your account manager or vendor contact to provide an "
                    "escalation contact — typically a named account manager or "
                    "a priority support line. Document it in the vendor register "
                    "alongside the regular support contact.")
        ))

    # ── Budget finding severity escalation when cost is high ─────
    # V.COST.amount is metadata (points=0) but is used here as a conditional
    # modifier: if a vendor is not budgeted AND the annual cost is material
    # (above $5,000), escalate the existing budget finding from medium to high.
    # This modifies findings already appended above — scan and upgrade in place.
    amount_raw = g("V.COST.amount")
    try:
        annual_cost_num = float(str(amount_raw).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        annual_cost_num = 0.0
    if annual_cost_num >= 5000:
        for f in findings:
            if f.title == "Subscription not in current budget":
                f.severity = "high"
                f.timing = "immediate"
                f.detail = (f.detail + f" Annual cost is approximately "
                            f"${annual_cost_num:,.0f} — an unbudgeted commitment "
                            f"at this level requires prompt finance visibility.")
                break

    return findings


# ── Renewal risk register ──────────────────────────────────────────

_NOTICE_DAYS_MAP = {
    "30 days or less":       30,
    "31–60 days":            60,
    "61–90 days":            90,
    "More than 90 days":    120,
    "Not specified in contract": None,
    "Unknown":              None,
}


def _renewal_risk_level(auto_renews, renewal_tracked, notice):
    """Assign a risk level to a vendor's renewal situation."""
    if auto_renews:
        if renewal_tracked not in ("Yes — in a calendar or system with a reminder set",
                                   "Tracked — but no reminder set"):
            return "high", "Auto-renews with no tracked reminder"
        if notice and notice >= 60:
            return "medium", f"Auto-renews; {notice}-day cancellation notice required"
        return "medium", "Auto-renews; ensure cancellation window is monitored"
    else:
        if renewal_tracked == "No — renewal date is not known":
            return "high", "Renewal date unknown — cannot plan for it"
        if renewal_tracked in ("No — renewal date known but not tracked",
                                "Tracked — but no reminder set"):
            return "medium", "Renewal date known but reminder not set"
        return "low", "Renewal tracked with reminder"


def build_renewal_risk_register(per_vendor_results):
    """Build and sort the renewal risk register from per-vendor results."""
    register = []
    for vr in per_vendor_results:
        if not vr.renewal_date or str(vr.renewal_date).strip().lower() in (
                "unknown", "none", "rolling", ""):
            # No date — flag as unknown-risk only if auto-renewing
            if vr.auto_renews:
                register.append(RenewalRisk(
                    vendor_name=vr.vendor_name,
                    category=vr.category,
                    renewal_date="Unknown",
                    auto_renews=True,
                    notice_days=None,
                    risk_level="high",
                    risk_reason="Auto-renews but renewal date is not recorded",
                ))
            continue

        risk_level, risk_reason = _renewal_risk_level(
            vr.auto_renews or False,
            "Yes — in a calendar or system with a reminder set",  # default safe
            None
        )

        register.append(RenewalRisk(
            vendor_name=vr.vendor_name,
            category=vr.category,
            renewal_date=str(vr.renewal_date),
            auto_renews=vr.auto_renews or False,
            notice_days=None,
            risk_level=risk_level,
            risk_reason=risk_reason,
        ))

    # Sort: high risk first, then by vendor name
    order = {"high": 0, "medium": 1, "low": 2}
    register.sort(key=lambda r: (order.get(r.risk_level, 9), r.vendor_name.lower()))
    return register


# ── School-wide governance findings (VR2) ─────────────────────────

def findings_for_school_wide(answers):
    findings = []
    g = lambda qid: _get_direct(answers, qid)

    vr2_1 = g("VR2.1")
    if vr2_1 in ("No — staff can adopt tools without review", "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="high", effort="M",
            owner="IT Director / Head of School", timing="immediate",
            rule_id="vg_no_software_approval",
            title="No software approval process — shadow IT risk",
            detail=("Staff can adopt tools and subscriptions without IT or business office "
                    "review. Shadow IT is one of the most common sources of untracked spend "
                    "and student data compliance gaps in schools. Tools holding student data "
                    "can be adopted without contracts, privacy reviews, or cost approval."),
            action=("Implement a lightweight software approval process. A simple request "
                    "form with a 48-hour IT turnaround closes the most common gap. Include "
                    "questions about cost, student data involvement, and renewal terms.")
        ))
    elif vr2_1 == "Informal — IT or business office is usually consulted but not required":
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director", timing="near_term",
            rule_id="software_approval_is_informal_not_consis",
            title="Software approval is informal — not consistently followed",
            detail=("IT is usually consulted before new tools are adopted, but the process "
                    "is informal and not required. Informal processes have gaps — particularly "
                    "when new staff join who do not know the convention."),
            action=("Formalise the approval process with a one-page policy and a simple "
                    "request form. Make it a requirement, not a suggestion, for any tool "
                    "that holds school or student data.")
        ))

    vr2_2 = g("VR2.2")
    if vr2_2 in ("No clear policy — contracts can be signed by multiple people without oversight",
                  "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="high", effort="S+",
            owner="Head of School / Business Manager", timing="immediate",
            rule_id="no_clear_contract_signing_authority",
            title="No clear contract signing authority",
            detail=("There is no clear policy about who can sign vendor contracts at the "
                    "school. Without defined signing authority, contracts may be signed by "
                    "staff without finance or leadership visibility, creating unapproved "
                    "financial commitments."),
            action=("Document which roles have signing authority for vendor contracts — "
                    "e.g. Head of School for contracts above $X, Business Manager for "
                    "smaller contracts. Share the policy with relevant staff.")
        ))
    elif vr2_2 == "Informal — generally understood but not written down":
        findings.append(VRFinding(
            area="Vendor Governance", severity="low", effort="S",
            owner="Head of School / Business Manager", timing="planned",
            rule_id="contract_signing_authority_informal_not_",
            title="Contract signing authority informal — not documented",
            detail=("Signing authority is informally understood but not written down. "
                    "This creates risk during staff transitions."),
            action=("Write down the signing authority policy — even a one-paragraph "
                    "email to relevant staff is a starting point. Formalise it in the "
                    "staff handbook or IT policy document.")
        ))

    # ── VR2.3: Spend threshold policy ────────────────────────────
    vr2_3 = g("VR2.3")
    if vr2_3 in ("No — no spend threshold policy", "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director / Head of School", timing="near_term",
            rule_id="no_it_procurement_spend_threshold_shadow",
            title="No IT procurement spend threshold — shadow IT risk",
            detail=("There is no defined spend threshold below which IT or departments "
                    "must obtain review before adopting a new tool. Without a threshold "
                    "policy, staff can subscribe to tools that hold student data, "
                    "auto-renew indefinitely, or create security gaps — all without "
                    "IT or finance visibility. This is one of the most common sources "
                    "of shadow IT in schools."),
            action=("Define a simple spend threshold policy: for example, any subscription "
                    "above $500/year or any tool that holds student or staff data requires "
                    "IT review before adoption. A one-page policy shared with staff closes "
                    "the most common gap. Pair it with the software approval process.")
        ))
    elif vr2_3 == "Informal — general understanding but not documented":
        findings.append(VRFinding(
            area="Vendor Governance", severity="low", effort="S",
            owner="IT Director / Head of School", timing="planned",
            rule_id="spend_threshold_policy_informal_not_docu",
            title="Spend threshold policy informal — not documented",
            detail=("A general understanding exists about spend thresholds for IT "
                    "purchases, but it is not written down. Informal policies fail "
                    "when new staff join or when edge cases arise."),
            action=("Write the threshold policy down — even a one-paragraph description "
                    "with a dollar amount and what triggers IT review. Add it to the "
                    "staff handbook or the IT policy document.")
        ))

    vr2_4 = g("VR2.4")
    if vr2_4 in ("No — this register is the first attempt", "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="M",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="no_master_vendor_register_existed_before",
            title="No master vendor register existed before this audit",
            detail=("The school did not have a central vendor or subscription register "
                    "before this audit. Without a register, the school cannot quickly "
                    "answer questions about spend, renewals, or data obligations."),
            action=("Use the output of this module as the school's master vendor register. "
                    "Assign a named joint owner (IT + Business Office) and schedule an "
                    "annual review, preferably before budget season.")
        ))
    elif vr2_4 == "Partial — IT has a list and Business Office has a list, but they are separate":
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="vg_siloed_vendor_lists",
            title="IT and Business Office maintain separate vendor lists",
            detail=("IT and the Business Office each maintain their own vendor list with "
                    "no shared view. This creates duplicate effort and gaps — IT may not "
                    "know about finance tools, and the Business Office may not know about "
                    "IT-managed subscriptions."),
            action=("Merge the two lists using this register as the foundation. Assign a "
                    "shared owner and agree on a single source of truth going forward.")
        ))

    vr2_5 = g("VR2.5")
    if vr2_5 in ("No — credentials stored informally (email, personal notes, spreadsheet)",
                  "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="high", effort="M",
            owner="IT Director", timing="immediate",
            rule_id="vg_no_password_manager",
            title="Vendor admin credentials not in a shared password manager",
            detail=("Vendor admin credentials are stored informally — in personal email, "
                    "notes, or a spreadsheet. If the person holding these credentials leaves, "
                    "the school may lose access to critical vendor portals, billing accounts, "
                    "and admin controls."),
            action=("Adopt a shared password manager for all vendor admin accounts. "
                    "Migrate existing credentials, verify at least two IT staff have access, "
                    "and include password manager onboarding in the IT offboarding checklist.")
        ))
    elif vr2_5 == "Partial — used for some accounts but not all":
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director", timing="near_term",
            rule_id="vg_password_manager_partial",
            title="Password manager used for some vendor accounts but not all",
            detail=("Some vendor admin credentials are in a shared password manager, "
                    "but not all. The accounts not covered represent single-person "
                    "dependencies."),
            action=("Audit which vendor accounts are not in the password manager and "
                    "migrate them. Prioritise accounts for vendors that hold student "
                    "or financial data.")
        ))

    vr2_6 = g("VR2.6")
    if vr2_6 in ("No — IT and Business Office track renewals independently with no shared system",
                  "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="vg_renewal_siloed",
            title="Renewal tracking is siloed — IT and Business Office not sharing",
            detail=("IT and the Business Office track vendor renewals independently. "
                    "This creates two failure modes: renewals IT manages can lapse "
                    "without budget approval, and renewals the Business Office manages "
                    "can cancel tools IT depends on."),
            action=("Establish a shared renewal calendar that both IT and the Business "
                    "Office can see and update. A shared spreadsheet or a calendar with "
                    "joint access is sufficient. Review it together at the start of each "
                    "budget cycle.")
        ))

    vr2_7 = g("VR2.7")
    if vr2_7 in ("No — vendor account ownership is not addressed in offboarding",
                  "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="high", effort="M",
            owner="HR / IT Director", timing="immediate",
            rule_id="vg_offboarding_missing",
            title="Offboarding does not cover vendor account ownership",
            detail=("When a staff member leaves, there is no process to transfer or revoke "
                    "vendor account ownership. Vendor portal logins, billing contacts, and "
                    "contract records may leave with the departing person, creating access "
                    "gaps and continuity risk."),
            action=("Add vendor account transfer to the IT offboarding checklist. For each "
                    "departing staff member who owned vendor accounts, reassign those accounts "
                    "before their last day. Check billing contacts and support portal accounts "
                    "specifically — these are the most commonly overlooked.")
        ))
    elif vr2_7 == "Partial — handled informally, not part of a documented checklist":
        findings.append(VRFinding(
            area="Vendor Governance", severity="low", effort="S",
            owner="HR / IT Director", timing="planned",
            rule_id="vg_offboarding_informal",
            title="Vendor account offboarding handled informally",
            detail=("Vendor account transfers are handled informally when staff leave, "
                    "but are not part of a documented checklist. Informal processes "
                    "are reliable only when the right people are available and aware."),
            action=("Add vendor accounts explicitly to the offboarding checklist. "
                    "Keep a list in the vendor register of which staff member owns "
                    "each vendor portal account.")
        ))

    vr2_8 = g("VR2.8")
    if vr2_8 in ("No — DPAs not centrally tracked", "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="high", effort="M",
            owner="IT Director / Business Office", timing="immediate",
            rule_id="vg_dpa_not_tracked",
            title="Student data privacy agreements not centrally tracked",
            detail=("There is no central record of which vendors have signed a Data "
                    "Processing Agreement (DPA) or Student Data Privacy Agreement. "
                    "Without a DPA register, the school cannot quickly demonstrate "
                    "compliance when required — by parents, auditors, or regulators."),
            action=("Create a DPA register. For each vendor in this module that holds "
                    "student data, record whether a DPA is in place and where it is stored. "
                    "This module's output is the starting point. Assign a named owner to "
                    "keep it current.")
        ))
    elif vr2_8 == "Partial — some DPAs tracked but not all vendors covered":
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director", timing="near_term",
            rule_id="vg_dpa_tracking_partial",
            title="DPA tracking incomplete — not all student-data vendors covered",
            detail=("A DPA register exists but does not cover all vendors that hold student "
                    "data. Gaps in DPA coverage leave the school partially exposed."),
            action=("Use this module's student-data findings to identify uncovered vendors. "
                    "Request DPAs from any vendor holding student data that is not yet covered.")
        ))

    vr2_9 = g("VR2.9")
    if vr2_9 in ("No — no annual review", "Unknown", None):
        findings.append(VRFinding(
            area="Vendor Governance", severity="medium", effort="S+",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="vg_no_annual_review",
            title="No annual vendor review process",
            detail=("The school does not conduct a deliberate annual pass through its "
                    "vendor portfolio. Without regular review, subscriptions accumulate, "
                    "unused tools continue to auto-renew, and value assessments are never "
                    "updated."),
            action=("Schedule an annual vendor review — ideally timed before budget "
                    "season. Walk through this register together: confirm renewals, "
                    "cancel unused tools, and update cost and ownership fields. "
                    "A 90-minute joint IT/Business Office session is sufficient for "
                    "most schools.")
        ))

    return findings


# ── Top priorities ─────────────────────────────────────────────────

def _build_top_priorities(per_vendor_results, school_wide_findings):
    """Return up to 8 highest-priority findings across all vendors and school-wide."""
    all_findings = []
    for vr in per_vendor_results:
        all_findings.extend(vr.findings)
    all_findings.extend(school_wide_findings)

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_findings.sort(key=lambda f: order.get(f.severity, 9))
    return all_findings[:8]


# ── Category breakdown ─────────────────────────────────────────────

def _build_category_breakdown(per_vendor_results):
    breakdown = {}
    for vr in per_vendor_results:
        cat = vr.category or "Unknown"
        breakdown[cat] = breakdown.get(cat, 0) + 1
    return breakdown


# ── Critical floor rules ───────────────────────────────────────────

def critical_floor_check(per_vendor_results):
    """
    Check whether any critical floor condition is met across the vendor portfolio.

    A critical floor caps the module overall grade at D regardless of the
    weighted average. This prevents a strong portfolio average from masking
    a genuinely dangerous gap in one or more critical vendors.

    Floor conditions (any one is sufficient to trigger the cap):
      VR-FLOOR-1: Any student-data vendor has no DPA AND no FERPA review
                  (both missing, not just one) — most severe compliance gap
      VR-FLOOR-2: Three or more high-priority vendors have undocumented admin
                  credentials (core-category or student-data vendors only)
      VR-FLOOR-3: Any vendor whose category is core/critical scores below 30%
                  (catastrophic operational control failure)

    Returns FloorCap if a floor condition fires, else None.
    """
    # VR-FLOOR-1: student-data vendor with BOTH no DPA AND no FERPA review
    floor1_vendors = []
    for r in per_vendor_results:
        if r.holds_student_data:
            has_no_dpa = any(
                f.title == "No Data Processing Agreement in place"
                for f in r.findings
            )
            has_no_ferpa = any(
                "FERPA/COPPA compliance not reviewed" in f.title
                for f in r.findings
            )
            if has_no_dpa and has_no_ferpa:
                floor1_vendors.append(r.vendor_name)

    if floor1_vendors:
        return FloorCap(
            cap_grade="D",
            reason=(
                "One or more vendors that hold student data have no signed DPA and "
                "no FERPA/COPPA compliance review. This is a direct FERPA compliance "
                "failure. The overall grade is capped at D until both gaps are resolved."
            ),
            trigger_vendors=floor1_vendors,
            trigger_finding="No Data Processing Agreement in place + FERPA/COPPA compliance not reviewed",
        )

    # VR-FLOOR-2: Three or more student-data or core-category vendors with
    # undocumented admin credentials
    try:
        _yaml_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  "modules", "module_3.yaml")
        with open(_yaml_path, "r", encoding="utf-8") as _f:
            _m3 = yaml.safe_load(_f)
        _core_cats = [c.lower() for c in _m3.get("core_vendor_categories", [])]
    except Exception:
        _core_cats = []

    def _is_core(category):
        return any(c in (category or "").lower() for c in _core_cats)

    cred_vendors = []
    for r in per_vendor_results:
        if r.holds_student_data or _is_core(r.category):
            if any(f.title == "Admin credentials not documented" and f.severity in ("high", "critical")
                   for f in r.findings):
                cred_vendors.append(r.vendor_name)

    if len(cred_vendors) >= 3:
        return FloorCap(
            cap_grade="D",
            reason=(
                f"{len(cred_vendors)} core or student-data vendors have undocumented "
                "admin credentials. Loss of access to this many critical systems during "
                "a staff transition is a severe operational continuity risk. The overall "
                "grade is capped at D until credentials are documented."
            ),
            trigger_vendors=cred_vendors,
            trigger_finding="Admin credentials not documented",
        )

    # VR-FLOOR-3: Any core-category vendor scores below 30%
    floor3_vendors = []
    for r in per_vendor_results:
        if _is_core(r.category) and r.max_pts > 0 and r.score_pct < 30:
            floor3_vendors.append(r.vendor_name)

    if floor3_vendors:
        return FloorCap(
            cap_grade="D",
            reason=(
                "One or more core/critical systems scored below 30%, indicating a "
                "near-complete absence of governance controls for a system the school "
                "depends on daily. The overall grade is capped at D until controls "
                "for these systems are documented."
            ),
            trigger_vendors=floor3_vendors,
            trigger_finding="Core/critical vendor — critically low governance score",
        )

    return None


# ── Main evaluation entry point ────────────────────────────────────

def evaluate_vr(answers, vendor_names, generated_section_ids):
    """
    Evaluate all vendor worksheets and school-wide governance (VR2).
    Returns a VRReport.
    """
    # Load core vendor categories from module_3.yaml so VR-S4 matching
    # is driven by data, not hardcoded Python.
    try:
        _yaml_path = os.path.join(os.path.dirname(__file__), "modules", "module_3.yaml")
        with open(_yaml_path, "r", encoding="utf-8") as _f:
            _m3 = yaml.safe_load(_f)
        core_categories = _m3.get("core_vendor_categories", [])
    except Exception:
        core_categories = []

    per_vendor_results = []

    for name, sid in zip(vendor_names, generated_section_ids):
        earned, max_pts, area_scores = score_vendor_section(answers, sid)
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        grade = _grade(pct)
        severity = _severity_from_pct(pct)

        vendor_findings = findings_for_vendor(answers, sid, name,
                                              core_categories=core_categories)
        strengths = _detect_strengths(answers, sid) if not vendor_findings else []

        category = _get(answers, sid, "V.ID.category") or "Unknown"
        renewal_date = _get(answers, sid, "V.RENEW.date")
        auto_raw = _get(answers, sid, "V.RENEW.auto")
        auto_renews = (auto_raw == "Yes — auto-renews; cancellation notice required before renewal date"
                       if auto_raw else None)
        annual_cost = _get(answers, sid, "V.COST.amount")
        holds_student = _get(answers, sid, "V.DATA.student") == "Yes — holds or processes student data"
        holds_staff   = _get(answers, sid, "V.DATA.staff")   == "Yes — holds or processes confidential staff data"

        # Compute criticality weight now so it can be stored and shown in the report
        is_core = any(cat.lower() in category.lower() for cat in core_categories)
        if is_core and holds_student:
            weight = 4
        elif is_core or holds_student:
            weight = 3
        elif holds_staff:
            weight = 2
        else:
            weight = 1

        per_vendor_results.append(VendorResult(
            vendor_name=name, section_id=sid, earned=earned, max_pts=max_pts,
            score_pct=pct, grade_label=grade, severity=severity,
            category=category, findings=vendor_findings, area_scores=area_scores,
            holds_student_data=holds_student, holds_staff_data=holds_staff,
            renewal_date=renewal_date, auto_renews=auto_renews,
            annual_cost=annual_cost, strengths=strengths,
            weight_multiplier=weight,
        ))

    school_wide = findings_for_school_wide(answers)
    renewal_register = build_renewal_risk_register(per_vendor_results)

    # Summary counts
    urgent  = sum(1 for r in per_vendor_results if r.severity == "urgent")
    concern = sum(1 for r in per_vendor_results if r.severity == "concern")
    watch   = sum(1 for r in per_vendor_results if r.severity == "watch")
    healthy = sum(1 for r in per_vendor_results if r.severity == "healthy")

    # ── VR2 school-wide governance score ────────────────────────────
    # VR2 questions are answered once for the whole school (not per-vendor).
    # Point values match the YAML definition. VR2 is weighted at multiplier=2
    # (equivalent to a medium-criticality vendor) so it influences but does
    # not dominate the overall grade. VR2.10 is a free-text notes field and
    # is intentionally excluded (0 points in YAML).
    _VR2_WEIGHTS = {
        "VR2.1": {"Yes — formal approval process, documented and followed": 8,
                  "Informal — IT or business office is usually consulted but not required": 4,
                  "No — staff can adopt tools without review": 0,
                  "Unknown": 0},
        "VR2.2": {"Clear policy — named role(s) with documented signing authority": 5,
                  "Informal — generally understood but not written down": 2,
                  "No clear policy — contracts can be signed by multiple people without oversight": 0,
                  "Unknown": 0},
        "VR2.3": {"Yes — documented spend threshold in place": 4,
                  "Informal — general understanding but not documented": 2,
                  "No — no spend threshold policy": 0,
                  "Unknown": 0},
        "VR2.4": {"Yes — maintained jointly by IT and Business Office": 7,
                  "Partial — IT has a list and Business Office has a list, but they are separate": 3,
                  "Partial — one list exists but it is incomplete or outdated": 3,
                  "No — this register is the first attempt": 0,
                  "Unknown": 0},
        "VR2.5": {"Yes — centralized password manager used by IT for all vendor admin accounts": 7,
                  "Partial — used for some accounts but not all": 3,
                  "No — credentials stored informally (email, personal notes, spreadsheet)": 0,
                  "Unknown": 0},
        "VR2.6": {"Yes — shared renewal calendar with IT and Business Office both notified": 5,
                  "Partial — one party tracks renewals and notifies the other informally": 2,
                  "No — IT and Business Office track renewals independently with no shared system": 0,
                  "Unknown": 0},
        "VR2.7": {"Yes — offboarding checklist explicitly covers vendor account transfer": 6,
                  "Partial — handled informally, not part of a documented checklist": 2,
                  "No — vendor account ownership is not addressed in offboarding": 0,
                  "Unknown": 0},
        "VR2.8": {"Yes — central DPA register maintained and current": 6,
                  "Partial — some DPAs tracked but not all vendors covered": 3,
                  "No — DPAs not centrally tracked": 0,
                  "Unknown": 0},
        "VR2.9": {"Yes — formal annual review, documented": 6,
                  "Informal — review happens but is not scheduled or documented": 3,
                  "No — no annual review": 0,
                  "Unknown": 0},
    }

    def _get_vr2(qid):
        rec = answers.get(qid, {})
        if isinstance(rec, dict):
            raw = rec.get("raw_answer")
            if isinstance(raw, bool):
                return "yes" if raw else "no"
            return raw
        return None

    vr2_earned = 0.0
    vr2_max = 0
    for qid, wmap in _VR2_WEIGHTS.items():
        q_max = max(wmap.values())
        if q_max == 0:
            continue
        vr2_max += q_max
        raw = _get_vr2(qid)
        if raw is not None:
            vr2_earned += wmap.get(str(raw), 0)

    vr2_pct = round(vr2_earned / vr2_max * 100) if vr2_max > 0 else 0

    # ── Criticality-weighted overall grade ───────────────────────────
    # Vendors that are both operationally critical AND hold sensitive data
    # carry the most weight. This prevents a healthy score on low-risk tools
    # (classroom apps, communication tools) from masking failures in the
    # school's most important systems.
    #
    # Multiplier logic:
    #   4x  — core/critical category AND holds student data
    #         (e.g. SIS, identity provider, LMS with student records)
    #   3x  — core/critical category OR holds student data (but not both)
    #         (e.g. firewall with no student data; gradebook app not in core list)
    #   2x  — holds confidential staff data only
    #         (e.g. HR system, payroll processor)
    #   1x  — everything else
    #         (e.g. classroom tools, communication apps, facilities software)
    #
    # VR2 school-wide governance score is folded in at multiplier=2 —
    # equivalent to a medium-criticality vendor, enough to matter without
    # dominating the grade when there are many vendors.
    #
    # ── Grade/severity boundary design note ─────────────────────────
    # _grade() and _severity_from_pct() use the same thresholds as Module 1
    # (90/80/65/50 for A/B/C/D/F; 80/65/40 for healthy/watch/concern/urgent).
    # These are intentional — not an oversight. Deviating from Module 1 thresholds
    # would make cross-module scores harder to compare. If the calibration ever
    # changes for Module 3 specifically, update the comment here and in FUTURE_IDEAS.

    weighted_sum = 0.0
    weight_total = 0.0
    for r in per_vendor_results:
        if r.max_pts > 0:
            weighted_sum += r.score_pct * r.weight_multiplier
            weight_total += r.weight_multiplier

    # Include VR2 school-wide governance score at weight=2
    if vr2_max > 0:
        weighted_sum += vr2_pct * 2
        weight_total += 2

    overall_pct = round(weighted_sum / weight_total) if weight_total > 0 else 0
    overall_grade = _grade(overall_pct)

    # ── Critical floor check ────────────────────────────────────────
    floor_cap = critical_floor_check(per_vendor_results)
    if floor_cap:
        _grade_order = ["A", "B", "C", "D", "F"]
        _ci = _grade_order.index(floor_cap.cap_grade) if floor_cap.cap_grade in _grade_order else 3
        _gi = _grade_order.index(overall_grade) if overall_grade in _grade_order else 4
        overall_grade = _grade_order[max(_ci, _gi)]

    all_findings = [f for r in per_vendor_results for f in r.findings] + school_wide
    critical_count = sum(1 for f in all_findings if f.severity == "critical")
    high_count     = sum(1 for f in all_findings if f.severity == "high")

    vendors_with_student_data = sum(1 for r in per_vendor_results if r.holds_student_data)
    vendors_missing_dpa = sum(
        1 for r in per_vendor_results
        if r.holds_student_data and any(
            f.title == "No Data Processing Agreement in place"
            for f in r.findings
        )
    )
    vendors_auto_untracked = sum(
        1 for r in per_vendor_results
        if r.auto_renews and any(
            "Auto-renewing contract with no tracked reminder" in f.title
            for f in r.findings
        )
    )

    top_priorities = _build_top_priorities(per_vendor_results, school_wide)
    category_breakdown = _build_category_breakdown(per_vendor_results)

    summary = VRSummary(
        total_vendors=len(vendor_names),
        vendors_scored=len(per_vendor_results),
        vendors_urgent=urgent, vendors_concern=concern,
        vendors_watch=watch, vendors_healthy=healthy,
        overall_grade=overall_grade,
        critical_finding_count=critical_count,
        high_finding_count=high_count,
        vendors_with_student_data=vendors_with_student_data,
        vendors_missing_dpa=vendors_missing_dpa,
        vendors_auto_renewing_untracked=vendors_auto_untracked,
        school_wide_findings=school_wide,
        top_priorities=top_priorities,
        category_breakdown=category_breakdown,
    )

    return VRReport(
        per_vendor_results=per_vendor_results,
        school_wide_results=school_wide,
        summary=summary,
        renewal_risk_register=renewal_register,
        floor_cap=floor_cap,
    )
