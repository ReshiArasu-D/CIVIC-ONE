"""
Deploys the 9 CivicOne Project Roles to ServiceNow sys_user_role.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"
SCOPE_NAME = "x_2229367_civicone"

ROLES = [
    (f"{SCOPE_NAME}.citizen", "Citizen", "Citizen user: submit, track own cases, submit feedback"),
    (f"{SCOPE_NAME}.case_worker", "Case Worker", "Field operative: resolve assigned cases and submit evidence"),
    (f"{SCOPE_NAME}.ward_head", "Ward Sub-district Head", "Ward and Sub-District supervisory oversight and Level 1 escalation"),
    (f"{SCOPE_NAME}.district_officer", "District Officer", "District-level administrator and Level 2 SLA breach escalation handler"),
    (f"{SCOPE_NAME}.state_head", "State Head", "State-level director: policy and cross-district grievance governance"),
    (f"{SCOPE_NAME}.zonal_officer", "Zonal Officer", "Zonal coordinator across multi-state regions"),
    (f"{SCOPE_NAME}.commissioner", "Commissioner", "Apex public authority: city/state-wide executive oversight"),
    (f"{SCOPE_NAME}.admin", "CivicOne Administrator", "Application administration, SLA configurations, master data"),
    (f"{SCOPE_NAME}.auditor", "Auditor", "Read-only auditor: compliance, grievance history, AI action audit trail"),
]


def deploy_roles(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: DEPLOYING PROJECT ROLES")
    print("=" * 60)

    for role_name, label, desc in ROLES:
        script = f"""
        var res = {{}};
        var roleGr = new GlideRecord('sys_user_role');
        roleGr.addQuery('name', '{role_name}');
        roleGr.query();
        if (roleGr.next()) {{
            roleGr.description = '{desc}';
            roleGr.update();
            res.status = 'EXISTS';
            res.sys_id = roleGr.getUniqueValue();
        }} else {{
            roleGr.initialize();
            roleGr.name = '{role_name}';
            roleGr.description = '{desc}';
            roleGr.sys_scope = '{SCOPE_SYS_ID}';
            var id = roleGr.insert();
            res.status = id ? 'CREATED' : 'FAILED';
            res.sys_id = id;
        }}
        res;
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        status_info = out.get("result", {}).get("evalResult", {})
        print(f"  Role {role_name:38} [{status_info.get('status')}] ID: {status_info.get('sys_id')}")

    print("\n" + "=" * 60)
    print("ROLES DEPLOYMENT COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_roles(c)
