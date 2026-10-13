"""
Reload Languages Script for CivicOne
Idempotently loads 23 Indian Scheduled Languages + English into x_2229367_civicone_language
"""

import csv
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
CSV_PATH = Path(__file__).resolve().parent.parent / "seed" / "09_language.csv"


def load_languages():
    c = ServiceNowClient()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        languages = list(reader)

    print(f"Loading {len(languages)} languages from {CSV_PATH.name}...")

    for l in languages:
        code = l["code"]
        name = l["name"]
        native_name = l["native_name"].replace("'", "\\'")
        is_default = l["is_default"].lower()

        script = f"""
        var gr = new GlideRecord('{SCOPE_NAME}_language');
        gr.addQuery('code', '{code}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{name}';
            gr.native_name = '{native_name}';
            gr.is_default = {is_default};
            gr.active = true;
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{code}';
            gr.name = '{name}';
            gr.native_name = '{native_name}';
            gr.is_default = {is_default};
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})

    # Verify total records and list codes
    verify_script = f"""
    var res = {{ count: 0, languages: [] }};
    var gr = new GlideRecord('{SCOPE_NAME}_language');
    gr.orderBy('code');
    gr.query();
    res.count = gr.getRowCount();
    while (gr.next()) {{
        res.languages.push(gr.getValue('code') + ': ' + gr.getValue('name') + ' (' + gr.getValue('native_name') + ')');
    }}
    JSON.stringify(res);
    """
    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": verify_script})
    result = out.get("result", {}).get("evalResult", "{}")
    import json
    parsed = json.loads(result) if isinstance(result, str) else result
    print(f"Total languages verified in instance: {parsed.get('count')}")
    for item in parsed.get("languages", []):
        try:
            print(f"  - {item}")
        except UnicodeEncodeError:
            print(f"  - {item.encode('ascii', 'backslashreplace').decode('ascii')}")
    return parsed


if __name__ == "__main__":
    load_languages()
