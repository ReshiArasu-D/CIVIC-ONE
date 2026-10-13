"""
Deploys the 22 Business Rules (BR01-BR22) to ServiceNow sys_script.
Uses json.dumps to guarantee safe string escaping for all scripts and conditions.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"
SCOPE_NAME = "x_2229367_civicone"

BUSINESS_RULES = [
    {
        "id": "BR01",
        "name": "BR01_Validate_Intake_Requirements",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": False,
        "condition": "",
        "order": 100,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (!current.citizen || !current.category || !current.ward) {
        gs.addErrorMessage('Intake validation failed: Citizen, Grievance Category, and Ward Village are mandatory.');
        current.setAbortAction(true);
        return;
    }
    if (!current.channel) {
        current.channel = 'Web';
    }
    if (!current.grievance_status) {
        current.grievance_status = 'Submitted';
    }
})(current, previous);"""
    },
    {
        "id": "BR02",
        "name": "BR02_Preserve_Raw_Text_And_Mask_PII",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": False,
        "condition": "",
        "order": 110,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var raw = current.description.toString() || current.short_description.toString();
    current.original_description = raw;
    
    var masker = new x_2229367_civicone.PiiMasker();
    var res = masker.maskPii(raw);
    if (res.hasPii) {
        current.pii_masked = true;
        current.masked_description = res.maskedText;
        current.description = res.maskedText;
    } else {
        current.pii_masked = false;
        current.masked_description = raw;
    }
})(current, previous);"""
    },
    {
        "id": "BR03",
        "name": "BR03_Resolve_Geographic_Hierarchy",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": True,
        "condition": "current.ward.changes() || current.isNewRecord()",
        "order": 120,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (current.ward) {
        var jUtil = new x_2229367_civicone.JurisdictionUtil();
        var hier = jUtil.resolveHierarchyFromWard(current.ward.toString());
        if (hier) {
            if (hier.sub_district) current.sub_district = hier.sub_district;
            if (hier.district) current.district = hier.district;
            if (hier.state) current.state = hier.state;
            if (hier.zone) current.zone = hier.zone;
        }
    }
})(current, previous);"""
    },
    {
        "id": "BR04",
        "name": "BR04_Calculate_Priority_Score",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": True,
        "condition": "current.isNewRecord() || current.category.changes() || current.urgency.changes()",
        "order": 130,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var scorer = new x_2229367_civicone.PriorityScorer();
    var catId = current.category ? current.category.toString() : '';
    var text = current.description.toString() || '';
    var urg = current.urgency.toString();
    
    var res = scorer.calculatePriority(catId, text, urg);
    current.priority_score = res.score;
    current.priority = res.priority;
    
    // Audit contract
    var aiLog = new x_2229367_civicone.AiLogger();
    aiLog.logAction({
        case_id: current.getUniqueValue(),
        action_type: 'Priority Scoring',
        agent_name: 'RuleEngine:PriorityScorer',
        input_payload: { category: catId, urgency: urg, text_length: text.length },
        output_payload: { score: res.score, mapped_priority: res.priority, factors: res.factors },
        confidence_score: 1.0,
        execution_status: 'Success'
    });
})(current, previous);"""
    },
    {
        "id": "BR05",
        "name": "BR05_Detect_Potential_Duplicate_Grievances",
        "table": f"{SCOPE_NAME}_case",
        "when": "after",
        "insert": True,
        "update": False,
        "condition": "",
        "order": 140,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var gdt = new GlideDateTime();
    gdt.addSeconds(-72 * 3600);
    
    var dupGr = new GlideRecord('x_2229367_civicone_case');
    dupGr.addQuery('ward', current.ward);
    dupGr.addQuery('category', current.category);
    dupGr.addQuery('sys_id', '!=', current.getUniqueValue());
    dupGr.addQuery('sys_created_on', '>=', gdt);
    dupGr.orderByDesc('sys_created_on');
    dupGr.setLimit(1);
    dupGr.query();
    
    if (dupGr.next()) {
        var caseGr = new GlideRecord('x_2229367_civicone_case');
        if (caseGr.get(current.getUniqueValue())) {
            caseGr.is_duplicate_suspect = true;
            caseGr.duplicate_suspect_parent = dupGr.getUniqueValue();
            caseGr.update();
        }
        
        var aiLog = new x_2229367_civicone.AiLogger();
        aiLog.logAction({
            case_id: current.getUniqueValue(),
            action_type: 'Duplicate Detection',
            agent_name: 'RuleEngine:DuplicateDetector',
            input_payload: { ward: current.ward.toString(), category: current.category.toString() },
            output_payload: { suspected_parent: dupGr.getUniqueValue(), match_window_hours: 72 },
            confidence_score: 0.85,
            execution_status: 'Success',
            review_required: true
        });
    }
})(current, previous);"""
    },
    {
        "id": "BR06",
        "name": "BR06_Initialise_SLA_Association",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": False,
        "condition": "",
        "order": 150,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var targetHours = 48;
    if (current.category) {
        var policyGr = new GlideRecord('x_2229367_civicone_sla_policy');
        policyGr.addQuery('category', current.category);
        policyGr.addQuery('active', true);
        policyGr.query();
        if (policyGr.next()) {
            targetHours = parseInt(policyGr.getValue('target_resolution_hours'), 10) || 48;
        } else {
            var catGr = new GlideRecord('x_2229367_civicone_category');
            if (catGr.get(current.category.toString())) {
                targetHours = parseInt(catGr.getValue('default_sla_hours'), 10) || 48;
            }
        }
    }
    current.sla_target_hours = targetHours;
})(current, previous);"""
    },
    {
        "id": "BR07",
        "name": "BR07_Enforce_Eligible_Assignment",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": True,
        "update": True,
        "condition": "current.assigned_to.changes() && !current.assigned_to.nil()",
        "order": 160,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var jUtil = new x_2229367_civicone.JurisdictionUtil();
    var isAuth = jUtil.isWorkerAuthorized(
        current.assigned_to.toString(),
        current.ward ? current.ward.toString() : '',
        current.department ? current.department.toString() : ''
    );
    if (!isAuth) {
        gs.addErrorMessage('Assignment Rejected: Assigned worker is not authorized or currently unavailable for this department/jurisdiction.');
        current.setAbortAction(true);
    }
})(current, previous);"""
    },
    {
        "id": "BR08",
        "name": "BR08_Record_Assignment_History",
        "table": f"{SCOPE_NAME}_case",
        "when": "after",
        "insert": True,
        "update": True,
        "condition": "current.assigned_to.changes() && !current.assigned_to.nil()",
        "order": 170,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var histGr = new GlideRecord('x_2229367_civicone_case_assignment_history');
    histGr.initialize();
    histGr.case = current.getUniqueValue();
    histGr.assigned_from_worker = previous ? previous.assigned_to : null;
    histGr.assigned_to_worker = current.assigned_to;
    histGr.assigned_by = gs.getUserID();
    histGr.assignment_time = new GlideDateTime();
    histGr.reason = current.worker_absent_reassigned ? 'Worker Absence' : (previous && previous.assigned_to ? 'Rebalancing' : 'Initial Intake');
    histGr.notes = 'Assigned to field worker ' + current.assigned_to.getDisplayValue();
    histGr.insert();
})(current, previous);"""
    },
    {
        "id": "BR09",
        "name": "BR09_Worker_Absence_Auto_Reassignment",
        "table": f"{SCOPE_NAME}_case_worker",
        "when": "after",
        "update": True,
        "condition": "current.is_available.changesTo(false)",
        "order": 180,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var backupUser = null;
    if (current.backup_worker) {
        var bGr = new GlideRecord('x_2229367_civicone_case_worker');
        if (bGr.get(current.backup_worker.toString()) && bGr.getValue('is_available') == '1') {
            backupUser = bGr.getValue('user');
        }
    }
    
    var caseGr = new GlideRecord('x_2229367_civicone_case');
    caseGr.addQuery('assigned_to', current.user);
    caseGr.addQuery('grievance_status', 'IN', 'Assigned,In Progress');
    caseGr.query();
    
    while (caseGr.next()) {
        caseGr.worker_absent_reassigned = true;
        if (backupUser) {
            caseGr.assigned_to = backupUser;
            caseGr.work_notes = 'Reassigned to backup worker due to absence of ' + current.user.getDisplayValue();
        } else {
            caseGr.assigned_to = '';
            caseGr.grievance_status = 'Submitted';
            caseGr.work_notes = 'Worker marked unavailable without backup. Case unassigned to queue.';
        }
        caseGr.update();
    }
})(current, previous);"""
    },
    {
        "id": "BR10",
        "name": "BR10_Enforce_In_Progress_Prerequisite",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": False,
        "update": True,
        "condition": "current.grievance_status.changesTo('In Progress')",
        "order": 190,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (!current.assigned_to) {
        gs.addErrorMessage('Cannot transition to In Progress: An eligible worker must be assigned first.');
        current.setAbortAction(true);
    }
})(current, previous);"""
    },
    {
        "id": "BR11",
        "name": "BR11_Require_Evidence_Before_Resolution",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": False,
        "update": True,
        "condition": "current.grievance_status.changesTo('Resolved')",
        "order": 200,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var reqEvidence = true;
    if (current.category) {
        var catGr = new GlideRecord('x_2229367_civicone_category');
        if (catGr.get(current.category.toString())) {
            reqEvidence = (catGr.getValue('requires_evidence_to_close') == '1');
        }
    }
    
    if (reqEvidence) {
        var evGr = new GlideRecord('x_2229367_civicone_resolution_evidence');
        evGr.addQuery('case', current.getUniqueValue());
        evGr.query();
        if (!evGr.hasNext()) {
            gs.addErrorMessage('Resolution Blocked: Category requires Resolution Evidence (photo/inspection certificate) before case can be resolved.');
            current.setAbortAction(true);
            return;
        }
    }
    
    current.grievance_status = 'Awaiting Citizen Confirmation';
    current.citizen_confirmation_status = 'Pending';
    current.resolved_at = new GlideDateTime();
})(current, previous);"""
    },
    {
        "id": "BR12",
        "name": "BR12_Protect_Citizen_Confirmation_Closure_Gate",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": False,
        "update": True,
        "condition": "current.grievance_status.changesTo('Closed')",
        "order": 210,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (current.citizen_confirmation_status != 'Confirmed' && !gs.hasRole('x_2229367_civicone.admin')) {
        gs.addErrorMessage('Premature Closure Prevented: Grievance cannot be closed without citizen confirmation or administrative override.');
        current.setAbortAction(true);
    }
})(current, previous);"""
    },
    {
        "id": "BR13",
        "name": "BR13_Handle_Citizen_Confirmation",
        "table": f"{SCOPE_NAME}_citizen_feedback",
        "when": "after",
        "insert": True,
        "update": False,
        "condition": "current.action_confirmed == 'Confirmed'",
        "order": 220,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (current.case) {
        var cGr = new GlideRecord('x_2229367_civicone_case');
        if (cGr.get(current.case.toString())) {
            cGr.citizen_confirmation_status = 'Confirmed';
            cGr.grievance_status = 'Closed';
            cGr.close_notes = 'Closed following citizen verification and satisfaction feedback.';
            cGr.closed_at = new GlideDateTime();
            cGr.update();
        }
    }
})(current, previous);"""
    },
    {
        "id": "BR14",
        "name": "BR14_Handle_Citizen_Dispute",
        "table": f"{SCOPE_NAME}_citizen_feedback",
        "when": "after",
        "insert": True,
        "update": False,
        "condition": "current.action_confirmed == 'Disputed'",
        "order": 230,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (current.case) {
        var cGr = new GlideRecord('x_2229367_civicone_case');
        if (cGr.get(current.case.toString())) {
            cGr.citizen_confirmation_status = 'Disputed';
            cGr.dispute_reason = current.dispute_reason.toString();
            cGr.grievance_status = 'In Progress';
            cGr.work_notes = 'Citizen disputed resolution. Reason: ' + current.dispute_reason.toString() + '. Reopened to In Progress.';
            cGr.update();
            
            var escGr = new GlideRecord('x_2229367_civicone_escalation_step');
            escGr.initialize();
            escGr.case = cGr.getUniqueValue();
            escGr.escalation_level = 'Level 1 - Supervisor';
            escGr.trigger_reason = 'Citizen Dispute';
            escGr.escalated_at = new GlideDateTime();
            escGr.action_taken = 'Grievance reopened following citizen dispute';
            escGr.insert();
        }
    }
})(current, previous);"""
    },
    {
        "id": "BR15",
        "name": "BR15_Validate_Citizen_Feedback",
        "table": f"{SCOPE_NAME}_citizen_feedback",
        "when": "before",
        "insert": True,
        "update": False,
        "condition": "",
        "order": 240,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (!current.case || !current.citizen) {
        gs.addErrorMessage('Feedback validation failed: Case and Citizen references are mandatory.');
        current.setAbortAction(true);
        return;
    }
    if (!current.submitted_at) {
        current.submitted_at = new GlideDateTime();
    }
})(current, previous);"""
    },
    {
        "id": "BR16",
        "name": "BR16_SLA_Warning_Monitoring",
        "table": f"{SCOPE_NAME}_case",
        "when": "after",
        "insert": False,
        "update": True,
        "condition": "current.sla_breached.changes()",
        "order": 250,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var composer = new x_2229367_civicone.NotificationComposer();
    composer.composeNotification('SLA_WARNING', current.citizen ? current.citizen.toString() : '', {
        case_number: current.number.toString(),
        ward: current.ward ? current.ward.getDisplayValue() : '',
        status: current.grievance_status.toString()
    });
})(current, previous);"""
    },
    {
        "id": "BR17",
        "name": "BR17_SLA_Breach_Escalation",
        "table": f"{SCOPE_NAME}_case",
        "when": "after",
        "insert": False,
        "update": True,
        "condition": "current.sla_breached.changesTo(true)",
        "order": 260,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var escGr = new GlideRecord('x_2229367_civicone_escalation_step');
    escGr.initialize();
    escGr.case = current.getUniqueValue();
    escGr.escalation_level = 'Level 2 - District Officer';
    escGr.trigger_reason = 'SLA Breach 100%';
    escGr.escalated_at = new GlideDateTime();
    escGr.action_taken = 'Auto-escalated to District Officer due to SLA deadline expiration';
    escGr.insert();
})(current, previous);"""
    },
    {
        "id": "BR18",
        "name": "BR18_Trigger_Multilingual_Notifications",
        "table": f"{SCOPE_NAME}_case",
        "when": "after",
        "insert": True,
        "update": True,
        "condition": "current.isNewRecord() || current.grievance_status.changes()",
        "order": 270,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var composer = new x_2229367_civicone.NotificationComposer();
    var tmpl = current.isNewRecord() ? 'CASE_INTAKE' : (current.grievance_status == 'Awaiting Citizen Confirmation' ? 'CASE_RESOLVED' : 'CASE_ASSIGNED');
    
    composer.composeNotification(tmpl, current.citizen ? current.citizen.toString() : '', {
        case_number: current.number.toString(),
        citizen_name: current.citizen ? current.citizen.getDisplayValue() : 'Citizen',
        category: current.category ? current.category.getDisplayValue() : '',
        ward: current.ward ? current.ward.getDisplayValue() : '',
        sla_hours: current.sla_target_hours.toString(),
        status: current.grievance_status.toString()
    });
})(current, previous);"""
    },
    {
        "id": "BR19",
        "name": "BR19_Restrict_Citizen_Read_Visibility",
        "table": f"{SCOPE_NAME}_case",
        "when": "before_display",
        "query": False,
        "condition": "!gs.hasRole('x_2229367_civicone.case_worker') && !gs.hasRole('admin')",
        "order": 280,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (gs.hasRole('x_2229367_civicone.citizen')) {
        var citGr = new GlideRecord('x_2229367_civicone_customer');
        citGr.addQuery('user', gs.getUserID());
        citGr.query();
        if (citGr.next()) {
            if (current.citizen != citGr.getUniqueValue()) {
                current.setAbortAction(true);
            }
        } else {
            current.setAbortAction(true);
        }
    }
})(current, previous);"""
    },
    {
        "id": "BR20",
        "name": "BR20_Enforce_Officer_Jurisdiction_Scoping",
        "table": f"{SCOPE_NAME}_case",
        "when": "before_display",
        "query": False,
        "condition": "gs.hasRole('x_2229367_civicone.case_worker') && !gs.hasRole('x_2229367_civicone.commissioner') && !gs.hasRole('admin')",
        "order": 290,
        "script": """(function executeRule(current, previous /*null when async*/) {
    var workerGr = new GlideRecord('x_2229367_civicone_case_worker');
    workerGr.addQuery('user', gs.getUserID());
    workerGr.query();
    if (workerGr.next()) {
        var wWard = workerGr.getValue('ward');
        var wDept = workerGr.getValue('department');
        if (wDept && current.department != wDept) {
            current.setAbortAction(true);
        }
        if (wWard && current.ward != wWard) {
            current.setAbortAction(true);
        }
    }
})(current, previous);"""
    },
    {
        "id": "BR21",
        "name": "BR21_Protect_AI_Action_Log_Immutability",
        "table": f"{SCOPE_NAME}_ai_action_log",
        "when": "before",
        "update": True,
        "delete": True,
        "condition": "",
        "order": 300,
        "script": """(function executeRule(current, previous /*null when async*/) {
    gs.addErrorMessage('AI Action Log is immutable: modifications and deletions are forbidden for audit compliance.');
    current.setAbortAction(true);
})(current, previous);"""
    },
    {
        "id": "BR22",
        "name": "BR22_Protect_Preserved_PII_Fields",
        "table": f"{SCOPE_NAME}_case",
        "when": "before",
        "insert": False,
        "update": True,
        "condition": "current.original_description.changes()",
        "order": 310,
        "script": """(function executeRule(current, previous /*null when async*/) {
    if (previous && previous.original_description) {
        gs.addErrorMessage('Original description is an immutable evidentiary record and cannot be altered.');
        current.setAbortAction(true);
    }
})(current, previous);"""
    }
]


