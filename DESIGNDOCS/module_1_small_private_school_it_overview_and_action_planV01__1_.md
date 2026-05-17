# Module 1 - Small Private School IT Overview and Action Plan
## Version 0.1

## Purpose
This module is the first implementation of the School IT Documentation Engine. It is designed to produce a practical overview of a small private school's IT environment and generate a deterministic near-term action plan.

This module should answer five core questions:
1. What exists?
2. What is known and documented?
3. What is missing, unclear, or risky?
4. What should be addressed in the next 30 to 90 days?
5. What broader improvements belong on a 12-month roadmap?

---

## Intended Use Cases
- New IT director or technology coordinator assessing an unfamiliar environment
- Existing school IT staff who want to document their environment and find their blind spots
- School IT staff preparing a baseline overview before a major project or planning cycle

### Out of scope for this module
This module is not designed for use by MSPs, consultants, or external parties operating on behalf of a school. It is not intended for public distribution before significant testing and validation. Future use cases may expand this scope after the core engine is proven.

---

## Output Goals
This module should produce:
- an environment overview
- a set of findings by domain
- a top risks/gaps summary
- a 30/60/90-day action plan
- a generalized annual follow-up calendar
- appendix details showing the structured answers

---

## Module Assumptions
- The school is small enough that some IT responsibilities may be shared or informal.
- Documentation may be partial or scattered.
- The respondent may not know all technical details.
- Unknown answers are expected and should remain visible.
- The goal is useful clarity, not perfection.

---

## Proposed Section List
1. School Identity, Profile, and Context
2. Governance, Budget, Staffing, and Ownership
3. Sites, Buildings, Network, and Internet
4. Identity, Accounts, and Access
5. Endpoints, Printing, and Classroom Technology
6. Core Systems, Servers, Vendors, and Contracts
7. Data Protection, Backup, and Recovery
8. Security Operations, Filtering, and Safeguards
9. Documentation and Operational Readiness
10. Near-Term Priorities and Planning Inputs

---

## Standard Output Tags for This Module
- visibility
- lifecycle
- supportability
- security
- continuity
- ownership
- vendor_management
- documentation
- planning
- compliance
- school_context

---

## Section 1: School Identity, Profile, and Context

### Purpose
Capture baseline organizational context used to tailor findings, recommendations, and calendar items.

### Key outputs fed by this section
- organization summary
- sizing assumptions
- support model context
- roadmap framing
- report header/profile information

### Implementation note for this section
Status values are working recommendations, not final decisions. You can still revise them as you review the module.

### Question catalog

#### 1.1 School name
- type: short_text
- status: core
- condition trigger: none
- prefill: yes — pre-populated from the school profile captured before the module starts; editable by the user
- report outputs: cover page, organization profile, executive summary context
- deterministic rule impact: display only

#### 1.2 School address
- type: short_text
- status: core
- condition trigger: none
- report outputs: organization profile, site context, appendix
- deterministic rule impact: display and location context only

#### 1.3 Main school phone number
- type: short_text
- status: optional
- condition trigger: none
- report outputs: organization profile, appendix
- deterministic rule impact: display only

#### 1.4 School website
- type: short_text
- status: core
- condition trigger: none
- prefill: yes — pre-populated from the school profile captured before the module starts; editable by the user
- report outputs: organization profile, appendix, report header
- deterministic rule impact: display only; used to prevent ambiguity in filing and records

#### 1.5 School mission statement
- type: long_text
- status: optional
- condition trigger: none
- report outputs: executive summary framing, context section
- deterministic rule impact: no scoring effect; narrative context only

#### 1.6 Does the school have an official logo or crest available for use in the report?
- type: yes_no_unknown plus notes
- status: optional
- condition trigger: none
- report outputs: report branding assets list
- deterministic rule impact: none; presentation only

#### 1.7 What is the name and role of the person creating this report?
- type: short_text
- status: core
- condition trigger: none
- report outputs: report metadata, appendix, internal audit trail
- deterministic rule impact: metadata only

#### 1.8 How many sites or campuses are supported?
- type: count
- status: core
- condition trigger: none
- report outputs: organization profile, complexity summary, planning context
- deterministic rule impact: sets environment complexity baseline; may influence priority weighting for network and documentation gaps

#### 1.9 How many buildings are supported in total?
- type: count
- status: core
- condition trigger: none
- report outputs: organization profile, complexity summary, planning context
- deterministic rule impact: sets physical-environment complexity baseline

#### 1.10 How many buildings are located at each site?
- type: list_of_items
- status: conditional
- condition trigger: ask if 1.8 is greater than 1 or if 1.9 is greater than 1
- report outputs: site profile, planning notes, appendix
- deterministic rule impact: increases specificity for multi-site findings and future branch logic

#### 1.11 What grades does the school serve?
- type: short_text or list_of_items
- status: core
- condition trigger: none
- report outputs: organization profile, device-program context, executive summary context
- deterministic rule impact: informs later interpretation of student device, filtering, and classroom tool questions

#### 1.12 Approximate student enrollment
- type: count
- status: core
- condition trigger: none
- report outputs: organization profile, scale summary, chart normalization inputs
- deterministic rule impact: scale context only; may affect intensity of recommendations

#### 1.13 Approximate faculty/staff count
- type: count
- status: core
- condition trigger: none
- report outputs: organization profile, scale summary, support model context
- deterministic rule impact: staffing scale context only

#### 1.14 Approximate total managed devices
- type: count
- status: core
- condition trigger: none
- report outputs: environment overview, scale summary, lifecycle context
- deterministic rule impact: supports inventory maturity interpretation and roadmap sizing

#### 1.15 Which device categories are in scope?
- type: multi_select
- status: core
- condition trigger: none
- report outputs: environment overview, scope summary, branching logic notes
- deterministic rule impact: enables later conditional questions and prevents irrelevant follow-ups

#### 1.16 What are the most important upcoming school calendar events that affect IT planning?
- type: long_text or list_of_items
- status: core
- condition trigger: none
- report outputs: annual follow-up calendar, near-term action timing, executive summary context
- deterministic rule impact: schedules recommendation timing and roadmap cadence

---

## Section 2: Governance, Budget, Staffing, and Ownership

### Purpose
Determine whether the environment has clear accountability for systems, vendors, credentials, recurring tasks, and spending.

### Key outputs
- ownership clarity score
- staffing risk indicators
- budgeting/planning context
- action items around role gaps and cross-training

### Implementation note for this section
This section feeds several high-value deterministic findings, especially around ownership gaps, key-person risk, and planning maturity.

### Question catalog

#### 2.1 Primary support model
- type: single_select
- options: internal IT staff, single IT director, outsourced MSP, hybrid internal plus MSP, volunteer or ad hoc support, other
- status: core
- condition trigger: none
- report outputs: environment overview, support model summary, executive summary
- deterministic rule impact: shapes interpretation of ownership, admin access, documentation maturity, and vendor dependency findings

#### 2.2 Is there a named person primarily responsible for IT leadership?
- type: yes_no_unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, key risks, action plan
- deterministic rule impact: if no or unknown, create ownership gap finding and near-term assignment action

#### 2.3 Are day-to-day support responsibilities clearly assigned?
- type: yes_no_unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, operational readiness summary, action plan
- deterministic rule impact: if no or unknown, create operational ownership finding and process formalization action

#### 2.4 Is there a documented list of system owners for major platforms and services?
- type: yes_no_unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, key risks, appendix gaps list
- deterministic rule impact: if no or unknown, create system ownership visibility finding

#### 2.5 Is there a documented list of vendor contacts and escalation paths?
- type: yes_no_unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, continuity risks, action plan
- deterministic rule impact: if no or unknown, create vendor dependency / continuity visibility finding

#### 2.6 Does the IT function have a formal budget?
- type: single_select
- options: yes annual, yes but informal, no, unknown
- status: core
- condition trigger: none
- report outputs: governance summary, roadmap framing, budget planning notes
- deterministic rule impact: if no or unknown, create planning maturity finding; if informal, create roadmap formalization recommendation

#### 2.7 Are there known budget or staffing constraints affecting IT work this year?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: executive summary context, roadmap framing, near-term planning notes
- deterministic rule impact: does not create a negative finding by itself; modifies recommended scope and timeline of actions

#### 2.8 Are shared credentials or emergency access methods documented and controlled?
- type: yes_no_unknown
- status: core
- condition trigger: none
- report outputs: security findings, continuity findings, key risks
- deterministic rule impact: if no or unknown, create access continuity and security control finding

#### 2.9 If the primary IT lead were unavailable for two weeks, could another person reasonably maintain operations?
- type: single_select
- options: yes, partially, no, unknown
- status: core
- condition trigger: none
- report outputs: key risks, executive summary, action plan
- deterministic rule impact: partial, no, or unknown contributes to key-person dependency finding and documentation/cross-training actions

#### 2.10 Are recurring IT tasks tracked on a calendar, checklist, or ticketing system?
- type: single_select
- options: yes fully, partially, no, unknown
- status: core
- condition trigger: none
- report outputs: operational readiness summary, action plan, annual follow-up calendar
- deterministic rule impact: if partial, no, or unknown, create recurring-operations maturity finding and schedule formalization action

#### 2.11 Is there a ticketing system for the IT team?
- type: single_select
- options: yes in regular use, yes but limited use, no, unknown
- status: optional
- condition trigger: none
- report outputs: support process maturity note, governance summary, appendix
- deterministic rule impact: if no or unknown, may contribute to process-maturity watch finding, but should not be a standalone urgent issue in v1

#### 2.12 Who decides whether new software or digital tools may be adopted for classroom use?
- type: long_text or single_select plus notes
- status: optional
- condition trigger: none
- report outputs: governance summary, software approval notes, compliance context
- deterministic rule impact: if decision ownership is unclear and software inventory/compliance visibility is weak, may contribute to governance finding

---

## Section 3: Sites, Buildings, Network, and Internet

### Purpose
Establish the physical shape, dependencies, equipment profile, and documentation status of the network environment.

### Key outputs
- network visibility score
- internet resilience indicators
- diagram/documentation gaps
- infrastructure action items

### Implementation note for this section
This is one of the most finding-heavy sections in Module 1. Many questions are core because missing network visibility tends to block later planning.

### Question catalog

