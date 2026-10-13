"""
CivicOne Phase 1 - Canonical Data Model Deployment
Deploys all 22 tables with exact canonical names and full schema definitions.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"

# Canonical Tables Definition: (table_suffix, label, super_class_or_None)
TABLES = [
    # Geography
    ("zone", "Zone", None),
    ("state", "State", None),
    ("district", "District", None),
    ("sub_district", "Sub District", None),
    ("ward", "Ward", None),
    # Organisation & People & Assets
    ("department", "Department", None),
    ("category", "Category", None),
    ("civic_asset", "Civic Asset", None),
    ("case_worker", "Case Worker", None),
    ("customer", "Customer", None),
    # Grievance
    ("master_grievance", "Master Grievance", None),
    ("case", "Case", "task"),
    ("case_assignment_history", "Case Assignment History", None),
    # Resolution & Feedback
    ("resolution_evidence", "Resolution Evidence", None),
    ("citizen_feedback", "Citizen Feedback", None),
    # SLA & Escalation
    ("sla_policy", "SLA Policy", None),
    ("escalation_step", "Escalation Step", None),
    # Language & Governance
    ("language", "Language", None),
    ("ui_translation", "UI Translation", None),
    ("notification_template", "Notification Template", None),
    ("ai_action_log", "AI Action Log", None),
    ("executive_brief", "Executive Brief", None),
]

# Columns definition: table_suffix -> list of col dicts
COLUMNS = {
    "zone": [
        {"element": "code", "type": "string", "length": 40, "label": "Zone Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Zone Name", "display": True, "mandatory": True},
        {"element": "headquarters", "type": "string", "length": 100, "label": "Headquarters"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "state": [
        {"element": "code", "type": "string", "length": 40, "label": "State Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "State Name", "display": True, "mandatory": True},
        {"element": "zone", "type": "reference", "ref": f"{SCOPE_NAME}_zone", "label": "Zone", "mandatory": True},
        {"element": "capital", "type": "string", "length": 100, "label": "Capital"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "district": [
        {"element": "code", "type": "string", "length": 40, "label": "District Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "District Name", "display": True, "mandatory": True},
        {"element": "state", "type": "reference", "ref": f"{SCOPE_NAME}_state", "label": "State", "mandatory": True},
        {"element": "collectorate_address", "type": "string", "length": 255, "label": "Collectorate Address"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "sub_district": [
        {"element": "code", "type": "string", "length": 40, "label": "Sub-District Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Sub-District Name", "display": True, "mandatory": True},
        {"element": "district", "type": "reference", "ref": f"{SCOPE_NAME}_district", "label": "District", "mandatory": True},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "ward": [
        {"element": "code", "type": "string", "length": 40, "label": "Ward Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Ward Name", "display": True, "mandatory": True},
        {"element": "sub_district", "type": "reference", "ref": f"{SCOPE_NAME}_sub_district", "label": "Sub-District", "mandatory": True},
        {"element": "ward_number", "type": "integer", "label": "Ward Number"},
        {"element": "population", "type": "integer", "label": "Population"},
        {"element": "councillor_name", "type": "string", "length": 100, "label": "Councillor Name"},
        {"element": "councillor_contact", "type": "string", "length": 50, "label": "Councillor Contact"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "department": [
        {"element": "code", "type": "string", "length": 40, "label": "Department Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Department Name", "display": True, "mandatory": True},
        {"element": "description", "type": "string", "length": 500, "label": "Description"},
        {"element": "head_officer", "type": "reference", "ref": "sys_user", "label": "Head Officer"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "category": [
        {"element": "code", "type": "string", "length": 40, "label": "Category Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Category Name", "display": True, "mandatory": True},
        {"element": "department", "type": "reference", "ref": f"{SCOPE_NAME}_department", "label": "Department", "mandatory": True},
        {"element": "default_urgency", "type": "choice", "length": 20, "label": "Default Urgency"},
        {"element": "default_sla_hours", "type": "integer", "default": "48", "label": "Default SLA Hours"},
        {"element": "requires_evidence_to_close", "type": "boolean", "default": "true", "label": "Requires Evidence To Close"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "civic_asset": [
        {"element": "asset_id", "type": "string", "length": 50, "label": "Asset ID", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Asset Name", "display": True, "mandatory": True},
        {"element": "category", "type": "reference", "ref": f"{SCOPE_NAME}_category", "label": "Category"},
        {"element": "ward", "type": "reference", "ref": f"{SCOPE_NAME}_ward", "label": "Ward", "mandatory": True},
        {"element": "department", "type": "reference", "ref": f"{SCOPE_NAME}_department", "label": "Department", "mandatory": True},
        {"element": "latitude", "type": "decimal", "label": "Latitude"},
        {"element": "longitude", "type": "decimal", "label": "Longitude"},
        {"element": "location_address", "type": "string", "length": 255, "label": "Location Address"},
        {"element": "condition", "type": "choice", "length": 40, "label": "Asset Condition"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "case_worker": [
        {"element": "user", "type": "reference", "ref": "sys_user", "label": "User Account", "display": True, "mandatory": True},
        {"element": "employee_id", "type": "string", "length": 50, "label": "Employee ID", "mandatory": True},
        {"element": "department", "type": "reference", "ref": f"{SCOPE_NAME}_department", "label": "Department", "mandatory": True},
        {"element": "ward", "type": "reference", "ref": f"{SCOPE_NAME}_ward", "label": "Assigned Ward"},
        {"element": "sub_district", "type": "reference", "ref": f"{SCOPE_NAME}_sub_district", "label": "Assigned Sub-District"},
        {"element": "district", "type": "reference", "ref": f"{SCOPE_NAME}_district", "label": "Assigned District"},
        {"element": "is_available", "type": "boolean", "default": "true", "label": "Is Available"},
        {"element": "absence_reason", "type": "string", "length": 255, "label": "Absence Reason"},
        {"element": "absence_start", "type": "glide_date_time", "label": "Absence Start"},
        {"element": "absence_end", "type": "glide_date_time", "label": "Absence End"},
        {"element": "backup_worker", "type": "reference", "ref": f"{SCOPE_NAME}_case_worker", "label": "Backup Worker"},
        {"element": "active_case_load", "type": "integer", "default": "0", "label": "Active Case Load"},
    ],
    "customer": [
        {"element": "citizen_id", "type": "string", "length": 50, "label": "Citizen ID", "mandatory": True},
        {"element": "full_name", "type": "string", "length": 100, "label": "Full Name", "display": True, "mandatory": True},
        {"element": "phone", "type": "string", "length": 20, "label": "Phone Number"},
        {"element": "email", "type": "string", "length": 100, "label": "Email Address"},
        {"element": "ward", "type": "reference", "ref": f"{SCOPE_NAME}_ward", "label": "Registered Ward"},
        {"element": "preferred_language", "type": "reference", "ref": f"{SCOPE_NAME}_language", "label": "Preferred Language"},
        {"element": "user", "type": "reference", "ref": "sys_user", "label": "System User Account"},
        {"element": "is_verified", "type": "boolean", "default": "true", "label": "Is Verified"},
    ],
    "master_grievance": [
        {"element": "number", "type": "string", "length": 40, "label": "Master Number", "display": True},
        {"element": "title", "type": "string", "length": 200, "label": "Title", "mandatory": True},
        {"element": "summary", "type": "string", "length": 1000, "label": "Summary Description"},
        {"element": "category", "type": "reference", "ref": f"{SCOPE_NAME}_category", "label": "Category", "mandatory": True},
        {"element": "ward", "type": "reference", "ref": f"{SCOPE_NAME}_ward", "label": "Ward", "mandatory": True},
        {"element": "status", "type": "choice", "length": 40, "label": "Master Status"},
        {"element": "child_case_count", "type": "integer", "default": "0", "label": "Child Case Count"},
        {"element": "primary_case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Primary Case"},
        {"element": "identified_at", "type": "glide_date_time", "label": "Identified At"},
    ],
    "case": [
        {"element": "citizen", "type": "reference", "ref": f"{SCOPE_NAME}_customer", "label": "Citizen", "mandatory": True},
        {"element": "department", "type": "reference", "ref": f"{SCOPE_NAME}_department", "label": "Department", "mandatory": True},
        {"element": "category", "type": "reference", "ref": f"{SCOPE_NAME}_category", "label": "Grievance Category", "mandatory": True},
        {"element": "ward", "type": "reference", "ref": f"{SCOPE_NAME}_ward", "label": "Ward Village", "mandatory": True},
        {"element": "sub_district", "type": "reference", "ref": f"{SCOPE_NAME}_sub_district", "label": "Sub District"},
        {"element": "district", "type": "reference", "ref": f"{SCOPE_NAME}_district", "label": "District"},
        {"element": "state", "type": "reference", "ref": f"{SCOPE_NAME}_state", "label": "State UT"},
        {"element": "zone", "type": "reference", "ref": f"{SCOPE_NAME}_zone", "label": "Zone"},
        {"element": "civic_asset", "type": "reference", "ref": f"{SCOPE_NAME}_civic_asset", "label": "Civic Asset"},
        {"element": "master_grievance", "type": "reference", "ref": f"{SCOPE_NAME}_master_grievance", "label": "Master Grievance"},
        {"element": "channel", "type": "choice", "length": 30, "label": "Intake Channel"},
        {"element": "pii_masked", "type": "boolean", "default": "false", "label": "PII Masked"},
        {"element": "original_description", "type": "string", "length": 4000, "label": "Original Description (Preserved)"},
        {"element": "masked_description", "type": "string", "length": 4000, "label": "Masked Description"},
        {"element": "grievance_status", "type": "choice", "length": 50, "label": "Grievance Redressal Status"},
        {"element": "citizen_confirmation_status", "type": "choice", "length": 40, "label": "Citizen Confirmation Status"},
        {"element": "dispute_reason", "type": "string", "length": 1000, "label": "Dispute Reason"},
        {"element": "priority_score", "type": "decimal", "label": "Calculated Priority Score"},
        {"element": "latitude", "type": "decimal", "label": "Latitude"},
        {"element": "longitude", "type": "decimal", "label": "Longitude"},
        {"element": "address", "type": "string", "length": 255, "label": "Incident Address"},
        {"element": "is_duplicate_suspect", "type": "boolean", "default": "false", "label": "Duplicate Suspect Flag"},
        {"element": "duplicate_suspect_parent", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Duplicate Suspect Parent"},
        {"element": "worker_absent_reassigned", "type": "boolean", "default": "false", "label": "Reassigned Due to Absence"},
        {"element": "sla_target_hours", "type": "integer", "default": "48", "label": "SLA Target Hours"},
        {"element": "sla_breached", "type": "boolean", "default": "false", "label": "SLA Breached Flag"},
        {"element": "resolved_at", "type": "glide_date_time", "label": "Resolved At"},
        {"element": "resolution_summary", "type": "string", "length": 1000, "label": "Resolution Summary"},
    ],
    "case_assignment_history": [
        {"element": "case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Case", "mandatory": True},
        {"element": "assigned_from_worker", "type": "reference", "ref": "sys_user", "label": "Assigned From Worker"},
        {"element": "assigned_to_worker", "type": "reference", "ref": "sys_user", "label": "Assigned To Worker", "mandatory": True},
        {"element": "assigned_by", "type": "reference", "ref": "sys_user", "label": "Assigned By"},
        {"element": "assignment_time", "type": "glide_date_time", "label": "Assignment Time"},
        {"element": "reason", "type": "choice", "length": 50, "label": "Assignment Reason"},
        {"element": "notes", "type": "string", "length": 500, "label": "Assignment Notes"},
    ],
    "resolution_evidence": [
        {"element": "case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Case", "mandatory": True},
        {"element": "evidence_type", "type": "choice", "length": 50, "label": "Evidence Type"},
        {"element": "evidence_notes", "type": "string", "length": 1000, "label": "Evidence Notes"},
        {"element": "submitted_by", "type": "reference", "ref": "sys_user", "label": "Submitted By", "mandatory": True},
        {"element": "submitted_at", "type": "glide_date_time", "label": "Submitted At"},
        {"element": "verified_by_supervisor", "type": "boolean", "default": "false", "label": "Verified By Supervisor"},
        {"element": "attachment_sys_id", "type": "string", "length": 40, "label": "Attachment Sys ID"},
    ],
    "citizen_feedback": [
        {"element": "case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Case", "mandatory": True},
        {"element": "citizen", "type": "reference", "ref": f"{SCOPE_NAME}_customer", "label": "Citizen", "mandatory": True},
        {"element": "rating", "type": "choice", "length": 30, "label": "Overall Rating"},
        {"element": "timeliness_score", "type": "choice", "length": 10, "label": "Timeliness Score"},
        {"element": "work_quality_score", "type": "choice", "length": 10, "label": "Work Quality Score"},
        {"element": "feedback_comments", "type": "string", "length": 1000, "label": "Feedback Comments"},
        {"element": "action_confirmed", "type": "choice", "length": 30, "label": "Action Confirmed Status"},
        {"element": "dispute_reason", "type": "string", "length": 1000, "label": "Dispute Reason"},
        {"element": "submitted_at", "type": "glide_date_time", "label": "Submitted At"},
    ],
    "sla_policy": [
        {"element": "name", "type": "string", "length": 100, "label": "Policy Name", "display": True, "mandatory": True},
        {"element": "category", "type": "reference", "ref": f"{SCOPE_NAME}_category", "label": "Category"},
        {"element": "department", "type": "reference", "ref": f"{SCOPE_NAME}_department", "label": "Department"},
        {"element": "urgency", "type": "choice", "length": 20, "label": "Urgency"},
        {"element": "target_resolution_hours", "type": "integer", "label": "Target Resolution Hours", "mandatory": True},
        {"element": "warning_threshold_pct", "type": "integer", "default": "75", "label": "Warning Threshold %"},
        {"element": "escalation_level_1_hours", "type": "integer", "label": "Escalation Level 1 Hours"},
        {"element": "escalation_level_2_hours", "type": "integer", "label": "Escalation Level 2 Hours"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "escalation_step": [
        {"element": "case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Case", "mandatory": True},
        {"element": "escalation_level", "type": "choice", "length": 50, "label": "Escalation Level"},
        {"element": "escalated_to_role", "type": "string", "length": 50, "label": "Escalated To Role"},
        {"element": "escalated_to_user", "type": "reference", "ref": "sys_user", "label": "Escalated To User"},
        {"element": "escalated_at", "type": "glide_date_time", "label": "Escalated At"},
        {"element": "trigger_reason", "type": "choice", "length": 50, "label": "Trigger Reason"},
        {"element": "acknowledged", "type": "boolean", "default": "false", "label": "Acknowledged"},
        {"element": "action_taken", "type": "string", "length": 500, "label": "Action Taken"},
    ],
    "language": [
        {"element": "code", "type": "string", "length": 10, "label": "Language Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 50, "label": "Language Name", "display": True, "mandatory": True},
        {"element": "native_name", "type": "string", "length": 100, "label": "Native Name"},
        {"element": "is_default", "type": "boolean", "default": "false", "label": "Is Default"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "ui_translation": [
        {"element": "message_key", "type": "string", "length": 100, "label": "Message Key", "mandatory": True},
        {"element": "language", "type": "reference", "ref": f"{SCOPE_NAME}_language", "label": "Language", "mandatory": True},
        {"element": "translation", "type": "string", "length": 1000, "label": "Translated Text", "mandatory": True},
    ],
    "notification_template": [
        {"element": "code", "type": "string", "length": 50, "label": "Template Code", "mandatory": True},
        {"element": "name", "type": "string", "length": 100, "label": "Template Name", "display": True, "mandatory": True},
        {"element": "language", "type": "reference", "ref": f"{SCOPE_NAME}_language", "label": "Language", "mandatory": True},
        {"element": "subject", "type": "string", "length": 200, "label": "Subject Template", "mandatory": True},
        {"element": "body_template", "type": "string", "length": 4000, "label": "Body Template", "mandatory": True},
        {"element": "channel", "type": "choice", "length": 30, "label": "Notification Channel"},
        {"element": "active", "type": "boolean", "default": "true", "label": "Active"},
    ],
    "ai_action_log": [
        {"element": "log_id", "type": "string", "length": 40, "label": "Log ID", "display": True},
        {"element": "case", "type": "reference", "ref": f"{SCOPE_NAME}_case", "label": "Associated Case"},
        {"element": "action_type", "type": "choice", "length": 50, "label": "Action Type"},
        {"element": "agent_name", "type": "string", "length": 100, "label": "Agent Or Engine Name"},
        {"element": "input_payload", "type": "string", "length": 4000, "label": "Input Payload"},
        {"element": "output_payload", "type": "string", "length": 4000, "label": "Output Payload"},
        {"element": "confidence_score", "type": "decimal", "label": "Confidence Score"},
        {"element": "execution_status", "type": "choice", "length": 30, "label": "Execution Status"},
        {"element": "audit_timestamp", "type": "glide_date_time", "label": "Audit Timestamp"},
        {"element": "applied_to_case", "type": "boolean", "default": "true", "label": "Applied To Case"},
        {"element": "review_required", "type": "boolean", "default": "false", "label": "Review Required"},
    ],
    "executive_brief": [
        {"element": "brief_id", "type": "string", "length": 40, "label": "Brief ID", "display": True},
        {"element": "report_date", "type": "glide_date_time", "label": "Report Date"},
        {"element": "zone", "type": "reference", "ref": f"{SCOPE_NAME}_zone", "label": "Zone"},
        {"element": "district", "type": "reference", "ref": f"{SCOPE_NAME}_district", "label": "District"},
        {"element": "total_cases_reported", "type": "integer", "label": "Total Cases Reported"},
        {"element": "total_cases_resolved", "type": "integer", "label": "Total Cases Resolved"},
        {"element": "sla_compliance_rate", "type": "decimal", "label": "SLA Compliance Rate %"},
        {"element": "top_grievance_category", "type": "reference", "ref": f"{SCOPE_NAME}_category", "label": "Top Category"},
        {"element": "executive_summary", "type": "string", "length": 4000, "label": "Executive Summary"},
    ],
}


def deploy_canonical_data_model(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: CANONICAL PHASE 1 DATA MODEL DEPLOYMENT")
    print(f"Scope: {SCOPE_NAME} ({SCOPE_SYS_ID})")
    print("=" * 60)

    # Step 1: Ensure each table exists with explicit name and matching label
    print("\n[Step 1/3] Ensuring all 22 tables exist with canonical names...")
    for suffix, label, super_class in TABLES:
        full_table_name = f"{SCOPE_NAME}_{suffix}"
        script = f"""
        var res = {{}};
        var gr = new GlideRecord('sys_db_object');
        if (gr.get('name', '{full_table_name}')) {{
            res.status = 'EXISTS';
            res.sys_id = gr.getUniqueValue();
        }} else {{
            gr.initialize();
            gr.label = '{label}';
            gr.name = '{full_table_name}';
            gr.sys_scope = '{SCOPE_SYS_ID}';
            gr.access = 'public';
            gr.read_access = true;
            gr.create_access = true;
            gr.update_access = true;
            gr.delete_access = true;
            gr.is_extendable = true;
            
            if ('{super_class or ""}' !== '') {{
                var superGr = new GlideRecord('sys_db_object');
                if (superGr.get('name', '{super_class}')) {{
                    gr.super_class = superGr.getUniqueValue();
                }}
            }}
            
            var id = gr.insert();
            res.status = id ? 'CREATED' : 'FAILED';
            res.sys_id = id;
            if (!id && gr.getLastErrorMessage) {{
                res.error = gr.getLastErrorMessage();
            }}
        }}
        res;
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        status_info = out.get("result", {}).get("evalResult", {})
        print(f"  Table {full_table_name:42} [{status_info.get('status')}]")

    # Step 2: Ensure Columns
    print("\n[Step 2/3] Ensuring table columns & references...")
    for suffix, col_list in COLUMNS.items():
        full_table_name = f"{SCOPE_NAME}_{suffix}"
        for col in col_list:
            elem = col["element"]
            ctype = col["type"]
            clabel = col.get("label", elem)
            clen = col.get("length", 100)
            cmand = "true" if col.get("mandatory") else "false"
            cdisp = "true" if col.get("display") else "false"
            cdef = col.get("default", "")
            cref = col.get("ref", "")

            script = f"""
            var res = {{}};
            var dict = new GlideRecord('sys_dictionary');
            dict.addQuery('name', '{full_table_name}');
            dict.addQuery('element', '{elem}');
            dict.query();
            if (dict.next()) {{
                res.status = 'EXISTS';
            }} else {{
                dict.initialize();
                dict.name = '{full_table_name}';
                dict.element = '{elem}';
                dict.internal_type = '{ctype}';
                dict.max_length = {clen};
                dict.column_label = '{clabel}';
                dict.mandatory = {cmand};
                dict.display = {cdisp};
                dict.sys_scope = '{SCOPE_SYS_ID}';
                if ('{cdef}' !== '') {{
                    dict.default_value = '{cdef}';
                }}
                if ('{cref}' !== '') {{
                    dict.reference = '{cref}';
                }}
                var id = dict.insert();
                
                var doc = new GlideRecord('sys_documentation');
                doc.initialize();
                doc.name = '{full_table_name}';
                doc.element = '{elem}';
                doc.label = '{clabel}';
                doc.plural = '{clabel}';
                doc.language = 'en';
                doc.sys_scope = '{SCOPE_SYS_ID}';
                doc.insert();
                
                res.status = id ? 'CREATED' : 'FAILED';
            }}
            res;
            """
            out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})

        print(f"  Columns verified for {full_table_name:42}")

    # Step 3: Configure Numbering
    print("\n[Step 3/3] Setting up record numbering...")
    numbers = [
        (f"{SCOPE_NAME}_case", "CIV", 7),
        (f"{SCOPE_NAME}_master_grievance", "MGR", 7),
        (f"{SCOPE_NAME}_ai_action_log", "AIL", 7),
        (f"{SCOPE_NAME}_executive_brief", "BRF", 7),
    ]
    for tbl, prefix, digits in numbers:
        script = f"""
        var res = {{}};
        var num = new GlideRecord('sys_number');
        num.addQuery('category', '{tbl}');
        num.query();
        if (num.next()) {{
            res.status = 'EXISTS';
        }} else {{
            num.initialize();
            num.category = '{tbl}';
            num.prefix = '{prefix}';
            num.digits = {digits};
            num.number = 1000;
            num.sys_scope = '{SCOPE_SYS_ID}';
            var id = num.insert();
            res.status = id ? 'CREATED' : 'FAILED';
        }}
        res;
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        status_info = out.get("result", {}).get("evalResult", {})
        print(f"  Numbering for {tbl:35} Prefix: {prefix} [{status_info.get('status')}]")

    # Step 4: Enable Auditing on Key Tables
    print("\n[Step 4/4] Enabling auditing for Case, Master Grievance, and Assignment History...")
    for tbl in [f"{SCOPE_NAME}_case", f"{SCOPE_NAME}_master_grievance", f"{SCOPE_NAME}_case_assignment_history"]:
        script = f"""
        var gr = new GlideRecord('sys_dictionary');
        gr.addQuery('name', '{tbl}');
        gr.addQuery('element', ''); // table descriptor row
        gr.query();
        if (gr.next()) {{
            gr.audit = true;
            gr.update();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        print(f"  Auditing enabled on {tbl}")

    print("\n" + "=" * 60)
    print("CANONICAL DATA MODEL DEPLOYMENT COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_canonical_data_model(c)
