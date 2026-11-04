"""Print the solution GUID for SOLUTION_NAME in .env (used by pa app push --solution-id)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env
from PowerPlatform.Dataverse.client import DataverseClient
load_env()
c = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
rows = list(c.records.list("solution", filter=f"uniquename eq '{os.environ['SOLUTION_NAME']}'", select=["solutionid"]))
print(rows[0]["solutionid"])
