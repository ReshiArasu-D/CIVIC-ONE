# CivicOne — Data Dictionary (Phase 1: Foundation)

**Scope Prefix:** `x_2229367_civicone`  
**Total Phase 1 Tables:** 22  

---

## 1. Geography Tables

### 1.1 Zone (`x_2229367_civicone_zone`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `ZN-NORTH`, `ZN-SOUTH` |
| `name` | String | 100 | Yes | Yes | Zone Name |
| `headquarters` | String | 100 | No | No | Regional administrative hub |
| `active` | Boolean | — | No | No | Active status |

### 1.2 State / UT (`x_2229367_civicone_state`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `ST-KA`, `ST-MH` |
| `name` | String | 100 | Yes | Yes | State/UT Name |
| `zone` | Reference | 32 | Yes | No | References `x_2229367_civicone_zone` |
| `capital` | String | 100 | No | No | State Capital City |
| `active` | Boolean | — | No | No | Active status |

### 1.3 District (`x_2229367_civicone_district`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `DT-BLR-U` |
| `name` | String | 100 | Yes | Yes | District Name |
| `state` | Reference | 32 | Yes | No | References `x_2229367_civicone_state` |
| `collectorate_address` | String | 255 | No | No | District Collectorate address |
| `active` | Boolean | — | No | No | Active status |

### 1.4 Sub-District (`x_2229367_civicone_sub_district`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | Taluk / Tehsil Code |
| `name` | String | 100 | Yes | Yes | Sub-District Name |
| `district` | Reference | 32 | Yes | No | References `x_2229367_civicone_district` |
| `active` | Boolean | — | No | No | Active status |

### 1.5 Ward / Village (`x_2229367_civicone_ward`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `WRD-12`, `WRD-15` |
| `name` | String | 100 | Yes | Yes | Ward Name (e.g. Ward 12 Indiranagar) |
| `sub_district` | Reference | 32 | Yes | No | References `x_2229367_civicone_sub_district` |
| `ward_number` | Integer | — | No | No | Numeric ward identifier |
| `population` | Integer | — | No | No | Census population |
| `councillor_name` | String | 100 | No | No | Elected municipal representative |
| `councillor_contact` | String | 50 | No | No | Official contact number |
| `active` | Boolean | — | No | No | Active status |

---

## 2. Organisation & People Tables

### 2.1 Department (`x_2229367_civicone_department`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `DEPT-WATER`, `DEPT-ROADS` |
| `name` | String | 100 | Yes | Yes | Department Name |
| `description` | String | 500 | No | No | Department scope |
| `head_officer` | Reference | 32 | No | No | References `sys_user` |
| `active` | Boolean | — | No | No | Active status |

### 2.2 Grievance Category (`x_2229367_civicone_category`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `code` | String | 40 | Yes | No | e.g. `CAT-WAT-LEAK` |
| `name` | String | 100 | Yes | Yes | Category Name |
| `department` | Reference | 32 | Yes | No | References `x_2229367_civicone_department` |
| `default_urgency` | Choice | 20 | No | No | 1-High, 2-Medium, 3-Low |
| `default_sla_hours` | Integer | — | No | No | Default SLA duration in hours |
| `requires_evidence_to_close` | Boolean | — | No | No | Mandatory resolution proof gate |
| `active` | Boolean | — | No | No | Active status |

### 2.3 Civic Asset (`x_2229367_civicone_civic_asset`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `asset_id` | String | 50 | Yes | No | Unique asset tag |
| `name` | String | 100 | Yes | Yes | Public infrastructure asset name |
| `category` | Reference | 32 | No | No | References `x_2229367_civicone_category` |
| `ward` | Reference | 32 | Yes | No | References `x_2229367_civicone_ward` |
| `department` | Reference | 32 | Yes | No | References `x_2229367_civicone_department` |
| `latitude` | Decimal | 10,6 | No | No | Asset GPS Latitude |
| `longitude` | Decimal | 10,6 | No | No | Asset GPS Longitude |
| `location_address` | String | 255 | No | No | Physical landmark / street address |
| `condition` | Choice | 40 | No | No | Operational, Degraded, Damaged, Critical |
| `active` | Boolean | — | No | No | Active status |