#### 3.1 Do you have digital blueprints, floor plans, or building maps for the school facilities?
- type: single_select
- options: yes current, partial, no, unknown
- status: optional
- condition trigger: none
- report outputs: facilities/context appendix, planning notes, wireless documentation context
- deterministic rule impact: if no or unknown, contributes to documentation maturity watch finding, especially when paired with AP location uncertainty

#### 3.2 Is there a current network diagram?
- type: single_select
- options: yes current, yes outdated, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, key risks, documentation gaps list, action plan
- deterministic rule impact: outdated, no, or unknown creates network visibility/documentation finding

#### 3.3 Is there a site map or closet/rack map for each campus or building?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: ask for all environments with network infrastructure in scope
- report outputs: findings by domain, documentation gaps, action plan
- deterministic rule impact: partial, no, or unknown contributes to infrastructure visibility and supportability finding

#### 3.4 Do you know where the wireless access points are physically located throughout the school?
- type: single_select
- options: yes fully, partial, no, unknown
- status: core
- condition trigger: ask if wireless networking is in scope or if APs exist
- report outputs: findings by domain, wireless planning notes, appendix gaps list
- deterministic rule impact: partial, no, or unknown contributes to wireless visibility finding; stronger when paired with poor coverage or absent floor plans

#### 3.5 What wireless access point platform or brand is used?
- type: short_text
- status: core
- condition trigger: ask if wireless networking is in scope or if APs exist
- report outputs: environment overview, infrastructure profile, vendor/platform appendix
- deterministic rule impact: platform identification only; supports later platform-specific branching in future versions

#### 3.6 Does the school have a firewall, and if so what platform or brand is used?
- type: single_select plus notes
- options: yes, no, unknown
- status: core
- condition trigger: none
- report outputs: environment overview, security profile, key risks
- deterministic rule impact: if no or unknown, create urgent perimeter visibility/control finding; if yes, capture platform for further interpretation

#### 3.7 What primary brand or platform is used for the wired network infrastructure?
- type: short_text
- examples: switches, routing, management platform
- status: core
- condition trigger: ask if wired network infrastructure is in scope
- report outputs: infrastructure profile, appendix, environment overview
- deterministic rule impact: platform identification only; supports later vendor concentration interpretation

#### 3.8 Are wireless access points inventoried with model and firmware information?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: ask if APs exist
- report outputs: findings by domain, lifecycle notes, documentation gaps list
- deterministic rule impact: partial, no, or unknown creates wireless asset visibility finding

#### 3.9 Are switches inventoried with model and firmware information?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: ask if switches exist
- report outputs: findings by domain, lifecycle notes, documentation gaps list
- deterministic rule impact: partial, no, or unknown creates wired infrastructure visibility finding

#### 3.10 Is there a switch map showing how major switches connect to one another?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: ask if switches exist or more than one closet/building exists
- report outputs: findings by domain, documentation gaps, action plan
- deterministic rule impact: partial, no, or unknown contributes to network topology visibility finding

#### 3.11 Are core network devices inventoried with make, model, location, and support status?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: infrastructure profile, lifecycle summary, findings by domain
- deterministic rule impact: partial, no, or unknown contributes to lifecycle and supportability finding

#### 3.12 Do you have administrative access to the network infrastructure?
- type: single_select
- options: yes full, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: key risks, findings by domain, action plan
- deterministic rule impact: partial, no, or unknown creates access/control dependency finding and escalation-path action

#### 3.13 How many internet connections are in place?
- type: count
- status: core
- condition trigger: none
- report outputs: environment overview, resilience context, appendix
- deterministic rule impact: informs redundancy interpretation; a value of 1 does not automatically create a finding without business context

#### 3.14 Who is the primary ISP or ISPs?
- type: list_of_items
- status: optional
- condition trigger: none
- report outputs: vendor list, infrastructure profile, appendix
- deterministic rule impact: vendor visibility only unless combined with redundancy concerns

#### 3.15 Is there internet failover or redundancy?
- type: single_select
- options: yes automatic, yes manual, no, unknown
- status: core
- condition trigger: ask if internet connectivity is required for school operations, which is effectively always in v1
- report outputs: key risks, resilience summary, action plan
- deterministic rule impact: no or unknown contributes to continuity/resilience finding; manual may create watch finding depending on site count and reliance

#### 3.16 Does the school have static public IP addresses?
- type: single_select
- options: yes, no, unknown
- status: optional
- condition trigger: none
- report outputs: infrastructure appendix, ISP notes
- deterministic rule impact: none in v1 unless future modules depend on externally hosted services or firewall rules

#### 3.17 Are firewall platform, firmware status, and support or warranty status known?
- type: single_select
- options: yes fully, partial, no, unknown
- status: core
- condition trigger: ask if 3.6 indicates a firewall exists
- report outputs: security findings, lifecycle summary, key risks, action plan
- deterministic rule impact: partial, no, or unknown creates perimeter security visibility/lifecycle finding

#### 3.18 Are switch and wireless configurations backed up or exportable?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if switches or APs exist
- report outputs: continuity findings, action plan, key risks
- deterministic rule impact: partial, no, or unknown creates infrastructure recovery readiness finding

#### 3.19 Is wireless coverage known to be adequate in instructional and administrative areas?
- type: single_select
- options: yes, mixed, no, unknown
- status: core
- condition trigger: ask if wireless networking is in scope
- report outputs: findings by domain, executive summary, action plan
- deterministic rule impact: mixed, no, or unknown creates wireless performance/visibility finding; stronger when AP locations are unknown

#### 3.20 Are network segments or VLAN purposes documented?
- type: single_select
- options: yes, partial, no, unknown
- status: conditional
- condition trigger: ask if managed switching, VLANs, or network segmentation are in use
- report outputs: findings by domain, security and supportability notes, appendix gaps list
- deterministic rule impact: partial, no, or unknown creates segmentation visibility finding

#### 3.21 Do network closets or server areas have battery backup or UPS protection for critical equipment?
- type: single_select
- options: yes fully, partial, no, unknown
- status: core
- condition trigger: ask if on-site network/server equipment exists
- report outputs: continuity findings, infrastructure summary, action plan
- deterministic rule impact: partial, no, or unknown creates power resilience finding

#### 3.22 Is UPS runtime for critical network or server equipment known?
- type: single_select
- options: yes documented, estimated only, no, unknown
- status: conditional
- condition trigger: ask if 3.21 is yes fully or partial
- report outputs: continuity notes, appendix, action plan
- deterministic rule impact: estimated, no, or unknown increases severity of power resilience finding

#### 3.23 Are UPS devices monitored or network-connected for alerting and status?
- type: single_select
- options: yes, partial, no, unknown
- status: optional
- condition trigger: ask if UPS devices exist
- report outputs: infrastructure maturity note, continuity appendix, action plan
- deterministic rule impact: may contribute to watch-level resilience finding, but not usually standalone critical in v1

#### 3.24 Is the network scanned or discovered regularly for connected devices?
- type: single_select
- options: yes regularly, occasionally, no, unknown
- status: optional
- condition trigger: none
- report outputs: operations maturity note, security visibility note, appendix
- deterministic rule impact: if no or unknown, may contribute to visibility watch finding when inventory is weak

#### 3.25 If the network is scanned or discovered, how often?
- type: single_select
- options: continuously, daily, weekly, monthly, ad hoc, unknown
- status: conditional
- condition trigger: ask if 3.24 is yes regularly or occasionally
- report outputs: operations maturity note, appendix
- deterministic rule impact: interpret maturity only; no direct finding unless combined with other visibility gaps

#### 3.26 Are there known connectivity pain points currently affecting school operations?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: executive summary, findings by domain, action plan
- deterministic rule impact: if yes, create service-impact finding and prioritize troubleshooting or remediation actions

---
## Section 4: Identity, Accounts, and Access

### Purpose
Assess how accounts are managed, secured, and transitioned.

### Key outputs
- identity hygiene findings
- onboarding/offboarding findings
- privileged access concerns

### Implementation note for this section
This section should stay strongly deterministic because identity and access issues often become high-priority actions even when the rest of the environment is only partially documented.

### Question catalog

#### 4.1 What is the primary identity and productivity platform?
- type: single_select
- options: Google Workspace, Microsoft 365, hybrid Google and Microsoft, local directory or Active Directory, other, unknown
- status: core
- condition trigger: none
- report outputs: environment overview, identity profile, executive summary context
- deterministic rule impact: environment classification only; informs branching and interpretation of later identity questions

#### 4.2 Is there Active Directory or another centralized login management system in place?
- type: single_select
- options: yes cloud-based, yes on-premises, yes hybrid, no, unknown
- status: core
- condition trigger: none
- report outputs: identity profile, infrastructure overview, appendix
- deterministic rule impact: identifies account-management model and supports later interpretation of onboarding, offboarding, and server questions

#### 4.3 Is there a documented onboarding process for staff accounts?
- type: single_select
- options: yes current, informal, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, operational readiness summary, action plan
- deterministic rule impact: informal, no, or unknown creates staff onboarding process finding and process documentation action

#### 4.4 Is there a documented offboarding process for staff accounts?
- type: single_select
- options: yes current, informal, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, security summary, action plan, key risks
- deterministic rule impact: informal, no, or unknown creates account lifecycle/security finding and prioritized offboarding formalization action

#### 4.5 Are student account lifecycle processes documented?
- type: single_select
- options: yes current, informal, no, unknown, not applicable
- status: conditional
- condition trigger: ask if student accounts are provisioned or managed by the school
- report outputs: findings by domain, operational readiness summary, appendix gaps list
- deterministic rule impact: informal, no, or unknown creates student account lifecycle finding where applicable

#### 4.6 Is MFA enabled for administrative or privileged accounts?
- type: single_select
- options: yes all privileged, some privileged, no, unknown
- status: core
- condition trigger: ask if privileged accounts exist, which is effectively always in v1
- report outputs: key risks, security findings, executive summary, action plan
- deterministic rule impact: some, no, or unknown creates privileged-access security finding; no or unknown may raise severity to urgent depending on other gaps

#### 4.7 Is there a reviewed list of global admins or equivalent privileged roles?
- type: single_select
- options: yes current, outdated, no, unknown
- status: core
- condition trigger: ask if cloud or centralized identity exists
- report outputs: security findings, key risks, action plan
- deterministic rule impact: outdated, no, or unknown creates privileged-role governance finding

