import { Card, CardHeader, Text, makeStyles, tokens } from '@fluentui/react-components';
import type { Bar } from '../data/metrics';

const useStyles = makeStyles({
  card: { padding: tokens.spacingVerticalL, gap: tokens.spacingVerticalS },
  row: {
    display: 'grid',
    gridTemplateColumns: 'minmax(120px, 40%) 1fr 32px',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  track: { height: '10px', borderRadius: tokens.borderRadiusCircular, backgroundColor: tokens.colorNeutralBackground5 },
  fill: { height: '100%', borderRadius: tokens.borderRadiusCircular, backgroundColor: tokens.colorBrandBackground },
  value: { textAlign: 'right', fontVariantNumeric: 'tabular-nums' },
  empty: { color: tokens.colorNeutralForeground3 },
});

/** Horizontal bars, no chart library: label, proportional bar, value. */
export function BarList({ title, subtitle, bars }: { title: string; subtitle: string; bars: Bar[] }) {
  const styles = useStyles();
  const max = Math.max(1, ...bars.map((b) => b.value));
  return (
    <Card className={styles.card}>
      <CardHeader header={<Text weight="semibold">{title}</Text>} description={<Text size={200}>{subtitle}</Text>} />
      {bars.length === 0 && <Text className={styles.empty}>Nothing open.</Text>}
      {bars.map((bar) => (
        <div key={bar.label} className={styles.row}>
          <Text size={300} truncate wrap={false} title={bar.label}>{bar.label}</Text>
          <div className={styles.track} aria-hidden>
            <div className={styles.fill} style={{ width: `${(bar.value / max) * 100}%` }} />
          </div>
          <Text weight="semibold" className={styles.value}>{bar.value}</Text>
        </div>
      ))}
    </Card>
  );
}
