"""Seed synthetic patients, discharge plans and discharge tasks for the demo.

All data is fictional (Contoso University Health). Dates are relative to the
anchor date (default: today) so the demo can be re-seeded right before recording.

Usage (repo root):
  python scripts/seed_data.py                 # seed into empty tables
  python scripts/seed_data.py --reset         # delete existing demo rows first
  python scripts/seed_data.py --reset --anchor 2026-10-22
"""
import argparse
import os
import random
import sys
from datetime import date, datetime, time, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from auth import get_credential, load_env  # noqa: E402
from PowerPlatform.Dataverse.client import DataverseClient  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--reset", action="store_true", help="delete existing rows in the 3 demo tables first")
ap.add_argument("--anchor", help="anchor date YYYY-MM-DD (default today)")
args = ap.parse_args()

load_env()
client = DataverseClient(os.environ["DATAVERSE_URL"], get_credential())
TODAY = date.fromisoformat(args.anchor) if args.anchor else date.today()
rng = random.Random(42)
ME = "Patrick O'Gorman"


def v(i):
    return 417000000 + i


# Choice indexes (must match scripts/create_schema.py order)
EN, ES, VI, ZH, RU, AR = range(6)
MEDICARE, MA, MEDICAID, COMMERCIAL, SELFPAY = range(5)
U5W, U6E, U7N, U4S = range(4)
PLANNING, MED_READY, PENDING, READY, DISCHARGED = range(5)
HOME, HOME_HH, SNF, IRF, LTACH, HOSPICE = range(6)
LOW, MOD, HIGH = range(3)
NOT_STARTED_S, DRAFT_S, SIGNED_S = range(3)
(PA, PLACEMENT, DME, HH_REF, TRANSPORT, FOLLOWUP, MEDREC, M2B, EDUCATION,
 PCP, CAREGIVER) = range(11)
T_NOT_STARTED, T_IN_PROGRESS, T_WAITING, T_BLOCKED, T_COMPLETED = range(5)
CM, SW, RN, PHARM, MD, PT = range(6)

BARRIER_TYPES = {PA, PLACEMENT, DME, HH_REF, TRANSPORT, MEDREC}


def d(offset):
    return (TODAY + timedelta(days=offset)).isoformat()


def ts(offset_days, hour=9, minute=0):
    # local Eastern-ish business hours expressed in UTC (+4h)
    dt_ = datetime.combine(TODAY + timedelta(days=offset_days), time(hour, minute)) + timedelta(hours=4)
    return dt_.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def lace(los, emergent, charlson, ed):
    if los < 1:
        l_pts = 0
    elif los <= 3:
        l_pts = los
    elif los <= 6:
        l_pts = 4
    elif los <= 13:
        l_pts = 5
    else:
        l_pts = 7
    c_pts = 5 if charlson >= 4 else charlson
    score = l_pts + (3 if emergent else 0) + c_pts + min(ed, 4)
    risk = HIGH if score >= 10 else MOD if score >= 5 else LOW
    return score, risk


ATTENDINGS = {U5W: ["Dr. Amara Okafor", "Dr. Raj Patel"], U6E: ["Dr. Henry Liu", "Dr. Elena Vasquez"],
              U7N: ["Dr. Sofia Marchetti"], U4S: ["Dr. Daniel Brooks"]}
SOCIAL_WORKERS = ["Grace Kim, LCSW", "Marcus Bell, LCSW"]
NURSES = ["Tasha Greene, RN", "Kevin Doyle, RN", "Mei Chen, RN", "Omar Siddiqui, RN"]
PHARMACIST = "Nadia Haddad, PharmD"
THERAPIST = "Jordan Ellis, DPT"
CASE_MANAGERS = {U6E: ME, U5W: "Dana Whitfield, RN CM", U7N: "Luis Ortega, RN CM", U4S: "Priya Raman, RN CM"}

