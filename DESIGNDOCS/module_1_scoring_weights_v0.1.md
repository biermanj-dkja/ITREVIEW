# Module 1 — Scoring Weight Framework
## Version 0.1

---

## Purpose
This document defines the scoring weights for all questions and sections in Module 1. Weights determine how much each question contributes to its section score, and how much each section contributes to the overall assessment score.

Scores are visible to the user at three levels — question, section, and total — per design document Decision #16.

---

## Scoring Philosophy

### Three dimensions of weight
Every question's weight reflects three factors:

1. **Worst-case severity** — a question whose worst answer fires urgent carries more weight than one that maxes at watch
2. **Operational impact** — questions whose gaps create active or imminent risk outweigh questions about planning maturity
3. **Amplification effect** — questions whose gap worsens other findings (documentation, credential access, admin access) carry bonus weight because their absence compounds everything else

### How section scores are calculated
- Each question has a **base point value** of 1–5
- A full-credit answer (healthy / yes / fully documented / confirmed) earns full points
- Partial answers earn partial points as defined per question
- Unknown answers earn zero points and trigger the unknown override floor per design document Decisions #11 and #12
- The section score = points earned / maximum possible points × 100
- Composite rules do not carry their own weight — they fire based on component questions

### How the total score is calculated
- The total score is a **weighted average** of section scores
- Section weights reflect domain importance (security, continuity, governance) not question count
- Section 1 and Section 10 carry zero weight in the total score — Section 1 is context only, Section 10 is calibration only

### Score display
- Question-level: shown as earned/maximum (e.g. 3/5) with a severity label
- Section-level: shown as a percentage with a severity label and color band
- Total: shown as a percentage with an overall severity label

---

## Section Weight Table

| Section | Title | Weight in total score | Rationale |
|---|---|---|---|
| Section 1 | School Identity, Profile, and Context | 0% | Context only — no findings |
| Section 2 | Governance, Budget, Staffing, and Ownership | 15% | Foundational — ownership gaps amplify all other sections |
| Section 3 | Sites, Buildings, Network, and Internet | 12% | Large section; network is infrastructure for everything else |
| Section 4 | Identity, Accounts, and Access | 14% | Direct security impact; offboarding and MFA gaps are active risks |
| Section 5 | Endpoints, Printing, and Classroom Technology | 10% | Important but more planning-oriented than access or continuity |
| Section 6 | Core Systems, Servers, Vendors, and Contracts | 12% | Server and vendor gaps create direct continuity risk |
| Section 7 | Data Protection, Backup, and Recovery | 15% | Highest direct consequence if wrong — data loss is unrecoverable |
| Section 8 | Security Operations, Filtering, and Safeguards | 12% | Baseline hygiene; safeguarding dimension elevates importance |
| Section 9 | Documentation and Operational Readiness | 10% | Amplifies other sections via RA-011; all questions score 3–5 points so internal weight is already high; low-weight/high-impact section — see note below |
| Section 10 | Near-Term Priorities and Planning Inputs | 0% | Calibration only — no findings, no scoring |
| **Total** | | **100%** | |

**Note on Section 7 and Section 2 being equal at 15%:** Section 7 carries the highest consequence (unrecoverable data loss) but Section 2 carries the highest amplification effect (no accountability makes every other finding harder to resolve). Treating them equally reflects this balance.

---

## Question Point Values

### Scoring key
- **5 points** — question directly gates urgent findings; unknown is as dangerous as absent
- **4 points** — question can fire urgent in combination or with escalation; significant operational impact
- **3 points** — question fires concern; material gap with clear action path
- **2 points** — question fires watch; maturity improvement with indirect risk
- **1 point** — contextual or optional; feeds other rules or display only; no standalone finding
- **0 points** — calibration, count, or platform identification only; no finding generated

### Partial credit rules
Unless otherwise specified:
- Full / Yes / Documented / Current = full points
- Partial / Informal / Outdated = 50% of points
- No = 0 points
- Unknown = 0 points (triggers unknown override floor separately)
- Not applicable = full points (question excluded from denominator)

---

## Section 2: Governance, Budget, Staffing, and Ownership

