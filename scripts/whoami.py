import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient

load_env()
client = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
pubs = client.records.get("publisher", select=["uniquename", "friendlyname", "customizationprefix"])
for page in pubs:
    for p in page:
        print(p["uniquename"], "|", p["friendlyname"], "|", p["customizationprefix"])