PAYER_PLANS = {
    MEDICARE: "Original Medicare Part A/B",
    MA: "Contoso Health Plan Medicare Advantage HMO",
    MEDICAID: "Fabrikam Community Medicaid Managed Care",
    COMMERCIAL: "Woodgrove Employer PPO",
    SELFPAY: "Self-pay (financial counseling referred)",
}
SNFS = ["Maple Grove Rehabilitation (SNF)", "Riverside Health & Rehab (SNF)", "Willow Creek Care Center (SNF)"]
IRF_NAME = "Contoso Rehabilitation Institute (IRF)"
LTACH_NAME = "Northbridge Specialty Hospital (LTACH)"
HH_AGENCY = "Northwind Home Health"
DME_VENDOR = "Fabrikam Medical Supply"
TRANSPORT_CO = "Tailspin Medical Transport"
PHARMACY = "Contoso University Health Outpatient Pharmacy"
HOSPICE_NAME = "Lakeside Hospice & Palliative Care"
PCP_PRACTICES = ["Contoso University Health - Eastside Primary Care",
                 "Contoso University Health - Midtown Internal Medicine",
                 "Lakeshore Family Medicine", "Contoso Community Health Center"]
PCPS = ["Dr. Ana Morales", "Dr. Kevin O'Brien", "Dr. Lily Tran", "Dr. Samuel Adeyemi", "Dr. Rachel Stein",
        "Dr. Victor Petrov"]

# ------------------------------------------------------------------ archetypes
# dx, unit, los range, destinations, comorbidities, charlson, meds, course template
ARCHETYPES = [
    ("Acute on chronic systolic heart failure exacerbation", U6E, (4, 7), [SNF, HOME_HH, HOME],
     "Heart failure with reduced ejection fraction; hypertension; type 2 diabetes.", 3,
     "Furosemide 40 mg PO daily\nCarvedilol 12.5 mg PO twice daily\nSacubitril/valsartan 49/51 mg PO twice daily\n"
     "Empagliflozin 10 mg PO daily\nAtorvastatin 40 mg PO nightly",
     "{age}{sex} with HFrEF admitted with volume overload. Diuresed with IV furosemide, net negative {fluid} L, "
     "transitioned to oral diuretic. Guideline-directed therapy optimized. Daily weights and 2 g sodium diet reviewed."),
    ("Non-ST elevation myocardial infarction, s/p PCI", U6E, (2, 4), [HOME, HOME_HH],
     "Coronary artery disease; hyperlipidemia; former smoker.", 1,
     "Aspirin 81 mg PO daily\nTicagrelor 90 mg PO twice daily (NEW)\nMetoprolol succinate 25 mg PO daily\n"
     "Atorvastatin 80 mg PO nightly (NEW)\nNitroglycerin 0.4 mg SL as needed",
     "{age}{sex} presented with chest pain, troponin elevation. Cath showed 90% LAD stenosis, drug-eluting stent placed. "
     "Uncomplicated post-procedure course. Cardiac rehab referral placed."),
    ("Atrial fibrillation with rapid ventricular response", U6E, (2, 4), [HOME],
     "Paroxysmal atrial fibrillation; hypertension; obstructive sleep apnea.", 1,
     "Apixaban 5 mg PO twice daily (NEW)\nDiltiazem ER 240 mg PO daily (NEW)\nLosartan 50 mg PO daily",
     "{age}{sex} with new rapid atrial fibrillation, rate controlled with IV then oral diltiazem. "
     "Anticoagulation started after shared decision-making. Echo with preserved EF."),
    ("COPD exacerbation", U5W, (3, 6), [HOME_HH, HOME, SNF],
     "Chronic obstructive pulmonary disease (GOLD 3); home oxygen 2 L; anxiety.", 2,
     "Tiotropium/olodaterol inhaler 2 puffs daily\nAlbuterol HFA 2 puffs every 4 hours as needed\n"
     "Prednisone 40 mg PO daily x 2 more days\nAzithromycin 250 mg PO daily x 2 more days",
     "{age}{sex} with severe COPD admitted with hypoxic respiratory distress. Treated with steroids, nebulizers and "
     "antibiotics; weaned back to baseline 2 L oxygen. Inhaler technique reviewed."),
    ("Community-acquired pneumonia", U5W, (3, 5), [HOME, HOME_HH],
     "Type 2 diabetes; chronic kidney disease stage 3a.", 3,
     "Amoxicillin/clavulanate 875 mg PO twice daily x 3 more days\nMetformin 500 mg PO twice daily\n"
     "Insulin glargine 18 units nightly",
     "{age}{sex} admitted with right lower lobe pneumonia and hyperglycemia. Improved on IV ceftriaxone and "
     "azithromycin, transitioned to oral antibiotics. Afebrile more than 48 hours, ambulating on room air."),
    ("Sepsis due to urinary tract infection", U5W, (4, 7), [SNF, HOME_HH],
     "Dementia (moderate); recurrent UTIs; osteoarthritis.", 2,
     "Cefpodoxime 200 mg PO twice daily x 5 more days\nDonepezil 10 mg PO nightly\nAcetaminophen 650 mg PO every 6 hours as needed",
     "{age}{sex} with moderate dementia admitted with sepsis from E. coli UTI. Treated with IV fluids and antibiotics; "
     "delirium improving. PT recommends supervision for mobility."),
    ("Acute ischemic stroke", U5W, (5, 9), [IRF, SNF],
     "Hypertension; hyperlipidemia; atrial fibrillation.", 3,
     "Apixaban 5 mg PO twice daily\nAtorvastatin 80 mg PO nightly\nAmlodipine 10 mg PO daily",
     "{age}{sex} with left MCA ischemic stroke causing right-sided weakness and expressive aphasia. "
     "Not a thrombectomy candidate. Neurology recommends acute inpatient rehabilitation."),
    ("Left hip fracture, s/p ORIF", U7N, (3, 5), [SNF, IRF],
     "Osteoporosis; hypertension; macular degeneration.", 1,
     "Enoxaparin 40 mg SC daily x 28 days\nOxycodone 5 mg PO every 6 hours as needed\nAcetaminophen 1 g PO every 8 hours\n"
     "Calcium/vitamin D PO twice daily",
     "{age}{sex} fell at home, sustained left intertrochanteric fracture, underwent ORIF on hospital day 1. "
     "Weight bearing as tolerated. Ambulating 40 ft with walker and moderate assist."),
    ("Primary right total knee arthroplasty", U7N, (1, 2), [HOME_HH, HOME],
     "Osteoarthritis; obesity; hypertension.", 0,
     "Aspirin 81 mg PO twice daily x 35 days\nOxycodone 5 mg PO every 4 hours as needed\nCelecoxib 200 mg PO daily",
     "{age}{sex} underwent elective right TKA. Pain controlled on oral regimen, cleared stairs with PT. "
     "Home PT arranged."),
    ("Neutropenic fever during chemotherapy", U4S, (3, 6), [HOME, HOME_HH],
     "Diffuse large B-cell lymphoma on R-CHOP cycle 3.", 2,
     "Levofloxacin 500 mg PO daily\nOndansetron 8 mg PO every 8 hours as needed\nFilgrastim per oncology plan",
     "{age}{sex} with DLBCL admitted with neutropenic fever. Cultures negative; treated with cefepime, counts recovering. "
     "Oncology follow-up and next cycle timing confirmed."),
    ("Small bowel obstruction", U4S, (4, 8), [HOME, HOME_HH, LTACH],
     "Metastatic colon cancer; prior bowel resection.", 6,
     "Ondansetron 4 mg PO every 8 hours as needed\nHydromorphone 2 mg PO every 4 hours as needed\nSenna 8.6 mg PO nightly",
     "{age}{sex} with metastatic colon cancer admitted with partial SBO, managed with bowel rest and NG decompression. "
     "Tolerating soft diet. Goals-of-care conversation held with oncology and palliative care."),
]

