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

Each SystemResult has:
  - system_name
  - section_id
  - score_pct
  - grade_label   ("A" / "B" / "C" / "D" / "F")
  - severity      ("healthy" / "watch" / "concern" / "urgent")
  - findings      : list of Finding

Finding fields:
  - area     : str   ("Access Control", "Backup & Recovery", …)
  - severity : str   ("critical" / "high" / "medium" / "low")
  - title    : str
  - detail   : str
  - action   : str
"""

from dataclasses import dataclass, field
from typing import List, Optional
from dynamic_engine import strip_section_prefix


# ── Data classes ───────────────────────────────────────────────────

@dataclass
class Finding:
    area: str
    severity: str          # critical / high / medium / low
    title: str
    detail: str
    action: str
    system_name: Optional[str] = None   # None for school-wide findings


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


@dataclass
class DGReport:
    per_system_results: List[SystemResult]
    school_wide_results: List[Finding]
    summary: DGSummary


# ── Helpers ────────────────────────────────────────────────────────

def _get(answers, section_id, template_qid):
    """Retrieve a raw answer for a generated question."""
    full_qid = f"{section_id}_{template_qid}"
    rec = answers.get(full_qid, {})
    if isinstance(rec, dict):
        raw = rec.get("raw_answer")
        if isinstance(raw, bool):
            return "yes" if raw else "no"
        return raw
    return None


def _answered(answers, section_id, template_qid):
    full_qid = f"{section_id}_{template_qid}"
    rec = answers.get(full_qid, {})
    return rec.get("answer_status") == "answered" if isinstance(rec, dict) else False


def _severity_order(s):
    return {"healthy": 0, "watch": 1, "concern": 2, "urgent": 3}.get(s, 0)


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


# ── Per-system scoring ─────────────────────────────────────────────

# Scoring key: {template_qid: {answer_value: points}}
# Points are defined in the YAML — this mirrors the engine.py logic
# but is hard-coded here for the DG module so the rules engine is
# self-contained.

QUESTION_WEIGHTS = {
    "SYS.A1":  {"Yes — complete list available": 8,
                 "Partial — list available but may be incomplete": 4,
                 "No — system does not easily provide this": 0,
                 "Unknown": 0},
    "SYS.A1a": {"no": 10, "yes": 0, "unknown": 0},    # inverted
    "SYS.A2":  {"Role-based — different roles see different data": 5,
                 "Flat — everyone with a login sees everything": 2,
                 "Unknown": 0},
    "SYS.A3":  {"Yes — required for all users": 10,
                 "Partial — available but not required": 5,
                 "No — not available or not enabled": 0,
                 "Unknown": 0},
    "SYS.A4":  {"yes": 5, "no": 2, "unknown": 0},
    "SYS.A4a": {"no": 5, "yes": 0, "unknown": 0},     # inverted
    "SYS.A5":  {"Yes — logs retained 90+ days and reviewed regularly": 5,
                 "Yes — logs exist but not reviewed regularly": 2,
                 "Yes — logs exist but retention period unknown": 1,
                 "No — no audit logging": 0,
                 "Unknown": 0},
    "SYS.B1":  {"Yes — school manages the backup": 10,
                 "Yes — vendor manages the backup": 7,
                 "Both — school and vendor both maintain copies": 10,
                 "No — not backed up": 0,
                 "Unknown": 0},
    "SYS.B3":  {"Within the last 12 months — documented": 8,
                 "Within the last 12 months — not documented": 5,
                 "More than 12 months ago": 3,
                 "Never tested": 0,
                 "Unknown": 0},
    "SYS.B4":  {"yes": 6, "no": 0, "unknown": 0},
    "SYS.C2a": {"Yes — all outbound transfers are encrypted": 8,
                 "Partial — some encrypted, some not": 4,
                 "No — transfers are not encrypted": 0,
                 "Unknown": 0},
    "SYS.D1":  {"Yes — signed DPA on file": 10,
                 "Terms of service only — no formal DPA": 3,
                 "No agreement on file": 0,
                 "Free tool — no contract": 5,
                 "Unknown": 0},
    "SYS.D2":  {"Yes — 72 hours or less": 8,
                 "Yes — more than 72 hours": 5,
                 "Yes — timeframe not specified": 3,
                 "No breach notification clause": 0,
                 "Unknown": 0},
    "SYS.D3":  {"Yes — deletion required with written confirmation": 7,
                 "Yes — deletion required, no written confirmation": 4,
                 "No — contract is silent on this": 0,
                 "Unknown": 0},
    "SYS.E3":  {"Documented secure deletion process with deletion log": 5,
                 "Deletion occurs but is not documented": 3,
                 "No deletion process — data accumulates indefinitely": 0,
                 "Vendor handles deletion — confirmed in writing": 5,
                 "Vendor handles deletion — not confirmed": 2,
                 "Unknown": 0},
    "SYS.E4":  {"Data exported and vendor deletion confirmed in writing": 15,
                 "Data exported but deletion not confirmed": 8,
                 "Data NOT exported — may still exist with vendor": 0,
                 "Accounts revoked but no export or deletion confirmation": 3,
                 "No shutdown documentation of any kind": 0,
                 "Unknown": 0},
}

MAX_POINTS_PER_SYSTEM = sum([
    8, 10, 5, 10, 5, 5, 5,   # A section
    10, 8, 6, 8,              # B section
    8,                         # C section
    10, 8, 7,                 # D section
    5,                         # E section
])  # = 120 (decommissioned systems replace E3 with E4 @ 15 pts)


def score_system_section(answers, section_id):
    """
    Score one per-system worksheet section.
    Returns (earned, max_pts).
    """
    earned = 0.0
    max_pts = 0

    status = _get(answers, section_id, "SYS.ID.status") or ""
    is_decommissioned = status in (
        "Inactive — still accessible but not being used",
        "Decommissioned — no longer in use"
    )

    for template_qid, weight_map in QUESTION_WEIGHTS.items():
        # Skip E4 for active systems, skip E3 for decommissioned
        if template_qid == "SYS.E4" and not is_decommissioned:
            continue
        if template_qid == "SYS.E3" and is_decommissioned:
            continue

        # Skip follow-up questions if their parent gate fired
        if template_qid == "SYS.B3" and _get(answers, section_id, "SYS.B1") in (
                "No — not backed up", "Unknown", None):
            continue
        if template_qid == "SYS.B4" and _get(answers, section_id, "SYS.B1") in (
                "No — not backed up", "Unknown", None):
            continue

        raw = _get(answers, section_id, template_qid)
        max_for_q = max(weight_map.values())
        if max_for_q == 0:
            continue
        max_pts += max_for_q

        if raw is None:
            continue
        # Normalise booleans
        if isinstance(raw, bool):
            raw = "yes" if raw else "no"

        points = weight_map.get(str(raw), 0)
        earned += points

    return earned, max_pts


# ── Per-system findings ────────────────────────────────────────────

def findings_for_system(answers, section_id, system_name):
    """Generate a list of Finding objects for one system."""
    findings = []
    g = lambda qid: _get(answers, section_id, qid)
    status = g("SYS.ID.status") or ""
    is_decommissioned = status in (
        "Inactive — still accessible but not being used",
        "Decommissioned — no longer in use"
    )

    # ── Access Control ───────────────────────────────────────────
    a1 = g("SYS.A1")
    if a1 in ("No — system does not easily provide this", "Unknown"):
        findings.append(Finding(
            area="Access Control",
            severity="high",
            system_name=system_name,
            title="User roster not readily available",
            detail=f"{system_name} does not provide an easy way to list all "
                   "current login accounts. Without this list, it is impossible "
                   "to verify that former staff accounts have been revoked.",
            action="Contact the vendor to request a full user account export. "
                   "If this cannot be generated easily, escalate as a finding "
                   "requiring remediation before the next offboarding event."
        ))

    a1a = g("SYS.A1a")
    if a1a == "yes":
        findings.append(Finding(
            area="Access Control",
            severity="critical",
            system_name=system_name,
            title="Former staff accounts still active",
            detail=f"One or more accounts belonging to staff who have left the "
                   f"school were found active in {system_name}. Active former-staff "
                   "accounts are a direct security risk.",
            action="Immediately revoke all identified former-staff accounts. "
                   "Review offboarding checklist to add this system explicitly."
        ))

    a3 = g("SYS.A3")
    if a3 == "No — not available or not enabled":
        findings.append(Finding(
            area="Access Control",
            severity="high",
            system_name=system_name,
            title="MFA not enabled",
            detail=f"{system_name} does not have multi-factor authentication "
                   "enabled. Any system holding student, health, or financial "
                   "data should require MFA.",
            action="Contact the vendor to enable MFA. If MFA is unavailable, "
                   "consider whether this system meets minimum security requirements."
        ))
    elif a3 == "Partial — available but not required":
        findings.append(Finding(
            area="Access Control",
            severity="medium",
            system_name=system_name,
            title="MFA available but not required",
            detail=f"MFA is available in {system_name} but is not mandatory. "
                   "Optional MFA is routinely not enabled by users.",
            action="Enable mandatory MFA for all accounts in this system. "
                   "Set a deadline and enforce it."
        ))

    a4a = g("SYS.A4a")
    if a4a == "yes":
        findings.append(Finding(
            area="Access Control",
            severity="medium",
            system_name=system_name,
            title="Shared or generic logins in use",
            detail=f"{system_name} is not connected to SSO and shared or generic "
                   "logins are in use. Shared logins prevent individual accountability "
                   "and create offboarding gaps.",
            action="Convert shared logins to individual accounts. "
                   "Document the change and update the offboarding checklist."
        ))

    # ── Backup & Recovery ────────────────────────────────────────
    b1 = g("SYS.B1")
    if b1 in ("No — not backed up", "Unknown") and not is_decommissioned:
        findings.append(Finding(
            area="Backup & Recovery",
            severity="critical",
            system_name=system_name,
            title="No backup in place",
            detail=f"No backup was confirmed for {system_name}. Data loss from "
                   "accidental deletion, ransomware, or vendor failure would be "
                   "permanent.",
            action="Implement a backup for this system immediately. "
                   "Confirm whether the vendor provides one and whether the school "
                   "needs an independent copy."
        ))

    b3 = g("SYS.B3")
    if b3 in ("Never tested", "Unknown") and b1 not in ("No — not backed up", None):
        findings.append(Finding(
            area="Backup & Recovery",
            severity="high",
            system_name=system_name,
            title="Backup never tested",
            detail=f"The backup for {system_name} has never been tested. "
                   "A backup that has never been restored is an assumption, not a "
                   "safety net.",
            action="Schedule and perform a restore test for this system. "
                   "Document the test date, what was restored, and who verified it."
        ))
    elif b3 == "More than 12 months ago":
        findings.append(Finding(
            area="Backup & Recovery",
            severity="medium",
            system_name=system_name,
            title="Backup test overdue",
            detail=f"The last restore test for {system_name} was more than "
                   "12 months ago.",
            action="Perform and document a restore test within the next 60 days."
        ))

    b4 = g("SYS.B4")
    if b4 == "no" and b1 not in ("No — not backed up", None):
        findings.append(Finding(
            area="Backup & Recovery",
            severity="high",
            system_name=system_name,
            title="Backup stored on same network as the original",
            detail=f"The backup for {system_name} is stored on the same network "
                   "as the system itself. A ransomware attack or hardware failure "
                   "could destroy both.",
            action="Move backups to an offsite or cloud location isolated from "
                   "the production network."
        ))

    # ── Data Flows ───────────────────────────────────────────────
    c2a = g("SYS.C2a")
    if c2a == "No — transfers are not encrypted":
        findings.append(Finding(
            area="Data Flows",
            severity="critical",
            system_name=system_name,
            title="Unencrypted data transfers",
            detail=f"Data leaving {system_name} is not encrypted in transit. "
                   "This exposes school data to interception.",
            action="Require all outbound data transfers to use HTTPS, SFTP, or TLS. "
                   "Contact the vendor if encrypted transfer options are unavailable."
        ))
    elif c2a == "Partial — some encrypted, some not":
        findings.append(Finding(
            area="Data Flows",
            severity="high",
            system_name=system_name,
            title="Some data transfers not encrypted",
            detail=f"Some outbound connections from {system_name} are not encrypted. "
                   "Review and remediate all unencrypted paths.",
            action="Identify which specific transfers are unencrypted and resolve "
                   "each one. Document when all transfers have been secured."
        ))

    c5 = g("SYS.C5")
    if c5 == "Yes — sub-processors exist but are not named":
        findings.append(Finding(
            area="Data Flows",
            severity="medium",
            system_name=system_name,
            title="Sub-processors not identified in contract",
            detail=f"The vendor for {system_name} sub-processes school data with "
                   "other companies, but those companies are not named in the contract. "
                   "School data may reach vendors the school has never evaluated.",
            action="Request a current sub-processor list from the vendor and "
                   "ensure they are named in the contract or DPA."
        ))

    # ── Vendor & Contract ────────────────────────────────────────
    d1 = g("SYS.D1")
    if d1 in ("No agreement on file", "Unknown"):
        findings.append(Finding(
            area="Vendor & Contract",
            severity="critical",
            system_name=system_name,
            title="No Data Processing Agreement on file",
            detail=f"No contract or Data Processing Agreement (DPA) exists for "
                   f"{system_name}. Without a DPA, the school has no contractual "
                   "protection for its data — the vendor can do whatever its terms "
                   "of service allow.",
            action="Request a DPA from the vendor immediately. If the vendor will "
                   "not provide one, assess whether continued use is appropriate."
        ))
    elif d1 == "Terms of service only — no formal DPA":
        findings.append(Finding(
            area="Vendor & Contract",
            severity="high",
            system_name=system_name,
            title="No formal DPA — terms of service only",
            detail=f"The school is relying on standard terms of service for "
                   f"{system_name} rather than a negotiated Data Processing "
                   "Agreement. Terms of service typically favour the vendor.",
            action="Request a DPA from the vendor. Prioritise systems that hold "
                   "student, health, or financial data."
        ))

    d2 = g("SYS.D2")
    if d1 == "Yes — signed DPA on file":
        if d2 in ("No breach notification clause", "Unknown"):
            findings.append(Finding(
                area="Vendor & Contract",
                severity="high",
                system_name=system_name,
                title="No breach notification requirement in contract",
                detail=f"The DPA for {system_name} does not require the vendor to "
                       "notify the school of a data breach. Florida law requires the "
                       "school to notify affected individuals within 30 days — impossible "
                       "if vendors notify late or not at all.",
                action="Amend the contract to require breach notification within 72 hours. "
                       "This is a standard clause and most vendors will accept it."
            ))
        elif d2 == "Yes — more than 72 hours":
            findings.append(Finding(
                area="Vendor & Contract",
                severity="medium",
                system_name=system_name,
                title="Breach notification window exceeds best practice",
                detail=f"The breach notification window in the {system_name} contract "
                       "exceeds 72 hours. This may make it difficult for the school to "
                       "meet its own Florida FIPA obligations.",
                action="Negotiate the notification window down to 72 hours or less "
                       "at the next contract renewal."
            ))

    # ── Decommissioned system checks ─────────────────────────────
    if is_decommissioned:
        e4 = g("SYS.E4")
        if e4 in (
            "Data NOT exported — may still exist with vendor",
            "No shutdown documentation of any kind",
            "Unknown", None
        ):
            findings.append(Finding(
                area="Retention & Disposal",
                severity="critical",
                system_name=system_name,
                title="Decommissioned system — data status unknown",
                detail=f"{system_name} is no longer in use but data export and "
                       "vendor deletion have not been confirmed. School data may "
                       "still exist with the vendor without the school's knowledge.",
                action="Contact the vendor to confirm the current status of school data. "
                       "Request written confirmation of deletion or export the data "
                       "and confirm deletion in writing."
            ))
        elif e4 == "Data exported but deletion not confirmed":
            findings.append(Finding(
                area="Retention & Disposal",
                severity="high",
                system_name=system_name,
                title="Decommissioned — deletion not confirmed in writing",
                detail=f"Data was exported from {system_name} before decommissioning, "
                       "but the vendor has not confirmed in writing that all school data "
                       "has been deleted from their systems.",
                action="Request written deletion confirmation from the vendor. "
                       "File this confirmation with the contract records."
            ))

    return findings


# ── School-wide (DG2) findings ─────────────────────────────────────

def findings_for_school_wide(answers):
    """Generate school-wide governance findings from DG2 answers."""
    findings = []
    g = lambda qid: _get_dg2(answers, qid)

    def _get_dg2(answers, qid):
        rec = answers.get(qid, {})
        if isinstance(rec, dict):
            raw = rec.get("raw_answer")
            if isinstance(raw, bool):
                return "yes" if raw else "no"
            return raw
        return None

    g = _get_dg2

    dg2_1 = g(answers, "DG2.1")
    if dg2_1 in ("Draft only — not formally adopted", "No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="high",
            title="No formal data governance policy",
            detail="The school does not have a formally adopted written data "
                   "governance or data privacy policy. Without this policy, "
                   "there is no authoritative reference for how data should be "
                   "handled, stored, or deleted.",
            action="Draft and formally adopt a data governance policy. "
                   "Review it annually and assign a named owner."
        ))

    dg2_2 = g(answers, "DG2.2")
    if dg2_2 in ("No — no one is responsible", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="high",
            title="No designated data privacy officer or responsible person",
            detail="No individual has formal responsibility for data privacy at "
                   "the school. Data protection decisions are made ad hoc.",
            action="Designate a named person — IT director, head of school, or "
                   "HR lead — as the responsible person for data privacy. "
                   "Document this designation."
        ))

    dg2_4 = g(answers, "DG2.4")
    if dg2_4 in ("Informal — general awareness but no written plan",
                  "No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="high",
            title="No documented data breach response plan",
            detail="The school does not have a written plan for responding to "
                   "a data breach. Florida FIPA requires breach notification to "
                   "affected individuals within 30 days — this is extremely "
                   "difficult without a pre-existing response plan.",
            action="Create a breach response plan that names who does what, "
                   "in what order, and within what timeframes. Test it annually."
        ))

    dg2_5 = g(answers, "DG2.5")
    if dg2_5 in ("No — staff can adopt tools without IT review",
                  "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="medium",
            title="No software approval process — shadow IT risk",
            detail="Staff can adopt tools and services without IT review. "
                   "Shadow IT is one of the most common sources of data governance "
                   "gaps in schools — tools that hold student data are adopted "
                   "without contracts, privacy reviews, or access controls.",
            action="Implement a lightweight software approval process. "
                   "Require IT sign-off before any new tool is used with "
                   "school or student data."
        ))

    dg2_7 = g(answers, "DG2.7")
    if dg2_7 in ("Informal — process exists but relies on memory",
                  "No — no formal offboarding process", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="critical",
            title="No documented offboarding process for system access",
            detail="The school does not have a documented checklist for revoking "
                   "system access when staff members leave. Former staff accounts "
                   "found in the per-system worksheets are the direct result of "
                   "this gap.",
            action="Create an offboarding checklist that names every system and "
                   "requires sign-off on access revocation for each. Run it for "
                   "every departure, on the last day of employment."
        ))

    dg2_9 = g(answers, "DG2.9")
    if dg2_9 in ("No", "Unknown", None):
        findings.append(Finding(
            area="School-Wide Governance",
            severity="medium",
            title="No data retention schedule",
            detail="The school does not have a written data retention schedule "
                   "defining how long each category of data must be kept. "
                   "Florida law sets minimum retention periods for student, "
                   "health, and financial records.",
            action="Create a data retention schedule aligned to Florida requirements. "
                   "Assign responsibility for enforcing it and review annually."
        ))

    return findings


# ── Main evaluation entry point ────────────────────────────────────

def evaluate_dg(answers, system_names, generated_section_ids):
    """
    Parameters
    ----------
    answers             : dict from database.get_answers()
    system_names        : list of str — ordered system names from DG1.3
    generated_section_ids : list of str — e.g. ["DG_SYS_1", "DG_SYS_2", …]

    Returns
    -------
    DGReport
    """
    per_system_results = []

    for i, (name, sid) in enumerate(zip(system_names, generated_section_ids), 1):
        earned, max_pts = score_system_section(answers, sid)
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        grade = _grade(pct)
        severity = _severity_from_pct(pct)
        sys_findings = findings_for_system(answers, sid, name)

        per_system_results.append(SystemResult(
            system_name=name,
            section_id=sid,
            earned=earned,
            max_pts=max_pts,
            score_pct=pct,
            grade_label=grade,
            severity=severity,
            findings=sys_findings
        ))

    school_wide = findings_for_school_wide(answers)

    # Summary
    urgent  = sum(1 for r in per_system_results if r.severity == "urgent")
    concern = sum(1 for r in per_system_results if r.severity == "concern")
    watch   = sum(1 for r in per_system_results if r.severity == "watch")
    healthy = sum(1 for r in per_system_results if r.severity == "healthy")

    all_pcts = [r.score_pct for r in per_system_results if r.max_pts > 0]
    overall_pct = round(sum(all_pcts) / len(all_pcts)) if all_pcts else 0
    overall_grade = _grade(overall_pct)

    all_findings = [f for r in per_system_results for f in r.findings] + school_wide
    critical_count = sum(1 for f in all_findings if f.severity == "critical")
    high_count     = sum(1 for f in all_findings if f.severity == "high")

    summary = DGSummary(
        total_systems=len(system_names),
        systems_scored=len(per_system_results),
        systems_urgent=urgent,
        systems_concern=concern,
        systems_watch=watch,
        systems_healthy=healthy,
        overall_grade=overall_grade,
        critical_finding_count=critical_count,
        high_finding_count=high_count,
        school_wide_findings=school_wide,
    )

    return DGReport(
        per_system_results=per_system_results,
        school_wide_results=school_wide,
        summary=summary,
    )
