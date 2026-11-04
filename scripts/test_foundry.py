"""Smoke-test both Foundry deployments through the OpenAI v1 chat completions endpoint.

Default: direct to Foundry with an Entra token from Azure CLI (the tenant disables API keys).
--apim:  through APIM with the subscription key (the path the Power Platform connector uses).
Secrets are fetched at runtime and never printed or stored.

Usage: python scripts/test_foundry.py [--apim]
"""
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from auth import load_env

load_env()
SUB = os.environ["AZURE_SUBSCRIPTION_ID"]
RG, FOUNDRY, APIM = os.environ["AZURE_RESOURCE_GROUP"], os.environ["FOUNDRY_ACCOUNT"], os.environ["APIM_NAME"]
USE_APIM = "--apim" in sys.argv


def az(*args):
    return subprocess.run(["az", *args, "-o", "tsv"], capture_output=True, text=True, check=True,
                          shell=(sys.platform == "win32")).stdout.strip()


if USE_APIM:
    base = f"https://{APIM}.azure-api.net/foundry"
    arm = (f"https://management.azure.com/subscriptions/{SUB}/resourceGroups/{RG}/providers/"
           f"Microsoft.ApiManagement/service/{APIM}/subscriptions/discharge-navigator/listSecrets?api-version=2024-05-01")
    headers = {"Ocp-Apim-Subscription-Key": az("rest", "--method", "post", "--url", arm, "--query", "primaryKey")}
else:
    base = f"https://{FOUNDRY}.openai.azure.com/openai/v1"
    token = az("account", "get-access-token", "--resource", "https://cognitiveservices.azure.com",
               "--query", "accessToken")
    headers = {"Authorization": f"Bearer {token}"}
headers["Content-Type"] = "application/json"

print(f"endpoint: {base}")
for deployment in ("patient-summary", "prior-auth"):
    body = {"model": deployment,
            "messages": [{"role": "system", "content": "Reply in one short sentence."},
                         {"role": "user", "content": "Say hello."}]}
    req = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read())
            print(f"[PASS] {deployment} -> model={data.get('model')}: {data['choices'][0]['message']['content']!r}")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] {deployment}: HTTP {e.code} {e.read().decode()[:300]}")
