"""Compute the Code App's KPI values from Dataverse with the same rules as code-app/src/data/metrics.ts.

--as-of YYYY-MM-DD gives the numbers as they'll read on that day (e.g. when seeded ahead for a recording date).
"""
import argparse, os, sys, statistics
from datetime import date, datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient

ap = argparse.ArgumentParser()
ap.add_argument("--as-of", help="day the Command Center is viewed, YYYY-MM-DD (default today)")
args = ap.parse_args()
AS_OF = date.fromisoformat(args.as_of) if args.as_of else date.today()

load_env()
c = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
DISCHARGED, HIGH, COMPLETED, PA = 417000004, 417000002, 417000004, 417000000
plans = list(c.records.list("amc_dischargeplan", select=["amc_dischargeplanid", "amc_name", "amc_status", "amc_medicallyreadyon",
             "amc_expecteddischarge", "amc_readmissionrisk"]))
tasks = list(c.records.list("amc_dischargetask", select=["amc_status", "amc_isbarrier", "amc_tasktype", "amc_requestedon",
             "amc_completedon", "_amc_dischargeplanid_value"]))
today = AS_OF.isoformat()
active = [p for p in plans if p["amc_status"] != DISCHARGED]
active_ids = {p["amc_dischargeplanid"] for p in active}
def avoid(p):
    r = (p.get("amc_medicallyreadyon") or "")[:10]
    return max(0, (date.fromisoformat(today) - date.fromisoformat(r)).days) if r else 0
ready = [p for p in active if avoid(p) > 0]
since = datetime.now(timezone.utc) + timedelta(days=(AS_OF - date.today()).days - 14)
hours = [(datetime.fromisoformat(t["amc_completedon"].replace("Z", "+00:00")) - datetime.fromisoformat(t["amc_requestedon"].replace("Z", "+00:00"))).total_seconds() / 3600
         for t in tasks if t["amc_tasktype"] == PA and t["amc_status"] == COMPLETED and t.get("amc_requestedon") and t.get("amc_completedon")
         and datetime.fromisoformat(t["amc_completedon"].replace("Z", "+00:00")) >= since]
print("expected discharges today:", sum(1 for p in active if (p.get("amc_expecteddischarge") or "")[:10] == today))
print("medically ready, still here:", len(ready), "| avoidable bed-days:", sum(avoid(p) for p in ready))
print("open barriers:", sum(1 for t in tasks if t["_amc_dischargeplanid_value"] in active_ids and t["amc_isbarrier"] and t["amc_status"] != COMPLETED))
print("prior-auth median hours:", round(statistics.median(hours)) if hours else None, f"(n={len(hours)})")
print("high risk active:", sum(1 for p in active if p["amc_readmissionrisk"] == HIGH))
top = sorted(active, key=lambda p: -avoid(p))[:5]
print("top of table:", [(p["amc_name"], avoid(p)) for p in top])
