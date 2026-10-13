# CivicOne — Business Rules Catalogue (BR01–BR22)

This catalogue documents all 22 server-side business rules implemented in `x_2229367_civicone`.

---

| Rule ID | Rule Name | Target Table | Timing | Insert | Update | Purpose | Implementation Detail |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BR01** | `Validate_Intake_Requirements` | `case` | `before` | Yes | No | Enforces intake requirements | Validates `citizen`, `category`, and `ward`. Defaults channel to 'Web' and status to 'Submitted'. |
| **BR02** | `Preserve_Raw_Text_And_Mask_PII` | `case` | `before` | Yes | No | Preserves evidence and protects privacy | Copies raw text to `original_description`. Runs `PiiMasker` to sanitize Aadhaar/PAN/phone/email, saving to `masked_description`. |
| **BR03** | `Resolve_Geographic_Hierarchy` | `case` | `before` | Yes | Yes | Auto-resolves geographic tree | Calls `JurisdictionUtil.resolveHierarchyFromWard` to link sub-district, district, state, and zone. |
| **BR04** | `Calculate_Priority_Score` | `case` | `before` | Yes | Yes | Multi-factor priority scoring | Calls `PriorityScorer.calculatePriority` based on category urgency, hazard keywords, and vulnerable populations. Logs audit to `ai_action_log`. |
| **BR05** | `Detect_Potential_Duplicate_Grievances` | `case` | `after` | Yes | No | Non-destructive duplicate suggestion | Queries 72-hour window in same ward & category. Sets `is_duplicate_suspect = true` and `duplicate_suspect_parent`. Never deletes or merges. |
| **BR06** | `Initialise_SLA_Association` | `case` | `before` | Yes | No | Associates target SLA hours | Queries `sla_policy` or `category.default_sla_hours` to initialize `sla_target_hours`. |
| **BR07** | `Enforce_Eligible_Assignment` | `case` | `before` | Yes | Yes | Validates worker eligibility | Calls `JurisdictionUtil.isWorkerAuthorized` to ensure worker is available and assigned to case department/ward. Rejects unauthorized assignments. |
| **BR08** | `Record_Assignment_History` | `case` | `after` | Yes | Yes | Immutable assignment audit trail | On worker change, inserts record into `case_assignment_history` capturing old worker, new worker, assigned by, and reason. |
| **BR09** | `Worker_Absence_Auto_Reassignment` | `case_worker` | `after` | No | Yes | Handles worker unavailability | When worker marked unavailable, reassigns active cases to `backup_worker` or returns to department queue. Flags `worker_absent_reassigned = true`. |
| **BR10** | `Enforce_In_Progress_Prerequisite` | `case` | `before` | No | Yes | Prevents premature in-progress status | Blocks moving to 'In Progress' unless an `assigned_to` worker is populated. |
| **BR11** | `Require_Evidence_Before_Resolution` | `case` | `before` | No | Yes | Enforces resolution evidence gate | If category requires evidence, verifies `resolution_evidence` record exists before allowing resolution. Routes to 'Awaiting Citizen Confirmation'. |
| **BR12** | `Protect_Citizen_Confirmation_Closure_Gate` | `case` | `before` | No | Yes | Prevents ordinary premature closure | Blocks moving directly to 'Closed' unless `citizen_confirmation_status == 'Confirmed'` or performed by administrator. |
| **BR13** | `Handle_Citizen_Confirmation` | `citizen_feedback` | `after` | Yes | No | Processes citizen satisfaction | When citizen confirms resolution, updates parent case to `Confirmed`, transitions status to `Closed`, logs close notes. |
| **BR14** | `Handle_Citizen_Dispute` | `citizen_feedback` | `after` | Yes | No | Handles citizen dissatisfaction | When citizen disputes resolution, reverts parent case to `In Progress`, sets `Disputed` status, logs dispute reason, and triggers escalation step. |
| **BR15** | `Validate_Citizen_Feedback` | `citizen_feedback` | `before` | Yes | No | Ensures feedback authenticity | Verifies `case` and `citizen` are valid and populates `submitted_at`. |
| **BR16** | `SLA_Warning_Monitoring` | `case` | `after` | No | Yes | Warns supervisors at 75% SLA | Triggers Level 1 escalation step and supervisor warning notification when warning threshold reached. |
| **BR17** | `SLA_Breach_Escalation` | `case` | `after` | No | Yes | Auto-escalates at 100% SLA breach | When `sla_breached == true`, creates Level 2 escalation step assigned to District Officer. |
| **BR18** | `Trigger_Multilingual_Notifications` | `case` | `after` | Yes | Yes | Dispatches localized communications | Invokes `NotificationComposer.composeNotification` on intake, assignment, and resolution. |
| **BR19** | `Restrict_Citizen_Read_Visibility` | `case` | `before_query` | N/A | N/A | Row-level citizen privacy gate | Citizens only query cases where `citizen.user == gs.getUserID()`. |
| **BR20** | `Enforce_Officer_Jurisdiction_Scoping` | `case` | `before_query` | N/A | N/A | Boundary security for officers | Scopes worker queries strictly to cases within their authorized ward and department. |
| **BR21** | `Protect_AI_Action_Log_Immutability` | `ai_action_log` | `before` | No | Yes (block) | Preserves governance integrity | Aborts any update or delete action on `ai_action_log`. |
| **BR22** | `Protect_Preserved_PII_Fields` | `case` | `before` | No | Yes (block) | Protects original complaint text | Aborts changes to `original_description` once inserted, preserving legal evidence. |

---

### Rule Deployment Hygiene & Single-Instance Enforcement
Following Phase 1 Remediation Sprint (LOG-01):
- `BR05_Detect_Potential_Duplicate_Grievanc`: Exactly one authoritative instance (`aa1f8dd3c3bb8754e54832f1b40131de`) is active; redundant deployment duplicates (`33ff0997...`, `546099d7...`) are deactivated.
- `BR12_Protect_Citizen_Confirmation_Closur`: Exactly one authoritative instance (`f9005997c3bb8754e54832f1b40131bb`) is active; redundant deployment duplicate (`fd601dd7...`) is deactivated.
- `BR19` and `BR20` are active as `before_query` server-side rules, operating in tandem with the hardened Case Read ACL.
