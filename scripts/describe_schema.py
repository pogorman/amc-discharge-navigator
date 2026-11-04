"""Print custom columns (logical name, type, display label) for the demo tables."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_token, load_env

load_env()
env = os.environ["DATAVERSE_URL"].rstrip("/")
token = get_token()
for t in ("amc_patient", "amc_dischargeplan", "amc_dischargetask"):
    url = (f"{env}/api/data/v9.2/EntityDefinitions(LogicalName='{t}')?$select=EntitySetName"
           f"&$expand=Attributes($select=LogicalName,AttributeType,DisplayName;$filter=IsCustomAttribute eq true)").replace(" ", "%20")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    d = json.loads(urllib.request.urlopen(req).read())
    print(f"== {t}  (entity set: {d['EntitySetName']})")
    for a in sorted(d["Attributes"], key=lambda a: a["LogicalName"]):
        lbl = (a.get("DisplayName") or {}).get("UserLocalizedLabel") or {}
        if a["AttributeType"] in ("Virtual",) or a["LogicalName"].endswith("name") and a["AttributeType"] == "String" and a["LogicalName"] != "amc_name":
            continue
        print(f"  {a['LogicalName']:<26} {a['AttributeType']:<10} {lbl.get('Label','')}")
