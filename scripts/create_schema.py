"""Create the publisher, solution and tables for the AMC Discharge Navigator demo.

Idempotent: skips the publisher, solution, tables and lookups that already exist.
Run from the repo root:  python scripts/create_schema.py
"""
import os
import sys
import time
from enum import IntEnum

import requests

sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env  # noqa: E402
from PowerPlatform.Dataverse.client import DataverseClient  # noqa: E402

load_env()
SOLUTION = os.environ["SOLUTION_NAME"]
PREFIX = os.environ["PUBLISHER_PREFIX"]
OPTION_PREFIX = 41700  # choice values start at 417000000

client = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())


def first(table, **kw):
    for page in client.records.get(table, top=1, **kw):
        for row in page:
            return row
    return None


# ---------------------------------------------------------------- publisher
pub = first("publisher", filter=f"customizationprefix eq '{PREFIX}'",
            select=["publisherid", "uniquename"])
if pub:
    publisher_id = pub["publisherid"]
    print(f"publisher exists: {pub['uniquename']}")
else:
    publisher_id = client.records.create("publisher", {
        "uniquename": "AMCAgentDemo",
        "friendlyname": "AMC Agent Demo",
        "customizationprefix": PREFIX,
        "customizationoptionvalueprefix": OPTION_PREFIX,
        "description": "Publisher for the AMC Apps & Agents demo (Contoso University Health).",
    })
    print(f"publisher created: {publisher_id}")

# ---------------------------------------------------------------- solution
sol = first("solution", filter=f"uniquename eq '{SOLUTION}'", select=["solutionid"])
if sol:
    print(f"solution exists: {SOLUTION}")
else:
    client.records.create("solution", {
        "uniquename": SOLUTION,
        "friendlyname": "AMC Discharge Navigator",
        "version": "1.0.0.0",
        "description": "Discharge planning demo: Dataverse tables, Copilot Studio agent, Code App.",
        "publisherid@odata.bind": f"/publishers({publisher_id})",
    })
    print(f"solution created: {SOLUTION}")


# ---------------------------------------------------------------- choices
def choice(name, labels):
    """Build a local option set Enum with display labels and 4170000xx values."""
    members = {f"O{i}": OPTION_PREFIX * 10000 + i for i in range(len(labels))}
    enum_cls = IntEnum(name, members)
    enum_cls.__labels__ = {1033: {f"O{i}": text for i, text in enumerate(labels)}}
    return enum_cls


Language = choice("Language", ["English", "Spanish", "Vietnamese", "Mandarin", "Russian", "Arabic"])
Payer = choice("Payer", ["Medicare", "Medicare Advantage", "Medicaid", "Commercial", "Self-pay"])
Unit = choice("Unit", ["5 West - Medicine", "6 East - Cardiology", "7 North - Orthopedics", "4 South - Oncology"])
PlanStatus = choice("PlanStatus", ["Planning", "Medically Ready", "Pending Barriers", "Ready for Discharge", "Discharged"])
Destination = choice("Destination", ["Home", "Home with Home Health", "Skilled Nursing Facility",
                                     "Inpatient Rehab", "Long-Term Acute Care", "Hospice"])
Risk = choice("Risk", ["Low", "Moderate", "High"])
SummaryStatus = choice("SummaryStatus", ["Not Started", "Draft", "Signed"])
TaskType = choice("TaskType", ["Prior Authorization", "Post-Acute Placement", "Durable Medical Equipment",
                               "Home Health Referral", "Transportation", "Follow-up Appointment",
                               "Medication Reconciliation", "Meds to Beds", "Patient Education",
                               "PCP Handoff", "Caregiver Coordination"])
TaskStatus = choice("TaskStatus", ["Not Started", "In Progress", "Waiting on External", "Blocked", "Completed"])
OwnerRole = choice("OwnerRole", ["Case Manager", "Social Worker", "Nurse", "Pharmacist", "Physician",
                                 "Physical Therapy"])


def s(n, label):
    return {"type": "string", "max_length": n, "display_name": label}


def memo(n, label):
    return {"type": "memo", "max_length": n, "display_name": label}


def date(label):
    return {"type": "datetime", "format": "DateOnly", "display_name": label}


def dt(label):
    return {"type": "datetime", "display_name": label}


def num(label):
    return {"type": "int", "display_name": label}


def flag(label):
    return {"type": "bool", "display_name": label}


