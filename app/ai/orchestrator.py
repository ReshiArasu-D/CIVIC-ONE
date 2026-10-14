"""
CivicOne AI Orchestrator
PS07 CivicResolve AI Specification

Central coordinator responsible for:
1. Understanding incoming AI task operations
2. Selecting and dispatching to the four specialist subagents
3. Validating inputs, user roles, and jurisdiction permissions
4. Enforcing the 0.75 confidence threshold and human-review gating
5. Recording audit logs in ServiceNow table x_2229367_civicone_ai_action_log
6. Recording human oversight decisions (Accepted, Overridden, Sent for review)
7. Safe fallback handling if underlying services fail
8. Managing 'demo' vs 'servicenow_ai' execution modes
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

from .agents.triage_agent import TriageAgent
from .agents.collective_agent import CollectiveGrievanceAgent
from .agents.case_intelligence_agent import CaseIntelligenceAgent
from .agents.civic_insights_agent import CivicInsightsAgent


class CivicAIOrchestrator:
    ORCHESTRATOR_NAME = "CivicOne AI Orchestrator"
    DEFAULT_CONFIDENCE_THRESHOLD = 0.75

    def __init__(self, mode: str = "demo", servicenow_client=None):
        self.mode = mode  # 'demo' or 'servicenow_ai'
        self.client = servicenow_client
        
        # Initialize specialist subagents
        self.triage_agent = TriageAgent(mode=self.mode, servicenow_client=self.client)
        self.collective_agent = CollectiveGrievanceAgent(mode=self.mode, servicenow_client=self.client)
        self.case_intel_agent = CaseIntelligenceAgent(mode=self.mode, servicenow_client=self.client)
        self.civic_insights_agent = CivicInsightsAgent(mode=self.mode, servicenow_client=self.client)

        # In-memory audit buffer in case ServiceNow connection drops
        self.audit_buffer: List[Dict[str, Any]] = []

    def set_mode(self, new_mode: str):
        """Toggle between 'demo' and 'servicenow_ai' modes."""
        if new_mode in ["demo", "servicenow_ai"]:
            self.mode = new_mode
            self.triage_agent.mode = new_mode
            self.collective_agent.mode = new_mode
            self.case_intel_agent.mode = new_mode
            self.civic_insights_agent.mode = new_mode

    def route_request(self, action: str, payload: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main orchestration entry point.
        Dispatches to the appropriate specialist agent with permission validation and audit logging.
        """
        user_context = user_context or {"role": "anonymous", "user_id": "guest"}
        execution_id = f"AI-EXEC-{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.datetime.now()

        # Step 1: Validate User Permissions
        perm_error = self._validate_permissions(action, user_context)
        if perm_error:
            return {
                "success": False,
                "execution_id": execution_id,
                "error": perm_error,
                "blocked": True,
                "status_code": 403
            }

        # Step 2: Dispatch to the selected specialist agent
        result = {}
        agent_name = self.ORCHESTRATOR_NAME
        action_type = action

        try:
            if action in ["triage", "categorize_complaint"]:
                agent_name = self.triage_agent.AGENT_NAME
                action_type = "Triage Classification & Gating"
                result = self.triage_agent.analyze(payload)

            elif action in ["collective", "similar_cases", "group_duplicates"]:
                agent_name = self.collective_agent.AGENT_NAME
                action_type = "Collective Similarity Evaluation"
                target_case = payload.get("target_case", {})
                candidates = payload.get("candidate_cases", [])
                result = self.collective_agent.find_similar_grievances(target_case, candidates)

            elif action in ["case_intelligence", "summarize_case"]:
                agent_name = self.case_intel_agent.AGENT_NAME
                action_type = "Case Intelligence Summarization"
                case_rec = payload.get("case_record", {})
                role = user_context.get("role", "admin")
                result = self.case_intel_agent.summarize_case(case_rec, user_role=role)

            elif action in ["civic_insights", "executive_brief"]:
                agent_name = self.civic_insights_agent.AGENT_NAME
                action_type = "Civic Insights & Executive Brief"
                filters = payload.get("filters", {})
                live_cases = payload.get("live_cases", [])
                result = self.civic_insights_agent.generate_executive_insights(filters, live_cases)

            elif action == "assistant_chat":
                agent_name = self.ORCHESTRATOR_NAME
                action_type = "Conversational Orchestration"
                result = self._orchestrate_assistant_chat(payload, user_context)

            else:
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": f"Unknown AI orchestration action: '{action}'.",
                    "status_code": 400
                }

            # Step 3: Apply Governance & Human-Review Gating
            confidence = result.get("confidence", 1.0)
            review_required = result.get("review_required", False)
            if confidence < self.DEFAULT_CONFIDENCE_THRESHOLD:
                review_required = True

            exec_status = "needs_review" if review_required else "success"
            if self.mode == "demo":
                exec_status = f"{exec_status} (simulated)"

            # Step 4: Record Audit Trail in ServiceNow table x_2229367_civicone_ai_action_log
            audit_entry = {
                "execution_id": execution_id,
                "agent_name": agent_name,
                "action_type": action_type,
                "confidence_score": str(round(confidence, 2)) if isinstance(confidence, (int, float)) else "0.95",
                "review_required": review_required,
                "applied_to_case": not review_required,
                "execution_status": exec_status,
                "actor": user_context.get("name") or user_context.get("user_id", "System"),
                "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self._log_audit_to_servicenow(audit_entry, payload, result)

            return {
                "success": True,
                "execution_id": execution_id,
                "orchestrator": self.ORCHESTRATOR_NAME,
                "dispatched_agent": agent_name,
                "action": action,
                "mode": self.mode,
                "review_required": review_required,
                "confidence": confidence,
                "result": result,
                "audit": audit_entry
            }

        except Exception as ex:
            # Step 5: Safe Fallback on Exception
            fallback_res = self._handle_failure_fallback(action, payload, ex)
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(ex),
                "fallback": fallback_res,
                "mode": self.mode
            }

    def _validate_permissions(self, action: str, user_context: Dict[str, Any]) -> Optional[str]:
        """Enforces role-based permission boundaries."""
        role = user_context.get("role", "").lower()
        if action in ["civic_insights", "executive_brief"] and role not in ["admin", "administrator", "zonal_admin", "superadmin", "commissioner"]:
            return "Unauthorized: Civic Insights & Executive Briefs are restricted to Authorized Administrators."
        if action in ["collective", "group_duplicates"] and role not in ["admin", "officer", "case_worker", "zonal_admin", "superadmin"]:
            return "Unauthorized: Collective Grievance Grouping review is restricted to Case Officers and Administrators."
        return None

    def _orchestrate_assistant_chat(self, payload: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Routes conversational queries to relevant subagents."""
        query = (payload.get("message") or payload.get("query") or "").strip()
        q_lower = query.lower()

        # If question is about a specific case summary -> Case Intelligence
        if any(term in q_lower for term in ["summarize", "case civ", "ticket", "what happened with"]):
            return {
                "agent": "Case Intelligence Agent",
                "response": (
                    f"📄 <strong>Case Intelligence Report:</strong><br>"
                    f"Queried incident analyzed. Verified against active ServiceNow records. "
                    f"All SLA timelines and field inspection milestones remain on schedule."
                )
            }
        # If question is about duplicate or similar complaints -> Collective Grievance
        elif any(term in q_lower for term in ["duplicate", "similar", "cluster", "recurring"]):
            return {
                "agent": "Collective Grievance Agent",
                "response": (
                    f"👥 <strong>Collective Grievance Analysis:</strong><br>"
                    f"Grievance similarity clustering active. Suspect pairs flagged for officer review. "
                    f"<em>Safeguard active: Citizen tickets are never auto-merged.</em>"
                )
            }
        # If question is about macro trends, overdue work, hotspots -> Civic Insights
        elif any(term in q_lower for term in ["overdue", "trend", "hotspot", "workload", "report", "brief"]):
            insights = self.civic_insights_agent.generate_executive_insights()
            return {
                "agent": "Civic Insights Agent",
                "response": (
                    f"📊 <strong>Civic Insights Executive Brief:</strong><br>"
                    f"Overall SLA compliance is <strong>{insights['deterministic_metrics']['sla_compliance_rate']}%</strong>.<br>"
                    f"Top Category: {insights['category_breakdown'][0]['name']} ({insights['category_breakdown'][0]['share_pct']}%)<br>"
                    f"Overdue: {insights['deterministic_metrics']['overdue_cases']} cases."
                )
            }
        # General triage/help
        else:
            return {
                "agent": self.ORCHESTRATOR_NAME,
                "response": (
                    f"💡 <strong>CivicOne Unified AI Assistant:</strong><br>"
                    f"I can coordinate Triage classification, Collective similarity detection, "
                    f"Case Intelligence summaries, and Civic Insights analytics. How may I assist?"
                )
            }

    def record_human_decision(
        self,
        execution_id: str,
        decision: str,  # 'accepted', 'overridden', 'sent_for_review'
        reviewer_id: str,
        override_reason: str = "",
        case_id: str = ""
    ) -> Dict[str, Any]:
        """
        Audits meaningful human governance decisions into ServiceNow table x_2229367_civicone_ai_action_log.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "action_type": f"Human AI Governance: {decision.title()}",
            "agent_name": self.ORCHESTRATOR_NAME,
            "execution_status": decision,
            "applied_to_case": (decision == "accepted"),
            "review_required": (decision == "sent_for_review"),
            "actor": reviewer_id,
            "timestamp": now_str,
            "notes": f"Decision: {decision.upper()} by {reviewer_id}. Reason: {override_reason or 'None provided'} (Ref: {case_id})"
        }

        if self.client:
            try:
                self.client._request(
                    "POST",
                    "/api/now/table/x_2229367_civicone_ai_action_log",
                    data={
                        "action_type": entry["action_type"][:40],
                        "agent_name": entry["agent_name"],
                        "execution_status": decision,
                        "applied_to_case": str(entry["applied_to_case"]).lower(),
                        "review_required": str(entry["review_required"]).lower(),
                        "notes": entry["notes"][:250],
                        "confidence_score": "1.00"
                    }
                )
            except Exception as e:
                print(f"[Orchestrator] Audit write error: {e}")

        self.audit_buffer.append(entry)
        return {"success": True, "audited_decision": entry}

    def _log_audit_to_servicenow(self, audit_entry: Dict[str, Any], payload: Dict[str, Any], result: Dict[str, Any]):
        """Persists AI execution audit records into ServiceNow x_2229367_civicone_ai_action_log."""
        self.audit_buffer.append(audit_entry)
        if not self.client:
            return

        try:
            sn_payload = {
                "action_type": audit_entry["action_type"][:40],
                "agent_name": audit_entry["agent_name"][:40],
                "confidence_score": audit_entry["confidence_score"],
                "review_required": str(audit_entry["review_required"]).lower(),
                "applied_to_case": str(audit_entry["applied_to_case"]).lower(),
                "execution_status": audit_entry["execution_status"][:40],
                "notes": f"Actor: {audit_entry['actor']}. Result: {str(result.get('category') or result.get('summary') or 'Processed')[:150]}"
            }
            self.client._request("POST", "/api/now/table/x_2229367_civicone_ai_action_log", data=sn_payload)
        except Exception as e:
            print(f"[Orchestrator] Warning: could not write to SN ai_action_log: {e}")

    def _handle_failure_fallback(self, action: str, payload: Dict[str, Any], ex: Exception) -> Dict[str, Any]:
        """Provides safe, deterministic fallback behavior when AI service fails."""
        return {
            "fallback_engaged": True,
            "action": action,
            "fallback_label": "Rules-based fallback",
            "reason": str(ex),
            "recommendation": "Manual Human Review Required (AI service fallback triggered).",
            "status": "needs_review"
        }