#### 4.8 Are shared accounts minimized and justified?
- type: single_select
- options: yes, partially, no, unknown
- status: core
- condition trigger: none
- report outputs: security findings, identity governance summary, action plan
- deterministic rule impact: partially, no, or unknown creates account hygiene finding; stronger when MFA or admin review is weak

#### 4.9 Are password reset and recovery procedures documented?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: continuity findings, operational readiness summary, action plan
- deterministic rule impact: partial, no, or unknown creates recovery readiness finding

#### 4.10 Are staff devices configured to automatically sync files to a cloud platform such as Google Drive or Microsoft OneDrive?
- type: single_select
- options: yes fully — all staff devices sync consistently, yes partially — some devices or some folders only, no, unknown
- status: conditional
- condition trigger: ask if 4.1 is google_workspace or microsoft_365 or hybrid
- report outputs: backup coverage context, staff device data protection notes, appendix
- deterministic rule impact: informs severity of R7-005 (staff device backup gap); full consistent sync reduces severity to watch; partial or absent sync keeps severity at concern; unknown defaults to concern until confirmed. Does not create a standalone finding — used as a modifier for Section 7 rules only

---

## Section 5: Endpoints, Printing, and Classroom Technology

### Purpose
Understand the school's device inventory, management posture, age profile, printing footprint, and replacement planning.

### Key outputs
- inventory maturity
- lifecycle risk
- endpoint management findings
- refresh planning recommendations

### Implementation note for this section
This section combines asset visibility, endpoint management, and replacement planning. In v1, questions should favor baseline control and lifecycle clarity over very detailed device analytics.

### Question catalog

#### 5.1 Is there a current inventory of managed devices?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, environment overview, appendix gaps list, action plan
- deterministic rule impact: partial, no, or unknown creates inventory maturity finding and baseline inventory action

#### 5.2 Does the inventory include owner or assignment, model, serial number, age or purchase date, and status?
- type: single_select
- options: yes fully, partial, no, unknown
- status: core
- condition trigger: ask if 5.1 is yes current or partial
- report outputs: findings by domain, lifecycle summary, appendix gaps list
- deterministic rule impact: partial, no, or unknown increases severity of inventory maturity finding

#### 5.3 Is the school a 1:1 environment for student devices?
- type: single_select
- options: yes all relevant grades, partial, no, unknown
- status: core
- condition trigger: ask if student devices are in scope
- report outputs: environment overview, device-program context, executive summary context
- deterministic rule impact: contextual only; affects interpretation of student device management and support expectations

#### 5.4 Do student devices go home with students?
- type: single_select
- options: yes all, some, no, unknown
- status: conditional
- condition trigger: ask if 5.3 is yes all relevant grades or partial
- report outputs: device-program context, support notes, policy context, appendix
- deterministic rule impact: contextual only in v1; may influence later recommendations around filtering, support, and break/fix planning

#### 5.5 Are school-owned devices managed through MDM or endpoint management?
- type: single_select
- options: yes most, yes some, no, unknown
- status: core
- condition trigger: ask if managed staff or student devices are in scope
- report outputs: findings by domain, endpoint management summary, action plan
- deterministic rule impact: some, no, or unknown creates endpoint management finding; severity may vary by total device count and 1:1 status

#### 5.6 Is there a documented standard for staff device provisioning?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if staff devices are in scope
- report outputs: operational readiness summary, findings by domain, action plan
- deterministic rule impact: partial, no, or unknown creates provisioning/process maturity finding

#### 5.7 Can staff devices be set up quickly and consistently using a defined process or toolset?
- type: single_select
- options: yes, partially, no, unknown
- status: core
- condition trigger: ask if staff devices are in scope
- report outputs: operational readiness summary, action plan, executive summary supportability notes
- deterministic rule impact: partially, no, or unknown strengthens provisioning maturity finding and may drive standardization action

#### 5.8 Are staff devices standardized on one operating system or a small number of supported builds?
- type: single_select
- options: yes, partially, no, unknown
- status: optional
- condition trigger: ask if staff devices are in scope
- report outputs: endpoint profile, supportability notes, appendix
- deterministic rule impact: no or unknown may contribute to supportability watch finding, but should not be standalone critical in v1

#### 5.9 Is there a defined refresh cycle for major device categories?
- type: single_select
- options: yes documented, informal, no, unknown
- status: core
- condition trigger: ask if school-owned devices are in scope
- report outputs: lifecycle summary, roadmap, action plan, executive summary
- deterministic rule impact: informal, no, or unknown creates lifecycle planning finding and refresh planning action

#### 5.10 Are there known devices beyond supported OS versions or manufacturer support?
- type: single_select
- options: none known, some, many, unknown
- status: core
- condition trigger: ask if school-owned devices are in scope
- report outputs: lifecycle risks, key findings, action plan, executive summary
- deterministic rule impact: some, many, or unknown creates lifecycle/supportability finding; many may raise severity to urgent depending on scope

#### 5.11 Are device warranties or support coverage tracked?
- type: single_select
- options: yes, partial, no, unknown
- status: optional
- condition trigger: ask if school-owned devices are in scope
- report outputs: lifecycle notes, budget planning notes, appendix
- deterministic rule impact: partial, no, or unknown contributes to lifecycle planning watch finding

#### 5.12 Are spares, loaners, or emergency replacement processes defined?
- type: single_select
- options: yes, partial, no, unknown
- status: optional
- condition trigger: ask if student or staff devices are operationally important
- report outputs: operational readiness summary, action plan, appendix
- deterministic rule impact: partial, no, or unknown may contribute to continuity/supportability finding, especially in 1:1 environments

#### 5.13 Is there a documented decommissioning or disposal process for retired devices?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if school-owned devices are in scope
- report outputs: operational readiness summary, lifecycle findings, action plan
- deterministic rule impact: partial, no, or unknown creates lifecycle/process maturity finding

#### 5.14 How many years does a staff device typically remain in service?
- type: number or short_text
- status: optional
- condition trigger: ask if staff devices are in scope
- report outputs: lifecycle summary, budget planning notes, roadmap context
- deterministic rule impact: contextual only in v1; supports future lifecycle benchmarking

#### 5.15 Do different student grades receive different device types?
- type: single_select
- options: yes, no, unknown
- status: optional
- condition trigger: ask if student devices are in scope
- report outputs: student device profile, appendix, planning notes
- deterministic rule impact: contextual only

#### 5.16 What is the rationale for different student device types by grade or program?
- type: long_text
- status: conditional
- condition trigger: ask if 5.15 is yes
- report outputs: planning notes, executive summary context, appendix
- deterministic rule impact: contextual only; may support narrative explanation of device strategy

#### 5.17 Are printers, specialty devices, and classroom technology tracked consistently?
- type: single_select
- options: yes, partial, no, unknown
- status: optional
- condition trigger: ask if printers, AV, or specialty classroom devices are in scope
- report outputs: environment overview, appendix gaps list, supportability notes
- deterministic rule impact: partial, no, or unknown contributes to peripheral visibility watch finding

#### 5.18 How many large multi-function printers or copier-class devices does the school have?
- type: count
- status: optional
- condition trigger: ask if printing is in scope
- report outputs: environment overview, printing profile, appendix
- deterministic rule impact: contextual only

#### 5.19 How many smaller desktop or small-office printers does the school have?
- type: count
- status: optional
- condition trigger: ask if printing is in scope
- report outputs: printing profile, supportability notes, appendix
- deterministic rule impact: contextual only; may inform later printing rationalization opportunities

---

## Section 6: Core Systems, Servers, Vendors, and Contracts

### Purpose
Capture the systems the school depends on, the server environment if present, and whether vendor relationships and renewal risks are visible.

### Key outputs
- vendor visibility
- application and infrastructure visibility
- renewal/calendar items
- concentration risk indicators

### Implementation note for this section
This section balances school-specific application discovery with practical infrastructure and contract visibility. It should identify operational dependencies without turning into a full CMDB.

### Question catalog

#### 6.1 What Student Information System (SIS) does the school use?
- type: short_text
- status: core
- condition trigger: none
- report outputs: core systems profile, environment overview, appendix
- deterministic rule impact: platform identification only; high-value context for school environment summary

#### 6.2 What Learning Management System (LMS) does the school use?
- type: short_text
- status: core
- condition trigger: none
- report outputs: core systems profile, environment overview, appendix
- deterministic rule impact: platform identification only

#### 6.3 Is there a list of core systems used by the school?
- type: single_select
- options: yes current, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, systems visibility summary, action plan
- deterministic rule impact: partial, no, or unknown creates core systems visibility finding

#### 6.4 Does that list include purpose, owner, vendor, renewal date, and admin access method?
- type: single_select
- options: yes fully, partial, no, unknown
- status: core
- condition trigger: ask if 6.3 is yes current or partial
- report outputs: findings by domain, renewal visibility notes, appendix gaps list, action plan
- deterministic rule impact: partial, no, or unknown increases severity of systems/vendor visibility finding

#### 6.5 Can you list the school's major software subscriptions and services?
- type: list_of_items
- status: optional
- condition trigger: none
- report outputs: subscription appendix, environment overview, planning notes
- deterministic rule impact: inventory seed only in v1; not a direct finding by itself

#### 6.6 For major software subscriptions, are cost, purpose, renewal timing, and primary user groups tracked?
- type: single_select
- options: yes fully, partial, no, unknown
- status: optional
- condition trigger: ask if major software subscriptions exist
- report outputs: governance summary, renewal planning notes, appendix gaps list
- deterministic rule impact: partial, no, or unknown contributes to subscription governance watch finding

#### 6.7 For major education or student-data systems, is FERPA or COPPA review status known?
- type: single_select
- options: yes for most, partial, no, unknown
- status: optional
- condition trigger: ask if student-data systems or educational apps are in use
- report outputs: compliance visibility notes, governance summary, appendix gaps list
- deterministic rule impact: partial, no, or unknown creates compliance visibility gap finding when paired with unclear software approval process

#### 6.8 Are contract renewal dates tracked in a calendar or system?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if recurring vendor contracts or subscriptions exist, which is effectively always in v1
- report outputs: renewal planning summary, action plan, annual follow-up calendar
- deterministic rule impact: partial, no, or unknown creates renewal visibility/planning finding