FIRST_M = ["James", "Robert", "Wei", "Ahmed", "Dmitri", "Carlos", "Thomas", "Minh", "George", "Samuel", "Frank",
           "Hector", "Arthur", "Joseph", "Kwame", "Luis"]
FIRST_F = ["Maria", "Linh", "Patricia", "Fatima", "Olga", "Dorothy", "Mei", "Grace", "Evelyn", "Rosa", "Barbara",
           "Aisha", "Helen", "Carmen", "Ruth", "Nora"]
LAST = ["Johnson", "Nguyen", "Kowalski", "Haddad", "Ivanova", "Garcia", "Washington", "Chen", "Murphy", "Okonkwo",
        "Rossi", "Patel", "Hernandez", "Thompson", "Baker", "Lopez", "Schmidt", "Tran", "Mensah", "Volkov",
        "Sullivan", "Moreau", "Jackson", "Lindqvist", "Brennan", "Castillo", "Yamamoto", "Abbott", "Fitzgerald",
        "Delgado", "Wright", "Novak", "Carter", "Pham", "Russo", "Hughes", "Petrova", "Kaplan", "Ortiz", "Bennett"]
LANG_BY_NAME_EXTRA = {"Pham": VI, "Petrova": RU, "Castillo": ES, "Delgado": ES, "Ortiz": ES}
LANG_BY_NAME = {"Nguyen": VI, "Tran": VI, "Chen": ZH, "Ivanova": RU, "Volkov": RU, "Haddad": AR,
                "Garcia": ES, "Hernandez": ES, "Lopez": ES}
