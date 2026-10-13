# CivicOne — System Architecture (Phase 1: Foundation)

**Application Name:** CivicOne  
**Application Scope:** `x_2229367_civicone`  
**Target Release:** ServiceNow Australia Release (Patch 3)  
**Implementation Phase:** Phase 1 — Foundation Only  

---

## 1. Architectural Overview

CivicOne is an enterprise citizen grievance redressal system built natively on the ServiceNow platform for PS07 public sector administration. The Foundation phase establishes the structural, geographical, organisational, data governance, security, and workflow base upon which Citizen Portals (Phase 2), Administrative Workspaces (Phase 3), and AI Agents (Phase 4) will be constructed.

```
       +-------------------------------------------------------------+
       |               CivicOne Foundation Architecture              |
       +-------------------------------------------------------------+
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
[Geographic Hierarchy]     [Organisation & Assets]       [Grievance Management]
- Zone                      - Department                  - Case (extends Task)
- State                     - Category                    - Master Grievance
- District                  - Civic Asset                 - Case Assignment History
- Sub-District              - Case Worker                 - Resolution Evidence
- Ward                      - Customer (Citizen)          - Citizen Feedback
       |                              |                              |
       +------------------------------+------------------------------+
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
[SLA & Escalation]         [Localization & Comms]        [Audit & Governance]
- SLA Policy                - Language                    - AI Action Log (Immutable)
- Escalation Step           - UI Translation              - Executive Brief
                            - Notification Template
```

---

## 2. Core Architectural Decisions

### 2.1 Task Extension for Case
- **Decision:** `x_2229367_civicone_case` directly extends ServiceNow base `task`.
- **Rationale:**
  - Inherits enterprise task attributes (`number`, `state`, `priority`, `assigned_to`, `assignment_group`, `comments`, `work_notes`).
  - Seamless native integration with ServiceNow SLA Engine (`contract_sla` and `task_sla`).
  - Provides built-in activity streams, audit logging, and task assignment dispatching.

### 2.2 Scoped Application Isolation
- **Scope Identifier:** `x_2229367_civicone`
- **Application Sys ID:** `26068197c33b8754e54832f1b40131d5`
- Cross-scope protection policies applied. Script Includes are exposed via `x_2229367_civicone.<ScriptIncludeName>` public APIs.

### 2.3 Deterministic Rule-Based Intake
- In Phase 1, intake validation, hierarchy resolution, priority scoring, duplicate detection, and worker assignment are 100% deterministic, implemented in Script Includes (`JurisdictionUtil`, `GeoRouter`, `PriorityScorer`, `PiiMasker`) and Business Rules (BR01–BR22).
- AI Action Log (`x_2229367_civicone_ai_action_log`) is deployed as an immutable audit contract, capturing rule engine factor explanations without requiring unverified external LLM dependencies in Foundation phase.

### 2.4 Citizen Confirmation Closure Gate
- Normal case resolution does NOT close tickets automatically. Cases transition to `Awaiting Citizen Confirmation`.
- Cases close only when citizen feedback records `action_confirmed == 'Confirmed'`, or via explicit administrative override with audit reasons.
- Citizen disputes automatically reopen tickets to `In Progress` and trigger supervisory review.

---

## 3. Directory Layout

```
CIVIC-ONE/
├── app/
│   ├── script_includes/    # Server-side Script Includes
│   │   ├── JurisdictionUtil.js
│   │   ├── GeoRouter.js
│   │   ├── PriorityScorer.js
│   │   ├── PiiMasker.js
│   │   ├── NotificationComposer.js
│   │   └── AiLogger.js
│   └── ui/
│       └── design_system.css # Reusable navy/blue design system
├── seed/                   # Synthetic CSV seed data in dependency order
│   ├── 01_geography_zone.csv
│   ├── 02_geography_state.csv
│   ├── 03_geography_district.csv
│   ├── 04_geography_sub_district.csv
│   ├── 05_geography_ward.csv
│   ├── 06_organisation_department.csv
│   ├── 07_organisation_category.csv
│   ├── 08_organisation_civic_asset.csv
│   ├── 09_language.csv
│   ├── 10_notification_template.csv
│   ├── 11_people_case_worker.csv
│   ├── 12_people_customer.csv
│   ├── 13_grievances_cases.csv
│   └── 14_sla_policy.csv
├── scripts/                # Repeatable deployment and verification scripts
│   ├── deploy_phase1_datamodel.py
│   ├── deploy_script_includes.py
│   ├── deploy_business_rules.py
│   ├── deploy_roles.py
│   ├── deploy_acls.py
│   ├── deploy_flows.py
│   ├── load_seed_data.py
│   └── export_update_set.md
├── tests/                  # Automated verification and checklist
│   ├── manual_checklist.md
│   └── atf/
└── docs/                   # Specifications, matrices, and capabilities
    ├── instance-capabilities.md
    ├── architecture.md
    ├── data-dictionary.md
    ├── business-rules.md
    ├── flow-catalog.md
    ├── security-matrix.md
    └── test-sheet.csv
```
