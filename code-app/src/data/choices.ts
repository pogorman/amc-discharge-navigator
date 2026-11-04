// Choice values for the amc_ tables (publisher option value prefix 41700).
// Labels come from the generated model maps so they always match Dataverse.
import {
  Amc_dischargeplansamc_destination,
  Amc_dischargeplansamc_readmissionrisk,
  Amc_dischargeplansamc_status,
  Amc_dischargeplansamc_summarystatus,
  Amc_dischargeplansamc_unit,
} from '../generated/models/Amc_dischargeplansModel';
import {
  Amc_dischargetasksamc_ownerrole,
  Amc_dischargetasksamc_status,
  Amc_dischargetasksamc_tasktype,
} from '../generated/models/Amc_dischargetasksModel';
import { Amc_patientsamc_payer, Amc_patientsamc_preferredlanguage } from '../generated/models/Amc_patientsModel';

export const PlanStatus = {
  Planning: 417000000,
  MedicallyReady: 417000001,
  PendingBarriers: 417000002,
  ReadyForDischarge: 417000003,
  Discharged: 417000004,
} as const;

export const TaskStatus = {
  NotStarted: 417000000,
  InProgress: 417000001,
  WaitingOnExternal: 417000002,
  Blocked: 417000003,
  Completed: 417000004,
} as const;

export const TaskType = { PriorAuthorization: 417000000 } as const;

export const SummaryStatus = { NotStarted: 417000000, Draft: 417000001, Signed: 417000002 } as const;

export const Risk = { Low: 417000000, Moderate: 417000001, High: 417000002 } as const;

export const Units = Object.entries(Amc_dischargeplansamc_unit).map(([value, text]) => ({
  value: Number(value),
  text,
}));

type LabelMap = Readonly<Record<number, string>>;

const label = (map: LabelMap) => (value?: number) => (value === undefined ? '' : map[value] ?? '');

export const planStatusLabel = label(Amc_dischargeplansamc_status);
export const summaryStatusLabel = label(Amc_dischargeplansamc_summarystatus);
export const unitLabel = label(Amc_dischargeplansamc_unit);
export const destinationLabel = label(Amc_dischargeplansamc_destination);
export const riskLabel = label(Amc_dischargeplansamc_readmissionrisk);
export const taskStatusLabel = label(Amc_dischargetasksamc_status);
export const taskTypeLabel = label(Amc_dischargetasksamc_tasktype);
export const ownerRoleLabel = label(Amc_dischargetasksamc_ownerrole);
export const languageLabel = label(Amc_patientsamc_preferredlanguage);
export const payerLabel = label(Amc_patientsamc_payer);