LIVING = [
    "Lives with spouse in a single-story home. Spouse able to assist.",
    "Lives alone in a 3rd-floor apartment with elevator. Son checks in weekly.",
    "Lives with adult daughter who works full time. Two steps to enter the home.",
    "Lives alone in a two-story home; bedroom upstairs (12 stairs). No local family.",
    "Lives with spouse who has limited mobility. One-level condo.",
    "Lives in an assisted living facility; returns there at baseline.",
]

used_first, used_last = {"Miguel"}, {"Reyes"}
LANG_BY_NAME.update(LANG_BY_NAME_EXTRA)


def make_name():
    """Unique first and last names across the dataset so nothing looks generated on camera."""
    while True:
        sex = rng.choice("MF")
        pool = FIRST_M if sex == "M" else FIRST_F
        first = rng.choice(pool)
        last = rng.choice(LAST)
        if last in used_last or (first in used_first and len(used_first) < len(FIRST_M) + len(FIRST_F)):
            continue
        used_first.add(first)
        used_last.add(last)
        return f"{first} {last}", sex, last


mrn_seq = [48213]


def next_mrn():
    mrn_seq[0] += rng.randint(37, 911)
    return f"CUH-{mrn_seq[0]:07d}"


# ------------------------------------------------------------------ task builder
def assignee(role, plan):
    return {CM: plan["cm"], SW: rng.choice(SOCIAL_WORKERS), RN: rng.choice(NURSES), PHARM: PHARMACIST,
            MD: plan["attending"], PT: THERAPIST}[role]


def task_templates(dest, payer, language, snf_name):
    lang_name = ["English", "Spanish", "Vietnamese", "Mandarin", "Russian", "Arabic"][language]
    edu = (f"Teach-back in {lang_name}: warning signs and new medications" if language != EN
           else "Teach-back: warning signs and new medications")
    t = []
    needs_pa = payer in (MA, COMMERCIAL, MEDICAID) and dest in (SNF, IRF, LTACH, HOME_HH)
    if dest in (SNF, IRF, LTACH):
        place = {SNF: snf_name, IRF: IRF_NAME, LTACH: LTACH_NAME}[dest]
        kind = {SNF: "SNF", IRF: "inpatient rehab", LTACH: "LTACH"}[dest]
        if needs_pa:
            t.append((PA, f"{kind.upper() if kind == 'SNF' else kind.title()} prior authorization", CM,
                      PAYER_PLANS[payer]))
        t.append((PLACEMENT, f"{kind.upper() if kind == 'SNF' else kind.title()} bed acceptance - {place.split(' (')[0]}",
                  SW, place))
        t.append((TRANSPORT, "Wheelchair van transport", CM, TRANSPORT_CO))
    if dest == HOME_HH:
        if needs_pa:
            t.append((PA, "Home health prior authorization", CM, PAYER_PLANS[payer]))
        t.append((HH_REF, "Home health referral (skilled nursing + PT)", CM, HH_AGENCY))
        if rng.random() < 0.6:
            t.append((DME, rng.choice(["Rolling walker delivery", "Shower chair and walker", "Home oxygen setup"]),
                      CM, DME_VENDOR))
    if dest == HOSPICE:
        t.append((PLACEMENT, "Hospice intake", SW, HOSPICE_NAME))
    t.append((MEDREC, "Discharge medication reconciliation", PHARM, ""))
    if dest in (HOME, HOME_HH):
        t.append((M2B, "Meds to Beds delivery", PHARM, PHARMACY))
        t.append((FOLLOWUP, "Follow-up appointment within 7 days", CM, ""))
    t.append((EDUCATION, edu, RN, ""))
    t.append((PCP, "PCP handoff and discharge summary", MD, ""))
    return t


