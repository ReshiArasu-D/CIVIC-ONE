"""
Agent 1 — Triage Agent
PS07 CivicResolve AI Specification

Analyzes citizen-submitted grievances, normalizes text, masks PII,
detects missing information, predicts category/subcategory/department/priority,
and gates recommendations through a strict 0.75 confidence threshold.
"""

import re
import datetime
from typing import Dict, Any, List, Optional


class TriageAgent:
    AGENT_NAME = "Triage Agent"
    CONFIDENCE_THRESHOLD = 0.75
    SIMULATION_LABEL = "Simulated AI recommendation — not production AI"

    # Canonical Category and Department Taxonomy
    TAXONOMY = {
        "Roads & Footpaths": {
            "department": "Roads and Infrastructure Department",
            "dept_code": "DEPT-ROADS",
            "keywords": ["pothole", "crater", "road", "tar", "asphalt", "footpath", "pavement", "curb", "speed breaker"],
            "subcategories": {
                "Dangerous Road Pothole": {
                    "keywords": ["pothole", "crater", "deep hole", "peeling asphalt"],
                    "priority": "High (Priority 1)"
                },
                "Damaged Asphalt / Crater": {
                    "keywords": ["damaged road", "uneven road", "crater", "rough surface"],
                    "priority": "Normal (Priority 2)"
                },
                "Broken Pedestrian Footpath": {
                    "keywords": ["footpath", "pavement", "broken slab", "pedestrian"],
                    "priority": "Normal (Priority 2)"
                }
            }
        },
        "Water Supply": {
            "department": "Water Supply and Sewerage Board",
            "dept_code": "DEPT-WATER",
            "keywords": ["water", "pipe", "pipeline", "leak", "burst", "pressure", "drinking", "turbid", "contamination", "tap"],
            "subcategories": {
                "Water Pipeline Leakage or Burst": {
                    "keywords": ["leak", "burst", "pipe burst", "flooding pipe", "gushing"],
                    "priority": "High (Priority 1)"
                },
                "Drinking Water Contamination": {
                    "keywords": ["contaminated", "muddy water", "foul smell", "turbid", "discolored", "yellow water"],
                    "priority": "Critical (Priority 1)"
                },
                "Low Water Pressure": {
                    "keywords": ["low pressure", "trickle", "no water", "intermittent"],
                    "priority": "Normal (Priority 2)"
                }
            }
        },
        "Streetlights & Electricity": {
            "department": "Electricity and Street Lighting",
            "dept_code": "DEPT-ELEC",
            "keywords": ["light", "streetlight", "lamp", "dark", "pole", "wire", "cable", "sparking", "shock", "electricity"],
            "subcategories": {
                "Exposed Live Electrical Wire": {
                    "keywords": ["wire", "exposed wire", "sparking", "hanging cable", "electric shock", "danger"],
                    "priority": "Critical (Priority 1)"
                },
                "Non-functioning Street Light": {
                    "keywords": ["streetlight off", "not working", "dark street", "bulb fused", "light out"],
                    "priority": "Normal (Priority 2)"
                },
                "Damaged Streetlight Pole": {
                    "keywords": ["pole bent", "pole damaged", "tilted pole", "rusty pole"],
                    "priority": "Normal (Priority 2)"
                }
            }
        },
        "Sanitation & Waste": {
            "department": "Solid Waste Management and Sanitation",
            "dept_code": "DEPT-SAN",
            "keywords": ["garbage", "trash", "waste", "dump", "bin", "sweep", "debris", "litter", "smell"],
            "subcategories": {
                "Uncollected Garbage Dump": {
                    "keywords": ["garbage dump", "uncollected waste", "pile of trash", "not collected", "stink"],
                    "priority": "Normal (Priority 2)"
                },
                "Overflowing Public Dustbins": {
                    "keywords": ["overflowing bin", "dustbin full", "spilling over"],
                    "priority": "Normal (Priority 2)"
                },
                "Street Sweeping Required": {
                    "keywords": ["sweeping", "dead leaves", "litter on road", "clean road"],
                    "priority": "Low (Priority 3)"
                }
            }
        },
        "Drainage & Sewage": {
            "department": "Roads and Infrastructure Department",
            "dept_code": "DEPT-ROADS",
            "keywords": ["drain", "drainage", "sewage", "manhole", "gutter", "waterlogging", "overflow", "choked"],
            "subcategories": {
                "Damaged / Open Manhole Cover": {
                    "keywords": ["open manhole", "broken manhole", "missing cover", "death trap"],
                    "priority": "Critical (Priority 1)"
                },
                "Blocked Stormwater Drain": {
                    "keywords": ["blocked drain", "choked drain", "waterlogging", "stormwater"],
                    "priority": "High (Priority 1)"
                },
                "Sewage Line Overflow": {
                    "keywords": ["sewage overflow", "septic overflow", "black water", "foul water"],
                    "priority": "High (Priority 1)"
                }
            }
        }
    }

    def __init__(self, mode: str = "demo", servicenow_client=None):
        self.mode = mode  # 'demo' or 'servicenow_ai'
        self.client = servicenow_client

    def mask_pii(self, text: str) -> str:
        """
        Enforces BR18 / PiiMasker: Masks phone numbers, Aadhaar numbers, and email addresses.
        Treats complaint text as untrusted data.
        """
        if not text:
            return ""
        # Mask 10-12 digit phone numbers or Aadhaar numbers
        masked = re.sub(r'\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b', '[REDACTED_PHONE]', text)
        masked = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '[REDACTED_AADHAAR]', masked)
        # Mask emails
        masked = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', masked)
        return masked

    def detect_missing_info(self, description: str, location_data: Dict[str, Any]) -> List[str]:
        """
        Checks for missing essential information required for field action:
        - Specific landmark or street
        - Substantive problem description
        - Geographic ward/area
        """
        missing = []
        desc_clean = (description or "").strip()

        if len(desc_clean) < 15:
            missing.append("Description is too brief. Please describe the specific issue or defect.")

        if not location_data.get("ward") and not location_data.get("area") and not location_data.get("address"):
            missing.append("Exact street or ward location is required for field dispatch.")

        # Check for vague input words
        vague_phrases = ["it is broken", "fix it", "not working", "problem here", "help please"]
        if desc_clean.lower() in vague_phrases:
            missing.append("Specific defect details missing (e.g. type of damage, hazard level).")

        return missing

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Triage classification.
        Input:
            payload: {
                "description": str,
                "location": { "area": str, "ward": str, "district": str, "zone": str },
                "attachments": List[Any],
                "scenario_key": Optional[str]
            }
        """
        raw_desc = payload.get("description", "")
        location = payload.get("location", {})
        attachments = payload.get("attachments", [])
        scenario_key = payload.get("scenario_key")

        # Step 1: Mask PII before passing to classification logic
        masked_text = self.mask_pii(raw_desc)
        missing_info = self.detect_missing_info(masked_text, location)

        # Step 2: In servicenow_ai mode, if Predictive Intelligence is active and configured
        if self.mode == "servicenow_ai" and self.client:
            # Native ServiceNow ML classification invocation hook
            try:
                # If a live PI model endpoint exists on instance
                pi_res = self._call_servicenow_predictive_intelligence(masked_text)
                if pi_res:
                    return pi_res
            except Exception as e:
                print(f"[TriageAgent] Live PI failed, falling back to deterministic: {e}")

        # Step 3: Deterministic / Demo Classification Engine
        rec_category = "General Civic Issue"
        rec_subcategory = "General Complaint"
        rec_department = "Municipal Administration"
        rec_priority = "Normal (Priority 2)"
        confidence = 0.50

        text_lower = masked_text.lower()
        best_cat_matches = 0

        # Score categories based on keyword frequency
        for cat_name, cat_info in self.TAXONOMY.items():
            matches = sum(1 for kw in cat_info["keywords"] if kw in text_lower)
            if matches > best_cat_matches:
                best_cat_matches = matches
                rec_category = cat_name
                rec_department = cat_info["department"]

                # Find subcategory
                best_sub_matches = 0
                for sub_name, sub_info in cat_info["subcategories"].items():
                    sub_matches = sum(1 for skw in sub_info["keywords"] if skw in text_lower)
                    if sub_matches > best_sub_matches:
                        best_sub_matches = sub_matches
                        rec_subcategory = sub_name
                        rec_priority = sub_info["priority"]

                # Compute calibrated confidence
                if best_cat_matches >= 3 or best_sub_matches >= 2:
                    confidence = 0.94
                elif best_cat_matches == 2:
                    confidence = 0.82
                elif best_cat_matches == 1:
                    confidence = 0.72  # Just below 0.75 threshold to trigger review
                else:
                    confidence = 0.45

        # If scenario_key is provided (from demo selector), honor high confidence preset
        if scenario_key == "pothole":
            rec_category = "Roads & Footpaths"
            rec_subcategory = "Dangerous Road Pothole"
            rec_department = "Roads and Infrastructure Department"
            rec_priority = "High (Priority 1)"
            confidence = 0.94
        elif scenario_key == "water_leak":
            rec_category = "Water Supply"
            rec_subcategory = "Water Pipeline Leakage or Burst"
            rec_department = "Water Supply and Sewerage Board"
            rec_priority = "High (Priority 1)"
            confidence = 0.96
        elif scenario_key == "street_light":
            rec_category = "Streetlights & Electricity"
            rec_subcategory = "Non-functioning Street Light"
            rec_department = "Electricity and Street Lighting"
            rec_priority = "Normal (Priority 2)"
            confidence = 0.91

        # Photo evidence adds confidence boost if substantive description exists
        if attachments and len(attachments) > 0 and confidence >= 0.70:
            confidence = min(0.98, confidence + 0.04)

        # Gate on confidence threshold (0.75) and missing information
        review_required = False
        review_reasons = []

        if confidence < self.CONFIDENCE_THRESHOLD:
            review_required = True
            review_reasons.append(f"Confidence score ({confidence:.2f}) is below statutory 0.75 threshold.")

        if len(missing_info) > 0:
            review_required = True
            review_reasons.extend(missing_info)
            # Downgrade confidence if essential info is missing
            confidence = min(confidence, 0.65)

        return {
            "agent": self.AGENT_NAME,
            "mode": self.mode,
            "simulation_label": self.SIMULATION_LABEL if self.mode == "demo" else "ServiceNow Predictive Intelligence",
            "category": rec_category,
            "subcategory": rec_subcategory,
            "department": rec_department,
            "priority_recommendation": rec_priority,
            "english_text": masked_text,
            "confidence": round(confidence, 2),
            "confidence_display": f"{int(confidence * 100)}%",
            "review_required": review_required,
            "review_reasons": review_reasons,
            "missing_info": missing_info,
            "decision_status": "needs_review" if review_required else "accepted",
            "autofill_ready": not review_required,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _call_servicenow_predictive_intelligence(self, text: str) -> Optional[Dict[str, Any]]:
        # Hook for native com.glide.platform_ml classification API
        return None
