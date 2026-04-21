"""
Rules Engine for Module 1 — Small Private School IT Overview and Action Plan
Schema version: 0.2

Evaluates normalized answers against all defined rules and produces a
structured findings object. Run on-demand after all answers are saved.

Usage:
    from rules_engine import evaluate_all, evaluate_section, findings_to_dict
    report = evaluate_all(answers, session_id, completed_sections)
    report = evaluate_section(answers, section_id="2")
    data   = findings_to_dict(report)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────

@dataclass
class Action:
    action_id: str
    description: str
    time_horizon: str
    schedule_category: Optional[int] = None
    constraint_flag: bool = False
    user_confirmed: bool = False


@dataclass
class Finding:
    finding_id: str
    rule_id: str
    section_id: str
    title: str
    severity: str
    description: str
    actions: list = field(default_factory=list)
    risk_category: Optional[str] = None
    affected_entity: Optional[str] = None
    notes_passthrough: Optional[str] = None
    aggregation_groups: list = field(default_factory=list)
    suppressed_by: Optional[str] = None
    plain_language_note: Optional[str] = None
    amplification_flag: bool = False


@dataclass
class FindingsReport:
    session_id: str
    section_ids_evaluated: list
    findings: list
    suppressed_findings: list
    constraint_flags: list
    key_risk_groups: dict
    data_confidence: str = "high"
    uncertain_sections: list = field(default_factory=list)
    has_incomplete_sections: bool = False


# ─────────────────────────────────────────────────────────────────
# ANSWER NORMALIZER
# ─────────────────────────────────────────────────────────────────

_YES_PATTERNS = (
    "yes — ", "yes — confirmed", "yes — current", "yes — all ", "yes — fully",
    "yes — documented", "yes — most", "yes — well", "yes — reviewed",
    "yes — shared", "yes — tracked", "yes — deployed", "yes — required",
    "yes — defined", "yes — in regular", "yes — loaded", "yes — coverage",
    "yes — configurations", "yes — sops", "yes — changes", "yes — tested",
    "yes — our response", "both — onsite and offsite",
)

_NO_PATTERNS = (
    "no — operations", "no — relies", "no — never tested",
    "no — single connection", "no — shared accounts", "no — access is controlled",
    "no — the environment",
)


def norm(raw) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return "yes" if raw else "no"
    s = str(raw).strip().lower()
    if s == "yes" or any(s.startswith(p) for p in _YES_PATTERNS):
        return "yes"
    if s == "no" or any(s.startswith(p) for p in _NO_PATTERNS):
        return "no"
    if s in ("unknown", "i don't know"):
        return "unknown"
    if s.startswith("partial") or s.startswith("partly"):
        return "partial"
    if s.startswith("informal"):
        return "informal"
    if s in ("partial — deployed on some devices", "yes some",
             "partial — some devices managed",
             "some — a small number of unsupported devices in use",
             "some — take-home for some grades or programs",
             "partial — some privileged accounts have mfa"):
        return "some"
    if s.startswith("many"):
        return "many"
    if s.startswith("maybe or assumed"):
        return "maybe"
    if "more than 12 months" in s:
        return "old"
    if s.startswith("irregularly") or s.startswith("sometimes"):
        return "irregularly"
    if s.startswith("limited or partial"):
        return "limited"
    if "outdated" in s and "not reviewed" in s:
        return "outdated"
    if "manual failover" in s:
        return "manual"
    if "onsite only" in s:
        return "onsite"
    if "offsite only" in s or s == "offsite":
        return "offsite"
    if s.startswith("inconsistent"):
        return "inconsistent"
    if "not applicable" in s:
        return "na"
    if "does not notify" in s:
        return "no_notify"
    return s


def get(answers: dict, qid: str) -> Optional[str]:
    data = answers.get(qid)
    if not data:
        return None
    status = data.get("answer_status", "unanswered")
    if status in ("unanswered", "skipped"):
        return None
    if status == "unknown":
        return "unknown"
    return norm(data.get("raw_answer"))


def get_raw(answers: dict, qid: str) -> Optional[str]:
    data = answers.get(qid)
    if not data:
        return None
    raw = data.get("raw_answer")
    if isinstance(raw, list):
        return "\n".join(str(x) for x in raw)
    return str(raw) if raw else None


def get_notes(answers: dict, qid: str) -> Optional[str]:
    data = answers.get(qid)
    return data.get("notes") if data else None


def get_count(answers: dict, qid: str) -> int:
    data = answers.get(qid)
    if not data or data.get("answer_status") in ("unanswered", "skipped", "unknown"):
        return 0
    try:
        return int(float(str(data.get("raw_answer", 0))))
    except (ValueError, TypeError):
        return 0


def is_yes(answers, qid):           return get(answers, qid) == "yes"
def is_no(answers, qid):            return get(answers, qid) == "no"
def is_unknown(answers, qid):       return get(answers, qid) == "unknown"
def is_no_or_unknown(answers, qid): return get(answers, qid) in ("no", "unknown", None)
def raw_is_yes(answers, qid):
    """For inverted questions where raw 'yes' means a problem exists."""
    data = answers.get(qid)
    if not data or data.get("answer_status") not in ("answered",):
        return False
    return data.get("raw_answer") == "yes"


# ─────────────────────────────────────────────────────────────────
# FINDING AND ACTION FACTORIES
# ─────────────────────────────────────────────────────────────────

def finding(fid, rule_id, section_id, title, severity, description,
            risk_category=None, affected_entity=None, notes_passthrough=None,
            aggregation_groups=None, plain_language_note=None):
    return Finding(
        finding_id=fid, rule_id=rule_id, section_id=section_id,
        title=title, severity=severity, description=description,
        risk_category=risk_category, affected_entity=affected_entity,
        notes_passthrough=notes_passthrough,
        aggregation_groups=aggregation_groups or [],
        plain_language_note=plain_language_note,
    )


def action(aid, description, time_horizon, schedule_category=None):
    return Action(action_id=aid, description=description,
                  time_horizon=time_horizon, schedule_category=schedule_category)


# ─────────────────────────────────────────────────────────────────
# SECTION 2: Governance, Budget, Staffing, and Ownership
# ─────────────────────────────────────────────────────────────────

def evaluate_section_2(answers):
    findings = []
    a = answers

    # R2-001 No named IT leader
    if is_no_or_unknown(a, "2.2"):
        f = finding("F2-001","R2-001","2","No named IT leader or accountable owner","urgent",
            "There is no named person accountable for IT leadership. This is the foundational governance gap that makes every other finding harder to resolve.",
            risk_category="ownership", affected_entity="IT operations", aggregation_groups=["A"])
        f.actions = [
            action("A2-001a","Identify and formally assign a named person accountable for IT leadership decisions and outcomes.","next_30_days"),
            action("A2-001b","Communicate this assignment to school leadership and document it in writing.","next_30_days"),
        ]
        findings.append(f)

    # R2-002 Day-to-day responsibilities
    v23 = get(a,"2.3")
    if v23 in ("no","unknown",None):
        sev = "urgent" if is_no_or_unknown(a,"2.2") else "concern"
        f = finding("F2-002","R2-002","2","Day-to-day IT support responsibilities not clearly assigned",sev,
            "There is no clear assignment of who handles help desk requests, device issues, account problems, and classroom tech support.",
            risk_category="ownership", affected_entity="IT operations", aggregation_groups=["A"])
        f.actions = [action("A2-002a","Define and document who is responsible for day-to-day IT support tasks.","next_30_days")]
        findings.append(f)

    # R2-003 System owners
    if is_no_or_unknown(a,"2.4"):
        f = finding("F2-003","R2-003","2","System ownership not documented","concern",
            "There is no documented record of who owns or is accountable for major platforms and services.",
            risk_category="ownership", affected_entity="systems and platforms", aggregation_groups=["A"])
        f.actions = [action("A2-003a","Create a system ownership register listing each major platform, its owner, and the backup contact.","next_90_days")]
        findings.append(f)

    # R2-004 Vendor contacts
    if is_no_or_unknown(a,"2.5"):
        f = finding("F2-004","R2-004","2","Vendor contacts and escalation paths not documented","concern",
            "There is no documented record of who to contact at key vendors when something goes wrong.",
            risk_category="continuity", affected_entity="vendor relationships", aggregation_groups=["C"])
        f.actions = [action("A2-004a","Create a vendor contact sheet listing each major vendor, support contact, contract or account number, and escalation path.","next_30_days")]
        findings.append(f)

    # R2-005 Budget
    v26 = get(a,"2.6")
    if v26 in ("no","unknown",None):
        f = finding("F2-005","R2-005","2","No formal IT budget exists","concern",
            "IT spending is not formally budgeted. There is no planned allocation for hardware refresh, software renewals, or unexpected failures.")
        f.actions = [action("A2-005a","Work with school leadership to establish a formal annual IT budget covering at minimum: hardware refresh, software renewals, support contracts, and a contingency reserve.","next_12_months")]
        findings.append(f)
    elif v26 == "informal":
        f = finding("F2-005-W","R2-005","2","IT budget exists but is not formally structured","watch",
            "IT spending happens but is not tied to a formal annual budget.")
        f.actions = [action("A2-005-Wa","Formalize the IT budget structure with defined line items for recurring and capital expenditures.","next_12_months")]
        findings.append(f)

    # R2-006 Constraints annotation
    if is_yes(a,"2.7"):
        f = finding("F2-006","R2-006","2","Known budget or staffing constraints affecting IT this year","watch",
            "The IT person has identified active constraints that will limit what can be accomplished this year. Recommendations that require significant spend or staff are flagged with a constraint marker.",
            notes_passthrough=get_notes(a,"2.7"))
        findings.append(f)

    # R2-007 Emergency credentials
    if is_no_or_unknown(a,"2.8"):
        f = finding("F2-007","R2-007","2","Emergency access methods and credentials not documented or controlled","urgent",
            "There is no documented or controlled record of emergency access methods or shared credentials. Undocumented shared credentials are frequently identified as a root cause in costly IT failures.",
            risk_category="continuity", affected_entity="emergency access and credential control", aggregation_groups=["B"])
        f.actions = [
            action("A2-007a","Identify all shared credentials and emergency access methods currently in use.","immediate"),
            action("A2-007b","Document, secure, and control access to these credentials — using a password manager, sealed physical record, or equivalent.","next_30_days"),
            action("A2-007c","Verify that at least one other authorized person can access these credentials without involving the primary IT person.","next_30_days"),
        ]
        findings.append(f)

    # R2-008 Coverage if IT lead unavailable
    v29 = get(a,"2.9")
    if v29 in ("no","unknown","partial",None) and v29 is not None:
        desc = {
            "no": "If the primary IT person is unexpectedly unavailable, the school has no reliable path to maintain basic IT operations.",
            "partial": "Basic IT operations could partially continue if the primary IT person were unavailable, but coverage is incomplete.",
            "unknown": "It is unknown whether IT operations could continue if the primary IT person were unavailable.",
        }.get(v29, "Coverage status unknown.")
        f = finding("F2-008","R2-008","2","Primary IT lead cannot be reliably covered if unavailable","concern",desc,
            risk_category="continuity", affected_entity="IT staffing resilience", aggregation_groups=["B"])
        f.actions = [
            action("A2-008a","Identify at least one person who could cover basic IT operations in an emergency.","next_90_days"),
            action("A2-008b","Document the minimum knowledge and access that person would need and begin cross-training.","next_90_days"),
            action("A2-008c","Consider establishing a relationship with an MSP or IT consultant as a coverage backstop.","next_12_months"),
        ]
        findings.append(f)

    # R2-009 Recurring tasks
    v210 = get(a,"2.10")
    if v210 in ("no","unknown",None) and v210 is not None:
        f = finding("F2-009","R2-009","2","Recurring IT tasks not tracked","concern",
            "Recurring IT tasks are not tracked in any system. Firmware reviews, backup checks, account audits, and renewal reminders depend entirely on memory.")
        f.actions = [action("A2-009a","Create a recurring IT task calendar covering monthly backup reviews, quarterly admin audits, firmware review cadence, and annual renewal reminders.","next_90_days")]
        findings.append(f)
    elif v210 in ("partial","informal"):
        f = finding("F2-009","R2-009","2","Recurring IT tasks only partially tracked","watch",
            "Some recurring IT tasks are tracked but the system is incomplete.")
        f.actions = [action("A2-009a","Complete the recurring IT task calendar or checklist.","next_90_days")]
        findings.append(f)

    # R2-010 Ticketing
    v211 = get(a,"2.11")
    if v211 in ("no","unknown",None) and v211 is not None:
        f = finding("F2-010","R2-010","2","No ticketing system in use for IT support","watch",
            "IT support requests are not tracked through a ticketing system. Without a record, recurring problems go unidentified.")
        f.actions = [action("A2-010a","Evaluate low-cost or free ticketing tools appropriate for a small school IT environment.","next_12_months")]
        findings.append(f)

    # R2-011 Software approval
    v212 = get(a,"2.12")
    if v212 in ("unknown",None) or (v212 and "ad hoc" in v212):
        f = finding("F2-011","R2-011","2","No clear process for approving new classroom software or digital tools","watch",
            "There is no defined process for deciding whether new software or digital tools may be adopted for classroom use. This creates risk around student data privacy, tool sprawl, and inconsistent IT support obligations.",
            aggregation_groups=["D"])
        f.actions = [action("A2-011a","Define and document who has authority to approve new classroom software, what review criteria apply, and how IT is notified.","next_12_months")]
        findings.append(f)

    # R2-C01 No accountability at any level
    if is_no_or_unknown(a,"2.2") and is_no_or_unknown(a,"2.3") and is_no_or_unknown(a,"2.4"):
        f = finding("F2-C01","R2-C01","2","No IT accountability structure exists at any level","urgent",
            "There is no named IT leader, no assignment of day-to-day responsibilities, and no documented system ownership. Every finding in this report should be read in that context.",
            risk_category="ownership", affected_entity="entire IT function", aggregation_groups=["A"])
        f.actions = [
            action("A2-001a","Identify and formally assign a named person accountable for IT leadership.","next_30_days"),
            action("A2-002a","Define and document who is responsible for day-to-day IT support tasks.","next_30_days"),
            action("A2-003a","Create a system ownership register.","next_90_days"),
        ]
        findings.append(f)

    # R2-C02 Single-person dependency with no emergency access
    if is_no_or_unknown(a,"2.9") and is_no_or_unknown(a,"2.8"):
        f = finding("F2-C02","R2-C02","2","Single-person IT dependency with no documented emergency access path","urgent",
            "The school depends entirely on one person for IT operations, and there is no documented path for anyone else to access critical systems in an emergency.",
            risk_category="continuity", affected_entity="IT staffing resilience and emergency access", aggregation_groups=["B"])
        f.actions = [
            action("A2-007a","Identify all shared credentials and emergency access methods.","immediate"),
            action("A2-007b","Document, secure, and control access to these credentials.","next_30_days"),
            action("A2-008a","Identify at least one person who could cover basic IT operations.","next_90_days"),
            action("A2-008b","Begin cross-training or access provisioning for that person.","next_90_days"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 3: Sites, Buildings, Network, and Internet
# ─────────────────────────────────────────────────────────────────

def evaluate_section_3(answers):
    findings = []
    a = answers

    # R3-001 Network diagram
    v32 = get(a,"3.2")
    if v32 in ("no","unknown",None):
        sev = "urgent" if is_no_or_unknown(a,"3.3") else "concern"
        f = finding("F3-001","R3-001","3","No network diagram exists",sev,
            "There is no network diagram. Without a diagram, troubleshooting, planning, and onboarding become significantly harder.")
        f.actions = [action("A3-001a","Create a network diagram reflecting: internet connections, firewall, core switches, wireless infrastructure, and server connections.","next_90_days")]
        findings.append(f)
    elif v32 and "outdated" in v32:
        f = finding("F3-001","R3-001","3","Network diagram exists but is outdated","watch",
            "An outdated diagram can be worse than none — it may lead troubleshooters in the wrong direction.")
        f.actions = [action("A3-001a","Update the network diagram to reflect the current environment.","next_90_days")]
        findings.append(f)

    # R3-002 Site/rack maps
    v33 = get(a,"3.3")
    if v33 in ("no","unknown",None):
        f = finding("F3-002","R3-002","3","No site or closet/rack maps exist","concern",
            "There are no maps documenting where network equipment is physically located.")
        f.actions = [action("A3-002a","Create site maps and closet/rack maps for all buildings with network infrastructure.","next_90_days")]
        findings.append(f)
    elif v33 == "partial":
        f = finding("F3-002","R3-002","3","Site and closet/rack maps incomplete","watch",
            "Some site or closet maps exist but coverage is incomplete.")
        f.actions = [action("A3-002a","Complete site and closet/rack maps for all buildings.","next_90_days")]
        findings.append(f)

    # R3-003 AP locations
    v34 = get(a,"3.4")
    if v34 in ("no","unknown",None):
        f = finding("F3-003","R3-003","3","Wireless access point locations not documented","concern",
            "The physical location of wireless APs is not known or documented. Without this, coverage analysis and troubleshooting are guesswork.")
        f.actions = [action("A3-003a","Walk the environment and document the physical location of every access point.","next_90_days")]
        findings.append(f)
    elif v34 == "partial":
        sev = "concern" if is_no_or_unknown(a,"3.1") else "watch"
        f = finding("F3-003","R3-003","3","Wireless access point locations partially documented",sev,
            "Some AP locations are known but documentation is incomplete.")
        f.actions = [action("A3-003a","Document all remaining access point locations.","next_90_days")]
        findings.append(f)

    # R3-004 Firewall existence (question 3.7)
    v37 = get(a,"3.7")
    if v37 in ("no","unknown",None):
        f = finding("F3-004","R3-004","3","No firewall confirmed or firewall existence unknown","urgent",
            "The school either has no firewall or cannot confirm whether one exists. A firewall is the most fundamental perimeter security control.",
            risk_category="security", affected_entity="network perimeter")
        f.actions = [
            action("A3-004a","Determine whether a firewall is currently in place.","immediate"),
            action("A3-004b","If no firewall exists, procure and deploy one appropriate for the school's size.","next_30_days"),
        ]
        findings.append(f)

    # R3-005 Firewall details (question 3.17, conditional on 3.7=yes)
    if v37 == "yes":
        v317 = get(a,"3.17")
        if v317 in ("no","unknown",None):
            f = finding("F3-005","R3-005","3","Firewall platform, firmware, or support status not fully known","concern",
                "A firewall is in place but its details are not documented. An unpatched or out-of-support firewall may provide less protection than assumed.")
            f.actions = [
                action("A3-005a","Document the firewall platform, model, firmware version, and support/warranty expiry.","next_30_days"),
                action("A3-005b","Verify firmware is current and schedule a review cadence — at minimum twice per year.","next_30_days",schedule_category=3),
            ]
            findings.append(f)
        elif v317 == "partial":
            f = finding("F3-005","R3-005","3","Firewall details partially documented","watch",
                "Some firewall details are documented but gaps remain.")
            f.actions = [action("A3-005a","Complete firewall documentation.","next_30_days")]
            findings.append(f)

    # R3-006 AP inventory (question 3.6)
    v36 = get(a,"3.6")
    if v36 in ("no","unknown",None):
        f = finding("F3-006","R3-006","3","Wireless AP inventory absent","concern",
            "APs are not inventoried with model and firmware information. Lifecycle planning and firmware management are impaired.")
        f.actions = [action("A3-006a","Create a wireless AP inventory including location, model, serial number, and firmware version.","next_90_days")]
        findings.append(f)
    elif v36 == "partial":
        f = finding("F3-006","R3-006","3","Wireless AP inventory incomplete","watch",
            "AP inventory exists but is missing information for some devices.")
        f.actions = [action("A3-006a","Complete the wireless AP inventory.","next_90_days")]
        findings.append(f)

    # R3-007 Switch inventory
    v39 = get(a,"3.9")
    if v39 in ("no","unknown",None):
        f = finding("F3-007","R3-007","3","Switch inventory absent","concern",
            "Switches are not inventoried with model and firmware information.")
        f.actions = [action("A3-007a","Create a switch inventory including location, model, serial number, and firmware version.","next_90_days")]
        findings.append(f)
    elif v39 == "partial":
        f = finding("F3-007","R3-007","3","Switch inventory incomplete","watch","Switch inventory exists but is incomplete.")
        f.actions = [action("A3-007a","Complete the switch inventory.","next_90_days")]
        findings.append(f)

    # R3-008 Switch topology map
    v310 = get(a,"3.10")
    if v310 in ("no","unknown",None):
        f = finding("F3-008","R3-008","3","Switch topology map absent","concern",
            "There is no complete map showing how the school's switches connect. In a multi-building environment, the absence of a topology map makes fault isolation extremely difficult.")
        f.actions = [action("A3-008a","Document the switch topology — which switch connects to which, via which ports, across which buildings.","next_90_days")]
        findings.append(f)
    elif v310 == "partial":
        f = finding("F3-008","R3-008","3","Switch topology map incomplete","watch","Some switch connections are undocumented.")
        f.actions = [action("A3-008a","Complete the switch topology documentation.","next_90_days")]
        findings.append(f)

    # R3-009 Core device inventory
    v311 = get(a,"3.11")
    if v311 in ("no","unknown",None):
        f = finding("F3-009","R3-009","3","Core network device inventory absent — lifecycle and support status unclear","concern",
            "Core network devices are not inventoried with make, model, location, and support status.")
        f.actions = [action("A3-009a","Complete a core network device inventory including make, model, serial number, location, firmware version, and warranty expiry.","next_90_days")]
        findings.append(f)
    elif v311 == "partial":
        f = finding("F3-009","R3-009","3","Core network device inventory incomplete","watch","Some device information is documented but key fields are missing.")
        f.actions = [action("A3-009a","Complete the core network device inventory.","next_90_days")]
        findings.append(f)

    # R3-010 Admin access
    v312 = get(a,"3.12")
    if v312 in ("no","unknown",None):
        f = finding("F3-010","R3-010","3","Administrative access to network infrastructure not confirmed","urgent",
            "The school either has no admin access to its own network or does not know whether it does. Without admin access, every network event requires third-party involvement.",
            risk_category="continuity", affected_entity="network infrastructure", aggregation_groups=["B"])
        f.actions = [
            action("A3-010a","Determine the current state of admin access to each network device.","immediate"),
            action("A3-010b","Obtain administrative credentials for all network infrastructure and store them securely.","next_30_days"),
        ]
        findings.append(f)
    elif v312 == "partial":
        f = finding("F3-010","R3-010","3","Administrative access to network infrastructure incomplete","concern",
            "Admin access exists for some devices but not all. Devices without documented admin access cannot be managed or recovered without vendor involvement.")
        f.actions = [action("A3-010a","Identify which devices lack confirmed admin access and obtain credentials.","next_30_days")]
        findings.append(f)

    # R3-011 Internet failover
    v315 = get(a,"3.15")
    if v315 in ("no","unknown",None):
        f = finding("F3-011","R3-011","3","No internet failover or redundancy in place","concern",
            "The school has a single internet connection with no failover. If that connection fails, all internet-dependent operations stop.")
        f.actions = [action("A3-011a","Evaluate the cost and feasibility of a secondary internet connection or LTE failover device.","next_12_months")]
        findings.append(f)
    elif v315 == "manual":
        f = finding("F3-011","R3-011","3","Internet failover requires manual intervention","watch",
            "A secondary connection exists but failover is manual. During an unattended outage, full internet loss occurs until someone intervenes.")
        f.actions = [action("A3-011a","Evaluate whether automatic failover can be configured on the current hardware.","next_12_months")]
        findings.append(f)

    # R3-012 Config backup
    v318 = get(a,"3.18")
    if v318 in ("no","unknown",None):
        f = finding("F3-012","R3-012","3","Switch and wireless configurations not backed up regularly","urgent",
            "Device configurations are not backed up. If a device fails and must be replaced, the configuration must be rebuilt from scratch — extending an outage from hours to days.",
            aggregation_groups=["B"])
        f.actions = [action("A3-012a","Establish a regular configuration backup process for all managed switches and wireless devices.","next_30_days")]
        findings.append(f)
    elif v318 == "partial":
        f = finding("F3-012","R3-012","3","Switch and wireless configurations partially backed up","concern",
            "Some device configurations are backed up but others are not.")
        f.actions = [action("A3-012a","Extend configuration backup to all managed devices.","next_30_days")]
        findings.append(f)

    # R3-015 Wireless coverage
    v319 = get(a,"3.19")
    if v319 in ("no","unknown",None) or v319 == "mixed":
        sev = "concern" if v319 in ("no","unknown",None) else "watch"
        f = finding("F3-015","R3-015","3",
            "Wireless coverage inadequate or mixed" if sev == "concern" else "Wireless coverage problems in some areas",
            sev,
            "There are known areas where staff or students regularly experience poor Wi-Fi. Coverage problems directly affect instruction and administration.")
        f.actions = [action("A3-015a","Conduct a wireless coverage assessment — walk the environment and document signal strength in all instructional and administrative areas.","next_90_days",schedule_category=4)]
        findings.append(f)

    # R3-016 UPS protection
    v321 = get(a,"3.21")
    if v321 in ("no","unknown",None):
        f = finding("F3-015b","R3-015b","3","Critical network equipment lacks UPS battery backup protection","concern",
            "Network closets or server areas do not have UPS protection. A brief power event can cause uncontrolled shutdowns.")
        f.actions = [action("A3-015a","Identify which critical devices lack UPS protection and prioritize adding protection.","next_90_days")]
        findings.append(f)

    # R3-017 Known connectivity pain points (inverted: raw 'yes' = problem)
    if raw_is_yes(a,"3.26"):
        f = finding("F3-017","R3-017","3","Known connectivity issues currently affecting school operations","concern",
            "The IT person has identified active connectivity problems affecting school operations. These are confirmed issues with current operational impact.",
            notes_passthrough=get_notes(a,"3.26"))
        f.actions = [
            action("A3-017a","Document each connectivity pain point and assess root cause.","immediate"),
            action("A3-017b","Develop a remediation plan for each confirmed pain point.","next_30_days"),
        ]
        findings.append(f)

    # R3-C01 Complete network documentation absence
    if is_no_or_unknown(a,"3.2") and is_no_or_unknown(a,"3.3") and is_no_or_unknown(a,"3.11"):
        f = finding("F3-C01","R3-C01","3","No network documentation exists at any level","urgent",
            "There is no network diagram, no site/rack maps, and no device inventory. The network is completely undocumented. Any troubleshooting must begin from scratch.")
        f.actions = [
            action("A3-001a","Create a network diagram.","next_90_days"),
            action("A3-002a","Create site maps and closet/rack maps.","next_90_days"),
            action("A3-009a","Complete a core network device inventory.","next_90_days"),
        ]
        findings.append(f)

    # R3-C02 No admin access, no docs, no config backup
    if is_no_or_unknown(a,"3.12") and is_no_or_unknown(a,"3.2") and is_no_or_unknown(a,"3.18"):
        f = finding("F3-C02","R3-C02","3","No administrative access, no documentation, and no configuration backup","urgent",
            "The school has no admin access to its own network, no network diagram, and no backup of device configurations. In the event of hardware failure, the school cannot access, document, or restore its own network.",
            risk_category="continuity", affected_entity="network infrastructure", aggregation_groups=["B"])
        f.actions = [
            action("A3-010a","Obtain admin credentials for all network infrastructure.","immediate"),
            action("A3-001a","Create a network diagram.","next_90_days"),
            action("A3-012a","Establish configuration backup for all managed network devices.","next_30_days"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 4: Identity, Accounts, and Access
# ─────────────────────────────────────────────────────────────────

def evaluate_section_4(answers):
    findings = []
    a = answers
    v42 = get(a,"4.2")

    # R4-001 No centralized identity
    if v42 in ("no","unknown",None):
        f = finding("F4-001","R4-001","4","No centralized login management system identified","concern",
            "There is no centralized directory or login management system. Without central account management, provisioning and deprovisioning become manual and error-prone.")
        f.actions = [action("A4-001a","Evaluate whether a cloud-based identity platform or on-premises directory is appropriate for the school's environment.","next_12_months")]
        findings.append(f)

    # R4-002 Onboarding
    v43 = get(a,"4.3")
    if v43 in ("no","unknown",None):
        f = finding("F4-002","R4-002","4","Staff account onboarding process not documented","concern",
            "There is no documented process for onboarding new staff accounts. New staff may receive inconsistent or excessive access.")
        f.actions = [action("A4-002a","Document the staff account onboarding process as a checklist.","next_90_days")]
        findings.append(f)
    elif v43 == "informal":
        f = finding("F4-002","R4-002","4","Staff account onboarding process informal","watch",
            "Staff onboarding happens informally. This works until a step is missed or the person who knows the process is unavailable.")
        f.actions = [action("A4-002a","Formalize the staff onboarding process as a documented checklist.","next_90_days")]
        findings.append(f)

    # R4-003 Offboarding
    v44 = get(a,"4.4")
    if v44 in ("no","unknown",None):
        f = finding("F4-003","R4-003","4","Staff account offboarding process absent","urgent",
            "There is no documented process for offboarding departing staff accounts. Former staff may retain access indefinitely. This is one of the most common sources of unauthorized access in school environments.",
            risk_category="security", affected_entity="account lifecycle")
        f.actions = [
            action("A4-003a","Document the staff offboarding process as a checklist — every system and account that must be deactivated.","next_30_days"),
            action("A4-003b","Review whether any former staff still have active accounts in major systems and deactivate where found.","immediate"),
        ]
        findings.append(f)
    elif v44 == "informal":
        f = finding("F4-003","R4-003","4","Staff account offboarding process informal","concern",
            "Staff offboarding happens informally. Informal processes are prone to missed steps — a forgotten account means a former employee retains access.",
            risk_category="security", affected_entity="account lifecycle")
        f.actions = [action("A4-003a","Formalize the staff offboarding process as a documented checklist.","next_30_days")]
        findings.append(f)

    # R4-004 Student account lifecycle
    v45 = get(a,"4.5")
    if v45 not in ("yes","na",None) and v45 is not None:
        if v45 in ("no","unknown"):
            f = finding("F4-004","R4-004","4","Student account lifecycle process not documented","concern",
                "There is no documented process for provisioning or deprovisioning student accounts.")
            f.actions = [action("A4-004a","Document the student account lifecycle — when accounts are created and when and how they are deactivated.","next_90_days")]
            findings.append(f)
        elif v45 == "informal":
            f = finding("F4-004","R4-004","4","Student account lifecycle handled informally","watch",
                "Student account lifecycle is handled informally. This creates risk around departing students retaining access.")
            f.actions = [action("A4-004a","Document the student account lifecycle process.","next_90_days")]
            findings.append(f)

    # R4-005 MFA on privileged accounts
    v46 = get(a,"4.6")
    if v46 in ("no","unknown",None):
        f = finding("F4-005","R4-005","4","Multi-factor authentication not enabled on privileged accounts","urgent",
            "MFA is not enabled on privileged accounts. A compromised admin credential without MFA gives an attacker immediate, unrestricted access to core systems. This is the highest-impact, lowest-cost control gap in this section.",
            risk_category="security", affected_entity="privileged accounts", aggregation_groups=["E"])
        f.actions = [
            action("A4-005a","Enable MFA on all administrative and privileged accounts immediately.","immediate"),
            action("A4-005b","Audit all privileged accounts and confirm MFA status for each.","next_30_days"),
        ]
        findings.append(f)
    elif v46 in ("some","partial"):
        f = finding("F4-005","R4-005","4","MFA not enabled on all privileged accounts","concern",
            "MFA is enabled on some privileged accounts but not all. Any privileged account without MFA represents a full compromise risk.",
            risk_category="security", affected_entity="privileged accounts", aggregation_groups=["E"])
        f.actions = [
            action("A4-005a","Enable MFA on all remaining privileged accounts.","next_30_days"),
            action("A4-005b","Audit all privileged accounts and confirm MFA status.","next_30_days"),
        ]
        findings.append(f)

    # R4-006 Admin list not reviewed
    v47 = get(a,"4.7")
    if v42 not in ("no",None) and v47 in ("no","unknown",None):
        f = finding("F4-006","R4-006","4","Global admin and privileged role list not current or not reviewed","urgent",
            "There is no known list of who holds global admin or equivalent privileged roles. Without knowing who has the highest-level access, it is impossible to manage, audit, or revoke it.",
            risk_category="security", affected_entity="privileged role governance", aggregation_groups=["E"])
        f.actions = [
            action("A4-006a","Pull a current list of all global admins and privileged role holders and review for accuracy.","immediate"),
            action("A4-006b","Remove or downgrade any accounts that no longer require privileged access.","next_30_days"),
            action("A4-006c","Establish a quarterly privileged role review as a recurring task.","next_90_days"),
        ]
        findings.append(f)
    elif v42 not in ("no",None) and v47 == "outdated":
        f = finding("F4-006","R4-006","4","Privileged role list exists but is outdated","concern",
            "A list of privileged roles exists but is outdated. It may include former staff or excess permissions.",
            aggregation_groups=["E"])
        f.actions = [
            action("A4-006a","Review the current privileged role list and verify accuracy.","next_30_days"),
            action("A4-006c","Establish a quarterly privileged role review.","next_90_days"),
        ]
        findings.append(f)

    # R4-007 Shared accounts
    v48 = get(a,"4.8")
    if v48 == "no":
        f = finding("F4-007","R4-007","4","Shared accounts not minimized or justified","concern",
            "Shared accounts are in active use and have not been reviewed or justified. Shared accounts make auditing impossible and complicate offboarding.")
        f.actions = [
            action("A4-007a","Inventory all shared accounts currently in use and document their purpose and who has access.","next_90_days"),
            action("A4-007b","Eliminate shared accounts where individual accounts are feasible; formally justify any that must remain.","next_90_days"),
        ]
        findings.append(f)
    elif v48 in ("partial","some","unknown") and v48 is not None:
        f = finding("F4-007","R4-007","4","Shared accounts exist but are not formally reviewed","watch",
            "Some shared accounts exist. The exposure is unclear because these accounts have not been formally reviewed.")
        f.actions = [action("A4-007a","Inventory all shared accounts and document their purpose.","next_90_days")]
        findings.append(f)

    # R4-008 Password reset procedures
    v49 = get(a,"4.9")
    if v49 in ("no","unknown",None):
        f = finding("F4-008","R4-008","4","Password reset and recovery procedures not documented","concern",
            "There are no documented procedures for password resets or account recovery. When a staff member is locked out, the IT person must improvise.")
        f.actions = [action("A4-008a","Document password reset and account recovery procedures for each major platform.","next_90_days")]
        findings.append(f)
    elif v49 == "partial":
        f = finding("F4-008","R4-008","4","Password reset procedures partially documented","watch",
            "Password reset procedures exist for some platforms but not all.")
        f.actions = [action("A4-008a","Complete password reset documentation for all major platforms.","next_90_days")]
        findings.append(f)

    # R4-C01 Privileged access completely uncontrolled
    if v46 in ("no","unknown",None) and v47 in ("no","unknown",None) and v48 == "no":
        f = finding("F4-C01","R4-C01","4","Privileged access is uncontrolled — no MFA, no admin inventory, shared accounts unreviewed","urgent",
            "The school has no MFA on privileged accounts, no current knowledge of who holds admin access, and unreviewed shared accounts. Privileged access to core systems is effectively uncontrolled.",
            risk_category="security", affected_entity="privileged account control", aggregation_groups=["E"])
        f.actions = [
            action("A4-005a","Enable MFA on all privileged accounts immediately.","immediate"),
            action("A4-006a","Pull a current list of all global admins and review for accuracy.","immediate"),
            action("A4-007a","Inventory all shared accounts.","next_90_days"),
        ]
        findings.append(f)

    # R4-C02 Account lifecycle unmanaged at both ends
    if v43 in ("no","unknown",None) and v44 in ("no","unknown",None):
        f = finding("F4-C02","R4-C02","4","Staff account lifecycle unmanaged — no onboarding or offboarding process","urgent",
            "There is no documented process for either creating or removing staff accounts. New staff may receive inconsistent access; departing staff may retain access indefinitely.",
            risk_category="security", affected_entity="account lifecycle")
        f.actions = [
            action("A4-002a","Document the staff account onboarding process as a checklist.","next_90_days"),
            action("A4-003a","Document the staff offboarding process as a checklist.","next_30_days"),
            action("A4-003b","Review whether any former staff still have active accounts and deactivate where found.","immediate"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 5: Endpoints, Printing, and Classroom Technology
# ─────────────────────────────────────────────────────────────────

def evaluate_section_5(answers):
    findings = []
    a = answers
    is_1to1 = get(a,"5.3") in ("yes","some","partial")

    v51 = get(a,"5.1")
    if v51 in ("no","unknown",None):
        f = finding("F5-001","R5-001","5","No current managed device inventory exists","concern",
            "There is no current inventory of managed devices. Without a baseline record, lifecycle planning, support, and security are all impaired.")
        f.actions = [action("A5-001a","Establish a managed device inventory covering all school-owned devices — device type, model, serial number, assigned user, and purchase date.","next_90_days",schedule_category=2)]
        findings.append(f)
    elif v51 == "partial":
        f = finding("F5-001","R5-001","5","Device inventory exists but is incomplete","watch",
            "A device inventory exists but is incomplete. Missing devices or fields reduce its usefulness.")
        f.actions = [action("A5-001a","Complete the device inventory — add missing devices and fill in missing key fields.","next_90_days")]
        findings.append(f)

    v52 = get(a,"5.2")
    if v51 in ("yes","partial") and v52 in ("no","unknown",None,"partial"):
        sev = "concern" if v52 in ("no","unknown",None) else "watch"
        f = finding("F5-002","R5-002","5","Device inventory missing key lifecycle fields",sev,
            "The device inventory does not include all fields needed for lifecycle planning and support.")
        f.actions = [action("A5-002a","Enrich the existing inventory to include purchase date or age, serial number, and assigned user or location.","next_90_days")]
        findings.append(f)

    v55 = get(a,"5.5")
    if v55 in ("no","unknown",None):
        sev = "urgent" if is_1to1 else "concern"
        desc = "School-owned devices are not managed through MDM. Without MDM, the school cannot enforce policies, push software, lock or wipe lost devices, or efficiently provision and decommission."
        if is_1to1: desc += " In a 1:1 student device environment, this gap affects every student device simultaneously."
        f = finding("F5-003","R5-003","5","School-owned devices not managed through MDM",sev,desc)
        f.actions = [
            action("A5-003a","Evaluate and select an MDM or endpoint management platform.","next_90_days"),
            action("A5-003b","Enroll all school-owned devices into the MDM platform.","next_12_months"),
        ]
        findings.append(f)
    elif v55 in ("some","partial"):
        f = finding("F5-003","R5-003","5","Device management through MDM incomplete","watch",
            "Some devices are managed through MDM but coverage is incomplete.")
        f.actions = [action("A5-003b","Extend MDM enrollment to all school-owned devices.","next_12_months")]
        findings.append(f)

    v56 = get(a,"5.6")
    v58 = get(a,"5.8")
    if v56 in ("no","unknown",None) and v58 in ("no","unknown",None,"partial"):
        f = finding("F5-004","R5-004","5","Staff device provisioning not standardized or documented","concern",
            "There is no documented standard for provisioning staff devices and devices cannot be set up quickly or consistently.")
        f.actions = [action("A5-004a","Document a staff device provisioning standard — required software, security settings, naming convention, and enrollment steps.","next_90_days")]
        findings.append(f)
    elif v56 in ("partial","informal") or v58 == "partial":
        f = finding("F5-004","R5-004","5","Staff device provisioning partially standardized","watch",
            "Staff device provisioning is partially standardized but not fully documented.")
        f.actions = [action("A5-004a","Document a complete staff device provisioning standard.","next_90_days")]
        findings.append(f)

    v59 = get(a,"5.9")
    if v59 in ("no","unknown",None):
        f = finding("F5-005","R5-005","5","No defined device refresh cycle","concern",
            "There is no defined refresh cycle for any major device category. Without a planned replacement schedule, devices are replaced reactively when they fail.",
            aggregation_groups=["F"])
        f.actions = [
            action("A5-005a","Define a target refresh cycle for each major device category.","next_12_months"),
            action("A5-005b","Use device inventory age data to estimate when the next major refresh wave will occur and begin budgeting.","next_12_months"),
        ]
        findings.append(f)
    elif v59 == "informal":
        f = finding("F5-005","R5-005","5","Device refresh cycle defined but not followed","watch",
            "A refresh cycle is defined but not consistently followed.",aggregation_groups=["F"])
        f.actions = [action("A5-005a","Formalize and document the refresh cycle and incorporate it into budget planning.","next_12_months")]
        findings.append(f)

    v510 = get(a,"5.10")
    if v510 == "many":
        desc = "Many devices are running unsupported OS versions or are past manufacturer support end-of-life. Unsupported devices receive no security patches."
        if is_1to1: desc += " In a 1:1 environment, this affects instruction and student safety tools directly."
        f = finding("F5-006","R5-006","5","Devices beyond supported OS or manufacturer support in active use","urgent",desc,
            risk_category="lifecycle", affected_entity="managed device fleet", aggregation_groups=["F"])
        f.actions = [
            action("A5-006a","Identify all devices running unsupported OS versions or past manufacturer support.","next_30_days"),
            action("A5-006b","Develop a prioritized replacement plan.","next_90_days"),
        ]
        findings.append(f)
    elif v510 in ("some","unknown") and v510 is not None:
        desc = "Some devices are running unsupported OS versions." if v510 == "some" else "The age profile of the device fleet is unknown."
        f = finding("F5-006","R5-006","5","Devices beyond supported OS or manufacturer support in active use","concern",desc,
            risk_category="lifecycle", affected_entity="managed device fleet", aggregation_groups=["F"])
        f.actions = [
            action("A5-006a","Identify all devices running unsupported OS versions or past manufacturer support.","next_30_days"),
            action("A5-006b","Develop a prioritized replacement plan.","next_90_days"),
        ]
        findings.append(f)

    if v51 in ("no","unknown",None) and v55 in ("no","unknown",None):
        f = finding("F5-C01","R5-C01","5","No device inventory and no endpoint management","urgent",
            "The school has no inventory of its devices and no MDM. It is impossible to know what devices exist, who has them, or what state they are in.")
        f.actions = [
            action("A5-001a","Establish a device inventory.","next_90_days"),
            action("A5-003a","Evaluate and select an MDM platform.","next_90_days"),
        ]
        findings.append(f)

    if v510 == "many" and is_1to1 and v59 in ("no","unknown",None):
        f = finding("F5-C02","R5-C02","5","Many unsupported devices in 1:1 program with no refresh plan","urgent",
            "A significant portion of the student device fleet is running unsupported operating systems with no defined refresh plan.",
            aggregation_groups=["F"])
        f.actions = [
            action("A5-006a","Identify all unsupported devices immediately.","next_30_days"),
            action("A5-005a","Define a device refresh cycle and incorporate it into the budget.","next_12_months"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 6: Core Systems, Servers, Vendors, and Contracts
# ─────────────────────────────────────────────────────────────────

def evaluate_section_6(answers):
    findings = []
    a = answers
    has_servers = get_count(a,"6.13") > 0

    v63 = get(a,"6.3")
    if v63 in ("no","unknown",None):
        f = finding("F6-001","R6-001","6","No list of core systems used by the school","concern",
            "There is no register of the major platforms the school depends on. Without a systems list, renewal planning, vendor management, and incident response lack a starting point.",
            aggregation_groups=["A","C"])
        f.actions = [action("A6-001a","Create a core systems register listing each major platform — include SIS, LMS, email, identity platform, and any other operationally critical tools.","next_30_days")]
        findings.append(f)
    elif v63 == "partial":
        f = finding("F6-002","R6-002","6","Core systems list exists but is incomplete","watch",
            "A systems list exists but is not complete. Missing systems create blind spots in renewal planning.")
        f.actions = [action("A6-001a","Complete the core systems register.","next_30_days")]
        findings.append(f)

    v64 = get(a,"6.4")
    if v63 in ("yes","partial") and v64 in ("no","unknown",None,"partial"):
        sev = "concern" if v64 in ("no","unknown",None) else "watch"
        f = finding("F6-003","R6-003","6","Core systems list missing key operational fields",sev,
            "The systems list does not include all fields needed for operational use. Missing renewal dates, owners, or admin access methods reduce its value.")
        f.actions = [action("A6-003a","Enrich the systems list to include purpose, owner, vendor, renewal date, and admin access method for each system.","next_90_days")]
        findings.append(f)

    v67 = get(a,"6.7")
    if v67 in ("no","unknown",None,"partial"):
        sev = "concern" if v67 in ("no","unknown",None) else "watch"
        f = finding("F6-004","R6-004","6","Student data system compliance review status not known",sev,
            "For major systems handling student data, FERPA or COPPA review status is not known for most or all platforms.",
            aggregation_groups=["D"])
        f.actions = [action("A6-004a","Conduct a FERPA/COPPA compliance review for all systems that handle student data.","next_12_months")]
        findings.append(f)

    v68 = get(a,"6.8")
    if v68 in ("no","unknown",None):
        f = finding("F6-005","R6-005","6","Contract renewal dates not tracked","concern",
            "There is no system for tracking contract and subscription renewal dates. Contracts that auto-renew waste budget; those that lapse disrupt operations.",
            aggregation_groups=["C"])
        f.actions = [action("A6-005a","Create a renewal calendar listing every major contract and subscription with its renewal date and a 60-day reminder.","next_30_days")]
        findings.append(f)
    elif v68 == "partial":
        f = finding("F6-005","R6-005","6","Contract renewal tracking incomplete","watch",
            "Some renewal dates are tracked but others are not.",aggregation_groups=["C"])
        f.actions = [action("A6-005a","Complete the renewal tracker — add all missing contracts and subscriptions.","next_30_days")]
        findings.append(f)

    v69 = get(a,"6.9")
    if v69 in ("no","unknown",None):
        f = finding("F6-006","R6-006","6","Vendor support escalation paths not documented","concern",
            "For critical vendors, there is no documented record of who to call and how to escalate when normal support fails.",
            aggregation_groups=["C"])
        f.actions = [action("A6-006a","Create a vendor escalation sheet listing each critical vendor, support contact, account number, and escalation path.","next_30_days")]
        findings.append(f)
    elif v69 == "partial":
        f = finding("F6-006","R6-006","6","Vendor escalation paths documented for some vendors only","watch",
            "Escalation paths are documented for some vendors but not all critical ones.")
        f.actions = [action("A6-006a","Complete vendor escalation documentation for all critical vendors.","next_30_days")]
        findings.append(f)

    # R6-007 Single-vendor/person dependencies (inverted)
    if raw_is_yes(a,"6.10"):
        f = finding("F6-007","R6-007","6","Single-vendor or single-person dependencies identified","concern",
            "The IT person has identified specific vendor or person dependencies that create operational risk.",
            notes_passthrough=get_notes(a,"6.10"), aggregation_groups=["B","C"])
        f.actions = [action("A6-007a","For each identified dependency, develop a mitigation plan — obtain credentials, establish a backup vendor relationship, or document a workaround.","next_90_days")]
        findings.append(f)

    if has_servers:
        v614 = get(a,"6.14")
        if v614 in ("no","unknown",None):
            f = finding("F6-009","R6-009","6","Server inventory absent","urgent",
                "Servers are in use but there is no inventory. An undocumented server environment is effectively unsupportable by anyone other than the person who built it.",
                aggregation_groups=["B"])
            f.actions = [action("A6-009a","Create a server inventory including model, serial number, role, location, OS version, and support status.","next_30_days")]
            findings.append(f)
        elif v614 == "partial":
            f = finding("F6-009","R6-009","6","Server inventory incomplete","concern","A partial server inventory exists but key fields are missing.")
            f.actions = [action("A6-009a","Complete the server inventory.","next_30_days")]
            findings.append(f)

        v616 = get(a,"6.16")
        if v616 in ("no","unknown",None):
            f = finding("F6-010","R6-010","6","Server administrative access not documented or not available","urgent",
                "Admin access methods for servers are not documented. If the primary IT person is unavailable, no one can access the servers.",
                risk_category="continuity", affected_entity="server infrastructure", aggregation_groups=["B"])
            f.actions = [
                action("A6-010a","Document the admin access method for every server.","immediate"),
                action("A6-010b","Ensure at least one other authorized person can access each server.","next_30_days"),
            ]
            findings.append(f)
        elif v616 == "partial":
            f = finding("F6-010","R6-010","6","Server admin access partially documented","concern","Some servers can be accessed without the primary IT person but gaps remain.",aggregation_groups=["B"])
            f.actions = [action("A6-010a","Complete server admin access documentation.","immediate")]
            findings.append(f)

        v617 = get(a,"6.17")
        if v617 in ("no","unknown",None):
            f = finding("F6-011","R6-011","6","No defined server patching or update cycle","concern",
                "There is no defined cycle for patching servers. Unpatched servers accumulate vulnerabilities.")
            f.actions = [action("A6-011a","Define and document a server patching cycle — at minimum monthly for security patches.","next_30_days",schedule_category=3)]
            findings.append(f)
        elif v617 == "informal":
            f = finding("F6-011","R6-011","6","Server patching informal","watch","Server patching happens informally — typically when the IT person remembers or notices an issue.")
            f.actions = [action("A6-011a","Formalize the server patching cycle.","next_30_days")]
            findings.append(f)

        v618 = get(a,"6.18")
        if v618 in ("no","unknown",None):
            f = finding("F6-012","R6-012","6","Server warranty and support coverage not tracked","concern",
                "A server that fails outside of warranty with no support contract may require full replacement at unplanned cost.",aggregation_groups=["F"])
            f.actions = [action("A6-012a","Document the warranty and support status for every server.","next_30_days")]
            findings.append(f)

        v619 = get(a,"6.19")
        if v619 in ("no","unknown",None):
            f = finding("F6-013","R6-013","6","No hardware refresh or lifecycle plan for servers","concern",
                "There is no defined lifecycle or refresh plan for server hardware.",aggregation_groups=["F"])
            f.actions = [
                action("A6-013a","Define a server lifecycle target — typically 5–7 years — and map current servers against that target.","next_90_days"),
                action("A6-013b","Incorporate server refresh into the IT budget planning cycle.","next_12_months"),
            ]
            findings.append(f)

        v615 = get(a,"6.15")
        if v614 in ("no","unknown",None) and v615 in ("no","unknown",None) and v616 in ("no","unknown",None):
            f = finding("F6-C02","R6-C02","6","Server environment completely undocumented","urgent",
                "The school has servers in use but no inventory, no documentation of what each server does, and no documented admin access methods.",
                risk_category="continuity", affected_entity="server infrastructure", aggregation_groups=["B","F"])
            f.actions = [
                action("A6-009a","Create a complete server inventory.","next_30_days"),
                action("A6-010a","Document admin access for every server.","immediate"),
            ]
            findings.append(f)

    if v63 in ("no","unknown",None) and v68 in ("no","unknown",None) and v69 in ("no","unknown",None):
        f = finding("F6-C01","R6-C01","6","No vendor or systems visibility at any level","urgent",
            "The school has no list of its core systems, no tracking of contract renewal dates, and no documented vendor escalation paths.",
            risk_category="visibility", affected_entity="all systems and vendors", aggregation_groups=["A","C"])
        f.actions = [
            action("A6-001a","Create a core systems register.","next_30_days"),
            action("A6-005a","Create a renewal calendar.","next_30_days"),
            action("A6-006a","Create a vendor escalation sheet.","next_30_days"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 7: Data Protection, Backup, and Recovery
# ─────────────────────────────────────────────────────────────────

def evaluate_section_7(answers):
    findings = []
    a = answers
    has_servers = get_count(a,"6.13") > 0

    # Gate: 7.1 = No or Unknown → R7-C01 fires directly, no other rules
    v71 = get(a,"7.1")
    if v71 in ("no","unknown",None):
        f = finding("F7-C01","R7-C01","7","No verifiable data protection in place","urgent",
            "There is no confirmed backup coverage. A single incident could result in permanent, unrecoverable data loss.")
        f.actions = [
            action("A7-001a","Identify what critical data and systems need to be backed up — SIS, email, network configurations, shared files.","immediate"),
            action("A7-001b","Select and configure a backup solution for all critical systems.","next_30_days"),
            action("A7-007a","Establish a weekly backup review cadence.","next_30_days"),
            action("A7-008a","Schedule and perform a documented restore test for at least one critical system.","next_30_days"),
        ]
        findings.append(f)
        return findings  # gate fired — no other rules evaluate

    # R7-002 Backup scope
    v73 = get(a,"7.3")
    if v73 in ("no","unknown",None):
        f = finding("F7-002","R7-002","7","Backup scope not documented","concern",
            "There is no documented list of what is backed up and what is not. A backup scope document prevents surprises during recovery.")
        f.actions = [action("A7-002a","Document the complete backup scope — list every system and data set, and explicitly note what is NOT protected.","next_30_days")]
        findings.append(f)
    elif v73 == "partial":
        f = finding("F7-002","R7-002","7","Backup scope partially documented","watch","Undocumented systems may not be protected.")
        f.actions = [action("A7-002a","Complete the backup scope documentation.","next_30_days")]
        findings.append(f)

    # R7-004 Server backup
    if has_servers:
        v74 = get(a,"7.4")
        if v74 in ("no","unknown",None):
            f = finding("F7-004","R7-004","7","Server backups absent or not confirmed","urgent",
                "Servers are in use but are not confirmed to be backed up. An unprotected server represents complete data loss risk for everything it hosts.")
            f.actions = [action("A7-004a","Confirm or establish backup coverage for all servers.","immediate")]
            findings.append(f)
        elif v74 == "partial":
            f = finding("F7-004","R7-004","7","Server backup coverage incomplete","urgent",
                "Some servers are backed up but others are not. Any unprotected server represents complete data loss risk.")
            f.actions = [action("A7-004a","Extend backup coverage to all servers.","immediate")]
            findings.append(f)

    # R7-005 Staff device backup
    if is_no_or_unknown(a,"7.5") and get(a,"4.10") not in ("yes",):
        f = finding("F7-005","R7-005","7","Staff device data not backed up","concern",
            "Staff devices are not confirmed to be backed up and cloud file sync is not confirmed as a substitute. Local files are at risk of permanent loss if a device fails or is stolen.")
        f.actions = [action("A7-005a","Confirm whether staff devices rely on cloud sync for data protection, or establish device backup coverage for locally-stored data.","next_30_days")]
        findings.append(f)

    # R7-006 Cloud data backup
    if is_no_or_unknown(a,"7.6"):
        f = finding("F7-006","R7-006","7","Critical cloud data not backed up","concern",
            "Critical cloud or online school data is not confirmed to be backed up.",
            plain_language_note="Cloud platforms provide availability but not always backup. A deleted file or ransomware event can propagate through a synced environment. Storing data in Google Drive or Microsoft 365 is not the same as having it backed up.")
        f.actions = [action("A7-006a","Evaluate and implement a cloud backup solution for critical cloud data.","next_90_days")]
        findings.append(f)

    # R7-007 Backup monitoring
    v77 = get(a,"7.7")
    if v77 in ("no","unknown",None,"irregularly"):
        sev = "urgent" if (v77 in ("no","unknown",None) and is_no_or_unknown(a,"7.8")) else "concern"
        f = finding("F7-007","R7-007","7","Backup success not regularly monitored",sev,
            "Backups may be running but are not reviewed for success. Silent backup failures are a common cause of data loss discovered only at the moment recovery is needed.")
        f.actions = [
            action("A7-007a","Establish a weekly backup review cadence.","next_30_days"),
            action("A7-007b","Configure alerting so backup failures notify the IT person automatically.","next_30_days"),
        ]
        findings.append(f)

    # R7-007b Backup storage location (new question)
    v77b = get(a,"7.7b")
    if v77b == "onsite":
        f = finding("F7-007b","R7-007b","7","Backups stored onsite only — no offsite or cloud copy confirmed","concern",
            "All backup copies are stored at the school. A single physical event — fire, flood, theft — can destroy both the primary data and the only backup simultaneously.")
        f.actions = [action("A7-007b-a","Establish offsite or cloud backup storage for all critical systems.","next_30_days")]
        findings.append(f)
    elif v77b == "inconsistent":
        f = finding("F7-007b","R7-007b","7","Backup storage location inconsistent","watch",
            "Some backups have offsite copies and some do not. The coverage of offsite protection is unclear.")
        f.actions = [action("A7-007b-a","Standardize backup storage to include offsite or cloud copies for all critical systems.","next_30_days")]
        findings.append(f)

    # R7-008 Restore test
    v78 = get(a,"7.8")
    if v78 in ("no","unknown",None,"old"):
        sev = "urgent" if (v78 in ("no","unknown",None) and v71 == "maybe") or \
                         (v78 == "old" and get(a,"7.9") in ("less than annually","never","unknown",None)) \
              else "concern"
        f = finding("F7-008","R7-008","7","Backup restore not tested or not tested recently",sev,
            "A backup that has never been tested — or not tested within a timeframe proportional to the backup's useful recovery window — cannot be relied upon.")
        f.actions = [
            action("A7-008a","Schedule and perform a documented restore test for at least one critical system.","next_30_days",schedule_category=3),
            action("A7-008b","Establish a recurring restore test schedule aligned with the backup retention window.","next_90_days"),
        ]
        findings.append(f)

    # R7-010 Recovery priority
    if get(a,"7.10") in ("no","unknown",None,"partial"):
        f = finding("F7-010","R7-010","7","No defined recovery priority for critical systems","concern",
            "When multiple systems are affected in an incident, the order of recovery matters. Without a defined priority, decisions are made under pressure without a plan.")
        f.actions = [action("A7-010a","Define and document a recovery priority order for critical systems.","next_90_days")]
        findings.append(f)

    # R7-011 Incident response reference
    v711 = get(a,"7.11")
    if v711 in ("no","unknown",None,"partial"):
        sev = "urgent" if is_no_or_unknown(a,"7.12") else "concern"
        f = finding("F7-011","R7-011","7","No written incident or disaster response reference",sev,
            "There is no documented reference for how to respond to a significant IT incident or outage. In a crisis, whoever is covering needs a written starting point. A one-page reference is sufficient.")
        f.actions = [action("A7-011a","Create a basic IT incident response reference covering: who to call, what systems to check first, how to access backup and recovery tools, and how to communicate during an outage.","next_90_days")]
        findings.append(f)

    # R7-012 Emergency credential access
    if get(a,"7.12") in ("no","unknown",None,"partial"):
        f = finding("F7-012","R7-012","7","Emergency access to critical credentials not confirmed","urgent",
            "Critical admin credentials and recovery materials are not confirmed to be accessible in an emergency. If the primary IT person is unavailable during an incident, recovery may be impossible.",
            risk_category="continuity", affected_entity="emergency access and credential control",
            aggregation_groups=["B"])
        f.actions = [
            action("A7-012a","Identify all critical admin credentials and recovery materials.","immediate"),
            action("A7-012b","Store credentials securely in a documented, accessible location.","next_30_days"),
            action("A7-012c","Verify that at least one other authorized person knows how to access these materials.","next_30_days"),
        ]
        findings.append(f)

    # R7-013 Recovery window not known
    v713 = get(a,"7.13")
    if v713 in ("unknown",None):
        f = finding("F7-013","R7-013","7","Backup useful recovery window not known","concern",
            "The IT person does not know how far back a backup restore would actually be useful. Without this, it is impossible to evaluate whether backup frequency and restore test cadence are appropriate.")
        f.actions = [
            action("A7-013a","Review the backup platform's retention policy and determine the practical useful recovery window.","next_30_days"),
            action("A7-013b","Document the retention window and use it to set restore test frequency.","next_30_days"),
        ]
        findings.append(f)

    # R7-014 Restore tests not aligned with window
    if v713 not in ("unknown",None) and v78 not in ("no",None) and is_no_or_unknown(a,"7.14"):
        f = finding("F7-014","R7-014","7","Restore test frequency not aligned with backup retention window","concern",
            "The school knows how far back a restore is useful but is not testing frequently enough to detect failures within that window.")
        f.actions = [action("A7-014a","Establish a restore test schedule aligned with the useful recovery window — at least one test per window period.","next_90_days")]
        findings.append(f)

    # R7-C02 Backups running but recovery unverified
    if (v71 in ("yes","maybe") and
            v77 in ("no","unknown",None,"irregularly") and
            v78 in ("no","unknown",None,"old")):
        sev = "urgent" if v71 == "maybe" else "concern"
        f = finding("F7-C02","R7-C02","7","Backups running but recovery confidence is low",sev,
            "Backups appear to be in place but are not monitored reliably and have not been tested recently. The school may believe it is protected when it is not.")
        f.actions = [action("A7-C02a","Perform an immediate backup review — confirm jobs are running, review success logs, and schedule a restore test.","next_30_days")]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 8: Security Operations, Filtering, and Safeguards
# ─────────────────────────────────────────────────────────────────

def evaluate_section_8(answers):
    findings = []
    a = answers
    is_1to1 = get(a,"5.3") in ("yes","some","partial")
    v81 = get(a,"8.1")
    ep_deployed = v81 in ("yes","some","partial")

    # R8-001 Endpoint protection (gate question 8.1)
    if v81 in ("no","unknown",None):
        desc = "Endpoint protection is not deployed on managed devices, or deployment status is unknown. Unprotected endpoints are a primary attack surface for malware and ransomware."
        if is_1to1: desc += " In a 1:1 student device environment, this is both a security and a safeguarding concern."
        f = finding("F8-001","R8-001","8","Endpoint protection not deployed across managed devices","urgent",desc,
            risk_category="security", affected_entity="managed device fleet", aggregation_groups=["E"])
        f.actions = [
            action("A8-001a","Identify which devices do not have endpoint protection and deploy coverage immediately.","immediate"),
            action("A8-001b","Verify endpoint protection is active and reporting on all managed devices.","next_30_days"),
        ]
        findings.append(f)
    elif v81 in ("some","partial"):
        f = finding("F8-001","R8-001","8","Endpoint protection deployed on some but not all managed devices","concern",
            "Endpoint protection is deployed on some devices but not all. Unprotected devices remain exposed regardless of how well other devices are protected.")
        f.actions = [action("A8-001a","Extend endpoint protection to all managed devices.","next_30_days")]
        findings.append(f)

    # R8-001b EP alerts not monitored (only if EP is deployed)
    if ep_deployed:
        v82b = get(a,"8.2b")
        if v82b in ("no","no_notify","unknown",None):
            desc = ("Endpoint protection is deployed but no one is consistently reviewing its alerts. Unmonitored alerts are functionally equivalent to no detection."
                    if v82b != "no_notify" else
                    "Endpoint protection is deployed but does not provide centralized notifications, making alert review impractical.")
            f = finding("F8-001b","R8-001b","8","Endpoint protection alerts not consistently monitored","concern",desc)
            f.actions = [
                action("A8-001b-a","Establish a weekly alert review cadence for endpoint protection alerts and trend reports.","next_30_days"),
                action("A8-001b-b","If the current platform does not support centralized alerting, evaluate platforms that do.","next_90_days"),
            ]
            findings.append(f)
        elif v82b == "irregularly":
            f = finding("F8-001b","R8-001b","8","Endpoint protection alerts reviewed irregularly","watch",
                "Alerts are reviewed occasionally. Threats may persist between reviews.")
            f.actions = [action("A8-001b-a","Establish a regular weekly alert review cadence.","next_30_days")]
            findings.append(f)

    # R8-002 Patching
    v83 = get(a,"8.3")
    if v83 in ("no","unknown",None):
        f = finding("F8-002","R8-002","8","Endpoint and server patching not managed on a defined schedule","concern",
            "There is no defined schedule for patching endpoints and servers. Unpatched systems accumulate vulnerabilities.")
        f.actions = [
            action("A8-002a","Define and document a patching schedule — at minimum monthly security patches, critical patches within 72 hours of release.","next_30_days"),
            action("A8-002b","Where MDM is in place, configure automated patch deployment.","next_90_days"),
        ]
        findings.append(f)
    elif v83 == "informal":
        f = finding("F8-002","R8-002","8","Endpoint and server patching informal","watch",
            "Patching happens when the IT person is aware of a specific issue rather than on a schedule.")
        f.actions = [action("A8-002a","Define and document a patching schedule.","next_30_days")]
        findings.append(f)

    # R8-003 Firmware review
    v84 = get(a,"8.4")
    if v84 in ("no","unknown",None):
        f = finding("F8-003","R8-003","8","Network and security device firmware not regularly reviewed","concern",
            "Critical network and security devices are not reviewed for firmware currency. Outdated firmware on a firewall or switch is functionally equivalent to leaving a known vulnerability unpatched.")
        f.actions = [
            action("A8-003a","Review current firmware on all critical network and security devices.","next_30_days"),
            action("A8-003b","Establish a twice-yearly firmware review cadence.","next_30_days",schedule_category=3),
        ]
        findings.append(f)
    elif v84 == "irregularly":
        f = finding("F8-003","R8-003","8","Network and security device firmware reviewed irregularly","watch",
            "Firmware is reviewed irregularly. Gaps between reviews represent periods where known vulnerabilities may be present.")
        f.actions = [action("A8-003b","Establish a twice-yearly firmware review cadence.","next_30_days")]
        findings.append(f)

    # R8-004 Web filter
    v85 = get(a,"8.5")
    if v85 in ("no","unknown",None,"limited"):
        sev = "urgent" if (v85 == "no" and is_1to1) else "concern"
        desc = ("There is no web or content filter protecting student internet access. Schools have legal and ethical obligations to protect students from harmful online content. The absence of filtering may conflict with E-rate CIPA obligations."
                if sev == "urgent" else
                "Web filtering is absent, unknown, or only partially implemented. Gaps leave users — particularly students — exposed to harmful content and phishing sites.")
        f = finding("F8-004","R8-004","8","Web or content filtering absent or inadequate",sev,desc,
            risk_category="security", affected_entity="student and staff internet access", aggregation_groups=["E"])
        f.actions = [
            action("A8-004a","Implement a web filter covering all student internet access.","immediate" if sev=="urgent" else "next_30_days"),
            action("A8-004b","Extend filtering to staff devices and document the filtering scope.","next_30_days"),
        ]
        findings.append(f)

    # R8-005 Safety controls not documented
    if get(a,"8.7") in ("no","unknown",None,"partial"):
        f = finding("F8-005","R8-005","8","Student safety and filtering controls not documented","watch",
            "Controls are in place but not documented well enough to understand coverage and gaps.")
        f.actions = [action("A8-005a","Document the current filtering and student safety control configuration — what is filtered, who is covered, and what the exception process is.","next_90_days")]
        findings.append(f)

    # R8-006 Incident response process
    v88 = get(a,"8.8")
    if v88 in ("no","unknown",None):
        f = finding("F8-006","R8-006","8","No documented process for responding to security incidents","concern",
            "There is no documented process for responding to malware, suspicious activity, or account compromise. When a security event occurs, the IT person must improvise under pressure.")
        f.actions = [action("A8-006a","Create a basic security incident response reference — how to identify a compromise, who to notify, how to contain the affected system, and when to involve external help.","next_90_days")]
        findings.append(f)
    elif v88 == "partial":
        f = finding("F8-006","R8-006","8","Incident response process partially documented","watch","Key scenarios or steps may be missing.")
        f.actions = [action("A8-006a","Complete the incident response reference.","next_90_days")]
        findings.append(f)

    # R8-007 Logs not reviewed
    if get(a,"8.9") in ("no","unknown",None,"irregularly","sometimes"):
        f = finding("F8-007","R8-007","8","System logs and alerts not regularly reviewed","watch",
            "Logs from key systems are not reviewed regularly. Security events go unnoticed until they become significant incidents.")
        f.actions = [action("A8-007a","Establish a monthly review of authentication logs, failed logins, and security alerts.","next_90_days")]
        findings.append(f)

    # R8-008 Known security concerns (inverted: raw 'yes' = problem)
    if raw_is_yes(a,"8.11"):
        sev = "urgent" if v81 in ("no","unknown",None) else "concern"
        f = finding("F8-008","R8-008","8","Known unresolved security concerns identified",sev,
            "The IT person has identified active, unresolved security concerns. These should be treated as immediate priorities." +
            (" With no endpoint protection deployed, these represent compounded risk." if sev=="urgent" else ""),
            notes_passthrough=get_notes(a,"8.11"),
            plain_language_note="Identifying a known problem scores better than not knowing — you cannot fix what you are not aware of.")
        f.actions = [
            action("A8-008a","Document each identified security concern with a description, estimated risk level, and a specific action and owner.","immediate"),
            action("A8-008b","Address each confirmed concern according to its severity.","next_30_days"),
        ]
        findings.append(f)

    # R8-C01 Baseline security hygiene absent
    if v81 in ("no","unknown",None) and v83 in ("no","unknown",None) and v85 in ("no","unknown",None):
        f = finding("F8-C01","R8-C01","8","Baseline security hygiene absent — no endpoint protection, no patching, no web filtering","urgent",
            "The school has no endpoint protection, no defined patching cadence, and no web filtering. Their simultaneous absence means devices, users, and students are exposed to common threats with no systematic defense.",
            risk_category="security", affected_entity="entire IT environment", aggregation_groups=["E"])
        f.actions = [
            action("A8-001a","Deploy endpoint protection on all managed devices immediately.","immediate"),
            action("A8-002a","Define a patching schedule.","next_30_days"),
            action("A8-004a","Implement web filtering for student internet access.","immediate" if is_1to1 else "next_30_days"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# SECTION 9: Documentation and Operational Readiness
# ─────────────────────────────────────────────────────────────────

def evaluate_section_9(answers):
    findings = []
    a = answers

    # R9-001 No central documentation location
    v91 = get(a,"9.1")
    if v91 in ("no","unknown",None):
        f = finding("F9-001","R9-001","9","No central location for IT documentation","concern",
            "There is no central location where IT documentation is stored. Documentation is effectively inaccessible to anyone other than the person who created it.")
        f.actions = [
            action("A9-001a","Designate a single authoritative location for all IT documentation — a wiki, shared drive folder, or IT documentation platform.","next_30_days"),
            action("A9-001b","Migrate existing documentation to the central location and establish a policy that new documentation is always created there.","next_90_days"),
        ]
        findings.append(f)
    elif v91 == "partial" or (v91 and "inconsistent" in v91):
        f = finding("F9-001","R9-001","9","Central documentation location exists but used inconsistently","watch",
            "A central location exists but is not used consistently. The value of a central location depends on consistent use.")
        f.actions = [action("A9-001a","Establish a policy that all new documentation is created in the central location and migrate scattered documentation.","next_90_days")]
        findings.append(f)

    # R9-002 Documentation not current
    v92 = get(a,"9.2")
    if v92 in ("no","unknown",None):
        f = finding("F9-002","R9-002","9","IT documentation not kept reasonably current","concern",
            "Network, systems, and vendor documentation is not kept current. Outdated documentation can be worse than none — it may misdirect troubleshooting.")
        f.actions = [
            action("A9-002a","Conduct a documentation audit — identify what is outdated and missing — and prioritize updates starting with network diagrams, server records, and vendor contacts.","next_90_days"),
            action("A9-002b","Establish a documentation review cadence — at minimum annual, with updates triggered by any significant change.","next_90_days"),
        ]
        findings.append(f)
    elif v92 == "partial":
        f = finding("F9-002","R9-002","9","Some IT documentation outdated","watch","Most documentation is reasonably current but some areas lag.")
        f.actions = [action("A9-002a","Identify and update outdated documentation sections.","next_90_days")]
        findings.append(f)

    # R9-003 SOPs not documented
    v93 = get(a,"9.3")
    if v93 in ("no","unknown",None):
        f = finding("F9-003","R9-003","9","Standard operating procedures not documented for recurring IT tasks","concern",
            "There are no documented SOPs for common recurring tasks. Without SOPs, every task depends on the IT person's memory. New staff or coverage personnel cannot perform these tasks reliably.")
        f.actions = [action("A9-003a","Identify the five most frequently performed IT tasks that rely on memory and document a simple step-by-step SOP for each.","next_90_days")]
        findings.append(f)
    elif v93 == "partial":
        f = finding("F9-003","R9-003","9","SOPs documented for some but not all recurring tasks","watch","Missing procedures represent tasks that cannot be delegated reliably.")
        f.actions = [action("A9-003a","Identify and document SOPs for the highest-risk undocumented recurring tasks.","next_90_days")]
        findings.append(f)

    # R9-004 No change documentation process
    v94 = get(a,"9.4")
    if v94 in ("no","unknown",None):
        f = finding("F9-004","R9-004","9","No process for documenting changes after projects or incidents","concern",
            "There is no process for documenting changes to the IT environment. Each undocumented change widens the gap between the documented and actual environment.")
        f.actions = [action("A9-004a","After any significant change to the environment, update the relevant documentation before the change is considered complete.","next_30_days")]
        findings.append(f)
    elif v94 == "informal":
        f = finding("F9-004","R9-004","9","Change documentation process informal","watch","Changes are sometimes documented informally.")
        f.actions = [action("A9-004a","Formalize the change documentation process.","next_30_days")]
        findings.append(f)

    # R9-005 Environment not understandable by third party
    v95 = get(a,"9.5")
    if v95 == "no":
        f = finding("F9-005","R9-005","9","IT environment not understandable or supportable from existing documentation","urgent",
            "A qualified third party could not understand or support the IT environment from existing documentation. The school is one departure or illness away from an environment no one can manage.",
            risk_category="continuity", affected_entity="entire IT environment", aggregation_groups=["B"])
        f.actions = [
            action("A9-005a","Identify the areas where documentation is weakest and prioritize documentation of these areas.","next_90_days"),
            action("A9-005b","Use the findings from this assessment as a starting point — every finding that references missing documentation is also a documentation task.","next_90_days"),
        ]
        findings.append(f)
    elif v95 in ("partial","unknown") and v95 is not None:
        f = finding("F9-005","R9-005","9","IT environment only partially understandable from existing documentation","concern",
            "The environment is only partially understandable. A third party could handle some situations but would be unable to support key areas without investigation.",
            aggregation_groups=["B"])
        f.actions = [action("A9-005a","Identify and document the areas where documentation is weakest.","next_90_days")]
        findings.append(f)

    # R9-006 Knowledge concentration (inverted: raw 'yes' = problem)
    if raw_is_yes(a,"9.6"):
        f = finding("F9-006","R9-006","9","Critical IT knowledge concentrated in a single person","concern",
            "Major IT knowledge areas exist only in one person's head. If that person leaves, becomes ill, or is unavailable, the school loses access to that knowledge entirely.",
            risk_category="continuity", notes_passthrough=get_notes(a,"9.6"),
            aggregation_groups=["B"],
            plain_language_note="Identifying and naming knowledge concentration areas earns partial credit — naming the gap is the first step to closing it.")
        f.actions = [
            action("A9-006a","Identify each area of knowledge concentration and develop a documentation or cross-training plan for each.","next_90_days"),
            action("A9-006b","Prioritize documentation of the highest-risk knowledge areas.","next_30_days"),
        ]
        findings.append(f)

    # R9-C01 Documentation completely absent
    if v91 in ("no","unknown",None) and v92 in ("no","unknown",None) and v95 in ("no","unknown",None):
        f = finding("F9-C01","R9-C01","9","No documentation exists and environment is non-transferable","urgent",
            "There is no central documentation location, existing documentation is not kept current, and the environment cannot be understood by anyone other than the current IT person. The school's entire IT environment exists only in one person's memory.",
            risk_category="continuity", affected_entity="entire IT environment", aggregation_groups=["B"])
        f.actions = [
            action("A9-001a","Designate a central documentation location immediately.","next_30_days"),
            action("A9-002a","Conduct a documentation audit and prioritize updates.","next_90_days"),
            action("A9-005a","Identify and document the areas where documentation is most critically missing.","next_90_days"),
        ]
        findings.append(f)

    return findings


# ─────────────────────────────────────────────────────────────────
# POST-PROCESSING
# ─────────────────────────────────────────────────────────────────

COMPOSITE_SUPPRESSION = {
    "F2-C01": {"F2-001","F2-002","F2-003"},
    "F2-C02": {"F2-007","F2-008"},
    "F3-C01": {"F3-001","F3-002","F3-009"},
    "F3-C02": {"F3-010","F3-001","F3-012"},
    "F4-C01": {"F4-005","F4-006","F4-007"},
    "F4-C02": {"F4-002","F4-003"},
    "F5-C01": {"F5-001","F5-003"},
    "F5-C02": {"F5-006","F5-005"},
    "F6-C01": {"F6-001","F6-005","F6-006"},
    "F6-C02": {"F6-009","F6-010"},
    "F7-C01": {"F7-001","F7-002","F7-007","F7-008"},
    "F8-C01": {"F8-001","F8-002","F8-004"},
    "F9-C01": {"F9-001","F9-002","F9-005"},
}

AMPLIFICATION_TARGETS = {
    "F3-001","F3-002","F3-008","F3-009","F3-012",
    "F6-001","F6-002","F6-009","F6-010",
    "F7-003","F7-010","F7-011",
}
AMPLIFICATION_NOTE = (
    "This finding is harder to resolve because the environment currently lacks a "
    "central documentation system — addressing Section 9 findings first will make "
    "this and other documentation gaps easier to close systematically."
)


def apply_suppression(all_findings):
    composite_ids = {f.finding_id for f in all_findings if f.finding_id in COMPOSITE_SUPPRESSION}
    suppressed_ids = set()
    for cid in composite_ids:
        suppressed_ids.update(COMPOSITE_SUPPRESSION.get(cid, set()))

    active, suppressed = [], []
    for f in all_findings:
        if f.finding_id in suppressed_ids and f.finding_id not in composite_ids:
            f.suppressed_by = next(
                (cid for cid, sids in COMPOSITE_SUPPRESSION.items()
                 if f.finding_id in sids and cid in composite_ids), None)
            suppressed.append(f)
        else:
            active.append(f)
    return active, suppressed


def apply_amplification(all_findings, amplification_active):
    if not amplification_active:
        return
    for f in all_findings:
        if f.finding_id in AMPLIFICATION_TARGETS:
            f.amplification_flag = True
            existing = f.plain_language_note or ""
            f.plain_language_note = (existing + "\n\n" + AMPLIFICATION_NOTE).strip()


def apply_constraint_flags(all_findings, constraint_active):
    if not constraint_active:
        return []
    flagged = []
    budget_kw = ("budget","cost","hire","staff","purchase","procure","invest","spend")
    for f in all_findings:
        for act in f.actions:
            if any(kw in act.description.lower() for kw in budget_kw):
                act.constraint_flag = True
                if f.finding_id not in flagged:
                    flagged.append(f.finding_id)
    return flagged


def build_key_risk_groups(active_findings):
    groups = {
        "A": {"title":"No accountable IT ownership structure","finding_ids":[],"severity":"watch"},
        "B": {"title":"Single-person dependency creates recovery and continuity risk","finding_ids":[],"severity":"watch"},
        "C": {"title":"Vendor relationships and renewal visibility","finding_ids":[],"severity":"watch"},
        "D": {"title":"Student data governance and software approval","finding_ids":[],"severity":"watch"},
        "E": {"title":"Privileged access and baseline security posture","finding_ids":[],"severity":"watch"},
        "F": {"title":"Device lifecycle and refresh planning gap","finding_ids":[],"severity":"watch"},
    }
    sev_order = ["healthy","watch","concern","urgent"]
    urgent_triggers = {
        "A": {"F2-C01","F6-C01"},
        "B": {"F2-C02","F7-012","F3-C02","F6-C02","F9-C01","F9-005"},
        "C": {"F6-C01"},
        "D": set(),
        "E": {"F4-C01","F4-005","F4-006","F8-C01"},
        "F": {"F5-C02"},
    }
    fired_ids = {f.finding_id for f in active_findings}

    for f in active_findings:
        for gid in f.aggregation_groups:
            if gid in groups:
                groups[gid]["finding_ids"].append(f.finding_id)
                cur = sev_order.index(groups[gid]["severity"])
                new = sev_order.index(f.severity)
                groups[gid]["severity"] = sev_order[max(cur, new)]

    for gid, triggers in urgent_triggers.items():
        if triggers & fired_ids:
            groups[gid]["severity"] = "urgent"

    return {k: v for k, v in groups.items() if v["finding_ids"]}


# ─────────────────────────────────────────────────────────────────
# SECTION 10: Planning metadata (no findings)
# ─────────────────────────────────────────────────────────────────

def get_section_10_metadata(answers):
    a = answers
    conf_map = {
        "high — most answers are documented or verified": "high",
        "moderate — most answers are based on recall or staff reports": "moderate",
        "low — many answers were estimated or unknown": "low",
        "mixed — confidence varies significantly by section": "mixed",
    }
    raw_conf = (a.get("10.7",{}).get("raw_answer") or "") if a.get("10.7") else ""
    confidence = conf_map.get(str(raw_conf).lower(), "high")

    uncertain_raw = a.get("10.8",{}).get("raw_answer") if a.get("10.8") else None
    uncertain = uncertain_raw if isinstance(uncertain_raw, list) else ([uncertain_raw] if uncertain_raw else [])

    return {
        "confidence": confidence,
        "uncertain_sections": uncertain,
        "leadership_expects_plan": is_yes(a,"10.5"),
        "leadership_plan_notes": get_notes(a,"10.5"),
        "known_priorities": a.get("10.1",{}).get("raw_answer") if a.get("10.1") else [],
        "planned_projects": get_raw(a,"10.2"),
        "known_deadlines": get_raw(a,"10.3"),
        "next_year_changes": get_raw(a,"10.4"),
        "known_obstacles": get_raw(a,"10.6"),
    }


# ─────────────────────────────────────────────────────────────────
# MAIN ENTRY POINTS
# ─────────────────────────────────────────────────────────────────

SECTION_EVALUATORS = {
    "2": evaluate_section_2,
    "3": evaluate_section_3,
    "4": evaluate_section_4,
    "5": evaluate_section_5,
    "6": evaluate_section_6,
    "7": evaluate_section_7,
    "8": evaluate_section_8,
    "9": evaluate_section_9,
}


def evaluate_all(answers, session_id="", completed_sections=None):
    """Evaluate all rules. Pass completed_sections to skip unanswered sections."""
    all_findings = []
    sections_evaluated = []

    for sid, evaluator in SECTION_EVALUATORS.items():
        if completed_sections is None or sid in completed_sections:
            all_findings.extend(evaluator(answers))
            sections_evaluated.append(sid)

    active, suppressed = apply_suppression(all_findings)
    s9_amp = any(f.finding_id in {"F9-C01","F9-005"} for f in active)
    apply_amplification(active, s9_amp)
    constraint_active = any(f.finding_id == "F2-006" for f in active)
    constraint_fids = apply_constraint_flags(active, constraint_active)
    key_risk_groups = build_key_risk_groups(active)
    s10 = get_section_10_metadata(answers)

    return FindingsReport(
        session_id=session_id,
        section_ids_evaluated=sections_evaluated,
        findings=active,
        suppressed_findings=suppressed,
        constraint_flags=constraint_fids,
        key_risk_groups=key_risk_groups,
        data_confidence=s10["confidence"],
        uncertain_sections=s10["uncertain_sections"],
    )


def evaluate_section(answers, section_id, session_id=""):
    """Evaluate a single section only."""
    evaluator = SECTION_EVALUATORS.get(section_id)
    if not evaluator:
        return FindingsReport(session_id=session_id, section_ids_evaluated=[],
                              findings=[], suppressed_findings=[],
                              constraint_flags=[], key_risk_groups={})
    section_findings = evaluator(answers)
    active, suppressed = apply_suppression(section_findings)
    return FindingsReport(
        session_id=session_id,
        section_ids_evaluated=[section_id],
        findings=active,
        suppressed_findings=suppressed,
        constraint_flags=[],
        key_risk_groups=build_key_risk_groups(active),
    )


def findings_to_dict(report):
    """Serialise a FindingsReport to a plain dict for JSON output or template rendering."""
    def f_to_dict(f):
        return {
            "finding_id": f.finding_id,
            "rule_id": f.rule_id,
            "section_id": f.section_id,
            "title": f.title,
            "severity": f.severity,
            "description": f.description,
            "actions": [{
                "action_id": a.action_id,
                "description": a.description,
                "time_horizon": a.time_horizon,
                "schedule_category": a.schedule_category,
                "constraint_flag": a.constraint_flag,
                "user_confirmed": a.user_confirmed,
            } for a in f.actions],
            "risk_category": f.risk_category,
            "affected_entity": f.affected_entity,
            "notes_passthrough": f.notes_passthrough,
            "aggregation_groups": f.aggregation_groups,
            "suppressed_by": f.suppressed_by,
            "plain_language_note": f.plain_language_note,
            "amplification_flag": f.amplification_flag,
        }
    return {
        "session_id": report.session_id,
        "section_ids_evaluated": report.section_ids_evaluated,
        "findings": [f_to_dict(f) for f in report.findings],
        "suppressed_findings": [f_to_dict(f) for f in report.suppressed_findings],
        "constraint_flags": report.constraint_flags,
        "key_risk_groups": report.key_risk_groups,
        "data_confidence": report.data_confidence,
        "uncertain_sections": report.uncertain_sections,
        "finding_count": len(report.findings),
        "by_severity": {
            "urgent":  [f.finding_id for f in report.findings if f.severity == "urgent"],
            "concern": [f.finding_id for f in report.findings if f.severity == "concern"],
            "watch":   [f.finding_id for f in report.findings if f.severity == "watch"],
        },
    }