### 2.4 Case Worker (`x_2229367_civicone_case_worker`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `user` | Reference | 32 | Yes | Yes | References `sys_user` |
| `employee_id` | String | 50 | Yes | No | Departmental employee badge |
| `department` | Reference | 32 | Yes | No | References `x_2229367_civicone_department` |
| `ward` | Reference | 32 | No | No | References `x_2229367_civicone_ward` |
| `sub_district` | Reference | 32 | No | No | References `x_2229367_civicone_sub_district` |
| `district` | Reference | 32 | No | No | References `x_2229367_civicone_district` |
| `is_available` | Boolean | — | No | No | Duty status |
| `absence_reason` | String | 255 | No | No | Reason for unavailability |
| `backup_worker` | Reference | 32 | No | No | References `x_2229367_civicone_case_worker` |
| `active_case_load` | Integer | — | No | No | Dynamic count of in-progress cases |

### 2.5 Citizen Customer (`x_2229367_civicone_customer`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `citizen_id` | String | 50 | Yes | No | Synthetic citizen identifier |
| `full_name` | String | 100 | Yes | Yes | Citizen Full Name |
| `phone` | String | 20 | No | No | Contact telephone |
| `email` | String | 100 | No | No | Contact email |
| `ward` | Reference | 32 | No | No | References `x_2229367_civicone_ward` |
| `preferred_language` | Reference | 32 | No | No | References `x_2229367_civicone_language` |
| `user` | Reference | 32 | No | No | References `sys_user` portal account |
| `is_verified` | Boolean | — | No | No | Verification status |

---

## 3. Grievance Management Tables

### 3.1 Case (`x_2229367_civicone_case`) — *Extends `task`*
*Inherits `number`, `short_description`, `description`, `state`, `priority`, `assigned_to`, `assignment_group`, `work_notes`, `comments` from `task`.*

| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `citizen` | Reference | 32 | Yes | References `x_2229367_civicone_customer` |
| `department` | Reference | 32 | Yes | References `x_2229367_civicone_department` |
| `category` | Reference | 32 | Yes | References `x_2229367_civicone_category` |
| `ward` | Reference | 32 | Yes | References `x_2229367_civicone_ward` |
| `sub_district` | Reference | 32 | No | Auto-resolved from Ward |
| `district` | Reference | 32 | No | Auto-resolved from Ward |
| `state` | Reference | 32 | No | Auto-resolved from Ward |
| `zone` | Reference | 32 | No | Auto-resolved from Ward |
| `civic_asset` | Reference | 32 | No | Proximity-matched or manual link |
| `master_grievance` | Reference | 32 | No | References parent clustered grievance |
| `channel` | Choice | 30 | No | Web, Mobile, Portal, In-Person, Call |
| `pii_masked` | Boolean | — | No | Flag set by PiiMasker |
| `original_description` | String | 4000 | No | Immutable raw citizen text (restricted ACL) |
| `masked_description` | String | 4000 | No | Sanitized public description |
| `grievance_status` | Choice | 50 | No | Submitted, Assigned, In Progress, Awaiting Citizen Confirmation, Closed, Disputed |
| `citizen_confirmation_status` | Choice | 40 | No | Pending, Confirmed, Disputed |
| `dispute_reason` | String | 1000 | No | Reason recorded upon citizen dispute |
| `priority_score` | Decimal | 5,2 | No | 0–100 computed by PriorityScorer |
| `latitude` | Decimal | 10,6 | No | GPS Latitude of complaint |
| `longitude` | Decimal | 10,6 | No | GPS Longitude of complaint |
| `is_duplicate_suspect` | Boolean | — | No | Flagged by BR05 duplicate check |
| `duplicate_suspect_parent` | Reference | 32 | No | References suspected original case |
| `sla_target_hours` | Integer | — | No | Target resolution SLA in hours |
| `sla_breached` | Boolean | — | No | SLA breach flag |
| `resolved_at` | GlideDateTime | — | No | Timestamp of initial resolution |
| `resolution_summary` | String | 1000 | No | Resolution summary by worker |

