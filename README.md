# CIVIC-ONE

This workspace connects to:
- **Git Repository**: [https://github.com/ReshiArasu-D/CIVIC-ONE.git](https://github.com/ReshiArasu-D/CIVIC-ONE.git)
- **ServiceNow Instance**: [https://dev187180.service-now.com](https://dev187180.service-now.com)

---

## 1. Git Repository Setup

The local folder is initialized and tracking the remote repository:
```bash
git remote -v
# origin  https://github.com/ReshiArasu-D/CIVIC-ONE.git (fetch)
# origin  https://github.com/ReshiArasu-D/CIVIC-ONE.git (push)
```

To pull the latest changes:
```bash
git pull origin main
```

To commit and push:
```bash
git add .
git commit -m "your commit message"
git push origin main
```

> **Security Note:** `.env` is added to `.gitignore` so your ServiceNow credentials will never be committed to GitHub.

---

## 2. ServiceNow Instance Configuration

Instance credentials are stored in `.env`:
```env
SERVICENOW_INSTANCE_URL=https://dev187180.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=<YOUR_SERVICENOW_PASSWORD>
```

---

## 3. Testing the ServiceNow Connection

Both **Python** and **Node.js** clients are included with zero external dependencies required.

### Using Python:
```bash
python servicenow_client.py
```

### Using Node.js:
```bash
node servicenow-client.js
```

### Python API Usage:
```python
from servicenow_client import ServiceNowClient

client = ServiceNowClient()

# Check connection
status = client.test_connection()
print(status)

# Fetch incidents
incidents = client.get_records("incident", limit=5, fields="number,short_description,priority,state")
for inc in incidents:
    print(inc["number"], inc["short_description"])

# Create an incident
new_inc = client.create_record("incident", {
    "short_description": "CIVIC-ONE issue reported",
    "urgency": "2",
    "impact": "2"
})
print("Created Incident:", new_inc["number"])
```

### Node.js API Usage:
```javascript
const { ServiceNowClient } = require('./servicenow-client');

async function main() {
  const client = new ServiceNowClient();
  const info = await client.testConnection();
  console.log(info);

  // Fetch incidents
  const incidents = await client.getRecords('incident', { limit: 5 });
  console.log(incidents);
}
main();
```

---

## 4. Connecting ServiceNow Studio to Git (Source Control)

To link an application inside your ServiceNow instance directly to this GitHub repository:
1. Log in to [https://dev187180.service-now.com](https://dev187180.service-now.com) as `admin`.
2. Navigate to **System Applications > Studio**.
3. Select your application (or create a new application for CIVIC-ONE).
4. Click **Source Control** in the top menu and select **Link to Source Control**.
5. Fill in the repository details:
   - **URL**: `https://github.com/ReshiArasu-D/CIVIC-ONE.git`
   - **Branch**: `main`
   - **Credential / Connection**: Use a GitHub Personal Access Token (PAT) with `repo` permissions.
6. Click **Link to Source Control**.