Maximum section score: 36 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 2.1 | Primary support model | 1 | Context only; shapes interpretation but no standalone finding |
| 2.2 | Named IT leader exists | 5 | No → urgent (F2-001); foundational accountability |
| 2.3 | Day-to-day responsibilities assigned | 4 | No → concern escalating to urgent with 2.2; operational ownership |
| 2.4 | System owners documented | 3 | No → concern; ownership visibility |
| 2.5 | Vendor contacts documented | 3 | No → concern; continuity risk |
| 2.6 | Formal IT budget exists | 2 | No → concern; informal → watch; planning maturity |
| 2.7 | Budget/staffing constraints noted | 1 | Constraint annotation only; no negative finding |
| 2.8 | Shared credentials documented | 5 | No → urgent (F2-007); root cause of costly IT failures |
| 2.9 | Coverage if IT lead unavailable | 4 | No → concern escalating to urgent with 2.8; key-person risk |
| 2.10 | Recurring tasks tracked | 2 | Partial → watch; no → concern; operational cadence |
| 2.11 | Ticketing system in use | 1 | Watch at most; maturity improvement only |
| 2.12 | Software approval process | 1 | Watch; governance context |

**Partial credit for 2.6:** Annual = 5pts, informal = 3pts (watch variant), no/unknown = 0pts
**Partial credit for 2.9:** Yes = 4pts, partially = 2pts, no/unknown = 0pts
**Partial credit for 2.10:** Yes fully = 2pts, partially = 1pt, no/unknown = 0pts
**Partial credit for 2.11:** Yes in regular use = 1pt, yes limited use = 0.5pts, no/unknown = 0pts

---

## Section 3: Sites, Buildings, Network, and Internet

Maximum section score: 46 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 3.1 | Digital floor plans exist | 1 | Optional; context modifier for AP location findings |
| 3.2 | Current network diagram | 3 | No → concern; outdated → watch; documentation |
| 3.3 | Site/closet/rack maps | 3 | No → concern; partial → watch; physical documentation |
| 3.4 | AP physical locations known | 3 | No → concern; wireless planning dependency |
| 3.5 | Wireless AP platform | 0 | Platform identification only |
| 3.6 | Firewall exists | 5 | No/unknown → urgent (F3-004); perimeter security |
| 3.7 | Wired network platform | 0 | Platform identification only |
| 3.8 | AP inventory with model/firmware | 3 | No → concern; lifecycle and supportability |
| 3.9 | Switch inventory with model/firmware | 3 | No → concern; lifecycle and supportability |
| 3.10 | Switch topology map | 3 | No → concern; topology visibility |
| 3.11 | Core device inventory with support status | 3 | No → concern; lifecycle planning |
| 3.12 | Admin access to network infrastructure | 5 | No/unknown → urgent (F3-010); control and continuity |
| 3.13 | Number of internet connections | 0 | Count; context for 3.15 |
| 3.14 | Primary ISP | 0 | Display only |
| 3.15 | Internet failover/redundancy | 2 | No → concern; resilience planning |
| 3.16 | Static public IPs | 0 | Display only; no v1 finding |
| 3.17 | Firewall firmware/support status | 3 | No → concern; security lifecycle |
| 3.18 | Switch/wireless config backup | 5 | No/unknown → urgent (F3-012); recovery capability |
| 3.19 | Wireless coverage adequate | 3 | No/mixed → concern; instructional impact |
| 3.20 | VLAN purposes documented | 2 | No → watch; security documentation |
| 3.21 | UPS protection for critical equipment | 2 | No → concern; power resilience |
| 3.22 | UPS runtime known | 1 | Watch; contextual modifier |
| 3.23 | UPS monitored/networked | 1 | Optional; watch at most |
| 3.24 | Network scanned regularly | 1 | Optional; visibility maturity |
| 3.25 | Scan frequency | 0 | Context for 3.24 |
| 3.26 | Known connectivity pain points | 3 | Yes → concern (active operational problem) |

**Partial credit for 3.2:** Current = 3pts, outdated = 1.5pts, no/unknown = 0pts
**Partial credit for 3.15:** Automatic = 2pts, manual = 1pt, no/unknown = 0pts
**Partial credit for 3.17:** Fully known = 3pts, partial = 1.5pts, no/unknown = 0pts
**Partial credit for 3.18:** Yes = 5pts, partial = 2.5pts, no/unknown = 0pts
**Partial credit for 3.26:** No pain points = 3pts (healthy signal), yes = 0pts (active problem)

---

## Section 4: Identity, Accounts, and Access