#### 6.9 Are vendor support escalation paths documented?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if third-party vendors support critical systems
- report outputs: continuity findings, key risks, action plan
- deterministic rule impact: partial, no, or unknown creates vendor support dependency finding

#### 6.10 Are there any single-vendor or single-person dependencies that create operational risk?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: key risks, executive summary, findings by domain, action plan
- deterministic rule impact: yes creates dependency-risk finding; unknown may strengthen visibility concern when documentation is weak

#### 6.11 Are there known tools or services the school is paying for but not actively using?
- type: yes_no_unknown plus notes
- status: optional
- condition trigger: none
- report outputs: planning notes, governance summary, appendix
- deterministic rule impact: yes may create optimization opportunity note, but should not be central to v1 risk scoring

#### 6.12 Who is the school's phone or voice service provider?
- type: short_text
- status: optional
- condition trigger: none
- report outputs: vendor appendix, environment overview, support contacts profile
- deterministic rule impact: display only in v1

#### 6.13 How many servers are currently in use?
- type: count
- status: conditional
- condition trigger: ask if on-premises or self-managed server infrastructure exists
- report outputs: infrastructure profile, server scope summary, appendix
- deterministic rule impact: contextual only; enables later server-specific interpretation

#### 6.14 Is there a documented inventory of servers including model, serial, role, location, operating system, and support status?
- type: single_select
- options: yes current, partial, no, unknown
- status: conditional
- condition trigger: ask if 6.13 is greater than 0 or server infrastructure exists
- report outputs: findings by domain, lifecycle summary, appendix gaps list, action plan
- deterministic rule impact: partial, no, or unknown creates server visibility and supportability finding

#### 6.15 Is the purpose of each server clearly documented?
- type: single_select
- options: yes, partial, no, unknown
- status: conditional
- condition trigger: ask if server infrastructure exists
- report outputs: findings by domain, appendix gaps list, action plan
- deterministic rule impact: partial, no, or unknown increases severity of server visibility finding

#### 6.16 Are server administrative access methods documented and available to the school?
- type: single_select
- options: yes full, partial, no, unknown
- status: conditional
- condition trigger: ask if server infrastructure exists
- report outputs: key risks, continuity findings, action plan
- deterministic rule impact: partial, no, or unknown creates server access/control dependency finding

#### 6.17 Is there a defined server patching or update cycle?
- type: single_select
- options: yes documented, informal, no, unknown
- status: conditional
- condition trigger: ask if server infrastructure exists
- report outputs: security findings, operational readiness summary, action plan
- deterministic rule impact: informal, no, or unknown creates server maintenance/process finding

#### 6.18 Are server warranties or support coverage known?
- type: single_select
- options: yes, partial, no, unknown
- status: conditional
- condition trigger: ask if physical or vendor-supported server infrastructure exists
- report outputs: lifecycle summary, budget planning notes, appendix
- deterministic rule impact: partial, no, or unknown contributes to server lifecycle watch finding

#### 6.19 Is there a hardware refresh or lifecycle plan for servers?
- type: single_select
- options: yes documented, informal, no, unknown
- status: conditional
- condition trigger: ask if server infrastructure exists
- report outputs: lifecycle findings, roadmap, action plan
- deterministic rule impact: informal, no, or unknown creates server lifecycle planning finding

---
## Section 7: Data Protection, Backup, and Recovery

### Purpose
Understand whether data protection exists, is documented, and can be relied upon during an incident.

### Key outputs
- continuity findings
- backup confidence status
- recovery planning actions

### Implementation note for this section
This section should favor verifiable recovery readiness over optimistic assumptions. In v1, backup existence matters, but restore confidence and clarity of scope matter more.

### Question catalog

#### 7.1 What backup service or platform is currently used?
- type: short_text
- status: core
- condition trigger: none
- report outputs: backup profile, environment overview, appendix
- deterministic rule impact: platform identification only; supports backup coverage interpretation

#### 7.2 Are backups in place for critical systems or data sets?
- type: single_select
- options: yes confirmed, maybe or assumed, no, unknown
- status: core
- condition trigger: none
- report outputs: key risks, continuity findings, executive summary, action plan
- deterministic rule impact: maybe or assumed, no, or unknown creates backup confidence finding; no may elevate severity to urgent depending on critical systems in scope

#### 7.3 Is there a documented list of what is backed up and what is not?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if backups exist or are believed to exist
- report outputs: findings by domain, appendix gaps list, action plan
- deterministic rule impact: partial, no, or unknown creates backup scope visibility finding

#### 7.4 Do backups cover servers?
- type: single_select
- options: yes, partial, no, unknown, not_applicable
- status: conditional
- condition trigger: ask if server infrastructure exists
- report outputs: backup coverage summary, findings by domain, appendix
- deterministic rule impact: partial, no, or unknown increases severity of backup coverage finding for server environments

#### 7.5 Do backups cover individual staff devices where appropriate?
- type: single_select
- options: yes, partial, no, unknown, not_applicable
- status: conditional
- condition trigger: ask if staff devices store important local data or if endpoint backup is expected
- report outputs: backup coverage summary, operational readiness notes, appendix
- deterministic rule impact: partial, no, or unknown may create endpoint data protection watch finding depending on device model and workflow

#### 7.6 Do backups cover critical cloud or online school data where appropriate?
- type: single_select
- options: yes, partial, no, unknown, not_applicable
- status: core
- condition trigger: ask if critical cloud systems or online school data are in use, which is effectively common in v1
- report outputs: backup coverage summary, continuity findings, action plan
- deterministic rule impact: partial, no, or unknown creates cloud data protection visibility finding

#### 7.7 Is backup success reviewed regularly?
- type: single_select
- options: yes, irregularly, no, unknown
- status: core
- condition trigger: ask if backups exist or are believed to exist
- report outputs: continuity findings, action plan, operational readiness summary
- deterministic rule impact: irregularly, no, or unknown creates backup operations maturity finding

#### 7.8 Has a restore test been performed and documented within the last 12 months?
- type: single_select
- options: yes, more than 12 months ago, no, unknown
- status: core
- condition trigger: ask if backups exist or are believed to exist
- report outputs: key risks, continuity findings, executive summary, action plan
- deterministic rule impact: more than 12 months ago, no, or unknown creates restore-confidence finding; no or unknown may elevate severity when backup scope is also unclear

#### 7.9 How often are restore tests performed?
- type: single_select
- options: quarterly, twice per year, annually, less than annually, never, unknown
- status: conditional
- condition trigger: ask if 7.8 is yes or more than 12 months ago
- report outputs: continuity maturity notes, appendix, action plan
- deterministic rule impact: less than annually, never, or unknown may strengthen restore-confidence finding but should not replace 7.8 as the primary control question

#### 7.10 Is there a defined recovery priority for critical systems?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: ask if more than one critical system exists, which is effectively common in v1
- report outputs: continuity findings, action plan, executive summary
- deterministic rule impact: partial, no, or unknown creates recovery-prioritization finding

#### 7.11 Is there a written incident or disaster response reference for IT operations?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: continuity findings, operational readiness summary, action plan
- deterministic rule impact: partial, no, or unknown creates incident/disaster readiness finding

#### 7.12 Are critical admin credentials and recovery materials accessible in an emergency?
- type: single_select
- options: yes securely, partially, no, unknown
- status: core
- condition trigger: none
- report outputs: key risks, continuity findings, action plan
- deterministic rule impact: partially, no, or unknown creates emergency access continuity finding; no may raise severity substantially
- rule reference: R7-012

#### 7.13 How far back can a backup restore go and still produce data the school could actually use?
- type: single_select
- options: less than 1 week, 1 to 2 weeks, 2 to 4 weeks, 1 to 3 months, more than 3 months, unknown
- status: core
- condition trigger: ask if backups exist or are believed to exist
- report outputs: continuity findings, backup maturity summary, appendix
- deterministic rule impact: unknown creates backup retention visibility finding; answer is used to evaluate whether restore test frequency in 7.14 is appropriate relative to the useful recovery window
- rule reference: R7-013

#### 7.14 Are restore tests performed at least once within every useful recovery window period?
- type: single_select
- options: yes, no, unknown
- status: conditional
- condition trigger: ask if 7.13 is answered (not unknown) AND 7.8 is not `no`
- report outputs: continuity findings, backup maturity summary, action plan
- deterministic rule impact: no or unknown creates restore frequency alignment finding; the finding is framed around the specific window identified in 7.13 rather than a generic calendar interval
- rule reference: R7-014

---

## Section 8: Security Operations, Filtering, and Safeguards

### Purpose
Capture practical security maturity without requiring a full formal audit.

### Key outputs
- baseline security posture
- urgent control gaps
- practical risk reduction actions

### Implementation note for this section
This section should identify obvious control gaps and visibility gaps without pretending to be a full security assessment. The emphasis is on baseline hygiene, operational response, and student-facing protections where applicable.

### Question catalog

#### 8.1 What endpoint protection or antivirus platform is in use?
- type: short_text
- status: core
- condition trigger: ask if endpoints are in scope
- report outputs: security profile, environment overview, appendix
- deterministic rule impact: control identification only; supports interpretation of endpoint protection coverage

#### 8.2 Is endpoint protection deployed on supported devices?
- type: single_select
- options: yes most, yes some, no, unknown
- status: core
- condition trigger: ask if endpoints are in scope
- report outputs: security findings, key risks, action plan, executive summary
- deterministic rule impact: some, no, or unknown creates endpoint security control finding; no or unknown may elevate severity depending on device count and exposure

#### 8.3 Is patching for endpoints and servers managed on a defined cadence?
- type: single_select
- options: yes documented, informal, no, unknown
- status: core
- condition trigger: ask if endpoints or servers are in scope
- report outputs: security findings, operational readiness summary, action plan
- deterministic rule impact: informal, no, or unknown creates patch-management finding

#### 8.4 Are critical network and security devices reviewed for firmware currency?
- type: single_select
- options: yes regularly, irregularly, no, unknown
- status: core
- condition trigger: ask if network/security infrastructure exists
- report outputs: security findings, lifecycle summary, action plan
- deterministic rule impact: irregularly, no, or unknown creates infrastructure maintenance/security finding

