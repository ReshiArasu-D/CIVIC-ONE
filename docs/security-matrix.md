# CivicOne — Security & Access Control Matrix (Phase 1)

This document establishes the security architecture, role permissions, row-level policies, and audit rules for CivicOne.

---

## 1. Project Roles Hierarchy

1. **`x_2229367_civicone.citizen`**: Citizen end-user. Restricted to self-service.
2. **`x_2229367_civicone.case_worker`**: Assigned field worker executing on-ground resolutions.
3. **`x_2229367_civicone.ward_head`**: Ward and Sub-District supervisory oversight.
4. **`x_2229367_civicone.district_officer`**: District administrative head, handles Level 2 SLA escalations.
5. **`x_2229367_civicone.state_head`**: State director, cross-district policy governance.
6. **`x_2229367_civicone.zonal_officer`**: Zonal regional coordinator.
7. **`x_2229367_civicone.commissioner`**: Apex authority with all-jurisdiction access.
8. **`x_2229367_civicone.admin`**: System administrator and master data manager.
9. **`x_2229367_civicone.auditor`**: Compliance officer with strictly read-only access across all records.

---

## 2. Table-Level Permission Matrix (CRUD)

| Table Name | Citizen | Case Worker | Ward Head | District Officer | State/Zonal/Commissioner | Auditor | Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`case`** | **CR** (own) | **RU** (assigned) | **CRUD** (ward) | **CRUD** (dist) | **RU** (all) | **R** (all) | **CRUD** |
| **`case_assignment_history`** | — | **R** | **RC** | **RC** | **R** | **R** | **CRUD** |
| **`master_grievance`** | **R** | **R** | **RU** | **CRUD** | **R** | **R** | **CRUD** |
| **`resolution_evidence`** | **R** (own) | **CR** | **CRU** | **CRU** | **R** | **R** | **CRUD** |
| **`citizen_feedback`** | **CR** (own) | — | **R** | **R** | **R** | **R** | **CRUD** |
| **`civic_asset`** | **R** | **R** | **RU** | **CRUD** | **R** | **R** | **CRUD** |
| **`sla_policy`** | **R** | **R** | **R** | **R** | **R** | **R** | **CRUD** |
| **`escalation_step`** | — | **R** | **RU** | **RU** | **RU** | **R** | **CRUD** |
| **`ai_action_log`** | — | — | — | — | **R** | **R** | **CRUD** |
| **`executive_brief`** | — | — | **R** | **R** | **CRU** | **R** | **CRUD** |

*Legend: C = Create, R = Read, U = Update, D = Delete, — = No Access*

---

## 3. Row-Level & Field-Level Security Rules

### 3.1 Citizen Data Isolation (BR19 & ACL)
- Citizens **CANNOT** read or search another citizen's complaints.
- Enforced server-side via `before_query` rule `BR19_Restrict_Citizen_Read_Visibility` and table ACL:
  ```javascript
  current.addQuery('citizen.user', gs.getUserID());
  ```

### 3.2 Officer Jurisdiction Scoping (BR20 & ACL)
- Case workers are restricted to complaints assigned to their department and ward.
- Ward Heads are restricted to cases within their ward.
- District Officers are restricted to cases within their district.

### 3.3 Field-Level Protection & ACL Implementation
- **Case Read Authorization (`sys_security_acl`: `78ce0993c3bb8754e54832f1b40131b0`)**:
  - Direct record read ACL evaluates advanced server-side script matching citizen ownership (`current.citizen.user == gs.getUserID()`) and worker jurisdiction (`ward` and `department`).
  - Works with `before_query` rule `BR19` and `BR20` to prevent unauthorized record access via Table API, REST, or list queries.
- **`original_description` Field ACL (`sys_security_acl`: `d0a9d553c33f8754e54832f1b4013140`)**:
  - Restricts raw unmasked complaint text to `x_2229367_civicone.admin` and `x_2229367_civicone.auditor` only.
  - Citizens, case workers, and external roles cannot read raw PII (Aadhaar/PAN).
  - Field is immutable once inserted (`BR22_Protect_Preserved_PII_Fields`).
- **`masked_description`**: Visible to field workers, citizens, and public reports.
- **`ai_action_log`**: Fully hidden from Citizens; read-only for Auditors; immutable on update/delete (`BR21_Protect_AI_Action_Log_Immutability`).

---

## 4. Attachment Security

- Attachments attached to `x_2229367_civicone_case` or `resolution_evidence` inherit parent record security.
- Citizens cannot read attachments on tickets they do not own.
- Only assigned case workers, ward heads, and admins can upload resolution evidence attachments.

---

## 5. Audit Logging Architecture

ServiceNow native auditing (`sys_audit`) is activated on:
- `x_2229367_civicone_case` (all status, priority, and assignment modifications)
- `x_2229367_civicone_master_grievance` (clustering changes)
- `x_2229367_civicone_case_assignment_history` (immutable assignment log)
