---
name: prior-auth-packet
description: Drafts a prior authorization packet for post-acute care (skilled nursing facility, inpatient rehab, home health) from the chart by calling the Foundry prior-auth model deployment. Use when the user asks for a prior auth packet, an authorization request, or clinical justification for a payer.
---
<!-- bic:source=blank -->
# Prior auth packet

The Foundry model deployment `prior-auth` writes the packet. Your job is to gather the chart excerpt from Dataverse, call the Foundry chat completion tool, and return its output. Never write or rewrite the packet yourself.

## Input
- The patient's name or DP number. If the user didn't give one, ask for it.

## Steps
1. With the Dataverse tool, find the discharge plan (amc_dischargeplan) whose amc_name contains the patient's name or DP number. If several match, ask which one. If none match, say so and stop.
2. From the plan, read: Primary Diagnosis (amc_primarydiagnosis), Admit Date (amc_admitdate), Hospital Course (amc_hospitalcourse), Discharge Destination (amc_destination), Expected Discharge (amc_expecteddischarge), Attending Physician (amc_attending) and Case Manager (amc_casemanager).
3. From the plan's patient (amc_patient, through amc_patientid), read: name (amc_name), MRN (amc_mrn), Date of Birth (amc_dateofbirth), Payer (amc_payer), Payer Plan (amc_payerplan), Comorbidities (amc_comorbidities), Medications (amc_medications), Living Situation (amc_livingsituation) and Caregiver (amc_caregiver).
4. Read every discharge task for the plan (amc_dischargetask where amc_dischargeplanid is the plan): name, Task Type, Task Status, External Party (amc_externalparty) and Notes (amc_notes). Include all task notes: the payer's requests are in the Prior Authorization task notes, and the receiving facility is in the placement task.
5. Use choice labels such as "Medicare Advantage" or "Skilled Nursing Facility", never numeric choice values.
6. Call the Foundry chat completion tool with:
   - Model deployment: `prior-auth`
   - Messages, in this order:
     1. role `system`, content: the system prompt below, word for word.
     2. role `user`, content: a chart excerpt with one labelled field per line, using these labels: Patient, MRN, Date of birth, Payer, Payer plan, Primary diagnosis, Admit date, Attending, Hospital course, Comorbidities, Medications, Living situation, Caregiver, Discharge destination, Expected discharge, then one "Task:" line per task with its type, status, external party and notes.
7. Reply with the completion's message content exactly as returned: don't shorten, reformat or add to it. After it, on its own line, add: `Model: <the model field from the tool response> | Draft for case manager review`.
8. Offer to save it to the plan. Only if the user says yes, use the Dataverse tool to set Prior Auth Packet (amc_priorauthpacket) to the content.

If the tool call fails, say the Foundry model is unavailable right now and stop. Don't write the packet yourself.

## System prompt
You are a utilization review assistant at Contoso University Health drafting a prior authorization request for post-acute care.
Using only the chart excerpt provided, produce:
1. Request summary: service, receiving facility, payer and plan, requested start date.
2. Clinical justification for skilled need: functional status, skilled nursing or therapy needs, medical complexity, and why home is not yet safe.
3. Documentation checklist: items present in the chart, and items the payer typically requires that are missing.
4. Open questions for the case manager.
Put the chart field each statement comes from in square brackets, e.g. [Hospital course].
Do not invent values. If the payer asked for something (see task notes), say whether the chart contains it and quote it.
End with: "DRAFT for case manager review - not submitted."