Maximum section score: 35 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 4.1 | Primary identity platform | 1 | Classification; informs other rules |
| 4.2 | Centralized identity management | 3 | No → concern; account management foundation |
| 4.3 | Staff onboarding documented | 3 | No → concern; informal → watch |
| 4.4 | Staff offboarding documented | 5 | No → urgent (F4-003); active unauthorized access risk |
| 4.5 | Student account lifecycle documented | 2 | No → concern; conditional on school managing student accounts |
| 4.6 | MFA on privileged accounts | 5 | No/unknown → urgent (F4-005); highest-impact security control |
| 4.7 | Reviewed admin/privileged role list | 5 | No/unknown → urgent (F4-006); access visibility |
| 4.8 | Shared accounts minimized | 3 | No → concern; partially → watch |
| 4.9 | Password reset procedures documented | 2 | No → concern; partial → watch |
| 4.10 | Auto file sync to cloud | 1 | Modifier for R7-005 only; no standalone finding |

**Partial credit for 4.3:** Current = 3pts, informal = 1.5pts, no/unknown = 0pts
**Partial credit for 4.4:** Current = 5pts, informal = 2pts, no/unknown = 0pts
**Partial credit for 4.7:** Current = 5pts, outdated = 2pts, no/unknown = 0pts
**Partial credit for 4.8:** Yes = 3pts, partially = 1.5pts, no/unknown = 0pts

---

## Section 5: Endpoints, Printing, and Classroom Technology

Maximum section score: 28 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 5.1 | Current device inventory exists | 4 | No → concern; inventory is prerequisite for everything else |
| 5.2 | Inventory includes key fields | 3 | No → concern; lifecycle planning depends on this |
| 5.3 | 1:1 environment | 0 | Context; modifies other rules but no standalone finding |
| 5.4 | Devices go home with students | 0 | Context only |
| 5.5 | MDM/endpoint management deployed | 4 | No → concern, escalates to urgent in 1:1; management control |
| 5.6 | Staff device provisioning standard | 2 | No → concern; partial → watch |
| 5.7 | Devices set up quickly/consistently | 2 | No → concern; operational efficiency |
| 5.8 | Devices standardized | 1 | Optional; supportability context |
| 5.9 | Refresh cycle defined | 3 | No → concern; lifecycle planning |
| 5.10 | Known unsupported devices | 4 | Many → urgent; unknown → concern; active lifecycle risk |
| 5.11 | Warranties tracked | 1 | Optional; watch at most |
| 5.12 | Spare/loaner process defined | 2 | No → concern in 1:1; watch otherwise |
| 5.13 | Decommissioning process documented | 2 | No → concern; data privacy risk |
| 5.14 | Typical staff device service life | 0 | Context only |
| 5.15 | Different student device types by grade | 0 | Context only |
| 5.16 | Rationale for different device types | 0 | Context only |
| 5.17 | Peripheral and classroom tech tracked | 1 | Optional; watch at most |
| 5.18 | Large MFP/copier count | 0 | Count only |
| 5.19 | Small printer count | 0 | Count only |

**Partial credit for 5.1:** Current = 4pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 5.2:** Fully = 3pts, partial = 1.5pts, no/unknown = 0pts
**Partial credit for 5.5:** Yes most = 4pts, yes some = 2pts, no/unknown = 0pts
**Partial credit for 5.10:** None known = 4pts (healthy), some = 2pts, many = 0pts, unknown = 0pts
**Partial credit for 5.9:** Documented = 3pts, informal = 1.5pts, no/unknown = 0pts

---

## Section 6: Core Systems, Servers, Vendors, and Contracts

Maximum section score: 38 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 6.1 | SIS used | 0 | Platform identification only |
| 6.2 | LMS used | 0 | Platform identification only |
| 6.3 | Core systems list exists | 4 | No → concern; systems visibility foundation |
| 6.4 | Systems list includes key fields | 3 | No → concern; operational management fields |
| 6.5 | Major software subscriptions listed | 0 | Inventory seed; no standalone finding |
| 6.6 | Subscription governance tracked | 2 | No → concern; watch variant; financial governance |
| 6.7 | FERPA/COPPA review status known | 2 | No → concern; student data compliance |
| 6.8 | Renewal dates tracked | 4 | No → concern; renewal blindness is a recurring operational failure |
| 6.9 | Vendor escalation paths documented | 3 | No → concern; incident response dependency |
| 6.10 | Single-vendor/person dependencies | 3 | Yes → concern; specific risks quoted in report |
| 6.11 | Unused paid tools identified | 1 | Watch; optimization opportunity |
| 6.12 | Phone/voice provider | 0 | Display only |
| 6.13 | Server count | 0 | Count; context for server sub-section |
| 6.14 | Server inventory with key fields | 5 | No/unknown → urgent (F6-009); environment unsupportable |
| 6.15 | Server purpose documented | 3 | No → concern; severity amplifier for 6.14 |
| 6.16 | Server admin access documented | 5 | No/unknown → urgent (F6-010); single-person dependency |
| 6.17 | Server patching cycle defined | 2 | No → concern; informal → watch |
| 6.18 | Server warranties tracked | 1 | No → concern; lifecycle planning |
| 6.19 | Server lifecycle/refresh plan | 1 | No → concern; informal → watch |