def statuses_for(plan_status, ttype):
    """Pick a task status consistent with where the plan is."""
    barrier = ttype in BARRIER_TYPES
    if plan_status == DISCHARGED:
        return T_COMPLETED
    if plan_status == READY:
        return T_COMPLETED if barrier else rng.choice([T_COMPLETED, T_IN_PROGRESS])
    if plan_status == PLANNING:
        return rng.choice([T_NOT_STARTED, T_NOT_STARTED, T_IN_PROGRESS])
    # MED_READY / PENDING
    if barrier:
        return rng.choice([T_COMPLETED, T_IN_PROGRESS, T_WAITING])
    return rng.choice([T_NOT_STARTED, T_IN_PROGRESS, T_COMPLETED])


NOTE_BY_STATUS = {
    (PA, T_WAITING): "Submitted via payer portal. Payer requested additional clinical documentation.",
    (PA, T_IN_PROGRESS): "Assembling clinical justification from the chart.",
    (PA, T_COMPLETED): "Approved. Authorization number on file.",
    (PLACEMENT, T_WAITING): "Referral sent. Facility reviewing clinicals; bed availability pending.",
    (PLACEMENT, T_COMPLETED): "Accepted. Bed confirmed.",
    (HH_REF, T_WAITING): "Referral sent; agency confirming start-of-care date.",
    (HH_REF, T_COMPLETED): "Start of care confirmed for day after discharge.",
    (DME, T_WAITING): "Order placed; delivery window pending.",
    (TRANSPORT, T_NOT_STARTED): "Schedule once destination accepts.",
    (MEDREC, T_COMPLETED): "Reconciled with outpatient list. Changes reviewed with patient.",
}

# ------------------------------------------------------------------ build data
patients, plans, tasks = [], [], []


def add_case(pat, plan, task_list):
    patients.append(pat)
    plans.append(plan)
    tasks.append(task_list)


