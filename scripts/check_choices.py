import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_token, load_env
load_env(); env = os.environ["DATAVERSE_URL"].rstrip("/"); token = get_token()
url = (f"{env}/api/data/v9.2/EntityDefinitions(LogicalName='amc_dischargeplan')/Attributes(LogicalName='amc_destination')"
       "/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$select=LogicalName&$expand=OptionSet($select=Options)")
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
d = json.loads(urllib.request.urlopen(req).read())
for o in d["OptionSet"]["Options"]:
    print(o["Value"], o["Label"]["UserLocalizedLabel"]["Label"])
url2 = f"{env}/api/data/v9.2/EntityDefinitions(LogicalName='amc_patient')/Attributes(LogicalName='amc_pcpname')?$select=LogicalName,DisplayName"
d2 = json.loads(urllib.request.urlopen(urllib.request.Request(url2, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})).read())
print(d2["LogicalName"], d2["DisplayName"]["UserLocalizedLabel"]["Label"])
