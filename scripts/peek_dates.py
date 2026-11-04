import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient
load_env()
c = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
for p in c.records.list("amc_dischargeplan", filter="amc_name eq 'DP-1001 Miguel Reyes'",
                        select=["amc_admitdate", "amc_medicallyreadyon", "amc_expecteddischarge", "amc_actualdischarge"]):
    print({k: v for k, v in p.items() if k.startswith("amc_")})
for t in c.records.list("amc_dischargetask", filter="amc_tasktype eq 417000000 and amc_status eq 417000004",
                        select=["amc_requestedon", "amc_completedon", "amc_duedate"], top=2):
    print({k: v for k, v in t.items() if k.startswith("amc_")})
