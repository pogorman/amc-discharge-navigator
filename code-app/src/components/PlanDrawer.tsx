import { useState, type ReactNode } from 'react';
import {
  Badge,
  Button,
  Divider,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  MessageBar,
  MessageBarBody,
  OverlayDrawer,
  Spinner,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { CheckmarkRegular, DismissRegular } from '@fluentui/react-icons';
import {
  TaskStatus,
  destinationLabel,
  languageLabel,
  ownerRoleLabel,
  planStatusLabel,
  taskStatusLabel,
  unitLabel,
} from '../data/choices';
import { avoidableDays } from '../data/metrics';
import type { PlanRow, Task } from '../data/useDischargeData';
import { DraftViewer } from './DraftViewer';
import { formatDate, planStatusColor, taskStatusColor } from './format';

const useStyles = makeStyles({
  facts: {
    display: 'grid',
    gridTemplateColumns: 'max-content 1fr',
    columnGap: tokens.spacingHorizontalL,
    rowGap: tokens.spacingVerticalXS,
    margin: `${tokens.spacingVerticalM} 0`,
  },
  key: { color: tokens.colorNeutralForeground3 },
  section: { display: 'block', margin: `${tokens.spacingVerticalL} 0 ${tokens.spacingVerticalS}` },
  course: { whiteSpace: 'pre-wrap', color: tokens.colorNeutralForeground2 },
  task: {
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    padding: tokens.spacingVerticalS,
    paddingLeft: tokens.spacingHorizontalM,
    marginBottom: tokens.spacingVerticalS,
    display: 'grid',
    gap: tokens.spacingVerticalXXS,
  },
  barrier: { borderLeft: `4px solid ${tokens.colorPaletteRedBorder2}` },
  taskTop: { display: 'flex', gap: tokens.spacingHorizontalS, alignItems: 'center', flexWrap: 'wrap' },
  taskMeta: { color: tokens.colorNeutralForeground3 },
  grow: { flexGrow: 1 },
});

function Fact({ label, children }: { label: string; children: ReactNode }) {
  const styles = useStyles();
  return (
    <>
      <Text className={styles.key}>{label}</Text>
      <Text>{children || '—'}</Text>
    </>
  );
}

interface Props {
  row?: PlanRow;
  onClose: () => void;
  onCompleteTask: (taskId: string) => Promise<void>;
  refreshing: boolean;
  onRefresh: () => void;
}

export function PlanDrawer({ row, onClose, onCompleteTask, refreshing, onRefresh }: Props) {
  const styles = useStyles();
  const [busyTask, setBusyTask] = useState<string>();
  const [error, setError] = useState<string>();

  const complete = async (task: Task) => {
    setBusyTask(task.amc_dischargetaskid);
    setError(undefined);
    try {
      await onCompleteTask(task.amc_dischargetaskid);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyTask(undefined);
    }
  };

  const plan = row?.plan;
  const patient = row?.patient;
  // Open work first, then by due date
  const tasks = [...(row?.tasks ?? [])].sort(
    (a, b) =>
      Number(a.amc_status === TaskStatus.Completed) - Number(b.amc_status === TaskStatus.Completed) ||
      (a.amc_duedate ?? '').localeCompare(b.amc_duedate ?? ''),
  );

  return (
    <OverlayDrawer open={!!row} position="end" size="medium" onOpenChange={(_, data) => !data.open && onClose()}>
      <DrawerHeader>
        <DrawerHeaderTitle
          action={<Button appearance="subtle" aria-label="Close" icon={<DismissRegular />} onClick={onClose} />}
        >
          {patient?.amc_name ?? plan?.amc_name}
        </DrawerHeaderTitle>
        {plan && (
          <Text size={200}>
            {plan.amc_name?.split(' ')[0]} · {unitLabel(plan.amc_unit)} · Bed {plan.amc_bed}{' '}
            <Badge appearance="tint" color={planStatusColor(plan.amc_status)}>
              {planStatusLabel(plan.amc_status)}
            </Badge>
          </Text>
        )}
      </DrawerHeader>
      <DrawerBody>
        {plan && row && (
          <>
            <div className={styles.facts}>
              <Fact label="Diagnosis">{plan.amc_primarydiagnosis}</Fact>
              <Fact label="Destination">{destinationLabel(plan.amc_destination)}</Fact>
              <Fact label="Expected discharge">{formatDate(plan.amc_expecteddischarge)}</Fact>
              <Fact label="Medically ready">
                {plan.amc_medicallyreadyon ? `${formatDate(plan.amc_medicallyreadyon)} (${avoidableDays(row)} avoidable days)` : ''}
              </Fact>
              <Fact label="Attending">{plan.amc_attending}</Fact>
              <Fact label="Case manager">{plan.amc_casemanager}</Fact>
              <Fact label="Language">{languageLabel(patient?.amc_preferredlanguage)}</Fact>
              <Fact label="Payer plan">{patient?.amc_payerplan}</Fact>
              <Fact label="PCP">{patient?.amc_pcpname}</Fact>
              <Fact label="Caregiver">{patient?.amc_caregiver}</Fact>
              <Fact label="Living situation">{patient?.amc_livingsituation}</Fact>
            </div>

            <Text weight="semibold" className={styles.section}>Hospital course</Text>
            <Text className={styles.course}>{plan.amc_hospitalcourse}</Text>

            <Divider className={styles.section} />
            <DraftViewer plan={plan} refreshing={refreshing} onRefresh={onRefresh} />

            <Divider className={styles.section} />
            <Text weight="semibold" className={styles.section}>Tasks and barriers</Text>
            {error && (
              <MessageBar intent="error">
                <MessageBarBody>{error}</MessageBarBody>
              </MessageBar>
            )}
            {tasks.map((task) => {
              const open = task.amc_status !== TaskStatus.Completed;
              return (
                <div
                  key={task.amc_dischargetaskid}
                  className={`${styles.task} ${open && task.amc_isbarrier ? styles.barrier : ''}`}
                >
                  <div className={styles.taskTop}>
                    <Text weight="semibold" className={styles.grow}>{task.amc_name}</Text>
                    {task.amc_isbarrier && open && <Badge appearance="outline" color="danger">Barrier</Badge>}
                    <Badge appearance="tint" color={taskStatusColor(task.amc_status)}>
                      {taskStatusLabel(task.amc_status)}
                    </Badge>
                    {open && (
                      <Button
                        size="small"
                        icon={busyTask === task.amc_dischargetaskid ? <Spinner size="extra-tiny" /> : <CheckmarkRegular />}
                        disabled={!!busyTask}
                        onClick={() => void complete(task)}
                      >
                        Mark complete
                      </Button>
                    )}
                  </div>
                  <Text size={200} className={styles.taskMeta}>
                    {ownerRoleLabel(task.amc_ownerrole)} · {task.amc_assignedto}
                    {task.amc_externalparty ? ` · ${task.amc_externalparty}` : ''} · due {formatDate(task.amc_duedate)}
                  </Text>
                  {task.amc_notes && <Text size={300}>{task.amc_notes}</Text>}
                </div>
              );
            })}
          </>
        )}
      </DrawerBody>
    </OverlayDrawer>
  );
}
