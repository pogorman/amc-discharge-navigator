import type { BadgeProps } from '@fluentui/react-components';
import { PlanStatus, Risk, TaskStatus } from '../data/choices';
import { dateKey } from '../data/metrics';

const shortDate = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });

/** Formats a date-only column ("YYYY-MM-DDT00:00:00Z") without shifting it by the viewer's time zone. */
export function formatDate(value?: string): string {
  const key = dateKey(value);
  return key ? shortDate.format(new Date(`${key}T00:00:00Z`)) : '—';
}

type BadgeColor = NonNullable<BadgeProps['color']>;

export function riskColor(value?: number): BadgeColor {
  if (value === Risk.High) return 'danger';
  if (value === Risk.Moderate) return 'warning';
  return 'success';
}

export function planStatusColor(value?: number): BadgeColor {
  switch (value) {
    case PlanStatus.PendingBarriers:
      return 'warning';
    case PlanStatus.MedicallyReady:
      return 'brand';
    case PlanStatus.ReadyForDischarge:
      return 'success';
    case PlanStatus.Discharged:
      return 'subtle';
    default:
      return 'informative';
  }
}

export function taskStatusColor(value?: number): BadgeColor {
  switch (value) {
    case TaskStatus.Completed:
      return 'success';
    case TaskStatus.Blocked:
      return 'danger';
    case TaskStatus.WaitingOnExternal:
      return 'warning';
    case TaskStatus.InProgress:
      return 'brand';
    default:
      return 'informative';
  }
}