# ---- Hero: Miguel Reyes (O'G's caseload) ----
hero_pat = {
    "amc_name": "Miguel Reyes",
    "amc_mrn": "CUH-0048213",
    "amc_dateofbirth": "1948-03-22",
    "amc_preferredlanguage": v(ES),
    "amc_payer": v(MA),
    "amc_payerplan": PAYER_PLANS[MA],
    "amc_pcpname": "Dr. Ana Morales",
    "amc_pcppractice": PCP_PRACTICES[0],
    "amc_caregiver": "Daughter: Lucia Reyes (works days, available after 5 PM), 555-0142",
    "amc_allergies": "Penicillin (hives)",
    "amc_livingsituation": ("Lives alone in a 2nd-floor walk-up apartment (14 stairs, no elevator). Daughter visits "
                            "most evenings. Uses a cane at baseline; PT now recommends a rolling walker."),
    "amc_comorbidities": ("Heart failure with reduced ejection fraction (EF 30%); type 2 diabetes; chronic kidney "
                          "disease stage 3a; hypertension; atrial fibrillation on anticoagulation."),
    "amc_medications": ("Furosemide 40 mg PO twice daily (CHANGED: was once daily)\n"
                        "Sacubitril/valsartan 24/26 mg PO twice daily (NEW)\n"
                        "Spironolactone 12.5 mg PO daily (NEW)\n"
                        "Metoprolol succinate 50 mg PO daily\n"
                        "Apixaban 5 mg PO twice daily\n"
                        "Metformin 500 mg PO twice daily\n"
                        "Atorvastatin 40 mg PO nightly"),
    "amc_edvisits6mo": 2,
    "amc_charlsonindex": 4,
}
hero_los = 5
h_score, h_risk = lace(hero_los, True, 4, 2)
hero_plan = {
    "amc_unit": v(U6E), "amc_bed": "6E-14", "amc_attending": "Dr. Henry Liu", "amc_casemanager": ME,
    "amc_primarydiagnosis": "Acute on chronic systolic heart failure (HFrEF) exacerbation",
    "amc_admitdate": d(-hero_los), "amc_emergentadmission": True, "amc_medicallyreadyon": d(-1),
    "amc_expecteddischarge": d(0), "amc_status": v(PENDING), "amc_destination": v(SNF),
    "amc_lacescore": h_score, "amc_readmissionrisk": v(h_risk), "amc_summarystatus": v(NOT_STARTED_S),
    "amc_hospitalcourse": (
        "78M with HFrEF (EF 30%) admitted via the ED with 3 days of worsening dyspnea, orthopnea and a 4 kg weight "
        "gain. Diuresed with IV furosemide, net negative 5.2 L; transitioned to oral furosemide 40 mg twice daily on "
        "hospital day 4. Started sacubitril/valsartan and spironolactone; potassium and creatinine stable. Ambulating "
        "150 ft with a rolling walker and standby assist. PT recommends short-term skilled nursing for strengthening "
        "before returning to a 2nd-floor walk-up. Medically ready for discharge as of yesterday."),
}
hero_tasks = [
    {"amc_name": "SNF prior authorization", "amc_tasktype": v(PA), "amc_status": v(T_WAITING),
     "amc_ownerrole": v(CM), "amc_assignedto": ME, "amc_isbarrier": True, "amc_duedate": d(0),
     "amc_requestedon": ts(-1, 10, 15), "amc_externalparty": PAYER_PLANS[MA],
     "amc_notes": ("Submitted via payer portal yesterday 10:15 AM (ref PA-2210-7734). Payer requested updated PT "
                   "notes with ambulation distance and assist level before review.")},
    {"amc_name": "SNF bed acceptance - Maple Grove Rehabilitation", "amc_tasktype": v(PLACEMENT),
     "amc_status": v(T_WAITING), "amc_ownerrole": v(SW), "amc_assignedto": "Grace Kim, LCSW", "amc_isbarrier": True,
     "amc_duedate": d(0), "amc_requestedon": ts(-2, 14, 0), "amc_externalparty": SNFS[0],
     "amc_notes": ("Referrals sent to 3 facilities. Maple Grove has a bed tomorrow, pending insurance authorization. "
                   "Riverside declined (no bed). Willow Creek still reviewing.")},
    {"amc_name": "Wheelchair van transport to SNF", "amc_tasktype": v(TRANSPORT), "amc_status": v(T_NOT_STARTED),
     "amc_ownerrole": v(CM), "amc_assignedto": ME, "amc_isbarrier": True, "amc_duedate": d(1),
     "amc_externalparty": TRANSPORT_CO, "amc_notes": "Schedule once SNF accepts and authorization is approved."},
    {"amc_name": "Discharge medication reconciliation", "amc_tasktype": v(MEDREC), "amc_status": v(T_COMPLETED),
     "amc_ownerrole": v(PHARM), "amc_assignedto": PHARMACIST, "amc_isbarrier": True, "amc_duedate": d(-1),
     "amc_requestedon": ts(-2, 8, 30), "amc_completedon": ts(-1, 15, 40),
     "amc_notes": ("Reconciled. NEW: sacubitril/valsartan, spironolactone. CHANGED: furosemide to twice daily. "
                   "Patient needs a Spanish-language medication list.")},
    {"amc_name": "Teach-back in Spanish: heart failure warning signs and daily weights",
     "amc_tasktype": v(EDUCATION), "amc_status": v(T_IN_PROGRESS), "amc_ownerrole": v(RN),
     "amc_assignedto": "Tasha Greene, RN", "amc_isbarrier": False, "amc_duedate": d(0),
     "amc_notes": "Interpreter booked for 2 PM. Patient-facing summary in Spanish not yet drafted."},
    {"amc_name": "Caregiver call - daughter Lucia Reyes", "amc_tasktype": v(CAREGIVER), "amc_status": v(T_COMPLETED),
     "amc_ownerrole": v(SW), "amc_assignedto": "Grace Kim, LCSW", "amc_isbarrier": False, "amc_duedate": d(-1),
     "amc_requestedon": ts(-2, 16, 0), "amc_completedon": ts(-1, 17, 30),
     "amc_notes": "Daughter agrees with SNF plan and prefers Maple Grove (close to her work)."},
    {"amc_name": "Cardiology follow-up within 7 days", "amc_tasktype": v(FOLLOWUP), "amc_status": v(T_NOT_STARTED),
     "amc_ownerrole": v(CM), "amc_assignedto": ME, "amc_isbarrier": False, "amc_duedate": d(1),
     "amc_notes": "Coordinate with SNF so the visit happens even while he is in rehab."},
    {"amc_name": "PCP handoff to Dr. Ana Morales", "amc_tasktype": v(PCP), "amc_status": v(T_NOT_STARTED),
     "amc_ownerrole": v(MD), "amc_assignedto": "Dr. Henry Liu", "amc_isbarrier": False, "amc_duedate": d(1),
     "amc_externalparty": PCP_PRACTICES[0],
     "amc_notes": "Send discharge summary and medication changes before the first follow-up."},
]
add_case(hero_pat, hero_plan, hero_tasks)


