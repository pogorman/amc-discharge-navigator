"""Read-only: is the target environment (POWER_PLATFORM_ENV_ID in .env) a Managed Environment, and which DLP policies apply to it?"""
import json, os, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from auth import load_env
load_env()
ENV = os.environ["POWER_PLATFORM_ENV_ID"]
tok = subprocess.run(["az", "account", "get-access-token", "--resource", "https://service.powerapps.com/",
                      "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True, check=True,
                     shell=(sys.platform == "win32")).stdout.strip()
def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig"))
env = get(f"https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/scopes/admin/environments/{ENV}?api-version=2021-04-01")
gov = env.get("properties", {}).get("governanceConfiguration", {})
print("environment:", env["properties"].get("displayName"), "| sku:", env["properties"].get("environmentSku"))
print("managed environment:", gov.get("protectionLevel") == "Standard", f"(protectionLevel={gov.get('protectionLevel')})")
pols = get("https://api.bap.microsoft.com/providers/PowerPlatform.Governance/v2/policies?api-version=2021-04-01").get("value", [])
print("DLP policies in tenant:", len(pols))
for p in pols:
    envs = [e.get("name") for e in (p.get("environments") or [])]
    applies = p.get("environmentType") == "AllEnvironments" or (p.get("environmentType") == "OnlyEnvironments" and ENV in envs) \
              or (p.get("environmentType") == "ExceptEnvironments" and ENV not in envs)
    print(f"  - {p.get('displayName')} | scope={p.get('environmentType')} | applies here: {applies}")
