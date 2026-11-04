import { useCallback, useEffect, useState } from 'react';
import type { Amc_dischargeplans } from '../generated/models/Amc_dischargeplansModel';
import type { Amc_dischargetasks } from '../generated/models/Amc_dischargetasksModel';
import type { Amc_patients } from '../generated/models/Amc_patientsModel';
import { Amc_dischargeplansService } from '../generated/services/Amc_dischargeplansService';
import { Amc_dischargetasksService } from '../generated/services/Amc_dischargetasksService';
import { Amc_patientsService } from '../generated/services/Amc_patientsService';
import { TaskStatus } from './choices';

export type Plan = Amc_dischargeplans;
export type Task = Amc_dischargetasks;
export type Patient = Amc_patients;

/** A discharge plan joined with its patient and tasks. */
export interface PlanRow {
  plan: Plan;
  patient?: Patient;
  tasks: Task[];
}

// Real columns only: the generated *name fields are virtual and can't be selected.
const PLAN_COLUMNS = [
  'amc_dischargeplanid', 'amc_name', 'amc_unit', 'amc_bed', 'amc_attending', 'amc_casemanager',
  'amc_primarydiagnosis', 'amc_admitdate', 'amc_medicallyreadyon', 'amc_expecteddischarge',
  'amc_actualdischarge', 'amc_status', 'amc_destination', 'amc_lacescore', 'amc_readmissionrisk',
  'amc_hospitalcourse', 'amc_summarystatus', 'amc_patientsummary', 'amc_priorauthpacket', '_amc_patientid_value',
];
const TASK_COLUMNS = [
  'amc_dischargetaskid', 'amc_name', 'amc_tasktype', 'amc_status', 'amc_ownerrole', 'amc_assignedto',
  'amc_isbarrier', 'amc_duedate', 'amc_requestedon', 'amc_completedon', 'amc_externalparty', 'amc_notes',
  '_amc_dischargeplanid_value',
];
const PATIENT_COLUMNS = [
  'amc_patientid', 'amc_name', 'amc_mrn', 'amc_preferredlanguage', 'amc_payer', 'amc_payerplan',
  'amc_pcpname', 'amc_caregiver', 'amc_livingsituation',
];

async function unwrap<T>(request: Promise<{ data: T[]; error?: unknown }>): Promise<T[]> {
  const result = await request;
  if (result.error) throw result.error;
  return result.data ?? [];
}

const errorText = (e: unknown) => (e instanceof Error ? e.message : typeof e === 'string' ? e : JSON.stringify(e));

export function useDischargeData() {
  const [rows, setRows] = useState<PlanRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [loadedAt, setLoadedAt] = useState<Date>();

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try {
      const [plans, tasks, patients] = await Promise.all([
        unwrap(Amc_dischargeplansService.getAll({ select: PLAN_COLUMNS })),
        unwrap(Amc_dischargetasksService.getAll({ select: TASK_COLUMNS })),
        unwrap(Amc_patientsService.getAll({ select: PATIENT_COLUMNS })),
      ]);
      const patientsById = new Map(patients.map((p) => [p.amc_patientid, p]));
      const tasksByPlan = new Map<string, Task[]>();
      for (const task of tasks) {
        const planId = task._amc_dischargeplanid_value;
        if (!planId) continue;
        tasksByPlan.set(planId, [...(tasksByPlan.get(planId) ?? []), task]);
      }
      setRows(
        plans.map((plan) => ({
          plan,
          patient: plan._amc_patientid_value ? patientsById.get(plan._amc_patientid_value) : undefined,
          tasks: tasksByPlan.get(plan.amc_dischargeplanid) ?? [],
        })),
      );
      setLoadedAt(new Date());
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  /** The one write in the app: close out a task, then reload so every view agrees. */
  const completeTask = useCallback(
    async (taskId: string) => {
      const result = await Amc_dischargetasksService.update(taskId, {
        amc_status: TaskStatus.Completed,
        amc_completedon: new Date().toISOString(),
      });
      if (result.error) throw new Error(errorText(result.error));
      await refresh();
    },
    [refresh],
  );

  return { rows, loading, error, loadedAt, refresh, completeTask };
}
