"""
Agent 2 — Collective Grievance Agent
PS07 CivicResolve AI Specification

Identifies semantic and geographic similarity between grievances,
suggests potential collective grievance groupings, flags clusters,
and enforces non-destructive safeguards (NEVER auto-merge tickets;
every citizen retains their unique Case ID and notifications).
"""

import math
import datetime
from typing import Dict, Any, List, Optional


class CollectiveGrievanceAgent:
    AGENT_NAME = "Collective Grievance Agent"
    SIMULATION_LABEL = "Simulated AI recommendation — not production AI"
    MANDATORY_SAFEGUARD_NOTICE = (
        "Similarity is an advisory recommendation only. Citizen tickets are NEVER automatically merged or deleted. "
        "Every citizen retains their own unique Case ID, notifications, and independent confirmation rights."
    )

    def __init__(self, mode: str = "demo", servicenow_client=None):
        self.mode = mode
        self.client = servicenow_client

    @staticmethod
    def _calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula to compute distance in meters between two coordinates."""
        if not lat1 or not lon1 or not lat2 or not lon2:
            return 99999.0
        r = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def find_similar_grievances(
        self,
        target_case: Dict[str, Any],
        candidate_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scans candidate cases and evaluates similarity score based on:
        - Category & Subcategory match (weight 40%)
        - Semantic keyword overlap in description (weight 35%)
        - Geographic proximity (< 500 meters) (weight 25%)
        """
        target_id = target_case.get("id") or target_case.get("number") or "TARGET"
        target_cat = (target_case.get("category") or "").lower()
        target_desc = (target_case.get("description") or target_case.get("short_description") or "").lower()
        target_lat = float(target_case.get("latitude") or 0.0)
        target_lon = float(target_case.get("longitude") or 0.0)

        target_words = set([w for w in target_desc.replace(",", " ").replace(".", " ").split() if len(w) > 3])

        matched_groups = []

        for cand in candidate_cases:
            cand_id = cand.get("id") or cand.get("number") or ""
            if cand_id == target_id:
                continue

            cand_cat = (cand.get("category") or "").lower()
            cand_desc = (cand.get("description") or cand.get("short_description") or "").lower()
            cand_lat = float(cand.get("latitude") or 0.0)
            cand_lon = float(cand.get("longitude") or 0.0)

            # 1. Category match score
            cat_score = 1.0 if target_cat and target_cat in cand_cat or cand_cat in target_cat else 0.0

            # 2. Semantic text overlap
            cand_words = set([w for w in cand_desc.replace(",", " ").replace(".", " ").split() if len(w) > 3])
            overlap = len(target_words.intersection(cand_words))
            text_score = min(1.0, overlap / max(1, min(len(target_words), 6)))

            # 3. Geographic proximity score
            dist_meters = self._calculate_distance_meters(target_lat, target_lon, cand_lat, cand_lon)
            if dist_meters <= 150:
                geo_score = 1.0
            elif dist_meters <= 500:
                geo_score = 0.7
            elif dist_meters <= 1500:
                geo_score = 0.3
            else:
                geo_score = 0.0

            # Composite similarity score
            composite = (cat_score * 0.40) + (text_score * 0.35) + (geo_score * 0.25)
            similarity_pct = int(round(composite * 100))

            if similarity_pct >= 60:
                same_issue = "yes" if similarity_pct >= 85 else ("unsure" if similarity_pct >= 70 else "no")
                reason = (
                    f"Strong semantic and geographical match ({similarity_pct}%): "
                    f"Both report {cand.get('category')} issues in close proximity ({int(dist_meters)}m). "
                    f"Matching incident keywords detected."
                )

                matched_groups.append({
                    "case_id": cand_id,
                    "title": cand.get("title") or cand.get("short_description") or cand.get("summary") or "Grievance Report",
                    "category": cand.get("category"),
                    "subcategory": cand.get("subcategory", "General"),
                    "location": cand.get("location") or cand.get("ward") or cand.get("area") or "Local Jurisdiction",
                    "status": cand.get("status") or "In Progress",
                    "submitted_on": cand.get("submitted_on") or cand.get("created_dt") or "Recent",
                    "similarity_score": similarity_pct,
                    "similarity_display": f"{similarity_pct}% Match",
                    "distance_meters": int(dist_meters),
                    "same_issue": same_issue,
                    "reason": reason,
                    "recommended_priority": "High (Priority 1)" if len(matched_groups) >= 2 else cand.get("priority", "Normal (Priority 2)")
                })

        # Sort by highest similarity first
        matched_groups.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Propose Master Grievance if 2 or more similar cases found
        proposed_master = None
        if len(matched_groups) >= 1:
            proposed_master = {
                "propose_grouping": True,
                "title": f"Collective Cluster: Multiple reports on {target_case.get('category', 'Civic Issue')}",
                "affected_reporters": len(matched_groups) + 1,
                "recommended_action": "Authorized Officer may link as Master Grievance cluster to coordinate shared field contractor.",
                "proposed_master_id": f"MST-{target_case.get('category', 'CIV')[:3].upper()}-CLUST"
            }

        return {
            "agent": self.AGENT_NAME,
            "mode": self.mode,
            "simulation_label": self.SIMULATION_LABEL if self.mode == "demo" else "ServiceNow Predictive Intelligence Similarity",
            "target_case_id": target_id,
            "safeguards": {
                "mandate": self.MANDATORY_SAFEGUARD_NOTICE,
                "auto_merge_blocked": True,
                "independent_notifications_preserved": True
            },
            "similar_cases_count": len(matched_groups),
            "groups": matched_groups,
            "proposed_master": proposed_master,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
