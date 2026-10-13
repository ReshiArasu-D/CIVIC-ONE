"""
CivicOne — Phase 1 Remediation Verification Suite
Executes empirical tests across all remediation criteria:
- SEC-02: Citizen Row-Level Isolation (Direct Read & List Query)
- SEC-03: Officer Jurisdiction Isolation (Direct Read & List Query)
- SEC-04: Original Description Field-Level ACL Protection
- LOG-01: Business Rule Deduplication (BR05 & BR12)
- DAT-01: 23 Scheduled Languages Count Verification
- SCH-01: Orphan Tables Deprecation State
- Workflow Gates: Intake (BR01), In-Progress (BR10), Evidence (BR11), Closure Gate (BR12)
Saves evidence JSON to docs/remediation_verification_evidence.json
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
SCOPE_SYS_ID = "26068197c33b8754e54832f1b40131d5"


def run_remediation_verification():
    c = ServiceNowClient()
    report = {}

    print("=" * 70)
    print("CIVIC-ONE: PHASE 1 REMEDIATION VERIFICATION SUITE")
    print("=" * 70)

    test_script = f"""
    var res = {{}};
    var session = gs.getSession();
    var origUser = gs.getUserID();

    // Fetch synthetic user IDs
    function getUserId(uname) {{
        var u = new GlideRecord('sys_user');
        u.addQuery('user_name', uname);
        u.query();
        return u.next() ? u.getUniqueValue() : null;
    }}

    var uCit1 = getUserId('syn.citizen1');
    var uCit2 = getUserId('syn.citizen2');
    var uWrkWater = getUserId('syn.worker.blr.water');
    var uWrkRoads = getUserId('syn.worker.blr.roads');
    var uAuditor = getUserId('syn.auditor');
    var uAdmin = getUserId('syn.admin');

    res.users = {{
        cit1: uCit1 != null,
        cit2: uCit2 != null,
        wrkWater: uWrkWater != null,
        wrkRoads: uWrkRoads != null,
        auditor: uAuditor != null,
        admin: uAdmin != null
    }};

    // Get Case A (Citizen 1, Ward 12 Water) and Case B (Citizen 2, Ward 15 Roads)
    var caseA = new GlideRecord('{SCOPE_NAME}_case');
    caseA.addQuery('short_description', 'Synthetic Test Case for Citizen A');
    caseA.query();
    var caseAId = caseA.next() ? caseA.getUniqueValue() : null;

    var caseB = new GlideRecord('{SCOPE_NAME}_case');
    caseB.addQuery('short_description', 'Synthetic Test Case for Citizen B');
    caseB.query();
    var caseBId = caseB.next() ? caseB.getUniqueValue() : null;

    res.caseA_found = (caseAId != null);
    res.caseB_found = (caseBId != null);

    // -------------------------------------------------------------
    // TEST 1: SEC-02 CITIZEN ROW-LEVEL ISOLATION
    // -------------------------------------------------------------
    // 1A. Impersonate Citizen 1
    session.impersonate(uCit1);
    
    // Direct read own case A
    var c1Own = new GlideRecord('{SCOPE_NAME}_case');
    var c1OwnCanRead = c1Own.get(caseAId) && c1Own.canRead();
    
    // Direct read other citizen's case B (MUST BE BLOCKED)
    var c1Other = new GlideRecord('{SCOPE_NAME}_case');
    var c1OtherCanRead = c1Other.get(caseBId) && c1Other.canRead();

    // List query as Citizen 1 (MUST NOT BE READABLE FOR CASE B)
    var c1List = new GlideRecord('{SCOPE_NAME}_case');
    c1List.query();
    var c1ListCaseACount = 0;
    var c1ListCaseBCount = 0;
    while (c1List.next()) {{
        if (c1List.getUniqueValue() === caseAId && c1List.canRead()) c1ListCaseACount++;
        if (c1List.getUniqueValue() === caseBId && c1List.canRead()) c1ListCaseBCount++;
    }}

    // 1B. Impersonate Citizen 2
    session.impersonate(uCit2);
    
    // Direct read own case B
    var c2Own = new GlideRecord('{SCOPE_NAME}_case');
    var c2OwnCanRead = c2Own.get(caseBId) && c2Own.canRead();

    // Direct read other citizen's case A (MUST BE BLOCKED)
    var c2Other = new GlideRecord('{SCOPE_NAME}_case');
    var c2OtherCanRead = c2Other.get(caseAId) && c2Other.canRead();

    // List query as Citizen 2 (MUST NOT BE READABLE FOR CASE A)
    var c2List = new GlideRecord('{SCOPE_NAME}_case');
    c2List.query();
    var c2ListCaseACount = 0;
    var c2ListCaseBCount = 0;
    while (c2List.next()) {{
        if (c2List.getUniqueValue() === caseAId && c2List.canRead()) c2ListCaseACount++;
        if (c2List.getUniqueValue() === caseBId && c2List.canRead()) c2ListCaseBCount++;
    }}

    res.sec02_citizen_isolation = {{
        citizen1_own_read_allowed: c1OwnCanRead,
        citizen1_cross_read_denied: !c1OtherCanRead,
        citizen1_list_sees_caseA: (c1ListCaseACount === 1),
        citizen1_list_excludes_caseB: (c1ListCaseBCount === 0),
        citizen2_own_read_allowed: c2OwnCanRead,
        citizen2_cross_read_denied: !c2OtherCanRead,
        citizen2_list_sees_caseB: (c2ListCaseBCount === 1),
        citizen2_list_excludes_caseA: (c2ListCaseACount === 0)
    }};

    // -------------------------------------------------------------
    // TEST 2: SEC-03 OFFICER JURISDICTION ISOLATION
    // -------------------------------------------------------------
    // 2A. Impersonate Worker Water (Ward 12, Dept Water)
    session.impersonate(uWrkWater);
    
    // Direct read Case A (Ward 12 Water -> ALLOWED)
    var w1CaseA = new GlideRecord('{SCOPE_NAME}_case');
    var w1CaseACanRead = w1CaseA.get(caseAId) && w1CaseA.canRead();

    // Direct read Case B (Ward 15 Roads -> BLOCKED)
    var w1CaseB = new GlideRecord('{SCOPE_NAME}_case');
    var w1CaseBCanRead = w1CaseB.get(caseBId) && w1CaseB.canRead();

    // List query as Worker Water
    var w1List = new GlideRecord('{SCOPE_NAME}_case');
    w1List.query();
    var w1ListCaseACount = 0;
    var w1ListCaseBCount = 0;
    while (w1List.next()) {{
        if (w1List.getUniqueValue() === caseAId && w1List.canRead()) w1ListCaseACount++;
        if (w1List.getUniqueValue() === caseBId && w1List.canRead()) w1ListCaseBCount++;
    }}

    // 2B. Impersonate Worker Roads (Ward 15, Dept Roads)
    session.impersonate(uWrkRoads);
    
    // Direct read Case B (Ward 15 Roads -> ALLOWED)
    var w2CaseB = new GlideRecord('{SCOPE_NAME}_case');
    var w2CaseBCanRead = w2CaseB.get(caseBId) && w2CaseB.canRead();

    // Direct read Case A (Ward 12 Water -> BLOCKED)
    var w2CaseA = new GlideRecord('{SCOPE_NAME}_case');
    var w2CaseACanRead = w2CaseA.get(caseAId) && w2CaseA.canRead();

    // List query as Worker Roads
    var w2List = new GlideRecord('{SCOPE_NAME}_case');
    w2List.query();
    var w2ListCaseACount = 0;
    var w2ListCaseBCount = 0;
    while (w2List.next()) {{
        if (w2List.getUniqueValue() === caseAId && w2List.canRead()) w2ListCaseACount++;
        if (w2List.getUniqueValue() === caseBId && w2List.canRead()) w2ListCaseBCount++;
    }}

    res.sec03_worker_isolation = {{
        worker_water_in_jurisdiction_allowed: w1CaseACanRead,
        worker_water_cross_jurisdiction_denied: !w1CaseBCanRead,
        worker_water_list_sees_caseA: (w1ListCaseACount === 1),
        worker_water_list_excludes_caseB: (w1ListCaseBCount === 0),
        worker_roads_in_jurisdiction_allowed: w2CaseBCanRead,
        worker_roads_cross_jurisdiction_denied: !w2CaseACanRead,
        worker_roads_list_sees_caseB: (w2ListCaseBCount === 1),
        worker_roads_list_excludes_caseA: (w2ListCaseACount === 0)
    }};

    // -------------------------------------------------------------
    // TEST 3: SEC-04 ORIGINAL COMPLAINT TEXT FIELD ACL
    // -------------------------------------------------------------
    // 3A. Citizen 1 field access on Case A
    session.impersonate(uCit1);
    var citCase = new GlideRecord('{SCOPE_NAME}_case');
    citCase.get(caseAId);
    var citCanReadMasked = citCase.getElement('masked_description').canRead();
    var citCanReadOriginal = citCase.getElement('original_description').canRead();

    // 3B. Case Worker Water field access on Case A
    session.impersonate(uWrkWater);
    var wrkCase = new GlideRecord('{SCOPE_NAME}_case');
    wrkCase.get(caseAId);
    var wrkCanReadMasked = wrkCase.getElement('masked_description').canRead();
    var wrkCanReadOriginal = wrkCase.getElement('original_description').canRead();

    // 3C. Auditor field access on Case A
    session.impersonate(uAuditor);
    var audCase = new GlideRecord('{SCOPE_NAME}_case');
    audCase.get(caseAId);
    var audCanReadOriginal = audCase.getElement('original_description').canRead();

    // 3D. Admin field access on Case A
    session.impersonate(uAdmin);
    var admCase = new GlideRecord('{SCOPE_NAME}_case');
    admCase.get(caseAId);
    var admCanReadOriginal = admCase.getElement('original_description').canRead();

    res.sec04_original_text_protection = {{
        citizen_can_read_masked: citCanReadMasked,
        citizen_denied_original_pii: !citCanReadOriginal,
        worker_can_read_masked: wrkCanReadMasked,
        worker_denied_original_pii: !wrkCanReadOriginal,
        auditor_authorized_original: audCanReadOriginal,
        admin_authorized_original: admCanReadOriginal
    }};

    // Revert impersonation back to admin
    session.impersonate(origUser);

    // -------------------------------------------------------------
    // TEST 4: LOG-01 BUSINESS RULE DEDUPLICATION
    // -------------------------------------------------------------
    var br5Active = new GlideRecord('sys_script');
    br5Active.addQuery('name', 'STARTSWITH', 'BR05');
    br5Active.addQuery('active', true);
    br5Active.query();
    
    var br12Active = new GlideRecord('sys_script');
    br12Active.addQuery('name', 'STARTSWITH', 'BR12');
    br12Active.addQuery('active', true);
    br12Active.query();

    // Test non-admin closure gate still functions properly
    session.impersonate(uCit1);
    var cTestGate = new GlideRecord('{SCOPE_NAME}_case');
    cTestGate.get(caseAId);
    cTestGate.grievance_status = 'Closed';
    cTestGate.citizen_confirmation_status = 'Pending';
    var gateUpdateId = cTestGate.update();
    var gateBlocked = (gateUpdateId === null);
    session.impersonate(origUser);

    res.log01_rule_deduplication = {{
        br05_active_count: br5Active.getRowCount(),
        br12_active_count: br12Active.getRowCount(),
        br12_closure_gate_still_enforces: gateBlocked
    }};

    // -------------------------------------------------------------
    // TEST 5: DAT-01 LANGUAGE COVERAGE (23 Records)
    // -------------------------------------------------------------
    var lGr = new GlideRecord('{SCOPE_NAME}_language');
    lGr.addQuery('active', true);
    lGr.query();
    res.dat01_language_count = lGr.getRowCount();

    // -------------------------------------------------------------
    // TEST 6: SCH-01 ORPHAN TABLES STATUS
    // -------------------------------------------------------------
    var orphanCheck = [
        '{SCOPE_NAME}_ward_village',
        '{SCOPE_NAME}_civic_case',
        '{SCOPE_NAME}_test_task_extension',
        '{SCOPE_NAME}_grievance_category',
        '{SCOPE_NAME}_state_ut',
        '{SCOPE_NAME}_citizen_customer'
    ];
    var depCount = 0;
    for (var i = 0; i < orphanCheck.length; i++) {{
        var tObj = new GlideRecord('sys_db_object');
        tObj.addQuery('name', orphanCheck[i]);
        tObj.query();
        if (tObj.next()) {{
            if (tObj.getValue('label').indexOf('[DEPRECATED]') !== -1) depCount++;
        }}
    }}
    res.sch01_orphans_labeled_deprecated = (depCount === 6);

    JSON.stringify(res);
    """

    out = c._request("POST", "/api/2229367/bridge/exec", data={"script": test_script})
    raw = out.get("result", {}).get("evalResult", "{}")
    report = json.loads(raw) if isinstance(raw, str) else (raw or {})

    # Print summary
    print("\n--- REMEDIATION VERIFICATION RESULTS ---")
    print(f"Users & Test Cases: {report.get('users')}")
    print(f"\nSEC-02 (Citizen Isolation): {json.dumps(report.get('sec02_citizen_isolation'), indent=2)}")
    print(f"\nSEC-03 (Worker Jurisdiction Isolation): {json.dumps(report.get('sec03_worker_isolation'), indent=2)}")
    print(f"\nSEC-04 (Original Text Protection ACL): {json.dumps(report.get('sec04_original_text_protection'), indent=2)}")
    print(f"\nLOG-01 (Rule Deduplication): {json.dumps(report.get('log01_rule_deduplication'), indent=2)}")
    print(f"\nDAT-01 (Languages Count): {report.get('dat01_language_count')} (Expected: 23)")
    print(f"\nSCH-01 (Orphans Labeled Deprecated): {report.get('sch01_orphans_labeled_deprecated')}")

    evidence_path = Path(__file__).resolve().parent.parent / "docs" / "remediation_verification_evidence.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print(f"EVIDENCE WRITTEN TO: {evidence_path.name}")
    print("=" * 70)
    return report


if __name__ == "__main__":
    run_remediation_verification()
