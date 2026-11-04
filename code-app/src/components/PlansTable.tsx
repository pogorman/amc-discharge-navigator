import {
  Badge,
  Card,
  Table,
  TableBody,
  TableCell,
  TableCellLayout,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { destinationLabel, planStatusLabel, riskLabel, unitLabel } from '../data/choices';
import { avoidableDays, isOpenBarrier } from '../data/metrics';
import type { PlanRow } from '../data/useDischargeData';
import { formatDate, planStatusColor, riskColor } from './format';

const useStyles = makeStyles({
  card: { padding: 0, overflowX: 'auto' },
  header: { padding: `${tokens.spacingVerticalM} ${tokens.spacingHorizontalL} 0` },
  row: { cursor: 'pointer' },
  num: { textAlign: 'right', fontVariantNumeric: 'tabular-nums' },
  hot: { color: tokens.colorPaletteRedForeground1, fontWeight: tokens.fontWeightSemibold },
  muted: { color: tokens.colorNeutralForeground3 },
});

export function PlansTable({ rows, onSelect }: { rows: PlanRow[]; onSelect: (row: PlanRow) => void }) {
  const styles = useStyles();
  const sorted = [...rows].sort(
    (a, b) =>
      avoidableDays(b) - avoidableDays(a) ||
      b.tasks.filter(isOpenBarrier).length - a.tasks.filter(isOpenBarrier).length,
  );

  return (
    <Card className={styles.card}>
      <div className={styles.header}>
        <Text weight="semibold">Active discharge plans</Text>{' '}
        <Text size={200} className={styles.muted}>sorted by avoidable days, select a row for detail</Text>
      </div>
      <Table aria-label="Active discharge plans" size="small">
        <TableHeader>
          <TableRow>
            <TableHeaderCell>Patient</TableHeaderCell>
            <TableHeaderCell>Unit / bed</TableHeaderCell>
            <TableHeaderCell>Plan status</TableHeaderCell>
            <TableHeaderCell>Destination</TableHeaderCell>
            <TableHeaderCell>Expected</TableHeaderCell>
            <TableHeaderCell className={styles.num}>Avoidable days</TableHeaderCell>
            <TableHeaderCell className={styles.num}>Open barriers</TableHeaderCell>
            <TableHeaderCell>Readmit risk</TableHeaderCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((row) => {
            const days = avoidableDays(row);
            const barriers = row.tasks.filter(isOpenBarrier).length;
            return (
              <TableRow
                key={row.plan.amc_dischargeplanid}
                className={styles.row}
                onClick={() => onSelect(row)}
                onKeyDown={(e) => e.key === 'Enter' && onSelect(row)}
                tabIndex={0}
              >
                <TableCell>
                  <TableCellLayout description={row.plan.amc_name?.split(' ')[0]}>
                    {row.patient?.amc_name ?? row.plan.amc_name}
                  </TableCellLayout>
                </TableCell>
                <TableCell>
                  {unitLabel(row.plan.amc_unit)} <span className={styles.muted}>· {row.plan.amc_bed}</span>
                </TableCell>
                <TableCell>
                  <Badge appearance="tint" color={planStatusColor(row.plan.amc_status)}>
                    {planStatusLabel(row.plan.amc_status)}
                  </Badge>
                </TableCell>
                <TableCell>{destinationLabel(row.plan.amc_destination)}</TableCell>
                <TableCell>{formatDate(row.plan.amc_expecteddischarge)}</TableCell>
                <TableCell className={`${styles.num} ${days > 0 ? styles.hot : ''}`}>{days || '—'}</TableCell>
                <TableCell className={`${styles.num} ${barriers > 0 ? styles.hot : ''}`}>{barriers || '—'}</TableCell>
                <TableCell>
                  <Badge appearance="filled" color={riskColor(row.plan.amc_readmissionrisk)}>
                    {riskLabel(row.plan.amc_readmissionrisk)} · {row.plan.amc_lacescore ?? '—'}
                  </Badge>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Card>
  );
}