**Partial credit for 6.3:** Current = 4pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 6.4:** Fully = 3pts, partial = 1.5pts, no/unknown = 0pts
**Partial credit for 6.8:** Yes = 4pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 6.10:** No dependencies = 3pts (healthy), yes = 1pt (concern but identified — awareness is progress), unknown = 0pts
**Partial credit for 6.14:** Current = 5pts, partial = 2.5pts, no/unknown = 0pts
**Partial credit for 6.17:** Documented = 2pts, informal = 1pt, no/unknown = 0pts

---

## Section 7: Data Protection, Backup, and Recovery

Maximum section score: 40 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 7.1 | Backup platform used | 0 | Platform identification; context for other rules |
| 7.2 | Backups in place for critical systems | 5 | No/unknown → urgent (R7-001/R7-002); foundational data protection |
| 7.3 | Documented list of what is backed up | 4 | No → concern; scope visibility is essential for recovery confidence |
| 7.4 | Backups cover servers | 5 | No/partial → urgent (R7-004); server data loss unrecoverable |
| 7.5 | Backups cover staff devices | 3 | Context-dependent; concern or watch based on cloud platform |
| 7.6 | Backups cover cloud data | 3 | No → concern; cloud availability ≠ backup |
| 7.7 | Backup success reviewed regularly | 4 | No → concern, escalates to urgent with 7.8; silent failures are common |
| 7.8 | Restore test in last 12 months | 5 | No/unknown → concern, escalates to urgent with 7.2; recovery proof |
| 7.9 | Restore test frequency | 3 | Too low → concern; proportional to recovery window |
| 7.10 | Recovery priority defined | 3 | No → concern; incident planning |
| 7.11 | Incident/disaster response reference | 3 | No → concern; escalates with 7.12 |
| 7.12 | Emergency credentials accessible | 5 | No → urgent (R7-012); amplifies all continuity findings |
| 7.13 | Useful backup recovery window known | 3 | Unknown → concern; prerequisite for test frequency alignment |
| 7.14 | Restore tests within recovery window | 3 | No → concern; retention-frequency alignment |

**Partial credit for 7.2:** Confirmed = 5pts, maybe/assumed = 2pts, no/unknown = 0pts
**Partial credit for 7.3:** Yes = 4pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 7.4:** Yes = 5pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 7.7:** Yes = 4pts, irregularly = 2pts, no/unknown = 0pts
**Partial credit for 7.8:** Yes = 5pts, more than 12 months ago = 2pts, no/unknown = 0pts
**Partial credit for 7.12:** Yes securely = 5pts, partially = 2pts, no/unknown = 0pts

---

## Section 8: Security Operations, Filtering, and Safeguards

Maximum section score: 30 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 8.1 | Endpoint protection platform | 0 | Platform identification only |
| 8.2 | Endpoint protection deployed | 5 | No/unknown → urgent (R8-001); unprotected devices are primary attack surface |
| 8.3 | Patching on defined cadence | 3 | No → concern; informal → watch |
| 8.4 | Network/security firmware reviewed | 3 | No → concern; infrastructure vulnerability |
| 8.5 | Web filter in place | 4 | No on student devices → urgent (R8-004); safeguarding obligation |
| 8.6 | Student safety monitoring platform | 1 | Contextual; no standalone finding in v1 |
| 8.7 | Filtering controls documented | 1 | Optional; watch at most |
| 8.8 | Incident response process documented | 4 | No → concern; operational response capability |
| 8.9 | Logs/alerts reviewed | 2 | Optional; watch; detection maturity |
| 8.10 | Cyber insurance carried | 1 | Optional; contextual; no finding in v1 |
| 8.11 | Known unresolved security concerns | 4 | Yes → concern (known problem); unknown → 0pts (worst outcome — cannot manage what you cannot see) |
| 8.12 | *(reserved for future)* | — | — |

