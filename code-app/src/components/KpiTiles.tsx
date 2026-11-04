import { Card, Text, makeStyles, tokens } from '@fluentui/react-components';
import type { Kpis } from '../data/metrics';

const useStyles = makeStyles({
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: tokens.spacingHorizontalM,
  },
  tile: { padding: tokens.spacingVerticalL, gap: tokens.spacingVerticalXXS },
  value: { fontSize: tokens.fontSizeHero800, lineHeight: tokens.lineHeightHero800, fontWeight: tokens.fontWeightSemibold },
  caption: { color: tokens.colorNeutralForeground2 },
  detail: { color: tokens.colorNeutralForeground3 },
  alert: { borderTop: `3px solid ${tokens.colorPaletteRedBorder2}` },
  calm: { borderTop: `3px solid ${tokens.colorBrandStroke1}` },
});

interface TileProps {
  value: string | number;
  caption: string;
  detail?: string;
  alert?: boolean;
}

function Tile({ value, caption, detail, alert }: TileProps) {
  const styles = useStyles();
  return (
    <Card className={`${styles.tile} ${alert ? styles.alert : styles.calm}`}>
      <Text className={styles.value}>{value}</Text>
      <Text weight="semibold" className={styles.caption}>{caption}</Text>
      {detail && <Text size={200} className={styles.detail}>{detail}</Text>}
    </Card>
  );
}

export function KpiTiles({ kpis }: { kpis: Kpis }) {
  const styles = useStyles();
  const pa = kpis.priorAuthMedianHours;
  return (
    <div className={styles.grid}>
      <Tile value={kpis.dischargesToday} caption="Expected discharges today" />
      <Tile
        value={kpis.medicallyReadyStillHere}
        caption="Medically ready, still here"
        detail={`${kpis.avoidableDays} avoidable bed-days`}
        alert={kpis.avoidableDays > 0}
      />
      <Tile value={kpis.openBarriers} caption="Open discharge barriers" alert={kpis.openBarriers > 0} />
      <Tile
        value={pa === undefined ? '—' : `${Math.round(pa)} h`}
        caption="Prior-auth turnaround (median)"
        detail={`${kpis.priorAuthSample} approvals, last 14 days`}
      />
      <Tile value={kpis.highRisk} caption="High readmission risk (LACE ≥ 10)" />
    </div>
  );
}
