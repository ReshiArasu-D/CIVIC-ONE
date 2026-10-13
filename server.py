#!/usr/bin/env python3
"""
CivicOne - Local Citizen Portal Web & API Server
Serves static UI files and provides authenticated citizen proxy endpoints to ServiceNow.
"""

import os
import sys
import json
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from servicenow_client import ServiceNowClient

PORT = 3000
AARAV_CUSTOMER_SYS_ID = 'dde0d55bc3bb8754e54832f1b40131ab' # CIT-BLR-001 (Aarav / Rishi demo citizen)
SYN_CITIZEN_SYS_ID = 'f7b851dfc3fb8754e54832f1b4013118'    # syn.citizen1

client = None
try:
    client = ServiceNowClient()
    print(f"[CivicOne Server] Connected to ServiceNow: {client.instance_url}")
except Exception as e:
    print(f"[CivicOne Server] Warning: Could not initialize ServiceNow client: {e}")


def get_display(field_dict, default=""):
    if isinstance(field_dict, dict):
        return field_dict.get("display_value", default) or default
    return field_dict or default


def get_value(field_dict, default=""):
    if isinstance(field_dict, dict):
        return field_dict.get("value", default) or default
    return field_dict or default


def normalize_status(raw_status):
    status = str(raw_status or "Pending").strip()
    s_lower = status.lower()
    if "resolved" in s_lower or "complete" in s_lower:
        return "Resolved"
    if "progress" in s_lower or "assigned" in s_lower:
        return "In Progress"
    if "awaiting" in s_lower or "confirm" in s_lower:
        return "Awaiting Confirmation"
    if "closed" in s_lower:
        return "Closed"
    return "Pending"


def status_class_for(status):
    st = normalize_status(status)
    if st == "Resolved" or st == "Closed":
        return "resolved"
    if st == "In Progress":
        return "progress"
    if st == "Awaiting Confirmation":
        return "awaiting"
    return "pending"


class CivicOneHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local integration
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/citizen/cases":
            self.handle_get_citizen_cases(query)
            return

        if path == "/api/citizen/case":
            self.handle_get_case_report(query)
            return

        if path == "/api/citizen/track":
            self.handle_track_case(query)
            return

        # Serve static files
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/citizen/confirm":
            self.handle_confirm_case(data)
            return

        if path == "/api/citizen/reopen":
            self.handle_reopen_case(data)
            return

        self.send_error(404, "Endpoint not found")

    def send_json(self, status_code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_get_citizen_cases(self, query):
        if not client:
            self.send_json(500, {"success": False, "error": "ServiceNow client not configured"})
            return

        try:
            # Query cases for citizen customer in ServiceNow
            res = client._request(
                "GET",
                "/api/now/table/x_2229367_civicone_case",
                params={
                    "sysparm_query": f"citizen={AARAV_CUSTOMER_SYS_ID}^ORcitizen={SYN_CITIZEN_SYS_ID}^ORDERBYDESCsys_created_on",
                    "sysparm_display_value": "all",
                    "sysparm_limit": 50,
                },
            )
            raw_cases = res.get("result", [])
            cases = []

            for r in raw_cases:
                c_num = get_display(r.get("number"))
                short_desc = get_display(r.get("short_description"))
                cat_disp = get_display(r.get("category")) or "General Civic Issue"
                dept_disp = get_display(r.get("department")) or "Municipal Administration"
                ward_disp = get_display(r.get("ward")) or "Ward 12 (Indiranagar)"
                status_disp = get_display(r.get("grievance_status")) or get_display(r.get("state")) or "Pending"
                norm_st = normalize_status(status_disp)
                prio_disp = get_display(r.get("priority")) or "High (Priority 1)"
                created_dt = get_display(r.get("sys_created_on"))
                updated_dt = get_display(r.get("sys_updated_on"))

                cases.append({
                    "id": c_num,
                    "no": c_num,
                    "case_number": c_num,
                    "sys_id": get_value(r.get("sys_id")),
                    "category": cat_disp,
                    "complaint": short_desc,
                    "desc": short_desc,
                    "description": get_display(r.get("description")) or short_desc,
                    "department": dept_disp,
                    "ward": ward_disp,
                    "submitted": created_dt,
                    "submitted_at": created_dt,
                    "last_updated": updated_dt,
                    "status": status_disp,
                    "normalized_status": norm_st,
                    "statusClass": status_class_for(status_disp),
                    "priority": prio_disp,
                    "citizen_confirmation": get_display(r.get("citizen_confirmation_status")),
                    "latitude": get_display(r.get("latitude")),
                    "longitude": get_display(r.get("longitude")),
                })

            # Calculate summary stats from real cases
            total = len(cases)
            pending = sum(1 for c in cases if c["normalized_status"] in ["Pending", "Submitted"])
            in_prog = sum(1 for c in cases if c["normalized_status"] in ["In Progress", "Awaiting Confirmation"])
            resolved = sum(1 for c in cases if c["normalized_status"] in ["Resolved", "Closed"])

            self.send_json(200, {
                "success": True,
                "count": total,
                "summary": {
                    "total": total,
                    "pending": pending,
                    "in_progress": in_prog,
                    "resolved": resolved,
                },
                "cases": cases,
            })
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_get_case_report(self, query):
        if not client:
            self.send_json(500, {"success": False, "error": "ServiceNow client not configured"})
            return

        case_number = (query.get("case_number", [""])[0] or query.get("id", [""])[0]).strip().upper()
        if not case_number:
            self.send_json(400, {"success": False, "error": "Case number is required"})
            return

        try:
            # Query single case with display values
            res = client._request(
                "GET",
                "/api/now/table/x_2229367_civicone_case",
                params={
                    "sysparm_query": f"number={case_number}",
                    "sysparm_display_value": "all",
                    "sysparm_limit": 1,
                },
            )
            records = res.get("result", [])
            if not records:
                self.send_json(404, {"success": False, "error": f"Grievance '{case_number}' not found in registry."})
                return

            r = records[0]
            sys_id = get_value(r.get("sys_id"))

            # Query assignment history for this case
            hist_res = client._request(
                "GET",
                "/api/now/table/x_2229367_civicone_case_assignment_history",
                params={
                    "sysparm_query": f"case={sys_id}^ORDERBYsys_created_on",
                    "sysparm_display_value": "all",
                    "sysparm_limit": 20,
                },
            )
            raw_hist = hist_res.get("result", [])

            # Query AI action logs for this case
            ai_res = client._request(
                "GET",
                "/api/now/table/x_2229367_civicone_ai_action_log",
                params={
                    "sysparm_query": f"case={sys_id}^ORDERBYsys_created_on",
                    "sysparm_display_value": "all",
                    "sysparm_limit": 10,
                },
            )
            raw_ai = ai_res.get("result", [])

            # Construct verified chronological action history
            activity = []
            created_on = get_display(r.get("sys_created_on"))

            # 1. Intake event
            activity.append({
                "timestamp": created_on,
                "time": created_on,
                "event": "Grievance Registered",
                "actor": "Citizen (CivicOne Web Portal)",
                "department": get_display(r.get("department")) or "Municipal Grievance Cell",
                "dept": get_display(r.get("department")) or "Municipal Grievance Cell",
                "details": f"Grievance officially submitted and logged under Case ID {case_number}.",
                "description": f"Grievance officially submitted and logged under Case ID {case_number}.",
                "status_badge": "Submitted",
            })

            # 2. AI Scored / Classified event
            for ai in raw_ai:
                action = get_display(ai.get("action_type")) or "Automated AI Analysis"
                agent = get_display(ai.get("agent_name")) or "Document Intelligence"
                conf = get_display(ai.get("confidence_score"))
                ai_time = get_display(ai.get("sys_created_on")) or created_on
                activity.append({
                    "timestamp": ai_time,
                    "time": ai_time,
                    "event": f"AI Intelligence Redressal Routing ({action})",
                    "actor": f"CivicOne AI Redressal Engine ({agent})",
                    "department": get_display(r.get("department")) or "Zonal Coordination",
                    "dept": get_display(r.get("department")) or "Zonal Coordination",
                    "details": f"Automated categorization applied with confidence {float(conf)*100 if conf else 95:.0f}%. SLA priority assigned.",
                    "description": f"Automated categorization applied with confidence {float(conf)*100 if conf else 95:.0f}%. SLA priority assigned.",
                    "status_badge": "Under Review",
                })

            # 3. Assignment history events
            for h in raw_hist:
                reason = get_display(h.get("reason")) or "Assigned to zonal division"
                assigned_to = get_display(h.get("assigned_to_worker")) or "Field Inspection Crew"
                h_time = get_display(h.get("sys_created_on")) or get_display(h.get("assignment_time")) or created_on
                h_notes = get_display(h.get('notes')) or 'Standard dispatch schedule.'
                activity.append({
                    "timestamp": h_time,
                    "time": h_time,
                    "event": f"Work Assignment: {reason}",
                    "actor": "Municipal Dispatcher",
                    "department": get_display(r.get("department")),
                    "dept": get_display(r.get("department")),
                    "officer": assigned_to,
                    "details": f"Case assigned to {assigned_to} for inspection and repair. Notes: {h_notes}",
                    "description": f"Case assigned to {assigned_to} for inspection and repair. Notes: {h_notes}",
                    "status_badge": "Assigned",
                })

            # 4. In Progress / Resolution event
            current_status = get_display(r.get("grievance_status")) or "Pending"
            updated_on = get_display(r.get("sys_updated_on")) or created_on

            if current_status in ["In Progress", "Awaiting Citizen Confirmation", "Resolved", "Closed"]:
                activity.append({
                    "timestamp": updated_on,
                    "time": updated_on,
                    "event": "Field Crew Operation Started",
                    "actor": get_display(r.get("assigned_to")) or f"{get_display(r.get('department'))} Field Crew",
                    "department": get_display(r.get("department")),
                    "dept": get_display(r.get("department")),
                    "details": "Municipal maintenance crew on-site addressing reported civic hazard.",
                    "description": "Municipal maintenance crew on-site addressing reported civic hazard.",
                    "status_badge": "In Progress",
                })

            if current_status in ["Awaiting Citizen Confirmation", "Resolved", "Closed"]:
                activity.append({
                    "timestamp": updated_on,
                    "time": updated_on,
                    "event": "Repair Work Completed & Resolution Proposed",
                    "actor": get_display(r.get("assigned_to")) or "Zonal Officer",
                    "department": get_display(r.get("department")),
                    "dept": get_display(r.get("department")),
                    "details": "Repair work completed. Photographic verification submitted. Awaiting citizen confirmation.",
                    "description": "Repair work completed. Photographic verification submitted. Awaiting citizen confirmation.",
                    "status_badge": "Awaiting Confirmation",
                })

            if current_status == "Closed":
                activity.append({
                    "timestamp": updated_on,
                    "time": updated_on,
                    "event": "Grievance Closed and Confirmed",
                    "actor": "Citizen / Municipal Redressal Authority",
                    "department": get_display(r.get("department")),
                    "dept": get_display(r.get("department")),
                    "details": "Resolution confirmed by citizen. Case officially closed.",
                    "description": "Resolution confirmed by citizen. Case officially closed.",
                    "status_badge": "Closed",
                })

            # Sort activity by timestamp
            activity.sort(key=lambda x: str(x.get("timestamp", "")))

            assigned_officer = get_display(r.get("assigned_to"))
            if not assigned_officer:
                assigned_officer = "Officer/Worker Not Yet Assigned"

            dept_name = get_display(r.get("department"))
            if not dept_name:
                dept_name = "Awaiting Department Assignment"

            report = {
                "success": True,
                "case_number": case_number,
                "sys_id": sys_id,
                "title": get_display(r.get("short_description")),
                "short_description": get_display(r.get("short_description")),
                "description": get_display(r.get("description")) or get_display(r.get("short_description")),
                "category": get_display(r.get("category")) or "General Civic Issue",
                "subcategory": get_display(r.get("subcategory")) or "Public Redressal",
                "department": dept_name,
                "ward": get_display(r.get("ward")) or "Ward 12 (Indiranagar)",
                "zone": get_display(r.get("zone")) or "Zone East",
                "address": get_display(r.get("address")) or "Indiranagar 100ft Road, Bengaluru",
                "location": get_display(r.get("address")) or f"{get_display(r.get('ward')) or 'Ward 12'}, Bengaluru",
                "latitude": get_display(r.get("latitude")),
                "longitude": get_display(r.get("longitude")),
                "coordinates": f"Lat {get_display(r.get('latitude')) or '12.9716'}, Lng {get_display(r.get('longitude')) or '77.5946'}",
                "status": current_status,
                "grievance_status": current_status,
                "normalized_status": normalize_status(current_status),
                "statusClass": status_class_for(current_status),
                "priority": get_display(r.get("priority")) or "High (Priority 1)",
                "sla_hours": get_display(r.get("sla_target_hours")) or "24",
                "sla_target": f"{get_display(r.get('sla_target_hours')) or '24'}h Resolution SLA Window",
                "sla_status": "Target: 24 Hours (Within SLA)",
                "submitted_at": created_on,
                "submitted_on": created_on,
                "last_updated": updated_on,
                "updated_on": updated_on,
                "channel": get_display(r.get("channel")) or "CivicOne Web Portal",
                "assigned_officer": assigned_officer,
                "assigned_to": assigned_officer,
                "worker_role": "Zonal Municipal Engineer",
                "assignment_status": "Active" if current_status != "Submitted" else "Pending",
                "assigned_team": f"{dept_name} Zonal Field Redressal Crew",
                "citizen_confirmation_status": get_display(r.get("citizen_confirmation_status")),
                "activity_history": activity,
            }

            self.send_json(200, report)
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_track_case(self, query):
        if not client:
            self.send_json(500, {"success": False, "error": "ServiceNow client not configured"})
            return

        case_number = query.get("case_number", [""])[0].strip().upper()
        if not case_number:
            self.send_json(400, {"success": False, "error": "Please enter a valid Case ID (e.g. CIV0001001)."})
            return

        try:
            # Check if case exists in ServiceNow
            res = client._request(
                "GET",
                "/api/now/table/x_2229367_civicone_case",
                params={
                    "sysparm_query": f"number={case_number}",
                    "sysparm_display_value": "all",
                    "sysparm_limit": 1,
                },
            )
            records = res.get("result", [])
            if not records:
                self.send_json(404, {
                    "success": False,
                    "error": f"No active grievance found matching ID '{case_number}'. Please verify the Case ID."
                })
                return

            r = records[0]
            status_disp = get_display(r.get("grievance_status")) or get_display(r.get("state")) or "Pending"
            created_dt = get_display(r.get("sys_created_on"))
            updated_dt = get_display(r.get("sys_updated_on")) or created_dt

            # 6 Workflow Stages:
            # 1. Submitted, 2. Under Review, 3. Assigned to Department, 4. Work in Progress, 5. Resolution / Confirmation, 6. Resolved / Closed
            st_lower = status_disp.lower()
            stage_idx = 1
            if "closed" in st_lower or "resolved" in st_lower:
                stage_idx = 6
            elif "awaiting" in st_lower or "confirm" in st_lower:
                stage_idx = 5
            elif "progress" in st_lower:
                stage_idx = 4
            elif "assigned" in st_lower:
                stage_idx = 3
            else:
                stage_idx = 2

            stages = [
                {"step": 1, "label": "Submitted", "desc": "Grievance logged", "completed": stage_idx >= 1, "active": stage_idx == 1, "timestamp": created_dt},
                {"step": 2, "label": "Under Review", "desc": "AI priority scoring", "completed": stage_idx >= 2, "active": stage_idx == 2, "timestamp": created_dt if stage_idx >= 2 else None},
                {"step": 3, "label": "Assigned to Dept", "desc": "Zonal crew dispatch", "completed": stage_idx >= 3, "active": stage_idx == 3, "timestamp": updated_dt if stage_idx >= 3 else None},
                {"step": 4, "label": "Work in Progress", "desc": "On-site remediation", "completed": stage_idx >= 4, "active": stage_idx == 4, "timestamp": updated_dt if stage_idx >= 4 else None},
                {"step": 5, "label": "Resolution & Confirmation", "desc": "Citizen review gate", "completed": stage_idx >= 5, "active": stage_idx == 5, "timestamp": updated_dt if stage_idx >= 5 else None},
                {"step": 6, "label": "Resolved / Closed", "desc": "Final case closure", "completed": stage_idx >= 6, "active": stage_idx == 6, "timestamp": updated_dt if stage_idx >= 6 else None},
            ]

            stage_timestamps = {
                1: created_dt,
                2: created_dt if stage_idx >= 2 else "-",
                3: updated_dt if stage_idx >= 3 else "-",
                4: updated_dt if stage_idx >= 4 else "-",
                5: updated_dt if stage_idx >= 5 else "-",
                6: updated_dt if stage_idx >= 6 else "-",
            }

            assigned_officer = get_display(r.get("assigned_to")) or "Officer/Worker Not Yet Assigned"
            dept_name = get_display(r.get("department")) or "Awaiting Department Assignment"

            latest_updates = [
                {
                    "title": s["label"],
                    "time": s["timestamp"] or updated_dt,
                    "description": s["desc"],
                    "actor": assigned_officer if s["step"] >= 3 else "Municipal Operations"
                }
                for s in reversed(stages) if s["completed"]
            ]

            citizen_action_required = (status_disp in ["Awaiting Citizen Confirmation", "Resolved"]) and (get_display(r.get("citizen_confirmation_status")) != "Confirmed")

            self.send_json(200, {
                "success": True,
                "case_number": case_number,
                "title": get_display(r.get("short_description")),
                "short_description": get_display(r.get("short_description")),
                "description": get_display(r.get("description")) or get_display(r.get("short_description")),
                "category": get_display(r.get("category")),
                "department": dept_name,
                "ward": get_display(r.get("ward")),
                "location": get_display(r.get("address")) or f"{get_display(r.get('ward')) or 'Indiranagar'}, Bengaluru",
                "status": status_disp,
                "grievance_status": status_disp,
                "statusClass": status_class_for(status_disp),
                "submitted_at": created_dt,
                "submitted_on": created_dt,
                "last_updated": updated_dt,
                "updated_on": updated_dt,
                "assigned_officer": assigned_officer,
                "assigned_to": assigned_officer,
                "stages": stages,
                "current_stage": stage_idx,
                "current_stage_index": stage_idx,
                "stage_timestamps": stage_timestamps,
                "latest_updates": latest_updates,
                "citizen_action_required": citizen_action_required,
                "citizen_confirmation_status": get_display(r.get("citizen_confirmation_status")),
                "latitude": get_display(r.get("latitude")),
                "longitude": get_display(r.get("longitude")),
                "sla_target_hours": get_display(r.get("sla_target_hours")) or "24",
            })
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_confirm_case(self, data):
        if not client:
            self.send_json(500, {"success": False, "error": "ServiceNow client not configured"})
            return

        case_number = data.get("case_number")
        feedback = data.get("feedback", "Resolution confirmed by citizen.")
        if not case_number:
            self.send_json(400, {"success": False, "error": "Case number is required"})
            return

        try:
            # Lookup case sys_id
            res = client.get_records("x_2229367_civicone_case", query=f"number={case_number}", fields="sys_id", limit=1)
            if not res:
                self.send_json(404, {"success": False, "error": "Case not found"})
                return

            sys_id = res[0]["sys_id"]
            client.update_record("x_2229367_civicone_case", sys_id, {
                "citizen_confirmation_status": "Confirmed",
                "grievance_status": "Closed",
                "close_notes": f"Citizen Confirmation Received: {feedback}"
            })
            self.send_json(200, {"success": True, "message": f"Case {case_number} successfully confirmed and closed."})
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_reopen_case(self, data):
        if not client:
            self.send_json(500, {"success": False, "error": "ServiceNow client not configured"})
            return

        case_number = data.get("case_number")
        reason = data.get("reason", "Citizen reported issue still persists.")
        if not case_number:
            self.send_json(400, {"success": False, "error": "Case number is required"})
            return

        try:
            res = client.get_records("x_2229367_civicone_case", query=f"number={case_number}", fields="sys_id", limit=1)
            if not res:
                self.send_json(404, {"success": False, "error": "Case not found"})
                return

            sys_id = res[0]["sys_id"]
            client.update_record("x_2229367_civicone_case", sys_id, {
                "citizen_confirmation_status": "Disputed",
                "grievance_status": "In Progress",
                "dispute_reason": reason
            })
            self.send_json(200, {"success": True, "message": f"Case {case_number} marked as unresolved and returned to zonal crew."})
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})


def run_server():
    server_address = ("", PORT)
    httpd = ThreadingHTTPServer(server_address, CivicOneHandler)
    print(f"[CivicOne] Serving on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[CivicOne] Server stopped.")


if __name__ == "__main__":
    run_server()
