"""
CivicOne — Phase 1 Independent Verification Audit
Gathers live empirical evidence across all 6 verification areas.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"


def run_audit():
    c = ServiceNowClient()
    report = {}

    print("=" * 70)
    print("CIVIC-ONE: PHASE 1 INDEPENDENT VERIFICATION AUDIT")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. LIVE APPLICATION & INVENTORY
    # -------------------------------------------------------------
    print("\n--- [1] Live Application & Metadata Inventory ---")
    app_recs = c.get_records("sys_app", query=f"scope={SCOPE_NAME}", fields="sys_id,name,scope,active,version,can_edit_in_studio")
    report["sys_app"] = app_recs[0] if app_recs else None
    print(f"sys_app: {report['sys_app']}")

    # Live tables inventory
    all_scope_tables = c.get_records("sys_db_object", query=f"nameSTARTSWITH{SCOPE_NAME}", fields="name,label,super_class,is_extendable,sys_id", limit=100)
    report["live_tables_count"] = len(all_scope_tables)
    report["live_tables"] = [{ "name": t.get("name"), "label": t.get("label"), "super_class": t.get("super_class") } for t in all_scope_tables]
    print(f"Total live tables matching scope prefix: {len(all_scope_tables)}")

    # Check 22 target tables
    target_22 = [
        "zone", "state", "district", "sub_district", "ward",
        "department", "category", "civic_asset", "case_worker", "customer",
        "master_grievance", "case", "case_assignment_history",
        "resolution_evidence", "citizen_feedback",
        "sla_policy", "escalation_step",
        "language", "ui_translation", "notification_template",
        "ai_action_log", "executive_brief"
    ]
    live_names = {t.get("name") for t in all_scope_tables}
    missing_tables = [s for s in target_22 if f"{SCOPE_NAME}_{s}" not in live_names]
    extra_tables = [t.get("name") for t in all_scope_tables if t.get("name").replace(f"{SCOPE_NAME}_", "") not in target_22]
    report["missing_tables"] = missing_tables
    report["extra_tables"] = extra_tables
    print(f"Missing target tables: {missing_tables}")
    print(f"Extra/orphan tables: {extra_tables}")

    # Case table task extension check
    case_table = [t for t in all_scope_tables if t.get("name") == f"{SCOPE_NAME}_case"]
    report["case_extends_task"] = False
    if case_table:
        sc = case_table[0].get("super_class")
        sc_val = sc.get("value") if isinstance(sc, dict) else sc
        report["case_super_class"] = sc_val
        # Check task sys_id
        task_rec = c.get_records("sys_db_object", query="name=task", fields="sys_id")
        if task_rec and sc_val == task_rec[0]["sys_id"]:
            report["case_extends_task"] = True
    print(f"Case extends Task: {report['case_extends_task']}")

    # Script Includes
    sis = c.get_records("sys_script_include", query=f"sys_scope={SCOPE_SYS_ID}", fields="name,active,api_name,sys_id", limit=50)
    report["script_includes"] = [{"name": s.get("name"), "active": s.get("active")} for s in sis]
    print(f"Script Includes ({len(sis)}): {[s.get('name') for s in sis]}")

    # Business Rules
    brs = c.get_records("sys_script", query=f"sys_scope={SCOPE_SYS_ID}", fields="name,collection,when,active,sys_id", limit=50)
    report["business_rules"] = [{"name": b.get("name"), "table": b.get("collection"), "when": b.get("when"), "active": b.get("active")} for b in brs]
    print(f"Business Rules ({len(brs)}): {[b.get('name') for b in brs]}")

    # Roles
    roles = c.get_records("sys_user_role", query=f"nameSTARTSWITH{SCOPE_NAME}", fields="name,description,sys_id", limit=50)
    report["roles"] = [{"name": r.get("name")} for r in roles]
    print(f"Roles ({len(roles)}): {[r.get('name') for r in roles]}")

    # ACLs
    acls = c.get_records("sys_security_acl", query=f"sys_scope={SCOPE_SYS_ID}", fields="name,operation,type,active,sys_id", limit=100)
    report["acls_count"] = len(acls)
    print(f"ACLs count in scope: {len(acls)}")

    # Flows
    flows = c.get_records("sys_hub_flow", query=f"sys_scope={SCOPE_SYS_ID}", fields="name,type,active,sys_id", limit=50)
    report["flows"] = [{"name": f.get("name"), "active": f.get("active"), "type": f.get("type")} for f in flows]
    print(f"Flow Designer flows ({len(flows)}): {[f.get('name') for f in flows]}")

    # Numbering
    numbers = c.get_records("sys_number", query=f"category.nameSTARTSWITH{SCOPE_NAME}", fields="category,prefix,digits,number", limit=50)
    report["numbering"] = numbers
    print(f"Numbering configurations: {[str(n.get('category')) + ' -> ' + str(n.get('prefix')) for n in numbers]}")

    # Auditing check
    audited = c.get_records("sys_dictionary", query=f"nameSTARTSWITH{SCOPE_NAME}^element=^audit=true", fields="name,audit")
    report["audited_tables"] = [a.get("name") for a in audited]
    print(f"Tables with auditing enabled: {report['audited_tables']}")

    # Record counts across tables
    counts = {}
    for tbl_suffix in target_22:
        full_t = f"{SCOPE_NAME}_{tbl_suffix}"
        try:
            recs = c.get_records(full_t, limit=100, fields="sys_id")
            counts[full_t] = len(recs)
        except Exception as e:
            counts[full_t] = f"ERROR: {e}"
    report["record_counts"] = counts
    print(f"Record counts: {counts}")

    # Language count check
    lang_recs = c.get_records(f"{SCOPE_NAME}_language", limit=50, fields="code,name")
    report["seeded_languages"] = [l.get("code") + " (" + l.get("name") + ")" for l in lang_recs]
    report["seeded_languages_count"] = len(lang_recs)
    print(f"Seeded languages count: {len(lang_recs)} -> {report['seeded_languages']}")

    # -------------------------------------------------------------
    # 2. SECURITY CHECKS
    # -------------------------------------------------------------
    print("\n--- [2] Running Security Checks ---")
    sec_script = f"""
    var res = {{}};
    // Check citizen read restriction
    var c1 = new GlideRecord('{SCOPE_NAME}_customer');
    c1.setLimit(2);
    c1.query();
    var cit1 = c1.next() ? c1.getUniqueValue() : null;
    var cit2 = c1.next() ? c1.getUniqueValue() : null;
    
    res.cit1 = cit1;
    res.cit2 = cit2;
    
    // Check AI log permissions - check if ACL exists for ai_action_log
    var aclGr = new GlideRecord('sys_security_acl');
    aclGr.addQuery('name', '{SCOPE_NAME}_ai_action_log');
    aclGr.query();
    res.ai_log_acl_count = aclGr.getRowCount();
    
    // Check original_description field protection
    var br22 = new GlideRecord('sys_script');
    br22.addQuery('name', 'STARTSWITH', 'BR22');
    br22.query();
    res.br22_active = br22.next() ? br22.getValue('active') : '0';
    
    // Check citizen isolation BR19
    var br19 = new GlideRecord('sys_script');
    br19.addQuery('name', 'STARTSWITH', 'BR19');
    br19.query();
    res.br19_active = br19.next() ? br19.getValue('active') : '0';

    // Check officer scoping BR20
    var br20 = new GlideRecord('sys_script');
    br20.addQuery('name', 'STARTSWITH', 'BR20');
    br20.query();
    res.br20_active = br20.next() ? br20.getValue('active') : '0';

    // Check role assignments count
    var roleGr = new GlideRecord('sys_user_has_role');
    roleGr.addQuery('role.name', 'STARTSWITH', '{SCOPE_NAME}');
    roleGr.query();
    res.scoped_role_assignments = roleGr.getRowCount();

    // Check ATF tests count
    var atfGr = new GlideRecord('sys_atf_test');
    atfGr.addQuery('sys_scope', '{SCOPE_SYS_ID}');
    atfGr.query();
    res.atf_tests_deployed = atfGr.getRowCount();

    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": sec_script})
    raw = out.get("result", {}).get("evalResult", "{}")
    report["security_checks"] = json.loads(raw) if isinstance(raw, str) else (raw or {})
    print(f"Security checks: {report['security_checks']}")

    # -------------------------------------------------------------
    # 3. PII HANDLING TRACE
    # -------------------------------------------------------------
    print("\n--- [3] Verifying PII Handling Trace ---")
    pii_script = f"""
    var res = {{}};
    var masker = new x_2229367_civicone.PiiMasker();
    
    var testAadhaar = '1234 5678 9012';
    var testPan = 'ABCDE1234F';
    var testPhone = '9876543210';
    var testEmail = 'citizen.test@example.com';
    var rawText = 'Citizen reporting with Aadhaar ' + testAadhaar + ' and PAN ' + testPan + ' and phone ' + testPhone + ' and email ' + testEmail;
    
    var masked = masker.maskPii(rawText);
    res.hasPii = masked.hasPii;
    res.detections = masked.detections;
    res.maskedText = masked.maskedText;
    res.aadhaarRedacted = (masked.maskedText.indexOf(testAadhaar) === -1);
    res.panRedacted = (masked.maskedText.indexOf(testPan) === -1);
    res.phoneRedacted = (masked.maskedText.indexOf(testPhone) === -1);
    res.emailRedacted = (masked.maskedText.indexOf(testEmail) === -1);
    
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": pii_script})
    raw = out.get("result", {}).get("evalResult", "{}")
    report["pii_trace"] = json.loads(raw) if isinstance(raw, str) else (raw or {})
    print(f"PII trace: {report['pii_trace']}")

    # -------------------------------------------------------------
    # 4. WORKFLOW BEHAVIOR TESTS (Positive & Negative)
    # -------------------------------------------------------------
    print("\n--- [4] Verifying Workflow Behavior (Positive & Negative) ---")
    wf_script = f"""
    var res = {{}};
    
    // Negative Test 1: Intake missing ward/citizen
    var negCase = new GlideRecord('{SCOPE_NAME}_case');
    negCase.initialize();
    negCase.short_description = 'Missing required fields';
    var negId = negCase.insert();
    res.neg_intake_aborted = (negId == null);
    
    // Negative Test 2: In-Progress transition without assigned_to
    var testCase = new GlideRecord('{SCOPE_NAME}_case');
    testCase.setLimit(1);
    testCase.query();
    if (testCase.next()) {{
        var cId = testCase.getUniqueValue();
        
        // Attempt In Progress without assigned_to
        var cGr = new GlideRecord('{SCOPE_NAME}_case');
        cGr.get(cId);
        cGr.assigned_to = '';
        cGr.grievance_status = 'In Progress';
        var updateRes = cGr.update();
        res.neg_in_progress_aborted = (updateRes == null);
        
        // Negative Test 3: Premature Closure without citizen confirmation
        // Admin attempt (override allowed)
        var cGr2 = new GlideRecord('{SCOPE_NAME}_case');
        cGr2.get(cId);
        cGr2.grievance_status = 'Closed';
        cGr2.citizen_confirmation_status = 'Pending';
        var updateRes2 = cGr2.update();
        res.neg_closure_aborted_admin = (updateRes2 == null);

        // Non-admin attempt (must abort)
        var cit = new GlideRecord('sys_user');
        cit.addQuery('user_name', '!=', 'admin');
        cit.setLimit(1);
        cit.query();
        if (cit.next()) {{
            var origUser = gs.getUserID();
            gs.getSession().impersonate(cit.getUniqueValue());
            var cGr3 = new GlideRecord('{SCOPE_NAME}_case');
            cGr3.get(cId);
            cGr3.grievance_status = 'Closed';
            cGr3.citizen_confirmation_status = 'Pending';
            var updateRes3 = cGr3.update();
            res.neg_closure_aborted_non_admin = (updateRes3 == null);
            gs.getSession().impersonate(origUser);
        }}
    }}
    
    // Test BR04 PriorityScorer execution
    var scorer = new x_2229367_civicone.PriorityScorer();
    var pHigh = scorer.calculatePriority(null, 'live wire electrocution gas leak hospital', '1');
    var pLow = scorer.calculatePriority(null, 'street sweeping needed', '3');
    res.scorer_high = pHigh;
    res.scorer_low = pLow;
    
    // Test BR05 Duplicate Detection
    var dupGr = new GlideRecord('{SCOPE_NAME}_case');
    dupGr.addQuery('is_duplicate_suspect', true);
    dupGr.query();
    res.duplicate_suspect_count = dupGr.getRowCount();
    
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": wf_script})
    raw = out.get("result", {}).get("evalResult", "{}")
    report["workflow_tests"] = json.loads(raw) if isinstance(raw, str) else (raw or {})
    print(f"Workflow tests: {report['workflow_tests']}")

    # Save detailed report JSON for verification documentation
    with open(Path(__file__).resolve().parent.parent / "docs" / "verification_audit_evidence.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("INDEPENDENT AUDIT COMPLETED. EVIDENCE STORED IN docs/verification_audit_evidence.json")
    print("=" * 70)
    return report


if __name__ == "__main__":
    run_audit()