#### 8.5 Is a web filter or content filter in place?
- type: single_select
- options: yes for students only, yes for students and staff, limited or partial, no, unknown
- status: core
- condition trigger: ask if internet access is provided to students or staff, which is effectively always in v1
- report outputs: security profile, student-safety context, findings by domain, action plan
- deterministic rule impact: limited or partial, no, or unknown creates filtering visibility/control finding; no may be more significant in student device environments

#### 8.6 Does the school use a student safety monitoring platform for self-harm, bullying, or related behavioral risk signals?
- type: single_select plus notes
- options: yes, no, unknown
- status: optional
- condition trigger: ask if student devices or student online systems are in scope
- report outputs: student-safety context, security profile, appendix
- deterministic rule impact: primarily contextual in v1; no should not be treated as an automatic negative finding unless required by school policy or expectations

#### 8.7 Are filtering, web protection, or student safety controls documented well enough to understand coverage and gaps?
- type: single_select
- options: yes, partial, no, unknown
- status: optional
- condition trigger: ask if 8.5 or 8.6 indicates controls exist or are expected
- report outputs: documentation gaps list, security maturity notes, appendix
- deterministic rule impact: partial, no, or unknown contributes to visibility watch finding for student protection controls

#### 8.8 Is there a documented process for responding to suspicious activity, malware, or account compromise?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: security findings, operational readiness summary, action plan, key risks
- deterministic rule impact: partial, no, or unknown creates incident-response process finding

#### 8.9 Are logs or alerts from key systems reviewed by someone?
- type: single_select
- options: yes regularly, sometimes, no, unknown
- status: optional
- condition trigger: ask if logs/alerts are available from core systems
- report outputs: security maturity notes, operations summary, appendix
- deterministic rule impact: sometimes, no, or unknown may contribute to detection/visibility watch finding

#### 8.10 Does the school carry cyber insurance?
- type: single_select
- options: yes, no, unknown
- status: optional
- condition trigger: none
- report outputs: risk-transfer note, governance summary, appendix
- deterministic rule impact: contextual only in v1; may influence roadmap recommendations but should not be a primary control finding

#### 8.11 Are there known unresolved security concerns today?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: executive summary, key risks, findings by domain, action plan
- deterministic rule impact: yes creates active security concern finding and may elevate action priority; unknown may contribute to visibility concern when other controls are weak

---

## Section 9: Documentation and Operational Readiness

### Purpose
Measure whether the environment is understandable and supportable by more than one person.

### Key outputs
- documentation maturity
- operational resilience findings
- suggested documentation tasks

### Implementation note for this section
This section is foundational to the whole framework. Poor documentation here should often amplify the severity of findings elsewhere because it reduces confidence, recoverability, and transferability.

### Question catalog

#### 9.1 Is there a central location where IT documentation is stored?
- type: single_select
- options: yes well used, yes but inconsistent, no, unknown
- status: core
- condition trigger: none
- report outputs: findings by domain, documentation maturity summary, action plan, appendix gaps list
- deterministic rule impact: inconsistent, no, or unknown creates central documentation maturity finding

#### 9.2 Are network, systems, and vendor documents kept in a reasonably current state?
- type: single_select
- options: yes, partly, no, unknown
- status: core
- condition trigger: ask if documentation exists or is expected
- report outputs: findings by domain, documentation maturity summary, action plan
- deterministic rule impact: partly, no, or unknown creates documentation currency finding

#### 9.3 Are standard operating procedures documented for common recurring tasks?
- type: single_select
- options: yes, partial, no, unknown
- status: core
- condition trigger: none
- report outputs: operational readiness summary, findings by domain, action plan
- deterministic rule impact: partial, no, or unknown creates SOP/process maturity finding

#### 9.4 Is there a known process for documenting changes after projects or incidents?
- type: single_select
- options: yes, informal, no, unknown
- status: core
- condition trigger: none
- report outputs: operational readiness summary, documentation findings, action plan
- deterministic rule impact: informal, no, or unknown creates change-documentation process finding

#### 9.5 Could a qualified third party understand the environment from existing documentation?
- type: single_select
- options: yes, partially, no, unknown
- status: core
- condition trigger: none
- report outputs: executive summary, documentation maturity summary, key risks, action plan
- deterministic rule impact: partially, no, or unknown creates transferability/supportability finding and often strengthens key-person dependency findings

#### 9.6 Are there major knowledge areas that currently live only in one person's head?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: key risks, executive summary, findings by domain, action plan
- deterministic rule impact: yes creates knowledge-concentration finding; unknown may strengthen documentation visibility concern

---

## Section 10: Near-Term Priorities and Planning Inputs

### Purpose
Capture what the IT person already knows they need to do, what is blocking them, and any context that helps the engine sequence and prioritize the action plan correctly. This section does not override deterministic findings — it calibrates and contextualizes them.

### Key outputs
- user-identified priority shortlist
- known project and deadline context
- action plan tuning inputs
- overall data confidence assessment

### Implementation note for this section
Answers here should be used to emphasize and sequence recommendations already supported by objective assessment data, not to suppress or override findings the respondent may not want to see. This section also closes the assessment with a self-assessment of data quality, which affects confidence weighting across the full report.

### Question catalog

#### 10.1 List up to five known IT problems or projects you already know need attention
- type: list_of_items (structured list, up to 5 entries)
- status: core
- condition trigger: none
- report outputs: executive summary, action plan prioritization notes, roadmap framing
- deterministic rule impact: does not create findings by itself; used to sort or emphasize recommendations already supported by assessment data; items not supported by assessment data are noted but not automatically elevated

#### 10.2 Are there IT projects or initiatives already approved or planned for the next 12 months?
- type: list_of_items
- status: core
- condition trigger: none
- report outputs: roadmap, annual follow-up calendar, planning context, appendix
- deterministic rule impact: contextual only; may alter timing and bundling of recommended actions where overlap exists

#### 10.3 Are there known deadlines, audits, renewals, or compliance events coming up that IT needs to be ready for?
- type: list_of_items
- status: core
- condition trigger: none
- report outputs: annual follow-up calendar, action plan timing, executive summary context
- deterministic rule impact: contextual only; influences recommended timing and sequencing of actions

#### 10.4 What changes are expected before the next school year?
- type: long_text
- status: core
- condition trigger: none
- report outputs: roadmap, seasonal planning notes, executive summary context
- deterministic rule impact: contextual only; helps align summer and pre-year recommendations with known environmental shifts such as new grade levels, device rollouts, staffing changes, or facility changes

#### 10.5 Is leadership or administration expecting a budget, refresh, or improvement plan from IT in the near future?
- type: yes_no_unknown plus notes
- status: core
- condition trigger: none
- report outputs: roadmap framing, action plan, executive summary context
- deterministic rule impact: yes may increase emphasis on budget-ready and roadmap recommendations; no does not suppress objective needs identified elsewhere in the assessment

#### 10.6 Are there known obstacles, constraints, or dependencies that will affect IT's ability to act on findings from this assessment?
- type: long_text
- status: optional
- condition trigger: none
- report outputs: executive summary context, action plan framing notes, appendix
- deterministic rule impact: contextual only; used to annotate the action plan with known blockers rather than alter scoring

#### 10.7 Overall, how confident are you in the accuracy of the information you provided across this assessment?
- type: single_select
- options: high — most answers are documented or verified, moderate — most answers are based on recall or staff reports, low — many answers were estimated or unknown, mixed — confidence varies significantly by section
- status: core
- condition trigger: none
- report outputs: executive summary caveat, appendix data quality note, confidence weighting input for findings
- deterministic rule impact: low or mixed reduces overall report confidence level and may widen the "Research Needed" classification across sections that had high unknown rates; does not suppress findings but adds a visible data-quality caveat to the report

#### 10.8 Are there specific sections or topic areas where you feel the data provided was particularly incomplete or uncertain?
- type: list_of_items or long_text
- status: optional
- condition trigger: recommended if 10.7 is moderate, low, or mixed
- report outputs: appendix data quality note, per-section confidence annotations
- deterministic rule impact: user-flagged sections receive an additional "respondent-flagged uncertainty" annotation in findings and recommendations; does not duplicate or override the automatic unknown threshold logic



---
## Normalized Answer Framework for Module 1

### Purpose
This section defines a first-pass normalization model so questionnaire responses can be stored consistently, scored deterministically, and reused in reports without every question requiring a custom parser.

This is a working normalization pass, not a final locked schema. The goal is to create a practical standard that is good enough to support programming and rule-writing.

---

### Design principles for normalization
1. Store the **raw answer** exactly as entered or selected.
2. Store a **normalized value** in a predictable shape.
3. Keep **unknown**, **not applicable**, and **unanswered** distinct.
4. Do not hide ambiguity by forcing it into yes/no.
5. Keep notes separate from the main normalized value.
6. Prefer reusable enums over question-specific custom labels.

---

### Standard answer record shape
Each answer should normalize into a structure like:

- question_id
- raw_answer
- normalized_type
- answer_status
- normalized_value
- normalized_flags[]
- notes
- evidence_status
- answered_by
- answered_on

---

### Standard answer_status values
- answered
- unknown
- not_applicable
- unanswered

### Guidance
- **answered** means a usable value was provided.
- **unknown** means the respondent explicitly does not know.
- **not_applicable** means the question does not apply to the environment.
- **unanswered** means the question was skipped, hidden, or not yet completed.

---

### Standard normalized_type values
- boolean
- enum
- integer
- decimal
- text
- text_list
- object
- date

---

### Standard evidence_status values
- documented
- observed
- reported_by_staff
- estimated
- unknown

This should remain separate from the answer itself. A weakly supported answer may still be valuable, but it should carry lower confidence.

---

## Common normalization patterns

### 1. yes_no_unknown
Use for questions where the core meaning is binary but uncertainty must remain visible.

#### Normalized shape
- normalized_type: boolean
- normalized_value: true | false | null
- answer_status:
  - answered when value is true or false
  - unknown when respondent chose unknown

#### Example
"Does the school carry cyber insurance?"
- yes -> normalized_value = true
- no -> normalized_value = false
- unknown -> normalized_value = null, answer_status = unknown

---

### 2. yes_no_unknown plus notes
Use when the binary state matters, but additional explanation may affect narrative or follow-up.

#### Normalized shape
- normalized_type: object
- normalized_value:
  - value: true | false | null
  - notes: string | null

