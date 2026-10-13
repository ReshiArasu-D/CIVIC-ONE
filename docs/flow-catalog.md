# CivicOne — Flow Designer Catalogue (Phase 1)

This document details the Flow Designer specifications for CivicOne Foundation: **F1, F4, F5, F6, and F8**.

---

## 1. F1: Grievance Intake Flow

- **Trigger:** Created record on `x_2229367_civicone_case`.
- **Purpose:** Full intake pipeline without AI dependency.
- **Workflow Steps:**
  1. **Intake Validation:** Verify `citizen`, `category`, and `ward` are populated. If missing, flag intake error.
  2. **Geo Routing & Asset Proximity:** If GPS coordinates or address are present, invoke `GeoRouter.resolveWard` to match closest `civic_asset`.
  3. **Deterministic Fallback:** If ward resolution cannot be resolved from coordinates, assign default headquarters ward (`WRD-12 Indiranagar`).
  4. **Eligible Worker Assignment:** Call `JurisdictionUtil.findEligibleWorker(ward, department)` to identify available worker with lowest workload.
  5. **SLA Initialization:** Query `sla_policy` for category and urgency to attach target resolution deadline.
  6. **Intake Logging:** Record initial assignment event in `case_assignment_history` and rule engine execution factors in `ai_action_log`.

---

## 2. F4: SLA and Escalation Flow

- **Trigger:** Scheduled SLA evaluation / timer trigger on `x_2229367_civicone_case`.
- **Purpose:** Proactive SLA monitoring and multi-tier escalation.
- **Workflow Steps:**
  1. **75% Warning Evaluation:** When 75% of `sla_target_hours` has elapsed without resolution:
     - Create `escalation_step` (Level 1 - Supervisor).
     - Send In-App notification to Ward / Sub-district Head.
     - Preserves case work notes.
  2. **100% Breach Escalation:** When 100% of `sla_target_hours` is breached:
     - Set `sla_breached = true` on case.
     - Create `escalation_step` (Level 2 - District Officer).
     - Escalate to District Officer queue.
     - Preserves complete escalation timeline.

---

## 3. F5: Resolution and Confirmation Flow

- **Trigger:** Updated record on `x_2229367_civicone_case` where status changes to `Resolved`.
- **Purpose:** Protects the citizen satisfaction closure gate.
- **Workflow Steps:**
  1. **Evidence Verification:** Check `requires_evidence_to_close` on category. Ensure at least one `resolution_evidence` record is attached.
  2. **Gate Transition:** Set `grievance_status = 'Awaiting Citizen Confirmation'` and `citizen_confirmation_status = 'Pending'`.
  3. **Citizen Notification:** Invoke F6 to dispatch resolution summary and evidence view link in citizen's preferred language.
  4. **Confirmation Path:** If citizen submits feedback with `Confirmed`:
     - Update case to `Closed`.
     - Record satisfaction rating and timeliness score.
  5. **Dispute Path:** If citizen submits feedback with `Disputed`:
     - Revert case status to `In Progress`.
     - Log dispute reason in work notes.
     - Create Level 1 Supervisor Escalation.
  6. **Zero Silent Closure:** Never silently close unconfirmed cases on timeout without explicit supervisor sign-off.

---

## 4. F6: Multilingual Notifications Flow

- **Trigger:** Subflow called from F1, F4, F5, or status change.
- **Purpose:** Composes and records localized communications.
- **Workflow Steps:**
  1. **Language Resolution:** Read citizen `preferred_language` (English, Hindi, Kannada, Tamil, Telugu, Marathi).
  2. **Template Selection:** Select active template from `x_2229367_civicone_notification_template` matching template code and language.
  3. **Dynamic Token Replacement:** Replace `{case_number}`, `{citizen_name}`, `{category}`, `{ward}`, `{sla_hours}` with runtime values.
  4. **Delivery Queueing:** Queue message for SMS/In-App delivery.
  5. **Outcome Logging:** Record delivery status and timestamp.

---

## 5. F8: Worker Absence Flow

- **Trigger:** Updated record on `x_2229367_civicone_case_worker` where `is_available` changes to `false`.
- **Purpose:** Safeguards ongoing grievances during field worker sick leave or emergency absence.
- **Workflow Steps:**
  1. **Identify Impacted Cases:** Query all open cases (`Assigned` or `In Progress`) assigned to the absent worker.
  2. **Policy Evaluation:**
     - Check if `backup_worker` is configured and available.
     - If backup is available: reassign cases to backup worker.
     - If no backup: call `JurisdictionUtil.findEligibleWorker` for an available peer worker in the same ward/department.
     - If no eligible peer: unassign to department triage queue and alert Ward Head.
  3. **Audit Tracking:** Flag `worker_absent_reassigned = true` on each case and insert an audit record into `case_assignment_history` with reason `Worker Absence`.

---

## 6. Runtime Engine & Execution Classification (WKF-01)

### 6.1 Architectural Execution Distinction
In ServiceNow scoped architecture, automated logic can be driven either by synchronous Business Rules / Script Includes or asynchronously via the Flow Designer execution engine (`sys_flow_context`).

During Phase 1 Foundation:
- **Synchronous Server Logic (Authoritative Runtime):** All intake, routing, priority calculation, SLA attachment, assignment history, evidence gating, and citizen confirmation gates are executed deterministically by the deployed Business Rules (`BR01`–`BR22`) and 6 Script Includes.
- **Flow Designer Metadata (`sys_hub_flow`):** The 5 flows (F1, F4, F5, F6, F8) exist as scoped catalog specifications in `draft` state (`compiled_snapshot = null`). Because the Business Rules execute synchronously, activating uncompiled flow triggers would create duplicate execution conflicts and uncompiled action errors.
- **Execution Evidence Classification:**
  - F1 Intake Pipeline: **EXECUTED & VERIFIED** via Business Rules (`BR01`, `BR03`, `BR04`, `BR06`, `BR07`, `BR08`).
  - F4 SLA Escalations: **EXECUTED & VERIFIED** via Business Rules (`BR06`, `BR16`, `BR17`).
  - F5 Resolution & Citizen Confirmation Gate: **EXECUTED & VERIFIED** via Business Rules (`BR11`, `BR12`, `BR13`, `BR14`).
  - F6 Multilingual Notifications: **EXECUTED & VERIFIED** via `BR18` and `NotificationComposer`.
  - F8 Worker Absence Handler: **EXECUTED & VERIFIED** via `BR09`.
  - Flow Designer Engine (`sys_flow_context`): **NOT TESTED** (catalog draft specifications; 0 engine contexts executed).