**Partial credit for 8.2:** Yes most = 5pts, yes some = 2.5pts, no/unknown = 0pts
**Partial credit for 8.3:** Documented = 3pts, informal = 1.5pts, no/unknown = 0pts
**Partial credit for 8.4:** Regularly = 3pts, irregularly = 1.5pts, no/unknown = 0pts
**Partial credit for 8.5:** Students and staff = 4pts, students only = 3pts, limited/partial = 2pts, no/unknown = 0pts
**Partial credit for 8.11:** No known concerns = 4pts (healthy signal), yes with notes = 2pts (concern but acknowledged — knowing your problems is better than not knowing them), yes without notes = 1pt, unknown = 0pts (worst outcome — you cannot address what you cannot see)

**Report note requirement for 8.11:** When the answer is `yes`, the score display must include: *"Scoring 2 out of 4 here reflects that identifying a security concern is better than being unaware of one. The finding still requires action — but honest awareness is the first step to resolution."* When the answer is `unknown`, the score display must include: *"Unknown scores lower than a confirmed yes — an unexamined security posture is more dangerous than a known problem. Conduct a basic security review to move this from unknown to known."*

---

## Section 9: Documentation and Operational Readiness

Maximum section score: 26 points

| Question | Description | Points | Rationale |
|---|---|---|---|
| 9.1 | Central documentation location | 4 | No → concern; documentation foundation |
| 9.2 | Documents kept current | 4 | No → concern; partly → watch |
| 9.3 | SOPs documented for recurring tasks | 4 | No → concern; operational transferability |
| 9.4 | Change documentation process | 3 | No → concern; informal → watch; environment drift |
| 9.5 | Environment understandable by third party | 5 | No → urgent (R9-005); total single-person dependency |
| 9.6 | Knowledge concentration in one person | 4 | Yes → concern (amplifies Key Risk Group B) |
| 9.7 | *(reserved)* | — | — |

**Partial credit for 9.1:** Well used = 4pts, inconsistent = 2pts, no/unknown = 0pts
**Partial credit for 9.2:** Yes = 4pts, partly = 2pts, no/unknown = 0pts
**Partial credit for 9.3:** Yes = 4pts, partial = 2pts, no/unknown = 0pts
**Partial credit for 9.4:** Yes = 3pts, informal = 1.5pts, no/unknown = 0pts
**Partial credit for 9.5:** Yes = 5pts, partially = 2pts, no/unknown = 0pts
**Partial credit for 9.6:** No concentration = 4pts (healthy signal), yes with notes identifying the specific areas = 1pt (concern but acknowledged and documented — naming the gap is the first step to closing it), yes without notes = 0pts, unknown = 0pts

**Report note requirement for 9.6:** When the answer is `yes` with notes, the score display must include: *"Scoring 1 out of 4 here reflects that identifying and naming knowledge concentration areas is meaningful progress. The finding still requires action — but documenting where knowledge lives is the prerequisite for cross-training or writing it down."*

---

## Section 10: Near-Term Priorities and Planning Inputs

All questions in Section 10 have a point value of 0. This section generates no scores and does not contribute to the total. Its questions are calibration and context inputs only.

---

## Score Display Specification

### During a section — question level
While the IT person is answering questions within a section, each question displays its **point value** alongside it — not its earned score. This gives the IT person a clear sense of relative importance before they answer.

Example display:
```
3.6  Does the school have a firewall?        [5 pts]
3.7  What wired network platform is used?   [0 pts]
3.12 Do you have admin access to the network? [5 pts]
```

The point value is visible at all times during the section. No partial scores or running totals are shown until the section is complete.

### After completing a section — section level
When the IT person submits or completes a section, the section score is revealed as:

**Points earned / Maximum points — Severity label**

Example: `28 / 36 — Watch`

The severity label is determined by the domain score logic for that section (healthy / watch / concern / urgent / unknown), not mechanically from the percentage alone. A section can score 80% and still be concern if a critical unknown override applies.

### Total score — summary screen
The total score is displayed as:

**Weighted percentage — Severity label**

Followed by a section-by-section breakdown table showing each section's score, weight, and contribution to the total.