# ---- Generated cases ----
def generated_case(unit, plan_status, discharged_days_ago=None):
    arch = rng.choice([a for a in ARCHETYPES if a[1] == unit])
    dx, _, (lo, hi), dests, comorb, charlson, meds, course = arch
    name, sex, last = make_name()
    age = rng.randint(52, 91)
    language = LANG_BY_NAME.get(last, EN) if rng.random() < 0.8 else EN
    payer = rng.choice([MEDICARE, MA, MA, MEDICAID, COMMERCIAL]) if age >= 65 else rng.choice([COMMERCIAL, MEDICAID, SELFPAY])
    if age >= 65 and payer in (COMMERCIAL, SELFPAY):
        payer = MA
    dest = rng.choice(dests)
    ed = rng.choice([0, 0, 0, 0, 0, 1, 1, 2, 3])
    los = rng.randint(lo, hi)
    emergent = "arthroplasty" not in dx

    if plan_status == DISCHARGED:
        actual = -discharged_days_ago
        avoidable = rng.choice([0, 0, 0, 1, 1, 2])
        med_ready = actual - avoidable
        admit = med_ready - los
        edd = med_ready
    else:
        # how far into the stay we are
        if plan_status == PLANNING:
            admit = -rng.randint(1, max(1, los - 1))
            med_ready = None
            edd = admit + los
        elif plan_status == READY:
            admit = -los
            med_ready = 0
            edd = 0
        else:  # MED_READY / PENDING
            delay = rng.choice([0, 1, 1, 2, 3])
            admit = -(los + delay)
            med_ready = -delay
            edd = 0 if delay == 0 else rng.choice([0, 1])
        actual = None
    total_los = (actual if actual is not None else edd) - admit
    score, risk = lace(total_los, emergent and rng.random() < 0.8, charlson, ed)

    cm = CASE_MANAGERS[unit]
    attending = rng.choice(ATTENDINGS[unit])
    pat = {
        "amc_name": name, "amc_mrn": next_mrn(),
        "amc_dateofbirth": date(TODAY.year - age, rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
        "amc_preferredlanguage": v(language), "amc_payer": v(payer), "amc_payerplan": PAYER_PLANS[payer],
        "amc_pcpname": rng.choice(PCPS), "amc_pcppractice": rng.choice(PCP_PRACTICES),
        "amc_caregiver": rng.choice(["Spouse", "Daughter", "Son", "Niece", "Friend"]) + f", 555-01{rng.randint(10, 99)}",
        "amc_allergies": rng.choice(["No known drug allergies", "Sulfa (rash)", "Codeine (nausea)", "Iodinated contrast (hives)",
                                     "No known drug allergies"]),
        "amc_livingsituation": rng.choice(LIVING), "amc_comorbidities": comorb, "amc_medications": meds,
        "amc_edvisits6mo": ed, "amc_charlsonindex": charlson,
    }
    plan = {
        "amc_unit": v(unit), "amc_bed": f"{['5W', '6E', '7N', '4S'][unit]}-{rng.randint(1, 28):02d}",
        "amc_attending": attending, "amc_casemanager": cm, "amc_primarydiagnosis": dx,
        "amc_admitdate": d(admit), "amc_emergentadmission": emergent,
        "amc_expecteddischarge": d(edd), "amc_status": v(plan_status), "amc_destination": v(dest),
        "amc_lacescore": score, "amc_readmissionrisk": v(risk),
        "amc_hospitalcourse": course.format(age=age, sex=sex, fluid=round(rng.uniform(2.5, 6.0), 1)),
        "amc_summarystatus": v(SIGNED_S if plan_status in (DISCHARGED, READY) else
                               DRAFT_S if plan_status == PENDING and rng.random() < 0.3 else NOT_STARTED_S),
    }
    if med_ready is not None:
        plan["amc_medicallyreadyon"] = d(med_ready)
    if actual is not None:
        plan["amc_actualdischarge"] = d(actual)
    if plan_status in (DISCHARGED, READY):
        plan["amc_patientsummary"] = (
            f"You were in the hospital for {dx.lower()}. Take your medicines exactly as listed, keep your follow-up "
            f"appointment, and call your care team or 911 right away if your symptoms get worse.")

    ctx = {"cm": cm, "attending": attending}
    snf = rng.choice(SNFS)
    task_list = []
    for ttype, title, role, external in task_templates(dest, payer, language, snf):
        st = statuses_for(plan_status, ttype)
        due = (actual if actual is not None else edd) - (1 if ttype == PCP and actual is None else 0)
        row = {
            "amc_name": title, "amc_tasktype": v(ttype), "amc_status": v(st), "amc_ownerrole": v(role),
            "amc_assignedto": assignee(role, ctx), "amc_isbarrier": ttype in BARRIER_TYPES,
            "amc_duedate": d(due + (1 if ttype == PCP else 0)),
        }
        if external:
            row["amc_externalparty"] = external
        if st != T_NOT_STARTED:
            req_day = (med_ready if med_ready is not None else edd) - rng.randint(1, 3)
            row["amc_requestedon"] = ts(req_day, rng.randint(8, 15), rng.choice([0, 15, 30, 45]))
            if st == T_COMPLETED:
                # turnaround: prior auth 6-72h, placement 12-60h, others 1-24h
                hours = {PA: rng.randint(6, 72), PLACEMENT: rng.randint(12, 60)}.get(ttype, rng.randint(1, 24))
                start = datetime.fromisoformat(row["amc_requestedon"].replace("Z", "+00:00"))
                done = start + timedelta(hours=hours)
                row["amc_completedon"] = done.isoformat().replace("+00:00", "Z")
        note = NOTE_BY_STATUS.get((ttype, st))
        if note:
            row["amc_notes"] = note
        task_list.append(row)
    return pat, plan, task_list


# Active census: O'G's 6 East caseload plus the other units
ACTIVE = (
    [(U6E, s) for s in [PENDING, MED_READY, PLANNING, PLANNING, READY, PENDING]] +
    [(U5W, s) for s in [PENDING, PENDING, MED_READY, PLANNING, READY, PLANNING]] +
    [(U7N, s) for s in [MED_READY, PENDING, READY, PLANNING, PLANNING]] +
    [(U4S, s) for s in [PLANNING, PENDING, MED_READY, READY]]
)
for unit, status in ACTIVE:
    add_case(*generated_case(unit, status))

# Discharged in the prior 14 days (metrics history)
for i in range(14):
    unit = [U6E, U5W, U7N, U4S][i % 4]
    add_case(*generated_case(unit, DISCHARGED, discharged_days_ago=rng.randint(1, 14)))

# ------------------------------------------------------------------ reset
TABLES = ["amc_dischargetask", "amc_dischargeplan", "amc_patient"]
if args.reset:
    for t in TABLES:
        ids = [r[f"{t}id"] for r in client.records.list(t, select=[f"{t}id"])]
        if ids:
            client.records.delete(t, ids, use_bulk_delete=False)
        print(f"reset {t}: deleted {len(ids)}")
else:
    existing = list(client.records.list("amc_patient", select=["amc_patientid"], top=1))
    if existing:
        sys.exit("amc_patient already has rows. Re-run with --reset to replace the demo data.")

# ------------------------------------------------------------------ write
plan_names = []
for i, (pat, plan) in enumerate(zip(patients, plans), start=1001):
    plan["amc_name"] = f"DP-{i} {pat['amc_name']}"
    plan_names.append(plan["amc_name"])

patient_ids = client.records.create("amc_patient", patients)
for plan, pid in zip(plans, patient_ids):
    plan["amc_PatientId@odata.bind"] = f"/amc_patients({pid})"
plan_ids = client.records.create("amc_dischargeplan", plans)

all_tasks = []
for plan_id, task_list in zip(plan_ids, tasks):
    for t in task_list:
        t["amc_DischargePlanId@odata.bind"] = f"/amc_dischargeplans({plan_id})"
        all_tasks.append(t)
task_ids = client.records.create("amc_dischargetask", all_tasks)

print(f"anchor date: {TODAY}")
print(f"patients: {len(patient_ids)}  plans: {len(plan_ids)}  tasks: {len(task_ids)}")
print(f"hero: {plan_names[0]}")