def pick(enum_cls, label):
    return {"type": enum_cls, "display_name": label}


p = PREFIX
TABLES = [
    (f"{p}_Patient", "Patient", {
        f"{p}_MRN": s(20, "MRN"),
        f"{p}_DateOfBirth": date("Date of Birth"),
        f"{p}_PreferredLanguage": pick(Language, "Preferred Language"),
        f"{p}_Payer": pick(Payer, "Payer"),
        f"{p}_PayerPlan": s(150, "Payer Plan"),
        f"{p}_PCPName": s(100, "Primary Care Provider"),
        f"{p}_PCPPractice": s(150, "PCP Practice"),
        f"{p}_Caregiver": s(200, "Caregiver"),
        f"{p}_Allergies": s(200, "Allergies"),
        f"{p}_LivingSituation": memo(2000, "Living Situation"),
        f"{p}_Comorbidities": memo(2000, "Comorbidities"),
        f"{p}_Medications": memo(4000, "Medications"),
        f"{p}_EDVisits6Mo": num("ED Visits (Prior 6 Months)"),
        f"{p}_CharlsonIndex": num("Charlson Comorbidity Index"),
    }),
    (f"{p}_DischargePlan", "Discharge Plan", {
        f"{p}_Unit": pick(Unit, "Unit"),
        f"{p}_Bed": s(20, "Bed"),
        f"{p}_Attending": s(100, "Attending Physician"),
        f"{p}_CaseManager": s(100, "Case Manager"),
        f"{p}_PrimaryDiagnosis": s(200, "Primary Diagnosis"),
        f"{p}_AdmitDate": date("Admit Date"),
        f"{p}_EmergentAdmission": flag("Emergent Admission"),
        f"{p}_MedicallyReadyOn": date("Medically Ready On"),
        f"{p}_ExpectedDischarge": date("Expected Discharge"),
        f"{p}_ActualDischarge": date("Actual Discharge"),
        f"{p}_Status": pick(PlanStatus, "Plan Status"),
        f"{p}_Destination": pick(Destination, "Discharge Destination"),
        f"{p}_LACEScore": num("LACE Score"),
        f"{p}_ReadmissionRisk": pick(Risk, "Readmission Risk"),
        f"{p}_HospitalCourse": memo(4000, "Hospital Course"),
        f"{p}_SummaryStatus": pick(SummaryStatus, "Summary Status"),
        f"{p}_PatientSummary": memo(8000, "Patient Discharge Summary"),
        f"{p}_PriorAuthPacket": memo(10000, "Prior Auth Packet"),
    }),
    (f"{p}_DischargeTask", "Discharge Task", {
        f"{p}_TaskType": pick(TaskType, "Task Type"),
        f"{p}_Status": pick(TaskStatus, "Task Status"),
        f"{p}_OwnerRole": pick(OwnerRole, "Owner Role"),
        f"{p}_AssignedTo": s(100, "Assigned To"),
        f"{p}_IsBarrier": flag("Discharge Barrier"),
        f"{p}_DueDate": date("Due Date"),
        f"{p}_RequestedOn": dt("Requested On"),
        f"{p}_CompletedOn": dt("Completed On"),
        f"{p}_ExternalParty": s(150, "External Party"),
        f"{p}_Notes": memo(4000, "Notes"),
    }),
]

# Tables and columns go straight to the Web API metadata endpoints. Dataverse SDK 1.0.0 dropped the
# dict column specs (display names, lengths) this script was written against, so the payloads are
# explicit here and match the original tables: date-only columns are UserLocal, the primary Name is
# required with length 850.
DATAVERSE_URL = os.environ["DATAVERSE_URL"].rstrip("/")
API = f"{DATAVERSE_URL}/api/data/v9.2"
CRM = "Microsoft.Dynamics.CRM"


def label(text):
    return {"LocalizedLabels": [{"Label": text, "LanguageCode": 1033}]}


def headers():
    token = get_credential().get_token(f"{DATAVERSE_URL}/.default").token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json",
            "OData-Version": "4.0", "OData-MaxVersion": "4.0", "MSCRM.SolutionUniqueName": SOLUTION}


def metadata_post(path, body, attempts=3):
    for attempt in range(1, attempts + 1):
        resp = requests.post(f"{API}/{path}", json=body, timeout=300, headers=headers())
        if resp.ok:
            return
        # 0x80040216 ("An unexpected error occurred") is often transient right after a table is created.
        if "0x80040216" not in resp.text or attempt == attempts:
            raise RuntimeError(f"POST {path}: HTTP {resp.status_code} {resp.text[:500]}")
        time.sleep(15)