Example:
```
Overall Score: 71% — Concern

Section                                    Score      Weight   Contribution
──────────────────────────────────────────────────────────────────────────
Governance, Budget, Staffing               24/36      15%      10.0%
Sites, Buildings, Network                  31/46      12%       8.1%
Identity, Accounts, and Access             28/35      14%      11.2%
Endpoints, Printing, Classroom Tech        19/28      10%       6.8%
Core Systems, Servers, Vendors             22/38      12%       6.9%
Data Protection, Backup, Recovery          30/40      15%      11.3%
Security Operations, Filtering             18/30      12%       7.2%
Documentation and Readiness                14/26      10%       5.4%
──────────────────────────────────────────────────────────────────────────
Total                                                100%      66.9% → 71%*
```

*Total displayed as rounded percentage. Section 9 low-weight note appears here per scoring design notes.

### Implementation notes
- Point values are stored in the question definition in the module schema — they are not computed at runtime
- The section score is computed when the section is marked complete in the Assessment Session
- The total score is computed when all sections are complete or when the IT person requests a partial summary
- Severity labels on section scores are drawn from domain score logic, not from percentage thresholds — a 78% section can be concern if a critical unknown override applies
- The total score severity label is drawn from the total score interpretation table in the scoring weights document

| Score range | Label | Meaning |
|---|---|---|
| 85–100% | Healthy | Strong baseline; focused maintenance and minor improvements needed |
| 70–84% | Watch | Solid foundation with meaningful gaps; near-term action plan warranted |
| 50–69% | Concern | Significant gaps across multiple domains; structured improvement program needed |
| 30–49% | Urgent | Serious deficiencies in critical areas; immediate action required in multiple domains |
| 0–29% | Critical | Foundational failures across the environment; comprehensive remediation needed |

---

## Scoring Design Notes

### Why Section 7 and Section 2 share the top weight
Section 7 carries the highest direct consequence — unrecoverable data loss. Section 2 carries the highest amplification effect — without accountability, every finding is harder to resolve. Equal weighting at 15% reflects that both are in a different class from the other sections.

### Why Section 9 is weighted lower than its foundational importance suggests
Section 9 findings amplify other sections through RA-011, but its own point values are already high (all questions 3–5 points). Giving it a higher section weight would double-count its importance. The 10% section weight plus the amplification behavior in the report is the right balance.

**Report note requirement:** The Section 9 score display must include a plain-language note explaining why the section weight appears low relative to its importance: *"Documentation and Operational Readiness is weighted at 10% of your total score, but improving it has an outsized effect on your overall assessment — every documentation gap makes other findings harder to resolve and reduces confidence in your data. This section also contains the most achievable near-term score improvements: creating a central documentation location, writing five SOPs, and documenting your change process are low-cost actions that directly raise your score in this section and improve confidence across the full report."*

### Why questions with zero points still exist in the module
Zero-weight questions serve three purposes: platform identification (feeds environment overview and appendix), count inputs (contextual modifiers for other rules), and display-only fields (organization profile). They matter for the report even when they don't matter for scoring.

### Unknown answers and the floor
Unknown answers earn zero points. But they also trigger the section floor rules (watch or concern) independent of the score calculation. This means a school that answers everything unknown will score zero in that section AND have its domain status set to at least concern — two separate mechanisms working together to surface the gap.

### Rewarding awareness over ignorance
For questions where `yes` means acknowledging a problem (8.11, 9.6) and `unknown` means being unaware of one, scoring deliberately gives partial credit to honest acknowledgment and zero to ignorance. The principle: you cannot fix what you do not know about, and you cannot know about what you have not looked for. Schools that have examined their environment and know their gaps are in a better position than schools that have not looked. The findings still fire — the partial credit reflects awareness, not resolution. Each of these questions includes a mandatory report note explaining the scoring logic so the IT person understands they are not being penalized for honesty.
The scoring model is designed to produce a comparable numeric output. Per design document Decision #17, a future version may allow schools to submit scores anonymously to a central database. The section weight table and point values defined here will be the basis for that comparison — they should not be changed casually once the engine is built, as changes would break comparability across assessments.

---

## Next Steps
1. Review section weights — particularly whether Section 4 (Identity) at 14% is appropriate relative to Section 3 (Network) at 12%
2. Review question point values for any that feel miscalibrated
3. Add partial credit rules for any questions not yet covered
4. Integrate scoring weights into the master rule schema document or implement directly in the engine
5. Define how the score is displayed in the UI — numeric, percentage, color band, or combination
