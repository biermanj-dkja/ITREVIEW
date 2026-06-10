"""
rules_engine_dg.py  —  Data Governance findings engine for module_2

Generates deterministic findings and a report card from the answers
collected in the Data Governance and Data Flow Audit (module_2).

Architecture
------------
evaluate_dg(answers, system_names) → DGReport

DGReport contains:
  - per_system_results   : list of SystemResult (one per system)
  - school_wide_results  : list of Finding (DG2 section)
  - summary              : DGSummary (counts, overall grade)
  - getting_started      : GettingStarted (checklist for low-maturity schools)

Each SystemResult has:
  - system_name
  - section_id
  - score_pct
  - grade_label   ("A" / "B" / "C" / "D" / "F")
  - severity      ("healthy" / "watch" / "concern" / "urgent")
  - findings      : list of Finding
  - area_scores   : dict {area_name: (earned, max)} — per-area breakdown
  - data_held     : list of str — data categories from SYS.5.1
  - strengths     : list of str — what's working well (for healthy/few-finding systems)

Finding fields:
  - area     : str   ("Access Control", "Backup & Recovery", …)
  - severity : str   ("critical" / "high" / "medium" / "low")
  - effort   : str   ("S" / "S+" / "M" / "M+" / "L")
  - owner    : str   — suggested responsible role
  - timing   : str   ("immediate" / "near_term" / "planned")
  - title    : str
  - detail   : str
  - action   : str

Effort ratings:
  S   = half a day (~4 hours)
  S+  = one day (~8 hours)
  M   = three days
  M+  = five days
  L   = ten days (~two weeks)

Timing buckets (from Magic EdTech K-12 governance framework):
  immediate  = Do within 30 days  (critical + high findings)
  near_term  = Do within 90 days  (medium findings)
  planned    = Schedule this year  (low findings)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from dynamic_engine import strip_section_prefix


# ── Data classes ───────────────────────────────────────────────────

@dataclass
class Finding:
    area: str
    severity: str          # critical / high / medium / low
    title: str
    detail: str
    action: str
    effort: str = "M"
    owner: str = "IT Director"
    timing: str = "near_term"    # immediate / near_term / planned
    system_name: Optional[str] = None
    rule_id: str = ""            # stable slug used as context-note key in templates


@dataclass
class SystemResult:
    system_name: str
    section_id: str
    earned: float
    max_pts: int
    score_pct: int
    grade_label: str
    severity: str
    findings: List[Finding] = field(default_factory=list)
    area_scores: Dict[str, Tuple[float, int]] = field(default_factory=dict)
    data_held: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class GettingStarted:
    """
    A 'Do This First' checklist for schools with low governance maturity.
    Based on the Magic EdTech K-12 governance framework: start small,
    assign owners, build a 15-minute monthly rhythm.
    Only shown when overall grade is C or below with significant gaps.
    """
    show: bool = False
    checklist: List[str] = field(default_factory=list)
    monthly_ritual_items: List[str] = field(default_factory=list)


@dataclass
class DGSummary:
    total_systems: int
    systems_scored: int
    systems_urgent: int
    systems_concern: int
    systems_watch: int
    systems_healthy: int
    overall_grade: str
    critical_finding_count: int
    high_finding_count: int
    school_wide_findings: List[Finding] = field(default_factory=list)
    top_priorities: List[Finding] = field(default_factory=list)
    data_at_risk_summary: str = ""


@dataclass
class FloorCap:
    """
    Set when a critical floor rule fires for the module.
    The overall_grade is capped at cap_grade regardless of the
    sensitivity-weighted average. The report shows this cap explicitly.
    """
    cap_grade: str            # "D"
    reason: str
    trigger_systems: List[str]
    trigger_finding: str


@dataclass
class DGReport:
    per_system_results: List[SystemResult]
    school_wide_results: List[Finding]
    summary: DGSummary
    getting_started: GettingStarted = field(default_factory=GettingStarted)
    floor_cap: Optional[FloorCap] = None


# ── Helpers ────────────────────────────────────────────────────────

def _get(answers, section_id, template_qid):
    # Canonical key format: DG_SYS_1_SYS.1.3  (single underscore between section and template qid).
    # dynamic_engine.py writes this format exclusively. No legacy fallback needed.
    full_qid = f"{section_id}_{template_qid}"
    rec = answers.get(full_qid) or {}
    if isinstance(rec, dict):
        raw = rec.get("raw_answer")
        if isinstance(raw, bool):
            return "yes" if raw else "no"
        return raw
    return None


def _answered(answers, section_id, template_qid):
    full_qid = f"{section_id}_{template_qid}"
    rec = answers.get(full_qid) or {}
    return rec.get("answer_status") == "answered" if isinstance(rec, dict) else False


def _grade(pct):
    if pct >= 90: return "A"
    if pct >= 80: return "B"
    if pct >= 65: return "C"
    if pct >= 50: return "D"
    return "F"


def _severity_from_pct(pct):
    if pct >= 85: return "healthy"
    if pct >= 65: return "watch"
    if pct >= 40: return "concern"
    return "urgent"


def _data_held_summary(data_held):
    """Build a short phrase describing data categories."""
    if not data_held:
        return ""
    short = {
        "Student academic records (grades, transcripts, reports)": "student academic records",
        "Student health records (medical, counseling, nurse)": "student health records",
        "Student behavioral records (discipline, incidents)": "student behavioral records",
        "Staff HR records (employment, performance)": "staff HR records",
        "Staff payroll and compensation data": "staff payroll data",
        "Financial and billing records (tuition, payments)": "financial records",
        "Parent and family contact data": "parent contact data",
        "Admissions and enrollment data": "admissions data",
        "Authentication credentials (usernames, passwords, tokens)": "authentication credentials",
        "Security and audit logs": "security logs",
        "Communications (email, messages, chat)": "communications data",
        "Intellectual property (curriculum, assessments)": "curriculum/IP",
        "Third-party or partner data": "third-party data",
        "Other": "other data",
    }
    labels = [short.get(d, d) for d in data_held if d]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + " and " + labels[-1]


# ── Per-system scoring ─────────────────────────────────────────────

AREA_QUESTIONS = {
    "Access Control": [
        "SYS.1.1", "SYS.1.1a", "SYS.1.2", "SYS.1.3",
        "SYS.1.4", "SYS.1.4a", "SYS.1.5",
    ],
    "Backup & Recovery": ["SYS.2.1", "SYS.2.3", "SYS.2.4"],
    "Data Flows": ["SYS.3.2a"],
    "Vendor & Contract": ["SYS.4.1", "SYS.4.2", "SYS.4.3"],
    "Retention & Disposal": ["SYS.5.3", "SYS.5.4"],
}

QUESTION_WEIGHTS = {
    "SYS.1.1":  {"Yes — complete list available": 8,
                 "Partial — list available but may be incomplete": 4,
                 "No — system does not easily provide this": 0, "Unknown": 0},
    "SYS.1.1a": {"no": 10, "yes": 0, "unknown": 0},
    "SYS.1.2":  {"Role-based — different roles see different data": 5,
                 "Flat — everyone with a login sees everything": 2, "Unknown": 0},
    "SYS.1.3":  {"Yes — required for all users": 10,
                 "Partial — available but not required": 5,
                 "No — not available or not enabled": 0, "Unknown": 0},
    "SYS.1.4":  {"yes": 5, "no": 2, "unknown": 0},
    "SYS.1.4a": {"no": 5, "yes": 0, "unknown": 0},
    "SYS.1.5":  {"Yes — logs retained 90+ days and reviewed regularly": 5,
                 "Yes — logs exist but not reviewed regularly": 2,
                 "Yes — logs exist but retention period unknown": 1,
                 "No — no audit logging": 0, "Unknown": 0},
    "SYS.2.1":  {"Yes — school manages the backup": 10,
                 "Yes — vendor manages the backup": 7,
                 "Both — school and vendor both maintain copies": 10,
                 "No — not backed up": 0, "Unknown": 0},
    "SYS.2.3":  {"Within the last 12 months — documented": 8,
                 "Within the last 12 months — not documented": 5,
                 "More than 12 months ago": 3, "Never tested": 0, "Unknown": 0},
    "SYS.2.4":  {"yes": 6, "no": 0, "unknown": 0},
    "SYS.3.2a": {"Yes — all outbound transfers are encrypted": 8,
                 "Partial — some encrypted, some not": 4,
                 "No — transfers are not encrypted": 0, "Unknown": 0},
    "SYS.4.1":  {"Yes — signed DPA on file": 10,
                 "Terms of service only — no formal DPA": 3,
                 "No agreement on file": 0, "Free tool — no contract": 5,
                 "Unknown": 0},
    "SYS.4.2":  {"Yes — 72 hours or less": 8, "Yes — more than 72 hours": 5,
                 "Yes — timeframe not specified": 3,
                 "No breach notification clause": 0, "Unknown": 0},
    "SYS.4.3":  {"Yes — deletion required with written confirmation": 7,
                 "Yes — deletion required, no written confirmation": 4,
                 "No — contract is silent on this": 0, "Unknown": 0},
    "SYS.5.3":  {"Documented secure deletion process with deletion log": 5,
                 "Deletion occurs but is not documented": 3,
                 "No deletion process — data accumulates indefinitely": 0,
                 "Vendor handles deletion — confirmed in writing": 5,
                 "Vendor handles deletion — not confirmed": 2, "Unknown": 0},
    "SYS.5.4":  {"Data exported and vendor deletion confirmed in writing": 15,
                 "Data exported but deletion not confirmed": 8,
                 "Data NOT exported — may still exist with vendor": 0,
                 "Accounts revoked but no export or deletion confirmation": 3,
                 "No shutdown documentation of any kind": 0, "Unknown": 0},
}


def score_system_section(answers, section_id):
    """Score one per-system worksheet. Returns (earned, max_pts, area_scores)."""
    earned = 0.0
    max_pts = 0
    area_scores = {area: [0.0, 0] for area in AREA_QUESTIONS}

    status = _get(answers, section_id, "SYS.ID.status") or ""
    is_decommissioned = status in (
        "Inactive — still accessible but not being used",
        "Decommissioned — no longer in use"
    )

    qid_to_area = {}
    for area, qids in AREA_QUESTIONS.items():
        for qid in qids:
            qid_to_area[qid] = area

    for template_qid, weight_map in QUESTION_WEIGHTS.items():
        if template_qid == "SYS.5.4" and not is_decommissioned:
            continue
        if template_qid == "SYS.5.3" and is_decommissioned:
            continue
        if template_qid == "SYS.2.3" and _get(answers, section_id, "SYS.2.1") in (
                "No — not backed up", "Unknown", None):
            continue
        if template_qid == "SYS.2.4" and _get(answers, section_id, "SYS.2.1") in (
                "No — not backed up", "Unknown", None):
            continue

        raw = _get(answers, section_id, template_qid)
        max_for_q = max(weight_map.values())
        if max_for_q == 0:
            continue
        max_pts += max_for_q

        area = qid_to_area.get(template_qid)
        if area:
            area_scores[area][1] += max_for_q

        if raw is None:
            continue
        if isinstance(raw, bool):
            raw = "yes" if raw else "no"

        points = weight_map.get(str(raw), 0)
        earned += points
        if area:
            area_scores[area][0] += points

    area_scores_final = {
        a: (v[0], v[1]) for a, v in area_scores.items() if v[1] > 0
    }
    return earned, max_pts, area_scores_final


# ── Strength detection ─────────────────────────────────────────────

def _detect_strengths(answers, section_id):
    """Return plain-language strings for what this system does well."""
    g = lambda qid: _get(answers, section_id, qid)
    strengths = []
    if g("SYS.1.3") == "Yes — required for all users":
        strengths.append("MFA is required for all users")
    if g("SYS.1.1") == "Yes — complete list available":
        strengths.append("A complete user roster is readily available")
    if g("SYS.1.5") == "Yes — logs retained 90+ days and reviewed regularly":
        strengths.append("Audit logs are retained and reviewed regularly")
    if g("SYS.2.1") in ("Yes — school manages the backup",
                         "Both — school and vendor both maintain copies"):
        strengths.append("School-managed backups are in place")
    if g("SYS.2.3") == "Within the last 12 months — documented":
        strengths.append("Backup restore was tested and documented within the last year")
    if g("SYS.2.4") == "yes":
        strengths.append("Backups are stored separately from the live system")
    if g("SYS.3.2a") == "Yes — all outbound transfers are encrypted":
        strengths.append("All outbound data transfers are encrypted")
    if g("SYS.4.1") == "Yes — signed DPA on file":
        strengths.append("A signed Data Processing Agreement is on file")
    if g("SYS.4.2") == "Yes — 72 hours or less":
        strengths.append("Contract requires breach notification within 72 hours")
    if g("SYS.1.4") == "yes":
        strengths.append("System is connected to central SSO")
    return strengths


# ── Per-system findings ────────────────────────────────────────────

def findings_for_system(answers, section_id, system_name):
    findings = []
    g = lambda qid: _get(answers, section_id, qid)
    status = g("SYS.ID.status") or ""
    is_decommissioned = status in (
        "Inactive — still accessible but not being used",
        "Decommissioned — no longer in use"
    )

    data_raw = _get(answers, section_id, "SYS.5.1")
    data_held = data_raw if isinstance(data_raw, list) else ([data_raw] if isinstance(data_raw, str) and data_raw else [])
    data_phrase = _data_held_summary(data_held)
    data_context = f" This system holds {data_phrase}." if data_phrase else ""

    # ── Access Control ───────────────────────────────────────────
    a1 = g("SYS.1.1")
    if a1 in ("No — system does not easily provide this", "Unknown"):
        findings.append(Finding(
            area="Access Control", severity="high", effort="S+",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="ac_roster_unavailable",
            title="User roster not readily available",
            detail=(f"{system_name} does not provide an easy way to list all current login "
                    f"accounts. Without this list, it is impossible to verify that former "
                    f"staff accounts have been revoked.{data_context}"),
            action=("Contact the vendor to request a full user account export. "
                    "If this cannot be generated easily, escalate as a finding "
                    "requiring remediation before the next offboarding event.")
        ))

    a1a = g("SYS.1.1a")
    if a1a == "yes":
        findings.append(Finding(
            area="Access Control", severity="critical", effort="S",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="ac_former_staff_active",
            title="Former staff accounts still active",
            detail=(f"One or more accounts belonging to staff who have left the school "
                    f"were found active in {system_name}. Active former-staff accounts "
                    f"are a direct security risk — an open door for people no longer "
                    f"authorised to access school data.{data_context}"),
            action=("Immediately revoke all identified former-staff accounts. "
                    "Review the offboarding checklist to add this system explicitly. "
                    "Assign a named owner responsible for running this check at every departure.")
        ))

    a3 = g("SYS.1.3")
    if a3 == "No — not available or not enabled":
        findings.append(Finding(
            area="Access Control", severity="high", effort="S+",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="ac_mfa_not_enabled",
            title="MFA not enabled",
            detail=(f"{system_name} does not have multi-factor authentication enabled. "
                    f"Any system holding student, health, or financial data should "
                    f"require MFA.{data_context}"),
            action=("Contact the vendor to enable MFA. If MFA is unavailable, "
                    "consider whether this system meets minimum security requirements.")
        ))
    elif a3 == "Partial — available but not required":
        findings.append(Finding(
            area="Access Control", severity="medium", effort="S",
            owner="IT Director", timing="near_term", system_name=system_name,
            rule_id="ac_mfa_optional",
            title="MFA available but not required",
            detail=(f"MFA is available in {system_name} but is not mandatory. "
                    f"Optional MFA is routinely not enabled by users, leaving accounts "
                    f"protected only by passwords.{data_context}"),
            action=("Enable mandatory MFA for all accounts in this system. "
                    "Set a deadline and enforce it.")
        ))

    a4a = g("SYS.1.4a")
    if a4a == "yes":
        findings.append(Finding(
            area="Access Control", severity="medium", effort="S+",
            owner="IT Director", timing="near_term", system_name=system_name,
            rule_id="ac_shared_logins",
            title="Shared or generic logins in use",
            detail=(f"{system_name} is not connected to SSO and shared or generic "
                    f"logins are in use. Shared logins prevent individual accountability "
                    f"and create offboarding gaps.{data_context}"),
            action=("Convert shared logins to individual accounts. "
                    "Document the change and update the offboarding checklist.")
        ))

    # Audit log quality findings
    a5 = g("SYS.1.5")
    if a5 in ("Yes — logs exist but not reviewed regularly",
              "Yes — logs exist but retention period unknown"):
        findings.append(Finding(
            area="Access Control", severity="low", effort="S",
            owner="IT Director", timing="planned", system_name=system_name,
            rule_id="ac_audit_logs_not_reviewed",
            title="Audit logs not being reviewed",
            detail=(f"{system_name} maintains audit logs, but they are not reviewed "
                    f"regularly (or the retention period is unknown). Logs that are "
                    f"never reviewed provide no early warning of unauthorised access "
                    f"or misuse.{data_context}"),
            action=("Establish a monthly log review — even a 15-minute check for unusual "
                    "login times or bulk exports adds real value. Confirm the retention "
                    "period with the vendor and document it. Assign a named owner "
                    "responsible for the monthly review.")
        ))
    elif a5 == "No — no audit logging":
        findings.append(Finding(
            area="Access Control", severity="medium", effort="S+",
            owner="IT Director", timing="near_term", system_name=system_name,
            rule_id="ac_no_audit_logging",
            title="No audit logging",
            detail=(f"{system_name} does not maintain audit logs. Without logs, there "
                    f"is no way to investigate a suspected breach or verify who accessed "
                    f"what data and when.{data_context}"),
            action=("Check whether audit logging can be enabled in system settings "
                    "or via a vendor support request. If logging is unavailable, "
                    "note this as a compensating control gap in the risk register.")
        ))

    # ── Backup & Recovery ────────────────────────────────────────
    b1 = g("SYS.2.1")
    if b1 in ("No — not backed up", "Unknown") and not is_decommissioned:
        findings.append(Finding(
            area="Backup & Recovery", severity="critical", effort="M",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="br_no_backup",
            title="No backup in place",
            detail=(f"No backup was confirmed for {system_name}. Data loss from "
                    f"accidental deletion, ransomware, or vendor failure would be "
                    f"permanent.{data_context}"),
            action=("Implement a backup for this system immediately. "
                    "Confirm whether the vendor provides one and whether the school "
                    "needs an independent copy.")
        ))

    b3 = g("SYS.2.3")
    if b3 in ("Never tested", "Unknown") and b1 not in ("No — not backed up", None):
        findings.append(Finding(
            area="Backup & Recovery", severity="high", effort="S",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="br_backup_never_tested",
            title="Backup never tested",
            detail=(f"The backup for {system_name} has never been tested. "
                    f"A backup that has never been restored is an assumption, "
                    f"not a safety net.{data_context}"),
            action=("Schedule and perform a restore test for this system. "
                    "Document the test date, what was restored, and who verified it.")
        ))
    elif b3 == "More than 12 months ago":
        findings.append(Finding(
            area="Backup & Recovery", severity="medium", effort="S",
            owner="IT Director", timing="near_term", system_name=system_name,
            rule_id="br_backup_test_overdue",
            title="Backup test overdue",
            detail=(f"The last restore test for {system_name} was more than "
                    f"12 months ago.{data_context}"),
            action="Perform and document a restore test within the next 60 days."
        ))

    b4 = g("SYS.2.4")
    if b4 == "no" and b1 not in ("No — not backed up", None):
        findings.append(Finding(
            area="Backup & Recovery", severity="high", effort="M",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="br_backup_same_network",
            title="Backup stored on same network as the original",
            detail=(f"The backup for {system_name} is stored on the same network "
                    f"as the system itself. A ransomware attack or hardware failure "
                    f"could destroy both.{data_context}"),
            action=("Move backups to an offsite or cloud location isolated from "
                    "the production network.")
        ))

    # ── Data Flows ───────────────────────────────────────────────
    c2a = g("SYS.3.2a")
    if c2a == "No — transfers are not encrypted":
        findings.append(Finding(
            area="Data Flows", severity="critical", effort="M",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="df_unencrypted_transfers",
            title="Unencrypted data transfers",
            detail=(f"Data leaving {system_name} is not encrypted in transit. "
                    f"This exposes school data to interception.{data_context}"),
            action=("Require all outbound data transfers to use HTTPS, SFTP, or TLS. "
                    "Contact the vendor if encrypted transfer options are unavailable.")
        ))
    elif c2a == "Partial — some encrypted, some not":
        findings.append(Finding(
            area="Data Flows", severity="high", effort="M",
            owner="IT Director", timing="immediate", system_name=system_name,
            rule_id="df_partial_encryption",
            title="Some data transfers not encrypted",
            detail=(f"Some outbound connections from {system_name} are not encrypted. "
                    f"Review and remediate all unencrypted paths.{data_context}"),
            action=("Identify which specific transfers are unencrypted and resolve "
                    "each one. Document when all transfers have been secured.")
        ))

    c5 = g("SYS.3.5")
    if c5 == "Yes — sub-processors exist but are not named":
        findings.append(Finding(
            area="Data Flows", severity="medium", effort="S+",
            owner="Business Office", timing="near_term", system_name=system_name,
            rule_id="df_subprocessors_unnamed",
            title="Sub-processors not identified in contract",
            detail=(f"The vendor for {system_name} sub-processes school data with "
                    f"other companies, but those companies are not named in the contract. "
                    f"School data may reach vendors the school has never evaluated.{data_context}"),
            action=("Request a current sub-processor list from the vendor and "
                    "ensure they are named in the contract or DPA.")
        ))

    # ── Vendor & Contract ────────────────────────────────────────
    d1 = g("SYS.4.1")
    if d1 in ("No agreement on file", "Unknown"):
        findings.append(Finding(
            area="Vendor & Contract", severity="critical", effort="M+",
            owner="Business Office", timing="immediate", system_name=system_name,
            rule_id="vc_no_dpa",
            title="No Data Processing Agreement on file",
            detail=(f"No contract or Data Processing Agreement (DPA) exists for "
                    f"{system_name}. Without a DPA, the school has no contractual "
                    f"protection for its data.{data_context}"),
            action=("Request a DPA from the vendor immediately. If the vendor will "
                    "not provide one, assess whether continued use is appropriate.")
        ))
    elif d1 == "Terms of service only — no formal DPA":
        findings.append(Finding(
            area="Vendor & Contract", severity="high", effort="M",
            owner="Business Office", timing="immediate", system_name=system_name,
            rule_id="vc_tos_only",
            title="No formal DPA — terms of service only",
            detail=(f"The school is relying on standard terms of service for "
                    f"{system_name} rather than a negotiated Data Processing Agreement. "
                    f"Terms of service typically favour the vendor.{data_context}"),
            action=("Request a DPA from the vendor. Prioritise systems that hold "
                    "student, health, or financial data.")
        ))

    d2 = g("SYS.4.2")
    if d1 == "Yes — signed DPA on file":
        if d2 in ("No breach notification clause", "Unknown"):
            findings.append(Finding(
                area="Vendor & Contract", severity="high", effort="M",
                owner="Business Office", timing="immediate", system_name=system_name,
                rule_id="vc_no_breach_notification",
                title="No breach notification requirement in contract",
                detail=(f"The DPA for {system_name} does not require the vendor to "
                        f"notify the school of a data breach. Applicable law in most "
                        f"jurisdictions requires prompt notification — typically within "
                        f"30 to 72 hours.{data_context}"),
                action=("Amend the contract to require breach notification within 72 hours. "
                        "This is a standard clause and most vendors will accept it.")
            ))
        elif d2 == "Yes — more than 72 hours":
            findings.append(Finding(
                area="Vendor & Contract", severity="medium", effort="S+",
                owner="Business Office", timing="near_term", system_name=system_name,
                rule_id="vc_breach_window_long",
                title="Breach notification window exceeds best practice",
                detail=(f"The breach notification window in the {system_name} contract "
                        f"exceeds 72 hours. This may make it difficult to meet applicable "
                        f"breach notification requirements.{data_context}"),
                action=("Negotiate the notification window down to 72 hours or less "
                        "at the next contract renewal.")
            ))

    # Vendor security review not performed
    d4 = g("SYS.4.4")
    if d4 in ("No — not reviewed", "Unknown"):
        findings.append(Finding(
            area="Vendor & Contract", severity="low", effort="S",
            owner="IT Director", timing="planned", system_name=system_name,
            rule_id="vc_security_not_reviewed",
            title="Vendor security practices not reviewed",
            detail=(f"The school has not reviewed the security practices of the vendor "
                    f"for {system_name}. A SOC 2 Type II report is the standard way to "
                    f"verify a cloud vendor's security controls — many provide it on "
                    f"request.{data_context}"),
            action=("Request a SOC 2 Type II report or the vendor's published security "
                    "documentation. Review it and file a copy with the contract records.")
        ))

    # ── Retention & Disposal ─────────────────────────────────────
    if not is_decommissioned:
        e3 = g("SYS.5.3")
        if e3 == "Deletion occurs but is not documented":
            findings.append(Finding(
                area="Retention & Disposal", severity="low", effort="S",
                owner="IT Director", timing="planned", system_name=system_name,
                rule_id="rd_deletion_not_documented",
                title="Data deletion not documented",
                detail=(f"{system_name} deletes data at the end of its retention period, "
                        f"but the process is not documented. An undocumented deletion "
                        f"process cannot be audited or verified."),
                action=("Document the deletion process: who initiates it, when, what "
                        "confirmation is received, and where the record is kept. "
                        "Add this to the annual IT calendar.")
            ))
        elif e3 == "No deletion process — data accumulates indefinitely":
            findings.append(Finding(
                area="Retention & Disposal", severity="medium", effort="M",
                owner="IT Director", timing="near_term", system_name=system_name,
                rule_id="rd_no_deletion_process",
                title="No data deletion process — data accumulates indefinitely",
                detail=(f"{system_name} has no process to delete data at the end of its "
                        f"retention period. Data accumulating indefinitely increases "
                        f"legal liability and makes it harder to respond to data requests "
                        f"or incidents.{data_context}"),
                action=("Define and document a deletion schedule for each data category "
                        "held in this system. Confirm the schedule with the Business Office "
                        "and assign a named owner responsible for annual execution.")
            ))

    # ── Decommissioned system checks ─────────────────────────────
    if is_decommissioned:
        e4 = g("SYS.5.4")
        if e4 in ("Data NOT exported — may still exist with vendor",
                  "No shutdown documentation of any kind", "Unknown", None):
            findings.append(Finding(
                area="Retention & Disposal", severity="critical", effort="M",
                owner="IT Director", timing="immediate", system_name=system_name,
                rule_id="rd_decom_data_unknown",
                title="Decommissioned system — data status unknown",
                detail=(f"{system_name} is no longer in use but data export and vendor "
                        f"deletion have not been confirmed. School data may still exist "
                        f"with the vendor without the school's knowledge."),
                action=("Contact the vendor to confirm the current status of school data. "
                        "Request written confirmation of deletion or export the data "
                        "and confirm deletion in writing.")
            ))
        elif e4 == "Data exported but deletion not confirmed":
            findings.append(Finding(
                area="Retention & Disposal", severity="high", effort="S",
                owner="IT Director", timing="immediate", system_name=system_name,
                rule_id="rd_decom_deletion_unconfirmed",
                title="Decommissioned — deletion not confirmed in writing",
                detail=(f"Data was exported from {system_name} before decommissioning, "
                        f"but the vendor has not confirmed in writing that all school data "
                        f"has been deleted from their systems."),
                action=("Request written deletion confirmation from the vendor. "
                        "File this confirmation with the contract records.")
            ))

    return findings


# ── School-wide (DG2) findings ─────────────────────────────────────

def _count_sources_in_text(text):
    if not text:
        return 0
    lines = [l.strip() for l in text.replace(',', '\n').splitlines() if l.strip()]
    return len(lines)


def check_data_source_coverage(answers, system_names, generated_section_ids):
    findings = []
    total_systems = len(system_names)
    flagged_systems = []
    for name, sid in zip(system_names, generated_section_ids):
        qid = f"{sid}_SYS.3.1"
        rec = answers.get(qid, {})
        raw = rec.get("raw_answer", "") if isinstance(rec, dict) else ""
        if not raw:
            continue
        source_count = _count_sources_in_text(str(raw))
        if source_count > total_systems:
            flagged_systems.append((name, source_count))
    if flagged_systems:
        names_str = ", ".join(f"{n} ({c} sources)" for n, c in flagged_systems)
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M",
            owner="IT Director", timing="near_term",
            rule_id="sw_data_sources_exceed_inventory",
            title="Data sources exceed system inventory — possible gaps in worksheet coverage",
            detail=(f"The following system worksheets list more inbound data sources in "
                    f"Section 3 (Data Flows) than the total number of systems in your "
                    f"inventory ({total_systems}): {names_str}. This suggests some systems "
                    f"sending data into your environment were not included in the original "
                    f"inventory, or that sources listed include external services not captured "
                    f"in DG1."),
            action=("Review the data sources listed in the affected worksheets. "
                    "For any source not already in your system inventory, add it to DG1 "
                    "and complete a worksheet for it. External services (government feeds, "
                    "testing bodies, payment processors) should be listed even if the school "
                    "does not log into them directly.")
        ))
    return findings


def findings_for_school_wide(answers):
    findings = []

    def g(answers, qid):
        rec = answers.get(qid, {})
        if isinstance(rec, dict):
            raw = rec.get("raw_answer")
            if isinstance(raw, bool):
                return "yes" if raw else "no"
            return raw
        return None

    dg2_1 = g(answers, "DG2.1")
    if dg2_1 in ("Draft only — not formally adopted", "No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="high", effort="M",
            owner="Head of School / IT Director", timing="immediate",
            rule_id="sw_no_governance_policy",
            title="No formal data governance policy",
            detail=("The school does not have a formally adopted written data governance "
                    "or data privacy policy. Without this policy, there is no authoritative "
                    "reference for how data should be handled, stored, or deleted — and no "
                    "basis for accountability when things go wrong."),
            action=("Draft and formally adopt a data governance policy. Keep the initial "
                    "version short and practical — a one-page policy with clear ownership "
                    "is more effective than a lengthy document no one reads. "
                    "Review it annually and assign a named owner.")
        ))

    dg2_2 = g(answers, "DG2.2")
    if dg2_2 in ("No — no one is responsible", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="high", effort="S",
            owner="Head of School", timing="immediate",
            rule_id="sw_no_privacy_officer",
            title="No designated data privacy officer or responsible person",
            detail=("No individual has formal responsibility for data privacy at the school. "
                    "Data protection decisions are made ad hoc, with no single person "
                    "accountable when issues arise."),
            action=("Designate a named person — IT director, head of school, or HR lead — "
                    "as the responsible person for data privacy. Also assign a backup to "
                    "ensure continuity when staff turn over. Document both designations.")
        ))

    dg2_3 = g(answers, "DG2.3")
    if dg2_3 in ("No — this audit is the first attempt", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M",
            owner="IT Director", timing="near_term",
            rule_id="sw_no_data_register",
            title="No master data register exists",
            detail=("The school does not maintain a master register of systems, what data "
                    "they hold, and how long it is kept. Without a register, the school "
                    "cannot quickly answer basic compliance questions about where student "
                    "data lives."),
            action=("Use the per-system worksheets from this audit as the foundation for "
                    "a master data register. Publish it on a shared intranet page — one "
                    "section per system with data categories, retention periods, vendor "
                    "name, and an owner contact. Assign someone to review it annually.")
        ))
    elif dg2_3 == "Partial — exists but incomplete or outdated":
        findings.append(Finding(
            area="School-Wide Governance", severity="low", effort="S+",
            owner="IT Director", timing="planned",
            rule_id="sw_data_register_outdated",
            title="Master data register exists but is incomplete or outdated",
            detail=("A data register exists but is not current. An outdated register may "
                    "not reflect newly adopted tools or changes to data flows."),
            action=("Update the register using the findings from this audit. Add all "
                    "systems, confirm data categories and retention periods, and schedule "
                    "an annual review.")
        ))

    dg2_4 = g(answers, "DG2.4")
    if dg2_4 in ("Informal — general awareness but no written plan", "No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="high", effort="M",
            owner="Head of School / IT Director", timing="immediate",
            rule_id="sw_no_breach_response_plan",
            title="No documented data breach response plan",
            detail=("The school does not have a written plan for responding to a data breach. "
                    "Applicable law requires prompt breach notification to affected individuals — "
                    "typically within 30 to 72 hours — which is extremely difficult without a "
                    "pre-existing response plan that names who does what and in what order."),
            action=("Create a breach response plan. It does not need to be long — a one-page "
                    "flowchart naming who does what and within what timeframes is sufficient. "
                    "Test it annually and update it when key staff change.")
        ))

    dg2_5 = g(answers, "DG2.5")
    if dg2_5 in ("No — staff can adopt tools without IT review", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M",
            owner="IT Director", timing="near_term",
            rule_id="sw_no_software_approval",
            title="No software approval process — shadow IT risk",
            detail=("Staff can adopt tools and services without IT review. Shadow IT is one "
                    "of the most common sources of data governance gaps in schools — tools "
                    "holding student data are adopted without contracts, privacy reviews, "
                    "or access controls."),
            action=("Implement a lightweight software approval process. Require IT sign-off "
                    "before any new tool is used with school or student data. A simple "
                    "request form with a 48-hour turnaround closes the most common gap.")
        ))

    dg2_6 = g(answers, "DG2.6")
    if dg2_6 in ("Ad hoc — training occurs but not on a schedule", "No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M",
            owner="HR / IT Director", timing="near_term",
            rule_id="sw_no_privacy_training",
            title="No regular staff data privacy training",
            detail=("Staff are not trained on data privacy and responsible data handling on "
                    "a regular schedule. Staff are a primary vector for data incidents — "
                    "phishing, accidental sharing, and mis-addressed emails are all "
                    "preventable with training."),
            action=("Schedule annual data privacy training for all staff. A 30-minute session "
                    "covering phishing, data sharing rules, and who to call if something goes "
                    "wrong is a strong baseline. Document attendance.")
        ))
    elif dg2_6 == "Partial — some staff trained, not all":
        findings.append(Finding(
            area="School-Wide Governance", severity="low", effort="S+",
            owner="HR / IT Director", timing="planned",
            rule_id="sw_privacy_training_partial",
            title="Data privacy training not reaching all staff",
            detail=("Some staff have received data privacy training, but not all. Gaps in "
                    "coverage leave the school partially exposed."),
            action=("Identify which staff groups have not received training and schedule "
                    "a session before the end of the academic year. Track attendance and "
                    "make it a requirement for new hires.")
        ))

    dg2_7 = g(answers, "DG2.7")
    if dg2_7 in ("Informal — process exists but relies on memory",
                  "No — no formal offboarding process", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="critical", effort="M",
            owner="HR / IT Director", timing="immediate",
            rule_id="sw_no_offboarding_process",
            title="No documented offboarding process for system access",
            detail=("The school does not have a documented checklist for revoking system "
                    "access when staff members leave. Former staff accounts found in the "
                    "per-system worksheets are the direct result of this gap. An informal "
                    "process that relies on memory will always have exceptions."),
            action=("Create an offboarding checklist that names every system and requires "
                    "sign-off on access revocation for each. Run it on the last day of "
                    "employment for every departure. Assign HR as the trigger and IT as "
                    "the executor. Review the checklist annually to add newly adopted systems.")
        ))

    dg2_8 = g(answers, "DG2.8")
    if dg2_8 in ("No — vendors are approved without security review", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="sw_no_vendor_review_process",
            title="No formal vendor security review process",
            detail=("New vendors are approved without a security review. The school may be "
                    "signing contracts with vendors whose security practices are unknown."),
            action=("Create a lightweight vendor review checklist: request a SOC 2 report "
                    "or equivalent, confirm a DPA is available, and check that breach "
                    "notification terms are present. Apply this to all new vendors before "
                    "contract signing.")
        ))

    dg2_9 = g(answers, "DG2.9")
    if dg2_9 in ("No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance", severity="medium", effort="M+",
            owner="IT Director / Business Office", timing="near_term",
            rule_id="sw_no_retention_schedule",
            title="No data retention schedule",
            detail=("The school does not have a written data retention schedule defining "
                    "how long each category of data must be kept. Federal and state law "
                    "sets minimum retention periods for student, health, and financial records."),
            action=("Create a data retention schedule aligned to applicable federal and state "
                    "requirements. Start with the highest-risk categories: student records, "
                    "health records, HR files, and financial data. Assign a named owner and "
                    "review annually.")
        ))

    return findings


# ── Getting Started checklist ──────────────────────────────────────

def build_getting_started(summary, school_wide_findings):
    """
    Build the Getting Started section for schools with significant governance gaps.
    Based on the Magic EdTech K-12 governance framework: start small,
    assign owners, build a 15-minute monthly rhythm that outlasts any
    individual staff member.
    """
    gs = GettingStarted()
    if summary.overall_grade not in ("C", "D", "F"):
        return gs
    serious_sw = [f for f in school_wide_findings if f.severity in ("critical", "high")]
    if not serious_sw and summary.critical_finding_count == 0:
        return gs

    gs.show = True
    gs.checklist = [
        "Write a one-sentence data governance vision and share it with leadership — "
        "e.g. 'Our school protects student data by knowing what we hold, who can "
        "access it, and how long we keep it.'",

        "Appoint a named Data Governance Owner (primary) and a backup. This does not "
        "require a new hire — assign it to the IT Director or a senior administrator "
        "and document it in writing.",

        "Use the Action Plan in this report to identify your top 3 actions. Assign "
        "each one a named owner and a deadline before this report is filed away.",

        "Schedule a recurring 15-minute monthly governance check-in with IT and at "
        "least one member of leadership. Keep a short written record of what was "
        "discussed and decided each month.",

        "Create a one-page data register from this audit's per-system worksheets and "
        "publish it on a shared drive. One row per system: data held, vendor, "
        "retention period, and owner contact.",
    ]
    gs.monthly_ritual_items = [
        "Review one open finding from the Action Plan — confirm whether the action "
        "was taken and update the record.",
        "Ask: has any new tool or vendor been adopted since last month? If yes, run "
        "the vendor approval checklist before data is shared.",
        "Check whether any staff have joined or left — confirm offboarding was "
        "completed for all departures.",
        "Note any policy or regulatory updates (e.g. state rule changes, new data "
        "categories) that may affect how the school handles data.",
        "Record the meeting: what was discussed, what was agreed, who owns it, and "
        "when it will be checked again.",
    ]
    return gs


# ── Summary helpers ────────────────────────────────────────────────

def _build_top_priorities(per_system_results, school_wide_results, n=5):
    effort_rank = {"L": 0, "M+": 1, "M": 2, "S+": 3, "S": 4}
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_findings = ([f for r in per_system_results for f in r.findings]
                    + school_wide_results)
    priority = [f for f in all_findings if f.severity in ("critical", "high")]
    priority.sort(key=lambda f: (sev_rank.get(f.severity, 9),
                                  effort_rank.get(f.effort, 5)))
    return priority[:n]


def _build_data_at_risk_summary(per_system_results):
    sensitive_keywords = {
        "student health", "financial", "payroll", "behavioral", "hr records", "credentials"
    }
    at_risk_data = set()
    for r in per_system_results:
        if r.severity in ("concern", "urgent"):
            for d in r.data_held:
                if any(kw in d.lower() for kw in sensitive_keywords):
                    at_risk_data.add(d)
    if not at_risk_data:
        return ""
    phrases = _data_held_summary(sorted(at_risk_data))
    return (f"Systems rated CONCERN or URGENT hold {phrases}. "
            "These categories carry the highest regulatory and reputational risk.")


# ── Critical floor rules ───────────────────────────────────────────

def critical_floor_check(per_system_results):
    """
    Check whether any critical floor condition is met across the assessed systems.

    A critical floor caps the module overall grade at D regardless of the
    sensitivity-weighted average. This prevents strong scores on peripheral
    systems from masking a genuinely dangerous gap in a primary data system.

    Floor conditions (any one is sufficient to trigger the cap):
      DG-FLOOR-1: Any system holds high-sensitivity data AND has former staff
                  accounts still active (SYS.1.1a = yes) — direct breach risk
      DG-FLOOR-2: Any system holds high-sensitivity data AND has NO MFA AND
                  no backup — two critical controls simultaneously absent
      DG-FLOOR-3: Any system holds high-sensitivity data AND has no DPA
                  AND no breach notification clause — contractual compliance failure

    Returns FloorCap if a floor condition fires, else None.
    """
    _HIGH_SENSITIVITY_KEYWORDS = {
        "health", "financial", "payroll", "hr records", "academic records",
        "behavioral", "credentials", "admissions"
    }

    def _is_high_sensitivity(data_held):
        if not data_held:
            return False
        combined = " ".join(d.lower() for d in data_held)
        return any(kw in combined for kw in _HIGH_SENSITIVITY_KEYWORDS)

    # DG-FLOOR-1: Former staff accounts active on a sensitive system
    floor1_systems = []
    for r in per_system_results:
        if _is_high_sensitivity(r.data_held):
            if any(f.title == "Former staff accounts still active" for f in r.findings):
                floor1_systems.append(r.system_name)

    if floor1_systems:
        return FloorCap(
            cap_grade="D",
            reason=(
                "One or more systems holding sensitive data have confirmed active accounts "
                "belonging to former staff. This is an active security risk — former employees "
                "retain access to student, financial, or health data. The overall grade is "
                "capped at D until all former staff accounts are revoked."
            ),
            trigger_systems=floor1_systems,
            trigger_finding="Former staff accounts still active",
        )

    # DG-FLOOR-2: High-sensitivity system with no MFA AND no backup
    floor2_systems = []
    for r in per_system_results:
        if _is_high_sensitivity(r.data_held):
            has_no_mfa    = any("MFA not enabled" in f.title for f in r.findings)
            has_no_backup = any(
                "not backed up" in f.title.lower() or "no backup" in f.title.lower()
                for f in r.findings
            )
            if has_no_mfa and has_no_backup:
                floor2_systems.append(r.system_name)

    if floor2_systems:
        return FloorCap(
            cap_grade="D",
            reason=(
                "One or more systems holding sensitive data have both MFA and backup "
                "controls absent simultaneously. This combination — no authentication "
                "protection and no recovery path — represents a critical unmitigated risk. "
                "The overall grade is capped at D until at least one of these gaps is closed "
                "on each affected system."
            ),
            trigger_systems=floor2_systems,
            trigger_finding="MFA not enabled and no backup — sensitive data system",
        )

    # DG-FLOOR-3: High-sensitivity system with no DPA and no breach notification clause
    floor3_systems = []
    for r in per_system_results:
        if _is_high_sensitivity(r.data_held):
            has_no_dpa    = any("No DPA" in f.title or "no agreement" in f.title.lower()
                                for f in r.findings)
            has_no_breach = any("breach notification" in f.title.lower()
                                for f in r.findings)
            if has_no_dpa and has_no_breach:
                floor3_systems.append(r.system_name)

    if floor3_systems:
        return FloorCap(
            cap_grade="D",
            reason=(
                "One or more systems holding sensitive data have no Data Processing Agreement "
                "and no breach notification clause — both contractual compliance controls "
                "are absent. This is a direct FERPA compliance gap. The overall grade is "
                "capped at D until DPA obligations are established for these systems."
            ),
            trigger_systems=floor3_systems,
            trigger_finding="No DPA and no breach notification clause — sensitive data system",
        )

    return None


# ── Main evaluation entry point ────────────────────────────────────

def evaluate_dg(answers, system_names, generated_section_ids):
    per_system_results = []

    for i, (name, sid) in enumerate(zip(system_names, generated_section_ids), 1):
        earned, max_pts, area_scores = score_system_section(answers, sid)
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        grade = _grade(pct)
        severity = _severity_from_pct(pct)
        sys_findings = findings_for_system(answers, sid, name)
        strengths = _detect_strengths(answers, sid) if not sys_findings else []

        data_raw = _get(answers, sid, "SYS.5.1")
        data_held = (data_raw if isinstance(data_raw, list)
                     else ([data_raw] if isinstance(data_raw, str) and data_raw else []))

        per_system_results.append(SystemResult(
            system_name=name, section_id=sid, earned=earned, max_pts=max_pts,
            score_pct=pct, grade_label=grade, severity=severity,
            findings=sys_findings, area_scores=area_scores,
            data_held=data_held, strengths=strengths,
        ))

    school_wide = findings_for_school_wide(answers)
    school_wide += check_data_source_coverage(answers, system_names, generated_section_ids)

    urgent  = sum(1 for r in per_system_results if r.severity == "urgent")
    concern = sum(1 for r in per_system_results if r.severity == "concern")
    watch   = sum(1 for r in per_system_results if r.severity == "watch")
    healthy = sum(1 for r in per_system_results if r.severity == "healthy")

    # ── Sensitivity-weighted overall grade ───────────────────────────
    # Systems holding higher-sensitivity data carry more weight in the overall
    # grade. This prevents a strong score on low-risk tools masking critical
    # failures in the school's primary data systems.
    #
    # Multiplier logic (per SYS.5.1 data categories):
    #   3x  — health/counseling records or financial/HR data
    #   2x  — student academic, behavioral, admissions, or auth credentials
    #   1x  — everything else (content filters, logging tools, etc.)
    _HIGH_SENSITIVITY = {
        "Student health records (medical, counseling, nurse)",
        "Staff HR records (employment, performance)",
        "Financial and payment data",
    }
    _MEDIUM_SENSITIVITY = {
        "Student academic records (grades, transcripts, reports)",
        "Student behavioral records (discipline, incidents)",
        "Admissions and enrollment data",
        "Authentication credentials (usernames, passwords, tokens)",
    }

    def _sensitivity_multiplier(data_held):
        if not data_held:
            return 1
        cats = set(data_held) if isinstance(data_held, list) else {data_held}
        if cats & _HIGH_SENSITIVITY:
            return 3
        if cats & _MEDIUM_SENSITIVITY:
            return 2
        return 1

    weighted_sum = 0.0
    weight_total = 0.0
    for r in per_system_results:
        if r.max_pts > 0:
            w = _sensitivity_multiplier(r.data_held)
            weighted_sum += r.score_pct * w
            weight_total += w

    overall_pct = round(weighted_sum / weight_total) if weight_total > 0 else 0
    overall_grade = _grade(overall_pct)

    # ── Critical floor check ────────────────────────────────────────────────────
    floor_cap = critical_floor_check(per_system_results)
    if floor_cap:
        # Cap grade at floor_cap.cap_grade if the computed grade is better
        order = ["A", "B", "C", "D", "F"]
        ci = order.index(floor_cap.cap_grade) if floor_cap.cap_grade in order else 3
        gi = order.index(overall_grade) if overall_grade in order else 4
        overall_grade = order[max(ci, gi)]

    all_findings = [f for r in per_system_results for f in r.findings] + school_wide
    critical_count = sum(1 for f in all_findings if f.severity == "critical")
    high_count     = sum(1 for f in all_findings if f.severity == "high")

    top_priorities = _build_top_priorities(per_system_results, school_wide)
    data_at_risk = _build_data_at_risk_summary(per_system_results)

    summary = DGSummary(
        total_systems=len(system_names), systems_scored=len(per_system_results),
        systems_urgent=urgent, systems_concern=concern,
        systems_watch=watch, systems_healthy=healthy,
        overall_grade=overall_grade,
        critical_finding_count=critical_count, high_finding_count=high_count,
        school_wide_findings=school_wide, top_priorities=top_priorities,
        data_at_risk_summary=data_at_risk,
    )

    getting_started = build_getting_started(summary, school_wide)

    return DGReport(
        per_system_results=per_system_results,
        school_wide_results=school_wide,
        summary=summary,
        getting_started=getting_started,
        floor_cap=floor_cap,
    )
