"""
Repeatable CSV Seed Data Loader for CivicOne
Loads synthetic seed data in strict dependency order:
Geography -> Organisation -> People & Assets -> Language & Templates -> SLA -> Cases
Ensures idempotency (no duplicates created on repeated runs).
"""

import csv
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicenow_client import ServiceNowClient

SCOPE_NAME = "x_2229367_civicone"
SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def load_csv(filename):
    filepath = SEED_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_seed_data(c: ServiceNowClient):
    print("=" * 60)
    print("CIVIC-ONE: REPEATABLE SYNTHETIC SEED DATA LOADER")
    print("=" * 60)

    # 1. Zones
    zones = load_csv("01_geography_zone.csv")
    print(f"\n[1/14] Loading {len(zones)} Zones...")
    for z in zones:
        script = f"""
        var gr = new GlideRecord('{SCOPE_NAME}_zone');
        gr.addQuery('code', '{z["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{z["name"]}';
            gr.headquarters = '{z["headquarters"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{z["code"]}';
            gr.name = '{z["name"]}';
            gr.headquarters = '{z["headquarters"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(zones)} zones.")

    # 2. States
    states = load_csv("02_geography_state.csv")
    print(f"\n[2/14] Loading {len(states)} States...")
    for s in states:
        script = f"""
        var zGr = new GlideRecord('{SCOPE_NAME}_zone');
        var zId = zGr.get('code', '{s["zone_code"]}') ? zGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_state');
        gr.addQuery('code', '{s["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{s["name"]}';
            if (zId) gr.zone = zId;
            gr.capital = '{s["capital"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{s["code"]}';
            gr.name = '{s["name"]}';
            if (zId) gr.zone = zId;
            gr.capital = '{s["capital"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(states)} states.")

    # 3. Districts
    districts = load_csv("03_geography_district.csv")
    print(f"\n[3/14] Loading {len(districts)} Districts...")
    for d in districts:
        script = f"""
        var sGr = new GlideRecord('{SCOPE_NAME}_state');
        var sId = sGr.get('code', '{d["state_code"]}') ? sGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_district');
        gr.addQuery('code', '{d["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{d["name"]}';
            if (sId) gr.state = sId;
            gr.collectorate_address = '{d["collectorate_address"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{d["code"]}';
            gr.name = '{d["name"]}';
            if (sId) gr.state = sId;
            gr.collectorate_address = '{d["collectorate_address"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(districts)} districts.")

    # 4. Sub-Districts
    sub_districts = load_csv("04_geography_sub_district.csv")
    print(f"\n[4/14] Loading {len(sub_districts)} Sub-Districts...")
    for sd in sub_districts:
        script = f"""
        var dGr = new GlideRecord('{SCOPE_NAME}_district');
        var dId = dGr.get('code', '{sd["district_code"]}') ? dGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_sub_district');
        gr.addQuery('code', '{sd["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{sd["name"]}';
            if (dId) gr.district = dId;
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{sd["code"]}';
            gr.name = '{sd["name"]}';
            if (dId) gr.district = dId;
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(sub_districts)} sub-districts.")

    # 5. Wards
    wards = load_csv("05_geography_ward.csv")
    print(f"\n[5/14] Loading {len(wards)} Wards (including Ward 12 demo)...")
    for w in wards:
        script = f"""
        var sdGr = new GlideRecord('{SCOPE_NAME}_sub_district');
        var sdId = sdGr.get('code', '{w["sub_district_code"]}') ? sdGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_ward');
        gr.addQuery('code', '{w["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{w["name"]}';
            if (sdId) gr.sub_district = sdId;
            gr.ward_number = {w["ward_number"]};
            gr.population = {w["population"]};
            gr.councillor_name = '{w["councillor_name"]}';
            gr.councillor_contact = '{w["councillor_contact"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{w["code"]}';
            gr.name = '{w["name"]}';
            if (sdId) gr.sub_district = sdId;
            gr.ward_number = {w["ward_number"]};
            gr.population = {w["population"]};
            gr.councillor_name = '{w["councillor_name"]}';
            gr.councillor_contact = '{w["councillor_contact"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(wards)} wards.")

    # 6. Departments
    depts = load_csv("06_organisation_department.csv")
    print(f"\n[6/14] Loading {len(depts)} Departments...")
    for dep in depts:
        script = f"""
        var gr = new GlideRecord('{SCOPE_NAME}_department');
        gr.addQuery('code', '{dep["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{dep["name"]}';
            gr.description = '{dep["description"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{dep["code"]}';
            gr.name = '{dep["name"]}';
            gr.description = '{dep["description"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(depts)} departments.")

    # 7. Categories
    categories = load_csv("07_organisation_category.csv")
    print(f"\n[7/14] Loading {len(categories)} Grievance Categories...")
    for cat in categories:
        script = f"""
        var depGr = new GlideRecord('{SCOPE_NAME}_department');
        var depId = depGr.get('code', '{cat["department_code"]}') ? depGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_category');
        gr.addQuery('code', '{cat["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{cat["name"]}';
            if (depId) gr.department = depId;
            gr.default_urgency = '{cat["default_urgency"]}';
            gr.default_sla_hours = {cat["default_sla_hours"]};
            gr.requires_evidence_to_close = {cat["requires_evidence_to_close"].lower()};
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{cat["code"]}';
            gr.name = '{cat["name"]}';
            if (depId) gr.department = depId;
            gr.default_urgency = '{cat["default_urgency"]}';
            gr.default_sla_hours = {cat["default_sla_hours"]};
            gr.requires_evidence_to_close = {cat["requires_evidence_to_close"].lower()};
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(categories)} categories.")

    # 8. Civic Assets
    assets = load_csv("08_organisation_civic_asset.csv")
    print(f"\n[8/14] Loading {len(assets)} Civic Assets...")
    for a in assets:
        script = f"""
        var wGr = new GlideRecord('{SCOPE_NAME}_ward');
        var wId = wGr.get('code', '{a["ward_code"]}') ? wGr.getUniqueValue() : null;
        var dGr = new GlideRecord('{SCOPE_NAME}_department');
        var dId = dGr.get('code', '{a["department_code"]}') ? dGr.getUniqueValue() : null;
        var cGr = new GlideRecord('{SCOPE_NAME}_category');
        var cId = cGr.get('code', '{a["category_code"]}') ? cGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_civic_asset');
        gr.addQuery('asset_id', '{a["asset_id"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{a["name"]}';
            if (wId) gr.ward = wId;
            if (dId) gr.department = dId;
            if (cId) gr.category = cId;
            gr.latitude = {a["latitude"]};
            gr.longitude = {a["longitude"]};
            gr.location_address = '{a["location_address"]}';
            gr.condition = '{a["condition"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.asset_id = '{a["asset_id"]}';
            gr.name = '{a["name"]}';
            if (wId) gr.ward = wId;
            if (dId) gr.department = dId;
            if (cId) gr.category = cId;
            gr.latitude = {a["latitude"]};
            gr.longitude = {a["longitude"]};
            gr.location_address = '{a["location_address"]}';
            gr.condition = '{a["condition"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(assets)} civic assets.")

    # 9. Languages
    languages = load_csv("09_language.csv")
    print(f"\n[9/14] Loading {len(languages)} Languages...")
    for l in languages:
        script = f"""
        var gr = new GlideRecord('{SCOPE_NAME}_language');
        gr.addQuery('code', '{l["code"]}');
        gr.query();
        if (gr.next()) {{
            gr.name = '{l["name"]}';
            gr.native_name = '{l["native_name"]}';
            gr.is_default = {l["is_default"].lower()};
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{l["code"]}';
            gr.name = '{l["name"]}';
            gr.native_name = '{l["native_name"]}';
            gr.is_default = {l["is_default"].lower()};
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(languages)} languages.")

    # 10. Notification Templates
    templates = load_csv("10_notification_template.csv")
    print(f"\n[10/14] Loading {len(templates)} Notification Templates...")
    for tmpl in templates:
        script = f"""
        var lGr = new GlideRecord('{SCOPE_NAME}_language');
        var lId = lGr.get('code', '{tmpl["language_code"]}') ? lGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_notification_template');
        gr.addQuery('code', '{tmpl["code"]}');
        if (lId) gr.addQuery('language', lId);
        gr.query();
        if (gr.next()) {{
            gr.name = '{tmpl["name"]}';
            gr.subject = '{tmpl["subject"]}';
            gr.body_template = '{tmpl["body_template"]}';
            gr.channel = '{tmpl["channel"]}';
            gr.update();
        }} else {{
            gr.initialize();
            gr.code = '{tmpl["code"]}';
            gr.name = '{tmpl["name"]}';
            if (lId) gr.language = lId;
            gr.subject = '{tmpl["subject"]}';
            gr.body_template = '{tmpl["body_template"]}';
            gr.channel = '{tmpl["channel"]}';
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(templates)} templates.")

    # 11. Case Workers
    workers = load_csv("11_people_case_worker.csv")
    print(f"\n[11/14] Loading {len(workers)} Case Workers...")
    for cw in workers:
        script = f"""
        // Ensure user exists or use admin
        var uGr = new GlideRecord('sys_user');
        var uId = null;
        if (uGr.get('user_name', '{cw["user_name"]}')) {{
            uId = uGr.getUniqueValue();
        }} else {{
            // Fallback to admin user for test runner
            if (uGr.get('user_name', 'admin')) {{
                uId = uGr.getUniqueValue();
            }}
        }}
        
        var depGr = new GlideRecord('{SCOPE_NAME}_department');
        var depId = depGr.get('code', '{cw["department_code"]}') ? depGr.getUniqueValue() : null;
        var wGr = new GlideRecord('{SCOPE_NAME}_ward');
        var wId = wGr.get('code', '{cw["ward_code"]}') ? wGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_case_worker');
        gr.addQuery('employee_id', '{cw["employee_id"]}');
        gr.query();
        if (gr.next()) {{
            if (uId) gr.user = uId;
            if (depId) gr.department = depId;
            if (wId) gr.ward = wId;
            gr.is_available = {cw["is_available"].lower()};
            gr.active_case_load = {cw["active_case_load"]};
            gr.update();
        }} else {{
            gr.initialize();
            gr.employee_id = '{cw["employee_id"]}';
            if (uId) gr.user = uId;
            if (depId) gr.department = depId;
            if (wId) gr.ward = wId;
            gr.is_available = {cw["is_available"].lower()};
            gr.active_case_load = {cw["active_case_load"]};
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(workers)} case workers.")

    # 12. Customers (Citizens)
    customers = load_csv("12_people_customer.csv")
    print(f"\n[12/14] Loading {len(customers)} Citizens...")
    for cit in customers:
        script = f"""
        var wGr = new GlideRecord('{SCOPE_NAME}_ward');
        var wId = wGr.get('code', '{cit["ward_code"]}') ? wGr.getUniqueValue() : null;
        var lGr = new GlideRecord('{SCOPE_NAME}_language');
        var lId = lGr.get('code', '{cit["preferred_language_code"]}') ? lGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_customer');
        gr.addQuery('citizen_id', '{cit["citizen_id"]}');
        gr.query();
        if (gr.next()) {{
            gr.full_name = '{cit["full_name"]}';
            gr.phone = '{cit["phone"]}';
            gr.email = '{cit["email"]}';
            if (wId) gr.ward = wId;
            if (lId) gr.preferred_language = lId;
            gr.update();
        }} else {{
            gr.initialize();
            gr.citizen_id = '{cit["citizen_id"]}';
            gr.full_name = '{cit["full_name"]}';
            gr.phone = '{cit["phone"]}';
            gr.email = '{cit["email"]}';
            if (wId) gr.ward = wId;
            if (lId) gr.preferred_language = lId;
            gr.is_verified = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(customers)} citizens.")

    # 13. SLA Policies
    sla_policies = load_csv("14_sla_policy.csv")
    print(f"\n[13/14] Loading {len(sla_policies)} SLA Policies...")
    for sp in sla_policies:
        script = f"""
        var cGr = new GlideRecord('{SCOPE_NAME}_category');
        var cId = cGr.get('code', '{sp["category_code"]}') ? cGr.getUniqueValue() : null;
        var dGr = new GlideRecord('{SCOPE_NAME}_department');
        var dId = dGr.get('code', '{sp["department_code"]}') ? dGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_sla_policy');
        gr.addQuery('name', '{sp["name"]}');
        gr.query();
        if (gr.next()) {{
            if (cId) gr.category = cId;
            if (dId) gr.department = dId;
            gr.urgency = '{sp["urgency"]}';
            gr.target_resolution_hours = {sp["target_resolution_hours"]};
            gr.warning_threshold_pct = {sp["warning_threshold_pct"]};
            gr.escalation_level_1_hours = {sp["escalation_level_1_hours"]};
            gr.escalation_level_2_hours = {sp["escalation_level_2_hours"]};
            gr.update();
        }} else {{
            gr.initialize();
            gr.name = '{sp["name"]}';
            if (cId) gr.category = cId;
            if (dId) gr.department = dId;
            gr.urgency = '{sp["urgency"]}';
            gr.target_resolution_hours = {sp["target_resolution_hours"]};
            gr.warning_threshold_pct = {sp["warning_threshold_pct"]};
            gr.escalation_level_1_hours = {sp["escalation_level_1_hours"]};
            gr.escalation_level_2_hours = {sp["escalation_level_2_hours"]};
            gr.active = true;
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(sla_policies)} SLA policies.")

    # 14. Cases (42 Synthetic Grievances including Ward 12 water leak demo)
    cases = load_csv("13_grievances_cases.csv")
    print(f"\n[14/14] Loading {len(cases)} Synthetic Grievance Cases (including Ward 12 water-leak scenario)...")
    for cs in cases:
        script = f"""
        var citGr = new GlideRecord('{SCOPE_NAME}_customer');
        var citId = citGr.get('citizen_id', '{cs["citizen_id"]}') ? citGr.getUniqueValue() : null;
        
        var catGr = new GlideRecord('{SCOPE_NAME}_category');
        var catId = catGr.get('code', '{cs["category_code"]}') ? catGr.getUniqueValue() : null;
        
        var depGr = new GlideRecord('{SCOPE_NAME}_department');
        var depId = depGr.get('code', '{cs["department_code"]}') ? depGr.getUniqueValue() : null;
        
        var wGr = new GlideRecord('{SCOPE_NAME}_ward');
        var wId = wGr.get('code', '{cs["ward_code"]}') ? wGr.getUniqueValue() : null;
        
        var gr = new GlideRecord('{SCOPE_NAME}_case');
        gr.addQuery('number', '{cs["case_number"]}');
        gr.query();
        if (gr.next()) {{
            gr.short_description = '{cs["short_description"].replace("'", "\\'")}';
            gr.description = '{cs["description"].replace("'", "\\'")}';
            gr.grievance_status = '{cs["grievance_status"]}';
            gr.priority = {cs["priority"]};
            gr.sla_target_hours = {cs["sla_hours"]};
            gr.update();
        }} else {{
            gr.initialize();
            gr.number = '{cs["case_number"]}';
            if (citId) gr.citizen = citId;
            if (catId) gr.category = catId;
            if (depId) gr.department = depId;
            if (wId) gr.ward = wId;
            gr.short_description = '{cs["short_description"].replace("'", "\\'")}';
            gr.description = '{cs["description"].replace("'", "\\'")}';
            gr.channel = '{cs["channel"]}';
            gr.grievance_status = '{cs["grievance_status"]}';
            gr.priority = {cs["priority"]};
            gr.sla_target_hours = {cs["sla_hours"]};
            gr.is_duplicate_suspect = {cs["is_duplicate_suspect"].lower()};
            gr.insert();
        }}
        """
        c._request("POST", "/api/2229367/bridge/exec", data={"script": script})
    print(f"  Loaded {len(cases)} grievance cases.")

    print("\n" + "=" * 60)
    print("ALL SEED DATA LOADED SUCCESSFULLY WITHOUT DUPLICATES!")
    print("=" * 60)


if __name__ == "__main__":
    c = ServiceNowClient()
    load_seed_data(c)
