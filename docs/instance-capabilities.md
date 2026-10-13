# ServiceNow Instance Capabilities Report

**Application:** CivicOne — Citizen Grievance Redressal (PS07)  
**Date of Inspection:** October 13, 2026  
**Inspection Mode:** Non-destructive Automated Capability Probe  
**Scoped Application:** `CivicOne`  
**Application Scope ID:** `26068197c33b8754e54832f1b40131d5`  
**Actual Platform Scope:** `x_2229367_civicone`  
*(Company Code: `2229367` assigned by ServiceNow Developer Program)*

---

## 1. Instance Version & Platform Baseline

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Instance URL** | `https://dev187180.service-now.com` | Personal Developer Instance (PDI) |
| **Glide Build Tag** | `glide-australia-02-11-2026__patch3-05-25-2026` | Australia Release, Patch 3 |
| **Glide Build Date** | `06-12-2026_1106` | Verified via `sys_properties` |
| **Glide WAR** | `glide-australia-02-11-2026__patch3-05-25-2026_06-12-2026_1106.zip` | Baseline release archive |
| **JavaScript Engine** | ES Latest (Rhino / Scoped ECMAScript 2021) | Scoped execution verified |

---

## 2. Scope & Application Architecture

- **Scope Name:** `x_2229367_civicone`
- **Scope Identifier (sys_scope):** `26068197c33b8754e54832f1b40131d5`
- **Application Record (sys_app):** `CivicOne` (version `1.0.0`)
- **Studio Support:** Enabled (`can_edit_in_studio: true`).
- **Source Control Support:** GitHub integration operational via Git repository `https://github.com/ReshiArasu-D/CIVIC-ONE.git`.

> **Note on Scope Name:** ServiceNow automatically enforces company-code scoping (`x_2229367_` + app name). All table names follow the format `x_2229367_civicone_<table_name>`. The build specification references `x_civres_` as an illustrative placeholder; as mandated by the instructions, the real platform scope `x_2229367_civicone` is strictly applied across all metadata, scripts, and tables.

---

## 3. Metadata Creation & Execution Capabilities

| Capability | Platform Status | Mechanism |
| :--- | :--- | :--- |
| **Scoped Tables & Fields** | **Available** | Created via `GlideTableCreator` / `sys_db_object` & `sys_dictionary` within scope |
| **Task Extension** | **Supported** | `task` table is extendable (`is_extendable: true`, `create_access: true`). Case table can extend `task` or implement standalone grievance with task-pattern fields. |
| **Script Includes** | **Available** | `sys_script_include` in scope `x_2229367_civicone` |
| **Business Rules** | **Available** | `sys_script` in scope `x_2229367_civicone` |
| **Access Control Lists (ACLs)** | **Available** | `sys_security_acl` and `sys_security_acl_role` in scope |
| **Flow Designer** | **Available** | `sys_hub_flow` and `sys_hub_action_type_definition` operational |
| **Automated Test Framework (ATF)** | **Available** | Plugin `com.glide.atf` active; `sys_atf_test` operational |
| **SLA Engine** | **Available** | `contract_sla` and `task_sla` engine operational |
| **Numbering Engine** | **Available** | `sys_number` operational |
| **Audit Engine** | **Available** | `sys_audit` operational; auditing configurable on scoped tables |

---

## 4. AI Entitlements & Studio Availability

| Component | Status | Capability Assessment |
| :--- | :--- | :--- |
| **Glide Virtual Agent (`com.glide.cs.chatbot`)** | **Available** | Plugin active; `sys_cs_topic` accessible for conversational intake in Phase 4. |
| **Natural Language Understanding (`sn_nlu`)** | **Available** | `sys_nlu_model` accessible for intent/entity parsing. |
| **Now Assist / GenAI Studio (`sn_now_assist`, `sn_genai`)** | **Unavailable (PDI Entitlement)** | Enterprise Now Assist licensing is not enabled on this PDI (`sys_gen_ai_prompt_template` inaccessible). |
| **Compatible Alternative for AI Phase (Phase 4)** | **Planned** | For Phase 4 AI capabilities, use external LLM REST integration via Scoped Script Include / Flow Action into `ai_action_log`, preserving full audit trail. Phase 1 implements the complete audit contract (`ai_action_log`) without invoking AI agents. |

---

## 5. Security & Credentials Policy

- **No Secrets in Version Control:** Credentials, tokens, session cookies, and passwords are strictly excluded via `.gitignore`.
- **Environment Isolation:** `.env` is stored locally and excluded from Git commits. A safe template `.env.example` is maintained.
- **Server-Side Security Enforcement:** All security and role validations are enforced server-side via ServiceNow ACLs and Business Rules, never client-side alone.
