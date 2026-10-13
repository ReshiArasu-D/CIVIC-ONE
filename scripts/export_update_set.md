# CivicOne — Update Set Export & Deployment Guide

This guide describes how to export and transfer the CivicOne Foundation update set between ServiceNow instances.

---

## 1. Active Application Scope
All metadata for CivicOne belongs to:
- **Application:** `CivicOne`
- **Scope Identifier:** `x_2229367_civicone` (`26068197c33b8754e54832f1b40131d5`)
- **Default Update Set:** `CivicOne 1.0.0 Foundation`

---

## 2. Exporting the Scoped Application Update Set

### Option A: Via Studio & Git (Recommended)
1. In ServiceNow, navigate to **System Applications > Studio**.
2. Select **CivicOne**.
3. In the top navigation, click **Source Control > Commit Changes**.
4. Enter commit comment: `Phase 1 Foundation Implementation Complete`.
5. Click **Commit Changes** to push directly to GitHub: `https://github.com/ReshiArasu-D/CIVIC-ONE.git`.

### Option B: Export as Scoped Application XML
1. Navigate to **System Applications > My Company Applications**.
2. Click the record for **CivicOne**.
3. Under Related Links, click **Publish to Update Set...** or **Export Application to XML**.
4. Download the XML archive: `x_2229367_civicone_1.0.0.xml`.

---

## 3. Importing into a Target Instance
1. In the target ServiceNow instance, navigate to **System Update Sets > Retrieved Update Sets**.
2. Click **Import Update Set from XML**.
3. Select `x_2229367_civicone_1.0.0.xml` and click **Upload**.
4. Open the retrieved update set record, click **Preview Update Set**.
5. Resolve any environment-specific collision warnings (ensure `sys_scope` matches).
6. Click **Commit Update Set**.
7. Run `python scripts/load_seed_data.py` to populate foundational geography, organisation, and test grievance records.
