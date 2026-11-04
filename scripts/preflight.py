"""Check the target environment for existing publishers, solution and amc_ tables before creating anything."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient

load_env()
c = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
print("target:", os.environ["DATAVERSE_URL"])
for p in c.records.list("publisher", select=["uniquename", "customizationprefix"]):
    print("publisher:", p["uniquename"], "| prefix:", p["customizationprefix"])
sol = list(c.records.list("solution", filter=f"uniquename eq '{os.environ['SOLUTION_NAME']}'", select=["uniquename"]))
print("solution exists:", bool(sol))
for t in ("amc_patient", "amc_dischargeplan", "amc_dischargetask"):
    print(f"table {t} exists:", bool(c.tables.get(t)))
