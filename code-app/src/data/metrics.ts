import { PlanStatus, Risk, TaskStatus, TaskType, taskTypeLabel, unitLabel } from './choices';
import type { PlanRow, Task } from './useDischargeData';

const DAY_MS = 86_400_000;

/** Date-only columns come back as "YYYY-MM-DDT00:00:00Z"; compare on the date part to avoid time-zone drift. */
export const dateKey = (value?: string) => value?.slice(0, 10);

export const todayKey = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
};

const daysBetween = (fromKey: string, toKey: string) =>
  Math.round((Date.parse(`${toKey}T00:00:00Z`) - Date.parse(`${fromKey}T00:00:00Z`)) / DAY_MS);

export const isActive = (row: PlanRow) => row.plan.amc_status !== PlanStatus.Discharged;

export const isOpenBarrier = (task: Task) => task.amc_isbarrier === true && task.amc_status !== TaskStatus.Completed;

/** Days a medically ready patient is still in a bed. Zero when not medically ready yet. */
export function avoidableDays(row: PlanRow, today = todayKey()): number {
  const ready = dateKey(row.plan.amc_medicallyreadyon);
  if (!ready || !isActive(row)) return 0;
  return Math.max(0, daysBetween(ready, today));
}

export function median(values: number[]): number | undefined {
  if (!values.length) return undefined;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export interface Kpis {
  dischargesToday: number;
  medicallyReadyStillHere: number;
  avoidableDays: number;
  openBarriers: number;
  priorAuthMedianHours?: number;
  priorAuthSample: number;
  highRisk: number;
}

/**
 * `active` rows drive census KPIs; `all` rows (including recent discharges) feed the
 * prior-auth turnaround so the metric has history behind it.
 */
export function computeKpis(active: PlanRow[], all: PlanRow[], today = todayKey()): Kpis {
  const since = Date.now() - 14 * DAY_MS;
  const turnaroundHours = all
    .flatMap((row) => row.tasks)
    .filter((t) => t.amc_tasktype === TaskType.PriorAuthorization && t.amc_status === TaskStatus.Completed)
    .filter((t) => t.amc_requestedon && t.amc_completedon && Date.parse(t.amc_completedon) >= since)
    .map((t) => (Date.parse(t.amc_completedon!) - Date.parse(t.amc_requestedon!)) / 3_600_000);

  const ready = active.filter((row) => avoidableDays(row, today) > 0);
  return {
    dischargesToday: active.filter((row) => dateKey(row.plan.amc_expecteddischarge) === today).length,
    medicallyReadyStillHere: ready.length,
    avoidableDays: ready.reduce((sum, row) => sum + avoidableDays(row, today), 0),
    openBarriers: active.reduce((sum, row) => sum + row.tasks.filter(isOpenBarrier).length, 0),
    priorAuthMedianHours: median(turnaroundHours),
    priorAuthSample: turnaroundHours.length,
    highRisk: active.filter((row) => row.plan.amc_readmissionrisk === Risk.High).length,
  };
}

export interface Bar {
  label: string;
  value: number;
}

const toBars = (counts: Map<string, number>): Bar[] =>
  [...counts.entries()].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value);

export function barriersByType(active: PlanRow[]): Bar[] {
  const counts = new Map<string, number>();
  for (const task of active.flatMap((row) => row.tasks).filter(isOpenBarrier)) {
    const key = taskTypeLabel(task.amc_tasktype);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return toBars(counts);
}

export function avoidableDaysByUnit(active: PlanRow[], today = todayKey()): Bar[] {
  const counts = new Map<string, number>();
  for (const row of active) {
    const key = unitLabel(row.plan.amc_unit);
    counts.set(key, (counts.get(key) ?? 0) + avoidableDays(row, today));
  }
  return toBars(counts);
}
