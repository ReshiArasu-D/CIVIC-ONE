"""
ServiceNow REST API Client for CIVIC-ONE
Handles authentication and operations against ServiceNow Table APIs.
Uses Python standard library (no pip dependencies required).
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path


def load_env(env_path=None):
    """Load key-value pairs from .env file into os.environ if not already set."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.is_file():
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val


class ServiceNowClient:
    def __init__(self, instance_url=None, username=None, password=None):
        load_env()
        self.instance_url = (
            instance_url or os.getenv("SERVICENOW_INSTANCE_URL", "")
        ).rstrip("/")
        self.username = username or os.getenv("SERVICENOW_USERNAME", "")
        self.password = password or os.getenv("SERVICENOW_PASSWORD", "")

        if not self.instance_url or not self.username or not self.password:
            raise ValueError(
                "Missing ServiceNow credentials. Please configure SERVICENOW_INSTANCE_URL, "
                "SERVICENOW_USERNAME, and SERVICENOW_PASSWORD in your .env file."
            )

        token = f"{self.username}:{self.password}".encode("utf-8")
        self._auth_header = f"Basic {base64.b64encode(token).decode('ascii')}"

    def _request(self, method, endpoint, params=None, data=None):
        url = f"{self.instance_url}/{endpoint.lstrip('/')}"
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": self._auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
                detail = err_json.get("error", {}).get("detail", "")
                raise RuntimeError(f"ServiceNow API Error ({e.code}): {msg} {detail}") from e
            except json.JSONDecodeError:
                raise RuntimeError(f"ServiceNow API Error ({e.code}): {err_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"ServiceNow Connection Error: {e.reason}") from e

    def execute_script(self, script):
        """Execute server-side JavaScript in the ServiceNow scoped application."""
        res = self._request("POST", "/api/2229367/bridge/exec", data={"script": script})
        if not res.get("result", {}).get("success"):
            error_msg = res.get("result", {}).get("error", "Unknown script error")
            raise RuntimeError(f"ServiceNow Server Execution Failed: {error_msg}")
        return res.get("result", {}).get("evalResult")

    def test_connection(self):
        """Test authentication and fetch active user and system information."""
        user_res = self._request(
            "GET",
            "/api/now/table/sys_user",
            params={
                "sysparm_query": f"user_name={self.username}",
                "sysparm_fields": "sys_id,user_name,name,email,active",
                "sysparm_limit": "1",
            },
        )
        user = user_res.get("result", [{}])[0] if user_res.get("result") else None

        props = self._request(
            "GET",
            "/api/now/table/sys_properties",
            params={
                "sysparm_query": "name=glide.war",
                "sysparm_fields": "value",
                "sysparm_limit": "1",
            },
        )
        version = (
            props.get("result", [{}])[0].get("value")
            if props.get("result")
            else "Unknown"
        )

        return {
            "connected": True,
            "instance_url": self.instance_url,
            "user": user,
            "build_version": version,
        }

    def get_records(self, table, query="", fields="", limit=10, offset=0):
        """Query records from any ServiceNow table."""
        params = {"sysparm_limit": str(limit), "sysparm_offset": str(offset)}
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = fields

        res = self._request("GET", f"/api/now/table/{table}", params=params)
        return res.get("result", [])

    def get_record(self, table, sys_id, fields=""):
        """Get a single record by sys_id."""
        params = {}
        if fields:
            params["sysparm_fields"] = fields
        res = self._request("GET", f"/api/now/table/{table}/{sys_id}", params=params)
        return res.get("result", {})

    def create_record(self, table, data):
        """Create a new record in a ServiceNow table."""
        res = self._request("POST", f"/api/now/table/{table}", data=data)
        return res.get("result", {})

    def update_record(self, table, sys_id, data):
        """Update an existing record by sys_id."""
        res = self._request("PATCH", f"/api/now/table/{table}/{sys_id}", data=data)
        return res.get("result", {})

    def delete_record(self, table, sys_id):
        """Delete a record by sys_id."""
        self._request("DELETE", f"/api/now/table/{table}/{sys_id}")
        return True


if __name__ == "__main__":
    print("Testing connection to ServiceNow...")
    client = ServiceNowClient()
    info = client.test_connection()
    print("=" * 50)
    print("SUCCESS: Connected to ServiceNow!")
    print(f"Instance URL: {info['instance_url']}")
    print(f"Logged in User: {info['user'].get('name')} ({info['user'].get('user_name')})")
    print(f"User Email: {info['user'].get('email')}")
    print(f"ServiceNow Build: {info['build_version']}")
    print("=" * 50)