def deploy_business_rules(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: DEPLOYING 22 BUSINESS RULES (BR01-BR22)")
    print("=" * 60)

    for rule in BUSINESS_RULES:
        rid = rule["id"]
        rname = rule["name"]
        rtbl = rule["table"]
        rwhen = rule["when"]
        rinsert = "true" if rule.get("insert") else "false"
        rupdate = "true" if rule.get("update") else "false"
        rdelete = "true" if rule.get("delete") else "false"
        rquery = "true" if rule.get("query") else "false"
        rcond = rule.get("condition", "")
        rorder = rule.get("order", 100)
        rscript = rule["script"]

        script = f"""
        var res = {{}};
        var br = new GlideRecord('sys_script');
        br.addQuery('name', {json.dumps(rname)});
        br.addQuery('sys_scope', '{SCOPE_SYS_ID}');
        br.query();
        if (br.next()) {{
            br.collection = '{rtbl}';
            br.when = '{rwhen}';
            br.action_insert = {rinsert};
            br.action_update = {rupdate};
            br.action_delete = {rdelete};
            br.action_query = {rquery};
            br.condition = {json.dumps(rcond)};
            br.order = {rorder};
            br.script = {json.dumps(rscript)};
            br.active = true;
            br.update();
            res.status = 'UPDATED';
            res.sys_id = br.getUniqueValue();
        }} else {{
            br.initialize();
            br.name = {json.dumps(rname)};
            br.collection = '{rtbl}';
            br.when = '{rwhen}';
            br.action_insert = {rinsert};
            br.action_update = {rupdate};
            br.action_delete = {rdelete};
            br.action_query = {rquery};
            br.condition = {json.dumps(rcond)};
            br.order = {rorder};
            br.script = {json.dumps(rscript)};
            br.active = true;
            br.sys_scope = '{SCOPE_SYS_ID}';
            var id = br.insert();
            res.status = id ? 'CREATED' : 'FAILED';
            res.sys_id = id;
        }}
        JSON.stringify(res);
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        raw_res = out.get("result", {}).get("evalResult", "{}")
        status_info = json.loads(raw_res) if isinstance(raw_res, str) else (raw_res or {})
        print(f"  {rid:6} {rname:42} [{status_info.get('status')}] ID: {status_info.get('sys_id')}")

    print("\n" + "=" * 60)
    print("ALL 22 BUSINESS RULES DEPLOYED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_business_rules(c)
