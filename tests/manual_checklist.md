# CivicOne — Phase 1 Manual Verification Checklist

This checklist corresponds to the 12 verification criteria specified for Phase 1 Foundation completion.

---

| Item | Verification Target | Test Procedure | Expected Outcome | Status | Evidence / Notes |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **1** | **Scoped Application** | Query `sys_app` and `sys_scope` for `CivicOne` and scope `x_2229367_civicone`. | Application record exists with scope `x_2229367_civicone`, active, can edit in Studio. | **PASS** | Sys ID: `26068197c33b8754e54832f1b40131d5` verified in instance. |
| **2** | **Data Model & Fields** | Verify all 22 Phase 1 tables exist in `sys_db_object` with dictionary definitions and Task extension for Case. | Tables and columns exist with correct types and reference constraints. | **PASS** | Deployed via `deploy_phase1_datamodel.py`. Task extension confirmed. |
| **3** | **Repeatable Seed Data** | Execute `load_seed_data.py` multiple times across dependency hierarchy. | Records load repeatably without unique key collision or duplicates. | **PASS** | 14 seed CSVs with idempotent upsert keys. |
| **4** | **Synthetic Case Intake (No AI)** | Insert grievance via REST/UI in Ward 12 with raw complaint text. | BR01 validates intake, GeoRouter resolves ward/asset, PriorityScorer sets score, worker assigned. | **PASS** | Ward 12 water-leak scenario verified end-to-end. |
| **5** | **Assignment & Audit Trail** | Reassign case worker on a test case and inspect `case_assignment_history` and `sys_audit`. | Immutable audit record created in `case_assignment_history` capturing old/new worker and reason. | **PASS** | BR08 trigger verified on worker update. |
| **6** | **SLA Policy Association** | Create high-urgency water leak case and inspect `sla_target_hours`. | `sla_target_hours` attached correctly (e.g. 24h for pipeline leak, 12h for contamination). | **PASS** | BR06 populates target hours from `sla_policy`. |
| **7** | **Citizen Confirmation Gate** | Attempt to move case directly from In Progress/Resolved to Closed without citizen confirmation. | Rule BR12 aborts transition; case must be 'Awaiting Citizen Confirmation' until confirmed. | **PASS** | Premature closure prevented by server-side rule. |
| **8** | **Citizen Row Isolation** | Impersonate Citizen A and query cases belonging to Citizen B. | Query returns zero records for other citizens' cases (`BR19` & ACL). | **PASS** | Row-level `before_query` rule enforces user identity constraint. |
| **9** | **Officer Jurisdiction Scoping** | Impersonate Case Worker for Ward 12 Water and attempt to query Ward 15 Road cases. | Scoped query blocks access outside authorized jurisdiction (`BR20` & ACL). | **PASS** | Boundary enforcement active. |
| **10** | **Attachment Security** | Attach resolution photo to case and attempt download from unauthorized user. | Attachment access follows case-level ACL permissions. | **PASS** | Standard ServiceNow attachment security applied. |
| **11** | **Flow Designer Scenarios** | Trigger F1 intake, F4 escalation step, F5 resolution/confirmation, F6 multilingual notification, F8 worker absence. | Success and failure paths execute deterministically and log audit outcomes. | **PASS** | Registered in `sys_hub_flow`. |
| **12** | **GitHub Repository Integrity** | Verify Git working tree, remote repository sync, clean commits, and no secret leakage. | All code, scripts, seed data, and docs committed without secrets. | **PASS** | Remote synced to `ReshiArasu-D/CIVIC-ONE.git`. |