#### Example
"Are there known unresolved security concerns today?"
- yes + notes -> value = true, notes captured
- unknown -> value = null, answer_status = unknown

---

### 3. single_select with maturity-style options
Many questions use variants like:
- yes current / partial / no / unknown
- yes documented / informal / no / unknown
- yes full / partial / no / unknown

These should normalize to a shared enum whenever possible.

#### Recommended shared enum family
- full
- partial
- none
- informal
- outdated
- mixed
- limited
- current
- unknown

#### Rule
Keep the original label for display, but map it to a canonical value for scoring.

#### Example mappings
- yes current -> current
- yes current, full detail -> full
- yes fully -> full
- yes -> full
- partial -> partial
- yes but limited use -> limited
- informal -> informal
- yes outdated -> outdated
- mixed -> mixed
- no -> none
- unknown -> unknown

#### Normalized shape
- normalized_type: enum
- normalized_value: one canonical enum value
- answer_status:
  - answered for all enum values except unknown
  - unknown when canonical value is unknown

---

### 4. single_select with security/control coverage options
Use for coverage questions like:
- yes all privileged
- some privileged
- no
- unknown

#### Recommended shared enum family
- full
- partial
- none
- unknown

#### Example mappings
- yes all privileged -> full
- yes most -> full
- yes some -> partial
- some privileged -> partial
- limited or partial -> partial
- no -> none
- unknown -> unknown

---

### 5. single_select with resilience or support states
Use for questions like:
- yes automatic
- yes manual
- no
- unknown

#### Recommended shared enum family
- automatic
- manual
- none
- unknown

#### Example
"Is there internet failover or redundancy?"
- yes automatic -> automatic
- yes manual -> manual
- no -> none
- unknown -> unknown

---

### 6. count
Use for numeric totals such as number of sites, devices, servers, or printers.

#### Normalized shape
- normalized_type: integer
- normalized_value: integer >= 0
- answer_status:
  - answered if integer present
  - unknown if explicitly unknown

#### Guidance
- Store counts as integers only.
- If a respondent gives an approximate count, store the integer and add a flag like `approximate` in normalized_flags.

#### Example flags
- approximate
- estimated

---

### 7. short_text
Use when the answer is a single freeform value such as vendor name, platform name, or website.

#### Normalized shape
- normalized_type: text
- normalized_value: trimmed string

#### Guidance
- Trim whitespace.
- Preserve capitalization for display.
- Optionally store a lowercase compare key for matching/report grouping.

---

### 8. long_text
Use for explanatory narrative, rationale, planning notes, or context.

#### Normalized shape
- normalized_type: text
- normalized_value: trimmed string

#### Guidance
- Do not over-normalize.
- This field is mainly for report narrative, notes, and future tagging.
- Deterministic rules should not depend heavily on long_text unless paired with a more structured answer.

---

### 9. list_of_items
Use for systems, subscriptions, deadlines, projects, or site-by-site details.

#### Normalized shape
- normalized_type: text_list
- normalized_value: array of strings

#### Guidance
- Split on line breaks, bullets, or commas where practical.
- Trim blank entries.
- Preserve original wording.

#### Example
"Google Workspace, Blackbaud, GoGuardian"
becomes
- ["Google Workspace", "Blackbaud", "GoGuardian"]

---

### 10. single_select plus notes
Use when the main answer must remain structured but the notes explain exceptions.

#### Normalized shape
- normalized_type: object
- normalized_value:
  - value: canonical enum or boolean
  - notes: string | null

#### Example
"Does the school have a firewall, and if so what platform or brand is used?"
- yes + Fortinet -> value = true, notes = "Fortinet"
- no -> value = false
- unknown -> value = null, answer_status = unknown

---

## Canonical enum sets for Module 1

### A. coverage_level
- full
- partial
- none
- unknown

Use for:
- MFA coverage
- endpoint protection coverage
- MDM coverage
- backup coverage variants
- support coverage variants

### B. documentation_maturity
- current
- partial
- outdated
- none
- unknown

Use for:
- network diagrams
- inventories
- maps
- documentation currency questions

### C. process_maturity
- documented
- informal
- none
- unknown

Use for:
- onboarding
- offboarding
- patching cycle
- change documentation process
- provisioning process

### D. confidence_level
- confirmed
- assumed
- estimated
- high
- moderate
- low
- mixed
- unknown

Use for:
- backup presence
- runtime knowledge
- infrastructure certainty
- overall assessment self-assessment (question 10.6)

### E. resilience_mode
- automatic
- manual
- none
- unknown

Use for:
- ISP failover
- other future failover-style questions

### F. condition_state
- healthy
- watch
- concern
- urgent
- unknown

Note: this set is for derived findings, not direct answers.

### G. restore_window
- less_than_1_week
- 1_to_2_weeks
- 2_to_4_weeks
- 1_to_3_months
- more_than_3_months
- unknown

Use for:
- useful backup recovery window (question 7.13)

---

## Suggested normalized mappings by repeated question family

### Family: "yes current / partial / no / unknown"
Map to:
- yes current -> current
- partial -> partial
- no -> none
- unknown -> unknown

### Family: "yes current / yes outdated / no / unknown"
Map to:
- yes current -> current
- yes outdated -> outdated
- no -> none
- unknown -> unknown

### Family: "yes fully / partial / no / unknown"
Map to:
- yes fully -> full
- partial -> partial
- no -> none
- unknown -> unknown

### Family: "yes documented / informal / no / unknown"
Map to:
- yes documented -> documented
- informal -> informal
- no -> none
- unknown -> unknown

### Family: "yes most / yes some / no / unknown"
Map to:
- yes most -> full
- yes some -> partial
- no -> none
- unknown -> unknown

### Family: "none known / some / many / unknown"
Map to:
- none known -> none
- some -> partial
- many -> full
- unknown -> unknown

Implementation note: in this family, `full` does **not** mean healthy. It means the condition is fully present. This family should usually be paired with a rule context such as `unsupported_device_exposure` so the meaning stays clear.

---

## Question-specific normalization notes for Module 1

### Profile questions
Questions like school name, address, website, report author, mission statement, SIS, LMS, ISP, phone provider, backup platform, antivirus platform should normalize as text.

### Count questions
Questions like sites, buildings, devices, servers, printers should normalize as integer values.

### Platform/vendor identification questions
Questions like wireless platform, firewall brand, wired network platform should normalize as text and may optionally also create a standardized compare_key for grouping similar answers.

### Risk/context questions with notes
Questions like unresolved security concerns, single-vendor dependency, connectivity pain points, budget constraints should normalize as object values with:
- value: boolean or enum
- notes: text

---

## Recommended normalized flags
Use normalized_flags sparingly to preserve useful nuance.

Suggested flags:
- approximate
- estimated
- inherited_from_vendor
- managed_by_msp
- needs_follow_up
- respondent_uncertain
- not_school_controlled

---

## Recommendation for rule writing
When writing deterministic rules, prefer this order:
1. check answer_status
2. check normalized_value
3. check evidence_status
4. inspect notes only if needed

This keeps rules explainable and avoids brittle text parsing.

---

## Recommendation for implementation
For v1, normalize at two levels:

### Level 1: generic parser rules
A reusable normalization layer by answer type and option family.

### Level 2: question overrides
Only use question-specific normalization when the generic parser is not enough.

This will keep the engine maintainable.

---

## What does not need to be fully normalized yet
The following can remain lightly structured in the first build:
- mission statement
- rationale text
- project lists
- planning notes
- narrative comments

These can still appear in reports without driving deterministic logic.

---

## Next normalization step after this pass
After this framework, the next refinement should be a compact per-question table with columns like:
- question_id
- raw type
- canonical enum family
- normalized_type
- normalized_value example
- notes allowed
- answer_status behavior

That will be the bridge from design document to implementation schema.

---

## Per-Question Normalization Table for Module 1

### Purpose
This section translates the normalization framework into a compact implementation-facing table for every question in Module 1.

### Column guide
- **Norm Type** = normalized_type
- **Enum Family** = canonical enum set to use when applicable
- **Notes** = whether a separate notes field is expected/allowed
- **Status Behavior** = expected answer_status behavior
- **Example** = example normalized_value

---

## Section 1 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 1.1 | School name | text | — | no | answered/unanswered | `"St. Mark School"` |
| 1.2 | School address | text | — | no | answered/unanswered | `"123 Main St, Orlando, FL"` |
| 1.3 | Main phone | text | — | no | answered/unanswered | `"407-555-1234"` |
| 1.4 | Website | text | — | no | answered/unanswered | `"https://school.org"` |
| 1.5 | Mission statement | text | — | no | answered/unanswered | `"To cultivate wisdom and service..."` |
| 1.6 | Logo/crest available | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "PNG on file" }` |
| 1.7 | Report author name and role | text | — | no | answered/unanswered | `"Joshua Bierman, Director of Technology"` |
| 1.8 | Number of sites/campuses | integer | — | no | answered/unknown/unanswered | `2` |
| 1.9 | Number of buildings | integer | — | no | answered/unknown/unanswered | `4` |
| 1.10 | Buildings per site | text_list | — | no | answered/unanswered | `["Main Campus: 3", "Athletics Campus: 1"]` |
| 1.11 | Grades served | text_list | — | no | answered/unanswered | `["PK", "K-5", "6-8", "9-12"]` |
| 1.12 | Student enrollment | integer | — | no | answered/unknown/unanswered | `640` |
| 1.13 | Faculty/staff count | integer | — | no | answered/unknown/unanswered | `92` |
| 1.14 | Total managed devices | integer | — | no | answered/unknown/unanswered | `780` |
| 1.15 | Device categories in scope | text_list | — | no | answered/unanswered | `["staff laptops", "student laptops", "printers", "servers"]` |
| 1.16 | Upcoming calendar events affecting IT | text_list | — | yes | answered/unanswered | `["summer refresh", "state testing", "accreditation visit"]` |

---

## Section 2 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 2.1 | Primary support model | enum | support_model | no | answered/unknown/unanswered | `"hybrid_internal_msp"` |
| 2.2 | Named IT leader exists | boolean | boolean | no | answered/unknown/unanswered | `true` |
| 2.3 | Day-to-day responsibilities assigned | boolean | boolean | no | answered/unknown/unanswered | `false` |
| 2.4 | System owners documented | boolean | boolean | no | answered/unknown/unanswered | `true` |
| 2.5 | Vendor contacts/escalations documented | boolean | boolean | no | answered/unknown/unanswered | `false` |
| 2.6 | Formal IT budget | enum | budget_maturity | no | answered/unknown/unanswered | `"annual"` |
| 2.7 | Budget/staffing constraints this year | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "One open position and reduced hardware budget" }` |
| 2.8 | Shared credentials/emergency access documented and controlled | boolean | boolean | no | answered/unknown/unanswered | `false` |
| 2.9 | Another person could maintain operations for 2 weeks | enum | continuity_cover | no | answered/unknown/unanswered | `"partial"` |
| 2.10 | Recurring tasks tracked | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 2.11 | Ticketing system exists/in use | enum | coverage_level | no | answered/unknown/unanswered | `"none"` |
| 2.12 | Who approves new classroom software | text | — | yes | answered/unanswered | `"Academic leadership with IT review"` |

