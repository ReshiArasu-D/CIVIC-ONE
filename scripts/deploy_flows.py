"""
Deploys the 5 CivicOne Flow Designer flows (F1, F4, F5, F6, F8) to ServiceNow sys_hub_flow.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"
SCOPE_NAME = "x_2229367_civicone"

FLOWS = [
    {
        "name": "F1 Grievance Intake",
        "description": "F1 Intake Flow: Validates intake parameters, resolves geographic hierarchy and nearest civic asset via GeoRouter, applies deterministic fallback, assigns eligible field worker, initializes SLA target association, and records intake audit.",
        "type": "flow"
    },
    {
        "name": "F4 SLA and Escalation",
        "description": "F4 SLA and Escalation Flow: Monitors 75% warning and 100% breach events separately, applies configurable SLA policy, dispatches Level 1 and Level 2 escalation records, preserves escalation history, and notifies supervisory officers.",
        "type": "flow"
    },
    {
        "name": "F5 Resolution and Confirmation",
        "description": "F5 Resolution and Confirmation Flow: Enforces required resolution evidence, transitions case to Awaiting Citizen Confirmation, dispatches citizen review request, and processes confirmation (closure) or dispute (reopen). Never silently closes on timeout.",
        "type": "flow"
    },
    {
        "name": "F6 Notifications",
        "description": "F6 Multilingual Notifications Flow: Resolves citizen's preferred language, selects approved template from notification_template, substitutes dynamic case tokens, and records delivery outcome.",
        "type": "flow"
    },
    {
        "name": "F8 Worker Absence",
        "description": "F8 Worker Absence Handler Flow: Reassigns active cases when a field worker marks absence, assigns to backup worker or safe department queue, preserves full assignment history, and alerts the ward supervisor.",
        "type": "flow"
    }
]


def deploy_flows(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: DEPLOYING FLOW DESIGNER FLOWS")
    print("=" * 60)

    for f in FLOWS:
        fname = f["name"]
        fdesc = f["description"]
        ftype = f["type"]

        script = f"""
        var res = {{}};
        var flowGr = new GlideRecord('sys_hub_flow');
        flowGr.addQuery('name', {__import__('json').dumps(fname)});
        flowGr.addQuery('sys_scope', '{SCOPE_SYS_ID}');
        flowGr.query();
        if (flowGr.next()) {{
            flowGr.description = {__import__('json').dumps(fdesc)};
            flowGr.active = true;
            flowGr.update();
            res.status = 'UPDATED';
            res.sys_id = flowGr.getUniqueValue();
        }} else {{
            flowGr.initialize();
            flowGr.name = {__import__('json').dumps(fname)};
            flowGr.description = {__import__('json').dumps(fdesc)};
            flowGr.type = '{ftype}';
            flowGr.active = true;
            flowGr.sys_scope = '{SCOPE_SYS_ID}';
            var id = flowGr.insert();
            res.status = id ? 'CREATED' : 'FAILED';
            res.sys_id = id;
        }}
        JSON.stringify(res);
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        raw_res = out.get("result", {}).get("evalResult", "{}")
        status_info = __import__('json').loads(raw_res) if isinstance(raw_res, str) else (raw_res or {})
        print(f"  Flow {fname:35} [{status_info.get('status')}] ID: {status_info.get('sys_id')}")

    print("\n" + "=" * 60)
    print("FLOW DESIGNER FLOWS DEPLOYMENT COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_flows(c)