def existing_columns(schema):
    resp = requests.get(f"{API}/EntityDefinitions(LogicalName='{schema.lower()}')/Attributes?$select=LogicalName",
                        headers=headers(), timeout=120)
    resp.raise_for_status()
    return {a["LogicalName"] for a in resp.json()["value"]}


def attribute(schema, spec):
    kind = spec["type"]
    base = {"SchemaName": schema, "DisplayName": label(spec["display_name"]), "RequiredLevel": {"Value": "None"}}
    if isinstance(kind, type) and issubclass(kind, IntEnum):
        options = [{"Value": int(m), "Label": label(kind.__labels__[1033][m.name])} for m in kind]
        return {"@odata.type": f"{CRM}.PicklistAttributeMetadata", **base, "OptionSet": {
            "@odata.type": f"{CRM}.OptionSetMetadata", "IsGlobal": False, "OptionSetType": "Picklist", "Options": options}}
    if kind == "string":
        return {"@odata.type": f"{CRM}.StringAttributeMetadata", **base, "MaxLength": spec["max_length"],
                "FormatName": {"Value": "Text"}}
    if kind == "memo":
        return {"@odata.type": f"{CRM}.MemoAttributeMetadata", **base, "MaxLength": spec["max_length"], "Format": "Text"}
    if kind == "datetime":
        return {"@odata.type": f"{CRM}.DateTimeAttributeMetadata", **base, "Format": spec.get("format", "DateAndTime"),
                "DateTimeBehavior": {"Value": "UserLocal"}}
    if kind == "int":
        return {"@odata.type": f"{CRM}.IntegerAttributeMetadata", **base, "Format": "None",
                "MinValue": -2147483648, "MaxValue": 2147483647}
    if kind == "bool":
        return {"@odata.type": f"{CRM}.BooleanAttributeMetadata", **base, "DefaultValue": False, "OptionSet": {
            "@odata.type": f"{CRM}.BooleanOptionSetMetadata",
            "TrueOption": {"Value": 1, "Label": label("Yes")}, "FalseOption": {"Value": 0, "Label": label("No")}}}
    raise ValueError(f"unsupported column type for {schema}: {kind}")


def create_table(schema, display):
    metadata_post("EntityDefinitions", {
        "@odata.type": f"{CRM}.EntityMetadata", "SchemaName": schema, "OwnershipType": "UserOwned",
        "DisplayName": label(display), "DisplayCollectionName": label(f"{display}s"),
        "HasActivities": False, "HasNotes": False, "IsActivity": False,
        "Attributes": [{"@odata.type": f"{CRM}.StringAttributeMetadata", "SchemaName": f"{p}_Name", "IsPrimaryName": True,
                        "DisplayName": label("Name"), "RequiredLevel": {"Value": "ApplicationRequired"},
                        "MaxLength": 850, "FormatName": {"Value": "Text"}}]})
    time.sleep(5)


for schema, display, columns in TABLES:
    if client.tables.get(schema.lower()):
        print(f"table exists: {schema}")
    else:
        create_table(schema, display)
        print(f"table created: {schema}")
    have = existing_columns(schema)
    missing = {c: spec for c, spec in columns.items() if c.lower() not in have}
    for column, spec in missing.items():
        metadata_post(f"EntityDefinitions(LogicalName='{schema.lower()}')/Attributes", attribute(column, spec))
    print(f"  columns added: {len(missing)} of {len(columns)}")

LOOKUPS = [
    (f"{p}_dischargeplan", f"{p}_PatientId", f"{p}_patient", "Patient"),
    (f"{p}_dischargetask", f"{p}_DischargePlanId", f"{p}_dischargeplan", "Discharge Plan"),
]
for referencing, field, referenced, label in LOOKUPS:
    try:
        result = client.tables.create_lookup_field(
            referencing_table=referencing, lookup_field_name=field, referenced_table=referenced,
            display_name=label, solution=SOLUTION)
        print(f"lookup created: {result.lookup_schema_name}")
    except Exception as e:  # already exists on re-run
        msg = str(e)
        if "0x80040237" in msg or "already exists" in msg.lower() or "not unique" in msg.lower():
            print(f"lookup exists: {field}")
        else:
            raise
    time.sleep(3)

print("done")