### 3.2 Master Grievance (`x_2229367_civicone_master_grievance`)
| Field Name | Type | Length | Mandatory | Display | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `number` | String | 40 | No | Yes | Numbering prefix `MGR` |
| `title` | String | 200 | Yes | No | Master issue title |
| `summary` | String | 1000 | No | No | Incident root cause summary |
| `category` | Reference | 32 | Yes | No | References `x_2229367_civicone_category` |
| `ward` | Reference | 32 | Yes | No | References `x_2229367_civicone_ward` |
| `status` | Choice | 40 | No | No | Open, Investigating, Work in Progress, Resolved, Closed |
| `child_case_count` | Integer | — | No | No | Total linked citizen cases |
| `primary_case` | Reference | 32 | No | No | References `x_2229367_civicone_case` |

### 3.3 Case Assignment History (`x_2229367_civicone_case_assignment_history`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `case` | Reference | 32 | Yes | References `x_2229367_civicone_case` |
| `assigned_from_worker` | Reference | 32 | No | Previous assigned worker |
| `assigned_to_worker` | Reference | 32 | Yes | New assigned worker |
| `assigned_by` | Reference | 32 | No | User initiating assignment |
| `assignment_time` | GlideDateTime | — | No | Assignment timestamp |
| `reason` | Choice | 50 | No | Initial Intake, Rebalancing, Escalation, Worker Absence, Manual Transfer |
| `notes` | String | 500 | No | Assignment notes |

### 3.4 Resolution Evidence (`x_2229367_civicone_resolution_evidence`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `case` | Reference | 32 | Yes | References `x_2229367_civicone_case` |
| `evidence_type` | Choice | 50 | No | Photo, Inspection Report, Completion Certificate, Sign-off Sheet |
| `evidence_notes` | String | 1000 | No | Evidence notes from field officer |
| `submitted_by` | Reference | 32 | Yes | References `sys_user` |
| `submitted_at` | GlideDateTime | — | No | Submission timestamp |
| `verified_by_supervisor` | Boolean | — | No | Supervisor validation flag |
| `attachment_sys_id` | String | 40 | No | Linked `sys_attachment` record |

### 3.5 Citizen Feedback (`x_2229367_civicone_citizen_feedback`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `case` | Reference | 32 | Yes | References `x_2229367_civicone_case` |
| `citizen` | Reference | 32 | Yes | References `x_2229367_civicone_customer` |
| `rating` | Choice | 30 | No | 1-Very Dissatisfied to 5-Very Satisfied |
| `timeliness_score` | Choice | 10 | No | 1 to 5 |
| `work_quality_score` | Choice | 10 | No | 1 to 5 |
| `feedback_comments` | String | 1000 | No | Citizen comments |
| `action_confirmed` | Choice | 30 | No | Confirmed, Disputed |
| `dispute_reason` | String | 1000 | No | Reason if citizen disputes resolution |
| `submitted_at` | GlideDateTime | — | No | Feedback timestamp |

---

## 4. SLA & Governance Tables

### 4.1 SLA Policy (`x_2229367_civicone_sla_policy`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `name` | String | 100 | Yes | Policy Name |
| `category` | Reference | 32 | No | Target Category |
| `department` | Reference | 32 | No | Target Department |
| `urgency` | Choice | 20 | No | 1-High, 2-Medium, 3-Low |
| `target_resolution_hours` | Integer | — | Yes | Target hours (e.g. 12, 24, 48) |
| `warning_threshold_pct` | Integer | — | No | Warning percentage (default: 75) |
| `escalation_level_1_hours` | Integer | — | No | Hours to Level 1 supervisor escalation |
| `escalation_level_2_hours` | Integer | — | No | Hours to Level 2 district officer escalation |
| `active` | Boolean | — | No | Active status |

### 4.2 Escalation Step (`x_2229367_civicone_escalation_step`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `case` | Reference | 32 | Yes | References `x_2229367_civicone_case` |
| `escalation_level` | Choice | 50 | No | Level 1 - Supervisor, Level 2 - District Officer, Level 3 - State Head, Level 4 - Commissioner |
| `escalated_to_role` | String | 50 | No | Target Role |
| `escalated_to_user` | Reference | 32 | No | References `sys_user` |
| `escalated_at` | GlideDateTime | — | No | Timestamp of escalation |
| `trigger_reason` | Choice | 50 | No | SLA Warning 75%, SLA Breach 100%, Citizen Dispute, Manual Escalation |
| `acknowledged` | Boolean | — | No | Officer acknowledgment flag |
| `action_taken` | String | 500 | No | Corrective actions logged |

