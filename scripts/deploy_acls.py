"""
Deploys Access Control Lists (ACLs) and Role Bindings for CivicOne.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"
SCOPE_NAME = "x_2229367_civicone"

TABLE_PERMISSIONS = [
    # (table, operation, roles_allowed_list)
    (f"{SCOPE_NAME}_case", "create", [f"{SCOPE_NAME}.citizen", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case", "read", [f"{SCOPE_NAME}.citizen", f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.district_officer", f"{SCOPE_NAME}.state_head", f"{SCOPE_NAME}.zonal_officer", f"{SCOPE_NAME}.commissioner", f"{SCOPE_NAME}.auditor", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case", "write", [f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.district_officer", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case", "delete", [f"{SCOPE_NAME}.admin"]),
    
    (f"{SCOPE_NAME}_case_assignment_history", "read", [f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.district_officer", f"{SCOPE_NAME}.auditor", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case_assignment_history", "create", [f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case_assignment_history", "write", [f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_case_assignment_history", "delete", [f"{SCOPE_NAME}.admin"]),

    (f"{SCOPE_NAME}_resolution_evidence", "read", [f"{SCOPE_NAME}.citizen", f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.district_officer", f"{SCOPE_NAME}.auditor", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_resolution_evidence", "create", [f"{SCOPE_NAME}.case_worker", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_resolution_evidence", "write", [f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_resolution_evidence", "delete", [f"{SCOPE_NAME}.admin"]),

    (f"{SCOPE_NAME}_citizen_feedback", "read", [f"{SCOPE_NAME}.citizen", f"{SCOPE_NAME}.ward_head", f"{SCOPE_NAME}.district_officer", f"{SCOPE_NAME}.commissioner", f"{SCOPE_NAME}.auditor", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_citizen_feedback", "create", [f"{SCOPE_NAME}.citizen", f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_citizen_feedback", "write", [f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_citizen_feedback", "delete", [f"{SCOPE_NAME}.admin"]),

    (f"{SCOPE_NAME}_ai_action_log", "read", [f"{SCOPE_NAME}.auditor", f"{SCOPE_NAME}.admin", f"{SCOPE_NAME}.commissioner"]),
    (f"{SCOPE_NAME}_ai_action_log", "create", [f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_ai_action_log", "write", [f"{SCOPE_NAME}.admin"]),
    (f"{SCOPE_NAME}_ai_action_log", "delete", [f"{SCOPE_NAME}.admin"]),
]


def deploy_acls(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: DEPLOYING ACCESS CONTROL LISTS (ACLs)")
    print("=" * 60)

    for tbl, op, roles in TABLE_PERMISSIONS:
        script = f"""
        var res = {{}};
        var acl = new GlideRecord('sys_security_acl');
        acl.addQuery('type', 'record');
        acl.addQuery('name', '{tbl}');
        acl.addQuery('operation', '{op}');
        acl.addQuery('sys_scope', '{SCOPE_SYS_ID}');
        acl.query();
        var aclId = null;
        if (acl.next()) {{
            aclId = acl.getUniqueValue();
            res.status = 'EXISTS';
        }} else {{
            acl.initialize();
            acl.type = 'record';
            acl.name = '{tbl}';
            acl.operation = '{op}';
            acl.description = 'CivicOne ACL: ' + '{tbl}' + ' - ' + '{op}';
            acl.sys_scope = '{SCOPE_SYS_ID}';
            acl.active = true;
            aclId = acl.insert();
            res.status = aclId ? 'CREATED' : 'FAILED';
        }}
        res.aclId = aclId;
        
        // Link roles
        if (aclId) {{
            var roleNames = {repr(roles)};
            for (var i = 0; i < roleNames.length; i++) {{
                var rName = roleNames[i];
                var rGr = new GlideRecord('sys_user_role');
                if (rGr.get('name', rName)) {{
                    var aclRole = new GlideRecord('sys_security_acl_role');
                    aclRole.addQuery('sys_security_acl', aclId);
                    aclRole.addQuery('sys_user_role', rGr.getUniqueValue());
                    aclRole.query();
                    if (!aclRole.hasNext()) {{
                        aclRole.initialize();
                        aclRole.sys_security_acl = aclId;
                        aclRole.sys_user_role = rGr.getUniqueValue();
                        aclRole.sys_scope = '{SCOPE_SYS_ID}';
                        aclRole.insert();
                    }}
                }}
            }}
        }}
        res;
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        status_info = out.get("result", {}).get("evalResult", {})
        print(f"  ACL {tbl:35} Operation: {op:7} [{status_info.get('status')}]")

    print("\n" + "=" * 60)
    print("ACL DEPLOYMENT COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_acls(c)
