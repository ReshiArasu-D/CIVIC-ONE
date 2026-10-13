"""
CivicOne — Phase 1 Remediation Deployment Script
Executes Sprint A and Sprint B changes:
1. Hardens Case Read ACL (78ce0993c3bb8754e54832f1b40131b0) with row-level server script.
2. Converts BR19 to before_query rule for server-side citizen case scoping.
3. Converts BR20 to before_query rule for server-side officer jurisdiction scoping.
4. Creates field-level read ACL on x_2229367_civicone_case.original_description for admin/auditor only.
5. Deactivates duplicate Business Rules (BR05 and BR12).
6. Updates dictionary labels for 6 orphan prototype tables to document deprecation.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"


def run_remediation():
    c = ServiceNowClient()
    print("=" * 70)
    print("CIVIC-ONE: EXECUTING PHASE 1 REMEDIATION DEPLOYMENT")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. HARDEN CASE READ ACL (SEC-02, SEC-03)
    # -------------------------------------------------------------
    print("\n[1/6] Hardening Case Read ACL (sys_security_acl: 78ce0993c3bb8754e54832f1b40131b0)...")
    acl_script = """
    var res = {};
    var acl = new GlideRecord('sys_security_acl');
    if (acl.get('78ce0993c3bb8754e54832f1b40131b0')) {
        acl.advanced = true;
        acl.script = "(function() {\\n" +
            "    // Senior administrative and audit roles have unrestricted read\\n" +
            "    if (gs.hasRole('admin') || \\n" +
            "        gs.hasRole('x_2229367_civicone.admin') || \\n" +
            "        gs.hasRole('x_2229367_civicone.auditor') || \\n" +
            "        gs.hasRole('x_2229367_civicone.commissioner') || \\n" +
            "        gs.hasRole('x_2229367_civicone.state_head') || \\n" +
            "        gs.hasRole('x_2229367_civicone.zonal_officer')) {\\n" +
            "        return true;\\n" +
            "    }\\n\\n" +
            "    // Citizen role: strict ownership match\\n" +
            "    if (gs.hasRole('x_2229367_civicone.citizen')) {\\n" +
            "        var cust = new GlideRecord('x_2229367_civicone_customer');\\n" +
            "        cust.addQuery('user', gs.getUserID());\\n" +
            "        cust.query();\\n" +
            "        if (cust.next()) {\\n" +
            "            return (current.citizen.toString() === cust.getUniqueValue());\\n" +
            "        }\\n" +
            "        return false;\\n" +
            "    }\\n\\n" +
            "    // Case worker: strict jurisdiction & department match\\n" +
            "    if (gs.hasRole('x_2229367_civicone.case_worker')) {\\n" +
            "        var worker = new GlideRecord('x_2229367_civicone_case_worker');\\n" +
            "        worker.addQuery('user', gs.getUserID());\\n" +
            "        worker.query();\\n" +
            "        if (worker.next()) {\\n" +
            "            var wWard = worker.getValue('ward');\\n" +
            "            var wDept = worker.getValue('department');\\n" +
            "            var matchWard = !wWard || (current.ward.toString() === wWard);\\n" +
            "            var matchDept = !wDept || (current.department.toString() === wDept);\\n" +
            "            return (matchWard && matchDept);\\n" +
            "        }\\n" +
            "        return false;\\n" +
            "    }\\n\\n" +
            "    // Ward head: ward match\\n" +
            "    if (gs.hasRole('x_2229367_civicone.ward_head')) {\\n" +
            "        var wh = new GlideRecord('x_2229367_civicone_case_worker');\\n" +
            "        wh.addQuery('user', gs.getUserID());\\n" +
            "        wh.query();\\n" +
            "        if (wh.next()) {\\n" +
            "            var whWard = wh.getValue('ward');\\n" +
            "            return !whWard || (current.ward.toString() === whWard);\\n" +
            "        }\\n" +
            "        return false;\\n" +
            "    }\\n\\n" +
            "    // District officer: district match\\n" +
            "    if (gs.hasRole('x_2229367_civicone.district_officer')) {\\n" +
            "        var doW = new GlideRecord('x_2229367_civicone_case_worker');\\n" +
            "        doW.addQuery('user', gs.getUserID());\\n" +
            "        doW.query();\\n" +
            "        if (doW.next()) {\\n" +
            "            var doDist = doW.getValue('district');\\n" +
            "            return !doDist || (current.district.toString() === doDist);\\n" +
            "        }\\n" +
            "        return false;\\n" +
            "    }\\n\\n" +
            "    return false;\\n" +
            "})();";
        acl.update();
        res.status = 'SUCCESS';
    } else {
        res.status = 'ACL_NOT_FOUND';
    }
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": acl_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    # -------------------------------------------------------------
    # 2. CONVERT BR19 TO BEFORE_QUERY (SEC-02)
    # -------------------------------------------------------------
    print("\n[2/6] Converting BR19 to before_query rule (SEC-02)...")
    br19_script = """
    var res = {};
    var br19 = new GlideRecord('sys_script');
    if (br19.get('354051d7c3bb8754e54832f1b4013184')) {
        br19.when = 'before_query';
        br19.condition = '';
        br19.script = "(function executeRule(current, previous /*null when async*/) {\\n" +
            "    if (gs.hasRole('x_2229367_civicone.citizen') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.case_worker') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.auditor') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.commissioner') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.state_head') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.zonal_officer') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.admin') && \\n" +
            "        !gs.hasRole('admin')) {\\n" +
            "        var citGr = new GlideRecord('x_2229367_civicone_customer');\\n" +
            "        citGr.addQuery('user', gs.getUserID());\\n" +
            "        citGr.query();\\n" +
            "        if (citGr.next()) {\\n" +
            "            current.addQuery('citizen', citGr.getUniqueValue());\\n" +
            "        } else {\\n" +
            "            current.addQuery('sys_id', '-1');\\n" +
            "        }\\n" +
            "    }\\n" +
            "})(current, previous);";
        br19.update();
        res.status = 'SUCCESS';
    } else {
        res.status = 'NOT_FOUND';
    }
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": br19_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    # -------------------------------------------------------------
    # 3. CONVERT BR20 TO BEFORE_QUERY (SEC-03)
    # -------------------------------------------------------------
    print("\n[3/6] Converting BR20 to before_query rule (SEC-03)...")
    br20_script = """
    var res = {};
    var br20 = new GlideRecord('sys_script');
    if (br20.get('7b605dd7c3bb8754e54832f1b40131fe')) {
        br20.when = 'before_query';
        br20.condition = '';
        br20.script = "(function executeRule(current, previous /*null when async*/) {\\n" +
            "    if (gs.hasRole('x_2229367_civicone.case_worker') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.commissioner') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.state_head') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.zonal_officer') && \\n" +
            "        !gs.hasRole('x_2229367_civicone.admin') && \\n" +
            "        !gs.hasRole('admin')) {\\n" +
            "        var workerGr = new GlideRecord('x_2229367_civicone_case_worker');\\n" +
            "        workerGr.addQuery('user', gs.getUserID());\\n" +
            "        workerGr.query();\\n" +
            "        if (workerGr.next()) {\\n" +
            "            var wWard = workerGr.getValue('ward');\\n" +
            "            var wDept = workerGr.getValue('department');\\n" +
            "            if (wDept) current.addQuery('department', wDept);\\n" +
            "            if (wWard) current.addQuery('ward', wWard);\\n" +
            "        } else {\\n" +
            "            current.addQuery('sys_id', '-1');\\n" +
            "        }\\n" +
            "    }\\n" +
            "})(current, previous);";
        br20.update();
        res.status = 'SUCCESS';
    } else {
        res.status = 'NOT_FOUND';
    }
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": br20_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    # -------------------------------------------------------------
    # 4. CREATE FIELD-LEVEL READ ACL ON original_description (SEC-04)
    # -------------------------------------------------------------
    print("\n[4/6] Creating field-level read ACL on original_description (SEC-04)...")
    field_acl_script = f"""
    var res = {{}};
    var aclName = '{SCOPE_NAME}_case.original_description';
    var acl = new GlideRecord('sys_security_acl');
    acl.addQuery('name', aclName);
    acl.addQuery('operation', 'read');
    acl.query();
    var aclId = null;
    if (acl.next()) {{
        aclId = acl.getUniqueValue();
        res.status = 'EXISTS';
    }} else {{
        acl.initialize();
        acl.name = aclName;
        acl.operation = 'read';
        acl.type = 'record';
        acl.description = 'Strict field-level protection: restricts unmasked raw complaint text to admin and auditor only.';
        acl.sys_scope = '{SCOPE_SYS_ID}';
        aclId = acl.insert();
        res.status = 'CREATED';
    }}
    res.aclId = aclId;

    // Link roles: x_2229367_civicone.admin and x_2229367_civicone.auditor
    var rolesToAdd = ['d39e0193c3bb8754e54832f1b40131e9', '779e4193c3bb8754e54832f1b4013163'];
    for (var i = 0; i < rolesToAdd.length; i++) {{
        var m2m = new GlideRecord('sys_security_acl_role');
        m2m.addQuery('sys_security_acl', aclId);
        m2m.addQuery('sys_user_role', rolesToAdd[i]);
        m2m.query();
        if (!m2m.hasNext()) {{
            m2m.initialize();
            m2m.sys_security_acl = aclId;
            m2m.sys_user_role = rolesToAdd[i];
            m2m.sys_scope = '{SCOPE_SYS_ID}';
            m2m.insert();
        }}
    }}
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": field_acl_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    # -------------------------------------------------------------
    # 5. RESOLVE DUPLICATE BUSINESS RULES (LOG-01)
    # -------------------------------------------------------------
    print("\n[5/6] Deactivating duplicate Business Rules (LOG-01)...")
    br_dup_script = """
    var res = { deactivated: [] };
    // Deactivate redundant BR05 duplicates
    var dupBR05Ids = ['33ff0997c3bb8754e54832f1b4013104', '546099d7c3bb8754e54832f1b40131c7'];
    for (var i = 0; i < dupBR05Ids.length; i++) {
        var gr = new GlideRecord('sys_script');
        if (gr.get(dupBR05Ids[i])) {
            gr.active = false;
            gr.update();
            res.deactivated.push('BR05 duplicate: ' + dupBR05Ids[i]);
        }
    }
    // Deactivate redundant BR12 duplicate
    var dupBR12Id = 'fd601dd7c3bb8754e54832f1b401310f';
    var gr12 = new GlideRecord('sys_script');
    if (gr12.get(dupBR12Id)) {
        gr12.active = false;
        gr12.update();
        res.deactivated.push('BR12 duplicate: ' + dupBR12Id);
    }
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": br_dup_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    # -------------------------------------------------------------
    # 6. DOCUMENT DEPRECATION FOR 6 ORPHAN TABLES (SCH-01)
    # -------------------------------------------------------------
    print("\n[6/6] Labeling 6 orphan tables as DEPRECATED (SCH-01)...")
    dep_script = f"""
    var res = {{ updated: [] }};
    var orphans = [
        '{SCOPE_NAME}_ward_village',
        '{SCOPE_NAME}_civic_case',
        '{SCOPE_NAME}_test_task_extension',
        '{SCOPE_NAME}_grievance_category',
        '{SCOPE_NAME}_state_ut',
        '{SCOPE_NAME}_citizen_customer'
    ];
    for (var i = 0; i < orphans.length; i++) {{
        var tGr = new GlideRecord('sys_db_object');
        tGr.addQuery('name', orphans[i]);
        tGr.query();
        if (tGr.next()) {{
            var lbl = tGr.getValue('label');
            if (lbl.indexOf('[DEPRECATED]') === -1) {{
                tGr.label = '[DEPRECATED] ' + lbl;
                tGr.update();
                res.updated.push(orphans[i]);
            }}
        }}
    }}
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": dep_script})
    print(f"  Result: {out.get('result', {}).get('evalResult')}")

    print("\n" + "=" * 70)
    print("PHASE 1 REMEDIATION DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_remediation()
