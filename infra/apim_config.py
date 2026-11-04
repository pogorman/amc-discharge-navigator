"""Apply the APIM API policy and create the connector subscription (idempotent).

Called by provision-apim.sh. Uses an ARM token from Azure CLI; avoids `az rest`, which
crashes on Windows when APIM returns BOM-prefixed policy XML.
"""
import json
import subprocess
import sys
import urllib.error
import urllib.request

SUB, RG, APIM, API_ID, SUBSCRIPTION_ID = sys.argv[1:6]
ARM = (f"https://management.azure.com/subscriptions/{SUB}/resourceGroups/{RG}"
       f"/providers/Microsoft.ApiManagement/service/{APIM}")
V = "api-version=2024-05-01"

token = subprocess.run(["az", "account", "get-access-token", "--resource", "https://management.azure.com",
                        "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True, check=True,
                       shell=(sys.platform == "win32")).stdout.strip()


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 404
        raise SystemExit(f"{method} {url} -> HTTP {e.code}: {e.read().decode('utf-8-sig')[:400]}")


POLICY = """<policies>
  <inbound>
    <base />
    <authentication-managed-identity resource="https://cognitiveservices.azure.com" />
    <set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
  </inbound>
  <backend><forward-request timeout="120" /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>"""

status = call("PUT", f"{ARM}/apis/{API_ID}/policies/policy?{V}",
              {"properties": {"format": "rawxml", "value": POLICY}})
print(f"api policy: HTTP {status}")

if call("GET", f"{ARM}/subscriptions/{SUBSCRIPTION_ID}?{V}") == 404:
    status = call("PUT", f"{ARM}/subscriptions/{SUBSCRIPTION_ID}?{V}",
                  {"properties": {"displayName": "Discharge Navigator connector",
                                  "scope": f"/apis/{API_ID}", "state": "active"}})
    print(f"subscription created: HTTP {status}")
else:
    print("subscription exists")