### 4.3 AI Action Log (`x_2229367_civicone_ai_action_log`) — *Immutable Audit Contract*
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `log_id` | String | 40 | No | Numbering prefix `AIL` |
| `case` | Reference | 32 | No | References `x_2229367_civicone_case` |
| `action_type` | Choice | 50 | No | Priority Scoring, Routing Suggestion, Duplicate Detection, PII Masking |
| `agent_name` | String | 100 | No | Execution engine or agent name |
| `input_payload` | String | 4000 | No | Serialized input parameters |
| `output_payload` | String | 4000 | No | Serialized outcome & explanation factors |
| `confidence_score` | Decimal | 5,2 | No | Confidence score (0.00 – 1.00) |
| `execution_status` | Choice | 30 | No | Success, Fallback, Error, Skipped |
| `audit_timestamp` | GlideDateTime | — | No | Timestamp of execution |
| `applied_to_case` | Boolean | — | No | Whether applied to case record |
| `review_required` | Boolean | — | No | Flag requiring human officer validation |

### 4.4 Executive Brief (`x_2229367_civicone_executive_brief`)
| Field Name | Type | Length | Mandatory | Notes |
| :--- | :--- | :--- | :---: | :--- |
| `brief_id` | String | 40 | No | Numbering prefix `BRF` |
| `report_date` | GlideDateTime | — | No | Reporting period date |
| `zone` | Reference | 32 | No | References `x_2229367_civicone_zone` |
| `district` | Reference | 32 | No | References `x_2229367_civicone_district` |
| `total_cases_reported` | Integer | — | No | Total intake count |
| `total_cases_resolved` | Integer | — | No | Total resolved count |
| `sla_compliance_rate` | Decimal | 5,2 | No | % cases resolved within SLA |
| `top_grievance_category` | Reference | 32 | No | Most frequent category |
| `executive_summary` | String | 4000 | No | Executive narrative summary |

---

## 5. Schema Reconciliation & Deprecated Prototype Tables (SCH-01)

### 5.1 Canonical 22-Table Architecture
The CivicOne Phase 1 data model consists of exactly 22 operational tables:
- **Geography (5):** `zone`, `state`, `district`, `sub_district`, `ward`
- **Organisation & Core (5):** `department`, `category`, `civic_asset`, `case_worker`, `customer`
- **Case Management & Audit (5):** `case` (extends `task`), `case_assignment_history`, `master_grievance`, `resolution_evidence`, `citizen_feedback`
- **SLA & Policy (2):** `sla_policy`, `escalation_step`
- **Localization (3):** `language` (23 languages), `ui_translation`, `notification_template`
- **Governance & Intelligence (2):** `ai_action_log`, `executive_brief`

### 5.2 Deprecated Prototype Tables Inventory
During initial platform bootstrapping and SDK prototyping, six exploratory tables were created in `sys_db_object`. An exhaustive dependency audit confirms:
1. **Zero Record Count:** Exactly 0 rows exist in all 6 tables.
2. **Zero Foreign Keys:** 0 fields in `sys_dictionary` reference them.
3. **Zero Script Dependencies:** 0 Business Rules, Script Includes, or flows invoke them.

In accordance with strict platform change management (no destructive deletes without change advisory approval), these tables have been formally labeled `[DEPRECATED]` in the live dictionary:
| Table Name | Label in Live Dictionary | Status | Dependency Count | Recommendation |
| :--- | :--- | :--- | :---: | :--- |
| `x_2229367_civicone_ward_village` | `[DEPRECATED] Ward Village` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |
| `x_2229367_civicone_civic_case` | `[DEPRECATED] Civic Case` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |
| `x_2229367_civicone_test_task_extension` | `[DEPRECATED] Test Task Extension` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |
| `x_2229367_civicone_grievance_category` | `[DEPRECATED] Grievance Category` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |
| `x_2229367_civicone_state_ut` | `[DEPRECATED] State UT` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |
| `x_2229367_civicone_citizen_customer` | `[DEPRECATED] Citizen Customer` | Deprecated Prototype | 0 | Safe to drop upon Change Approval |