---

## Section 3 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 3.1 | Digital blueprints/floor plans exist | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 3.2 | Current network diagram | enum | documentation_maturity | no | answered/unknown/unanswered | `"current"` |
| 3.3 | Site/closet/rack maps exist | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 3.4 | AP physical locations known | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 3.5 | Wireless AP platform | text | — | no | answered/unanswered | `"Aruba"` |
| 3.6 | Firewall exists and brand | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Fortinet" }` |
| 3.7 | Wired network platform | text | — | no | answered/unanswered | `"Cisco Meraki"` |
| 3.8 | AP inventory with model/firmware | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 3.9 | Switch inventory with model/firmware | enum | documentation_maturity | no | answered/unknown/unanswered | `"none"` |
| 3.10 | Switch map exists | enum | documentation_maturity | no | answered/unknown/unanswered | `"current"` |
| 3.11 | Core network devices inventoried with support status | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 3.12 | Admin access to network infrastructure | enum | access_level | no | answered/unknown/unanswered | `"full"` |
| 3.13 | Number of internet connections | integer | — | no | answered/unknown/unanswered | `1` |
| 3.14 | ISP or ISPs | text_list | — | no | answered/unanswered | `["Spectrum"]` |
| 3.15 | Internet failover/redundancy | enum | resilience_mode | no | answered/unknown/unanswered | `"manual"` |
| 3.16 | Static public IPs | boolean | boolean | no | answered/unknown/unanswered | `true` |
| 3.17 | Firewall firmware/support status known | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 3.18 | Switch/wireless configs backed up/exportable | enum | coverage_level | no | answered/unknown/unanswered | `"full"` |
| 3.19 | Wireless coverage adequate | enum | service_quality | no | answered/unknown/unanswered | `"mixed"` |
| 3.20 | VLAN/segment purposes documented | enum | documentation_maturity | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 3.21 | UPS protection for critical equipment | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"full"` |
| 3.22 | UPS runtime known | enum | confidence_level | no | answered/unknown/unanswered/not_applicable | `"estimated"` |
| 3.23 | UPS monitored/network-connected | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"none"` |
| 3.24 | Network scanned/discovered regularly | enum | frequency_presence | no | answered/unknown/unanswered | `"regular"` |
| 3.25 | How often scanning/discovery occurs | enum | frequency_level | no | answered/unknown/unanswered/not_applicable | `"weekly"` |
| 3.26 | Connectivity pain points exist | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Gym and library Wi-Fi issues" }` |

---

## Section 4 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 4.1 | Primary identity/productivity platform | enum | identity_platform | no | answered/unknown/unanswered | `"google_workspace"` |
| 4.2 | Centralized login management in place | enum | directory_model | no | answered/unknown/unanswered | `"cloud"` |
| 4.3 | Staff onboarding documented | enum | process_maturity | no | answered/unknown/unanswered | `"documented"` |
| 4.4 | Staff offboarding documented | enum | process_maturity | no | answered/unknown/unanswered | `"informal"` |
| 4.5 | Student account lifecycle documented | enum | process_maturity | no | answered/unknown/unanswered/not_applicable | `"none"` |
| 4.6 | MFA on privileged accounts | enum | coverage_level | no | answered/unknown/unanswered | `"full"` |
| 4.7 | Reviewed list of global admins/privileged roles | enum | documentation_maturity | no | answered/unknown/unanswered | `"outdated"` |
| 4.8 | Shared accounts minimized/justified | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 4.9 | Password reset/recovery procedures documented | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 4.10 | Staff devices configured for automatic cloud file sync | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |

---

## Section 5 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 5.1 | Current managed device inventory exists | enum | documentation_maturity | no | answered/unknown/unanswered | `"current"` |
| 5.2 | Inventory includes required lifecycle fields | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 5.3 | School is 1:1 for student devices | enum | one_to_one_state | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 5.4 | Student devices go home | enum | take_home_state | no | answered/unknown/unanswered/not_applicable | `"some"` |
| 5.5 | Devices managed through MDM/endpoint management | enum | coverage_level | no | answered/unknown/unanswered | `"full"` |
| 5.6 | Staff device provisioning standard documented | enum | process_maturity | no | answered/unknown/unanswered/not_applicable | `"documented"` |
| 5.7 | Staff devices can be set up quickly/consistently | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 5.8 | Staff devices standardized | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"full"` |
| 5.9 | Refresh cycle defined | enum | process_maturity | no | answered/unknown/unanswered | `"informal"` |
| 5.10 | Unsupported devices present | enum | unsupported_device_exposure | no | answered/unknown/unanswered | `"some"` |
| 5.11 | Warranties/support coverage tracked | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 5.12 | Spares/loaners/emergency replacement defined | enum | coverage_level | no | answered/unknown/unanswered | `"none"` |
| 5.13 | Decommissioning/disposal process documented | enum | process_maturity | no | answered/unknown/unanswered | `"none"` |
| 5.14 | Typical staff device service life | integer | — | no | answered/unknown/unanswered | `5` |
| 5.15 | Different student device types by grade | enum | yes_no_unknown_enum | no | answered/unknown/unanswered/not_applicable | `"yes"` |
| 5.16 | Rationale for different student device types | text | — | no | answered/unanswered/not_applicable | `"Touch devices in lower school, laptops in upper school"` |
| 5.17 | Printers/specialty/classroom tech tracked consistently | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 5.18 | Large multi-function printer count | integer | — | no | answered/unknown/unanswered/not_applicable | `6` |
| 5.19 | Small printer count | integer | — | no | answered/unknown/unanswered/not_applicable | `18` |

---

## Section 6 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 6.1 | SIS used | text | — | no | answered/unanswered | `"Blackbaud SIS"` |
| 6.2 | LMS used | text | — | no | answered/unanswered | `"Canvas"` |
| 6.3 | Core systems list exists | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 6.4 | Core systems list includes owner/vendor/renewal/access | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"none"` |
| 6.5 | Major software subscriptions/services list | text_list | — | no | answered/unanswered | `["Google Workspace", "Blackbaud", "GoGuardian"]` |
| 6.6 | Subscription cost/purpose/renewal/users tracked | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 6.7 | FERPA/COPPA review status known | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 6.8 | Contract renewal dates tracked | enum | coverage_level | no | answered/unknown/unanswered | `"none"` |
| 6.9 | Vendor escalation paths documented | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 6.10 | Single-vendor or single-person dependencies exist | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Firewall managed only by MSP" }` |
| 6.11 | Paying for unused tools/services | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Unused Zoom Rooms license" }` |
| 6.12 | Phone/voice provider | text | — | no | answered/unanswered | `"RingCentral"` |
| 6.13 | Number of servers in use | integer | — | no | answered/unknown/unanswered/not_applicable | `3` |
| 6.14 | Server inventory with model/serial/role/location/OS/support | enum | documentation_maturity | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 6.15 | Server purpose clearly documented | enum | documentation_maturity | no | answered/unknown/unanswered/not_applicable | `"none"` |
| 6.16 | Server admin access methods documented and available | enum | access_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 6.17 | Defined server patch/update cycle | enum | process_maturity | no | answered/unknown/unanswered/not_applicable | `"informal"` |
| 6.18 | Server warranties/support known | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 6.19 | Server hardware refresh/lifecycle plan | enum | process_maturity | no | answered/unknown/unanswered/not_applicable | `"none"` |

---

## Section 7 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 7.1 | Backup platform used | text | — | no | answered/unanswered | `"Acronis"` |
| 7.2 | Backups in place for critical systems/data | enum | confidence_level | no | answered/unknown/unanswered | `"confirmed"` |
| 7.3 | Documented list of what is and is not backed up | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 7.4 | Backups cover servers | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"full"` |
| 7.5 | Backups cover staff devices where appropriate | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"none"` |
| 7.6 | Backups cover critical cloud/online school data | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 7.7 | Backup success reviewed regularly | enum | review_cadence | no | answered/unknown/unanswered/not_applicable | `"irregular"` |
| 7.8 | Restore test performed/documented in last 12 months | enum | restore_recency | no | answered/unknown/unanswered/not_applicable | `"older_than_12_months"` |
| 7.9 | Restore test frequency | enum | frequency_level | no | answered/unknown/unanswered/not_applicable | `"annually"` |
| 7.10 | Recovery priority defined for critical systems | enum | coverage_level | no | answered/unknown/unanswered | `"none"` |
| 7.11 | Written incident/disaster response reference exists | enum | process_maturity | no | answered/unknown/unanswered | `"partial"` |
| 7.12 | Critical admin credentials/recovery materials accessible in emergency | enum | coverage_level | no | answered/unknown/unanswered | `"partial"` |
| 7.13 | Useful backup recovery window | enum | restore_window | no | answered/unknown/unanswered/not_applicable | `"2_to_4_weeks"` |
| 7.14 | Restore tests performed within useful recovery window period | boolean | boolean | no | answered/unknown/unanswered/not_applicable | `false` |

---

