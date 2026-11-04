"""Create the "amc-foundry-key" connection for the Foundry Deployments custom connector and bind the agent's
connection reference to it.

The APIM subscription key is read from Azure at runtime and sent straight to the Power Apps API; it's never
printed or stored. Idempotent: reuses an existing connection with the same display name.
Run from the repo root:  python scripts/create_foundry_connection.py
"""
import json
import os
import subprocess
import sys
import uuid

import requests

sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env  # noqa: E402

load_env()
ENV_ID = os.environ["POWER_PLATFORM_ENV_ID"]
DATAVERSE_URL = os.environ["DATAVERSE_URL"].rstrip("/")
DISPLAY_NAME = "amc-foundry-key"
POWERAPPS = "https://api.powerapps.com/providers/Microsoft.PowerApps"
API_VERSION = "api-version=2016-11-01"


def az(*args):
    return subprocess.run(["az", *args, "-o", "tsv"], capture_output=True, text=True, check=True,
                          shell=(sys.platform == "win32")).stdout.strip()


def dataverse(method, path, body=None):
    token = get_credential().get_token(f"{DATAVERSE_URL}/.default").token
    resp = requests.request(method, f"{DATAVERSE_URL}/api/data/v9.2/{path}", json=body, timeout=120, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json() if resp.content else None


connector = dataverse("GET", "connectors?$select=connectorinternalid&$filter=name eq 'new_foundry-20deployments'")["value"][0]
api_name = connector["connectorinternalid"]
reference = dataverse("GET", "connectionreferences?$select=connectionreferenceid,connectionid"
                             f"&$filter=connectorid eq '/providers/Microsoft.PowerApps/apis/{api_name}'")["value"][0]

pa_headers = {"Authorization": f"Bearer {az('account', 'get-access-token', '--resource', 'https://service.powerapps.com/', '--query', 'accessToken')}",
              "Content-Type": "application/json"}
existing = requests.get(f"{POWERAPPS}/apis/{api_name}/connections?{API_VERSION}&$filter=environment eq '{ENV_ID}'",
                        headers=pa_headers, timeout=120)
existing.raise_for_status()
match = [c for c in existing.json().get("value", []) if c["properties"].get("displayName") == DISPLAY_NAME]

if match:
    connection_name = match[0]["name"]
    print(f"connection exists: {DISPLAY_NAME} ({connection_name})")
else:
    sub, rg, apim = os.environ["AZURE_SUBSCRIPTION_ID"], os.environ["AZURE_RESOURCE_GROUP"], os.environ["APIM_NAME"]
    key = az("rest", "--method", "post", "--url",
             f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.ApiManagement"
             f"/service/{apim}/subscriptions/discharge-navigator/listSecrets?api-version=2024-05-01",
             "--query", "primaryKey")
    connection_name = uuid.uuid4().hex
    resp = requests.put(f"{POWERAPPS}/apis/{api_name}/connections/{connection_name}?{API_VERSION}&$filter=environment eq '{ENV_ID}'",
                        headers=pa_headers, timeout=120, data=json.dumps({"properties": {
                            "environment": {"id": f"/providers/Microsoft.PowerApps/environments/{ENV_ID}", "name": ENV_ID},
                            "displayName": DISPLAY_NAME, "connectionParameters": {"api_key": key}}}))
    if not resp.ok:
        raise RuntimeError(f"create connection: HTTP {resp.status_code} {resp.text[:300]}")
    statuses = [s.get("status") for s in resp.json()["properties"].get("statuses", [])]
    print(f"connection created: {DISPLAY_NAME} ({connection_name}) status={statuses}")

if reference.get("connectionid") != connection_name:
    dataverse("PATCH", f"connectionreferences({reference['connectionreferenceid']})", {"connectionid": connection_name})
    print("connection reference bound")
else:
    print("connection reference already bound")
