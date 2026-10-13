# CivicOne — Automated Test Framework (ATF) Test Suite Specification

**Scope:** `x_2229367_civicone`  
**Test Suite:** `CivicOne - Phase 1 Foundation Test Suite`  

---

## 1. Test 1: Grievance Intake Validation & PII Masking (ATF-CIV-01)
- **Objective:** Verify mandatory fields and PII sanitization on grievance creation.
- **Steps:**
  1. Create synthetic user with role `x_2229367_civicone.citizen`.
  2. Attempt to create `case` record without `ward` -> Verify submission is aborted with error.
  3. Create `case` record with description:
     `"My Aadhaar is 1234 5678 9012 and phone is 9876543210. Clean water leaking near school."`
  4. Assert `pii_masked` is `true`.
  5. Assert `original_description` preserves raw text.
  6. Assert `masked_description` contains `"XXXX-XXXX-9012"` and `"XXXXXX3210"`.

---

## 2. Test 2: Priority Scoring & Duplicate Suggestion (ATF-CIV-02)
- **Objective:** Verify deterministic priority calculation and non-destructive duplicate suggestion.
- **Steps:**
  1. Create Case A in Ward 12 with Category `CAT-WAT-LEAK` and text: `"Gas leak and live wire near primary hospital."`
  2. Assert `priority` is `1` (Critical) and `priority_score >= 80`.
  3. Create Case B in Ward 12 with same Category within 1 hour: `"Water pipe burst outside school gate."`
  4. Assert Case B has `is_duplicate_suspect == true` and `duplicate_suspect_parent == Case A`.
  5. Assert Case B is NOT deleted or merged.

---

## 3. Test 3: Citizen Confirmation Closure Gate (ATF-CIV-03)
- **Objective:** Verify tickets cannot be closed prematurely without citizen verification.
- **Steps:**
  1. Open Case in status `In Progress`.
  2. Worker marks case `Resolved` -> Assert status becomes `Awaiting Citizen Confirmation`.
  3. Attempt to update status directly to `Closed` as worker -> Assert action aborted by BR12.
  4. Citizen submits `citizen_feedback` with `action_confirmed == 'Confirmed'` -> Assert case status transitions to `Closed`.

---

## 4. Test 4: Citizen Dispute Reopening (ATF-CIV-04)
- **Objective:** Verify citizen dispute reopens ticket and triggers supervisory review.
- **Steps:**
  1. Open Case in status `Awaiting Citizen Confirmation`.
  2. Citizen submits `citizen_feedback` with `action_confirmed == 'Disputed'` and dispute reason: `"Pothole was only partially filled with sand; still deep hole."`
  3. Assert case status reverts to `In Progress`.
  4. Assert `citizen_confirmation_status` is `Disputed`.
  5. Assert `escalation_step` record created with `Level 1 - Supervisor` and reason `Citizen Dispute`.