## Section 8 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 8.1 | Endpoint protection/AV platform | text | — | no | answered/unanswered | `"Microsoft Defender for Business"` |
| 8.2 | Endpoint protection deployed on supported devices | enum | coverage_level | no | answered/unknown/unanswered | `"full"` |
| 8.3 | Patching managed on defined cadence | enum | process_maturity | no | answered/unknown/unanswered | `"informal"` |
| 8.4 | Critical network/security firmware reviewed for currency | enum | review_cadence | no | answered/unknown/unanswered/not_applicable | `"irregular"` |
| 8.5 | Web/content filter in place | enum | filtering_scope | no | answered/unknown/unanswered | `"students_and_staff"` |
| 8.6 | Student safety monitoring platform used | object | boolean | yes | answered/unknown/unanswered/not_applicable | `{ "value": true, "notes": "GoGuardian Beacon" }` |
| 8.7 | Filtering/web protection/student safety controls documented | enum | coverage_level | no | answered/unknown/unanswered/not_applicable | `"partial"` |
| 8.8 | Response process for malware/account compromise documented | enum | process_maturity | no | answered/unknown/unanswered | `"none"` |
| 8.9 | Logs/alerts reviewed by someone | enum | review_cadence | no | answered/unknown/unanswered/not_applicable | `"sometimes"` |
| 8.10 | Cyber insurance carried | boolean | boolean | no | answered/unknown/unanswered | `true` |
| 8.11 | Known unresolved security concerns exist | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Old Windows lab devices still in use" }` |

---

## Section 9 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 9.1 | Central location for IT documentation | enum | documentation_maturity | no | answered/unknown/unanswered | `"current"` |
| 9.2 | Network/systems/vendor docs kept reasonably current | enum | documentation_maturity | no | answered/unknown/unanswered | `"partial"` |
| 9.3 | SOPs documented for recurring tasks | enum | process_maturity | no | answered/unknown/unanswered | `"partial"` |
| 9.4 | Known process for documenting changes | enum | process_maturity | no | answered/unknown/unanswered | `"informal"` |
| 9.5 | Qualified third party could understand environment from docs | enum | transferability_level | no | answered/unknown/unanswered | `"partial"` |
| 9.6 | Major knowledge areas live only in one person’s head | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Firewall and phone system mainly known by one admin" }` |

---

## Section 10 normalization table

| ID | Summary | Norm Type | Enum Family | Notes | Status Behavior | Example |
|---|---|---|---|---|---|---|
| 10.1 | Known IT problems or projects needing attention (up to 5) | text_list | priority_list | yes | answered/unanswered | `["Aging devices", "weak backup testing", "network documentation"]` |
| 10.2 | Approved or planned projects in next 12 months | text_list | project_list | yes | answered/unanswered | `["Wi-Fi refresh", "SIS migration"]` |
| 10.3 | Known deadlines/audits/renewals/compliance events | text_list | event_list | yes | answered/unanswered | `["E-rate filing", "July ISP renewal"]` |
| 10.4 | Expected changes before next school year | text | — | yes | answered/unanswered | `"New 6th grade 1:1 rollout and staff laptop refresh"` |
| 10.5 | Leadership expecting budget/refresh/improvement plan | object | boolean | yes | answered/unknown/unanswered | `{ "value": true, "notes": "Board wants refresh plan by May" }` |
| 10.6 | Known obstacles or constraints affecting ability to act | text | — | yes | answered/unanswered | `"Budget freeze until Q3; one open IT position"` |
| 10.7 | Overall confidence in accuracy of assessment data | enum | confidence_level | no | answered/unanswered | `"moderate"` |
| 10.8 | Sections or areas where data was particularly incomplete | text_list | — | yes | answered/unanswered/not_applicable | `["Section 3 network", "Section 7 backups"]` |

---

## Additional canonical enum families introduced by the table

### support_model
- internal_it_staff
- single_it_director
- outsourced_msp
- hybrid_internal_msp
- volunteer_or_ad_hoc
- other
- unknown

### budget_maturity
- annual
- informal
- none
- unknown

### continuity_cover
- full
- partial
- none
- unknown

### access_level
- full
- partial
- none
- unknown

### frequency_presence
- regular
- occasional
- none
- unknown

### frequency_level
- continuous
- daily
- weekly
- monthly
- ad_hoc
- quarterly
- twice_per_year
- annually
- less_than_annual
- never
- unknown

### service_quality
- full
- mixed
- poor
- unknown

### identity_platform
- google_workspace
- microsoft_365
- hybrid_google_microsoft
- local_directory_or_active_directory
- other
- unknown

### directory_model
- cloud
- on_premises
- hybrid
- none
- unknown

### one_to_one_state
- full
- partial
- none
- unknown

### take_home_state
- all
- some
- none
- unknown

### yes_no_unknown_enum
- yes
- no
- unknown

### unsupported_device_exposure
- none
- some
- many
- unknown

### review_cadence
- regular
- irregular
- none
- sometimes
- unknown

### restore_recency
- within_12_months
- older_than_12_months
- none
- unknown

### filtering_scope
- students_only
- students_and_staff
- partial
- none
- unknown

### transferability_level
- full
- partial
- none
- unknown

### priority_list
- freeform_text_list

### project_list
- freeform_text_list

### event_list
- freeform_text_list

---

## Deterministic Finding Framework for Module 1

### Finding categories
- missing documentation
- unknown critical state
- lifecycle concern
- single point of failure
- continuity gap
- security control gap
- ownership gap
- planning gap
- compliance visibility gap
- access dependency gap

### Example finding logic patterns

#### Pattern A: Unknown critical state
If one or more critical-state questions are unknown, create a finding emphasizing limited visibility.
Example critical-state areas:
- firewall support or firmware
- backup coverage
- privileged account review
- device inventory status
- server ownership or access

#### Pattern B: Missing process
If onboarding, offboarding, restore testing, patching cadence, or device provisioning is not documented, create an operational readiness finding.

#### Pattern C: Single-person dependency
If ownership is concentrated and backup coverage is weak, create a resilience finding.

#### Pattern D: Unsupported assets
If devices are beyond support and no refresh cycle exists, create a lifecycle finding and planning action.

#### Pattern E: No central documentation system
If there is no central documentation location or documents are outdated, create a documentation maturity finding.

#### Pattern F: Control without visibility
If a service exists but inventory, access, ownership, or renewal details are unclear, create a visibility/control finding rather than assuming maturity.

---

## Deterministic Action Framework for Module 1

### Time horizons
- immediate
- next_30_days
- next_90_days
- next_12_months

### Suggested action templates
- document current state
- verify and test
- assign ownership
- remediate unsupported systems
- formalize process
- schedule recurring review
- prepare budget or refresh plan
- centralize subscriptions or vendor records

### Note: School calendar scheduling
Action items should eventually be tagged with a school calendar scheduling category (school year, evenings/off-hours, winter break, spring break, or summer) in addition to the priority time horizon. The priority scale (immediate / next_30_days / next_90_days / next_12_months) and the scheduling category are separate dimensions — a priority of "immediate" combined with a scheduling category of "spring break" means the work is urgent but requires a break window to execute safely. Full integration of the scheduling category into the action framework is deferred to a future iteration. The design document (v0.2, Decision #19) defines the scheduling categories and their criteria.

### Note: Question-level scoring weights
Each question will need a scoring weight or scoring contribution flag once the scoring framework is built. This is tracked as a next-iteration item in both this module and the design document.

#### Rule: Backup uncertainty
If backups are assumed, not verified, or restore testing is missing:
- action 1: confirm backup scope and ownership
- action 2: perform and document a restore test
- horizon: next_30_days

#### Rule: Admin access uncertainty
If privileged roles are not reviewed or MFA is incomplete:
- action 1: inventory privileged accounts
- action 2: verify MFA and reduce unnecessary admin rights
- horizon: immediate or next_30_days

#### Rule: Inventory weakness
If inventory is partial or absent:
- action 1: establish a baseline device and infrastructure inventory
- action 2: define required inventory fields
- horizon: next_90_days

#### Rule: No documented lifecycle
If refresh planning is absent and aging devices exist:
- action 1: define lifecycle targets by device class
- action 2: prepare replacement budget estimate
- horizon: next_12_months

#### Rule: Network control dependency
If the school does not have admin access to key systems:
- action 1: verify ownership and admin access paths
- action 2: document escalation and recovery procedures
- horizon: immediate or next_30_days

---

## Proposed Domain Status Logic
Each section should produce a domain status:
- healthy
- watch
- concern
- urgent
- unknown

### Suggested logic approach
- heavy weighting for unknowns in critical areas
- urgent only when there is both risk and likely operational impact
- concern when gaps are material but not necessarily immediate
- watch when there is partial maturity or improvement needed

This should remain rule-based and explainable.

---

## Proposed Charts for Module 1 Report
- domain status summary
- known vs unknown answers by section
- findings by category
- action items by time horizon
- asset lifecycle concern snapshot
- subscription and renewal visibility snapshot

---

## Generalized Annual Follow-Up Calendar
This section should not pretend to know the exact school calendar. It should create a generalized operational cadence based on answers.

### Example calendar items
- summer: major refresh, infrastructure changes, wireless validation, account cleanup
- pre-school-year: classroom readiness, staff onboarding, device prep, printing checks
- quarterly: admin review, backup review, documentation updates, firmware review
- annually: vendor renewal review, restore test, lifecycle planning, policy review

---

## Appendix Design
The appendix should include:
- section-by-section responses
- unknown answer list
- documentation gaps list
- systems or vendors mentioned
- planning dates or events captured from the questionnaire

---

## Open Questions for This Module

Questions that are programmatic in nature (scoring visibility, effort bands, output formats, branching depth) have been moved to the design document and are tracked there. The following are module-specific open questions only.

| # | Question | Status |
|---|----------|--------|
| 1 | Which questions should be mandatory vs skippable in the v1 intake UI? | Open |
| 2 | What is the smallest useful version of the appendix for v1? | Open |
| 3 | Should software subscription tracking in Section 6 be expanded, or deferred to a future dedicated applications/finance module? | **Noted** — current approach is intentionally light; a dedicated subscriptions/licensing module is planned for a later version |
| 4 | Should question scoring weights be defined at the module level or centrally in the engine? | Open — defer until scoring framework is built |

---

## Next Iteration Targets
1. Define scoring weights or contribution flags for each question.
2. Add explicit rule IDs for all findings and actions.
3. Map school calendar scheduling categories to action items in the action framework.
4. Draft the DOCX report section templates fed by this module.
5. Reduce or combine any questions that do not clearly support an output.
6. Define which questions are mandatory vs skippable in the v1 UI.
7. Determine the minimum useful appendix structure for v1.

