"""Sanity-check seeded demo data: status mix, caseload, hero tasks, lookup binding."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient

load_env()
c = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
FMT = "OData.Community.Display.V1.FormattedValue"
plans = list(c.records.list("amc_dischargeplan", select=["amc_name", "amc_status", "amc_unit", "amc_casemanager",
         "amc_readmissionrisk", "_amc_patientid_value"], include_annotations=FMT))
print("plans by status:", dict(Counter(p[f"amc_status@{FMT}"] for p in plans)))
print("plans by unit:  ", dict(Counter(p[f"amc_unit@{FMT}"] for p in plans)))
print("risk:           ", dict(Counter(p[f"amc_readmissionrisk@{FMT}"] for p in plans)))
mine = [p for p in plans if p["amc_casemanager"] == "Patrick O'Gorman" and p[f"amc_status@{FMT}"] != "Discharged"]
print(f"O'G active caseload: {len(mine)} -> {[p['amc_name'] for p in mine]}")
print("plans missing patient lookup:", sum(1 for p in plans if not p.get("_amc_patientid_value")))
hero = next(p for p in plans if p["amc_name"].endswith("Miguel Reyes"))
tasks = list(c.records.list("amc_dischargetask", filter=f"_amc_dischargeplanid_value eq {hero['amc_dischargeplanid']}",
         select=["amc_name", "amc_status", "amc_isbarrier"], include_annotations=FMT))
print("hero tasks:")
for t in tasks:
    print(f"  [{t[f'amc_status@{FMT}']:<20}] {'BARRIER ' if t['amc_isbarrier'] else '        '}{t['amc_name']}")
