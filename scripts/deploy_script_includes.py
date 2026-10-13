"""
Deploys the 6 CivicOne Server-Side Script Includes to ServiceNow sys_script_include.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"
SCRIPT_INCLUDES_DIR = Path(__file__).resolve().parent.parent / "app" / "script_includes"

SCRIPTS = [
    ("JurisdictionUtil", "JurisdictionUtil.js", "Geographic hierarchy and jurisdiction validation utilities"),
    ("GeoRouter", "GeoRouter.js", "Coordinates and address routing to administrative wards"),
    ("PriorityScorer", "PriorityScorer.js", "Deterministic multi-factor priority scoring engine"),
    ("PiiMasker", "PiiMasker.js", "Aadhaar, PAN, phone and email PII detection and masking"),
    ("NotificationComposer", "NotificationComposer.js", "Multilingual notification template composer"),
    ("AiLogger", "AiLogger.js", "Audit logging contract for AI and automated rule actions"),
]


def deploy_script_includes(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: DEPLOYING SCRIPT INCLUDES")
    print("=" * 60)

    for name, filename, description in SCRIPTS:
        filepath = SCRIPT_INCLUDES_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        script = f"""
        var res = {{}};
        var si = new GlideRecord('sys_script_include');
        si.addQuery('name', '{name}');
        si.addQuery('sys_scope', '{SCOPE_SYS_ID}');
        si.query();
        if (si.next()) {{
            si.script = {repr(code)};
            si.description = '{description}';
            si.active = true;
            si.access = 'public';
            si.update();
            res.status = 'UPDATED';
            res.sys_id = si.getUniqueValue();
        }} else {{
            si.initialize();
            si.name = '{name}';
            si.api_name = 'x_2229367_civicone.' + '{name}';
            si.script = {repr(code)};
            si.description = '{description}';
            si.active = true;
            si.access = 'public';
            si.sys_scope = '{SCOPE_SYS_ID}';
            var id = si.insert();
            res.status = id ? 'CREATED' : 'FAILED';
            res.sys_id = id;
        }}
        res;
        """
        out = c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        status_info = out.get("result", {}).get("evalResult", {})
        print(f"  Script Include {name:25} [{status_info.get('status')}] ID: {status_info.get('sys_id')}")

    print("\n" + "=" * 60)
    print("SCRIPT INCLUDES DEPLOYMENT COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    deploy_script_includes(c)
