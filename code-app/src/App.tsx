import { useMemo, useState } from 'react';
import {
  Button,
  MessageBar,
  MessageBarBody,
  Spinner,
  Tab,
  TabList,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ArrowClockwiseRegular, BotSparkleRegular, HeartPulseRegular } from '@fluentui/react-icons';
import { AgentPanel } from './components/AgentPanel';
import { BarList } from './components/BarList';
import { KpiTiles } from './components/KpiTiles';
import { PlanDrawer } from './components/PlanDrawer';
import { PlansTable } from './components/PlansTable';
import { Units } from './data/choices';
import { avoidableDaysByUnit, barriersByType, computeKpis, isActive } from './data/metrics';
import { useDischargeData } from './data/useDischargeData';
import { APP_VERSION } from './version';

const useStyles = makeStyles({
  shell: { minHeight: '100vh', backgroundColor: tokens.colorNeutralBackground2 },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalM,
    padding: `${tokens.spacingVerticalM} ${tokens.spacingHorizontalXXL}`,
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  title: { display: 'flex', flexDirection: 'column', flexGrow: 1 },
  version: { opacity: 0.8 },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: tokens.spacingHorizontalM,
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalXXL}`,
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  spacer: { flexGrow: 1 },
  muted: { color: tokens.colorNeutralForeground3 },
  content: {
    display: 'grid',
    gap: tokens.spacingVerticalL,
    padding: `${tokens.spacingVerticalL} ${tokens.spacingHorizontalXXL}`,
    maxWidth: '1500px',
  },
  panels: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: tokens.spacingHorizontalM },
  loading: { padding: tokens.spacingVerticalXXXL },
});

const ALL = 'all';

export default function App() {
  const styles = useStyles();
  const { rows, loading, error, loadedAt, refresh, completeTask } = useDischargeData();
  const [unit, setUnit] = useState<string>(ALL);
  const [selectedId, setSelectedId] = useState<string>();
  const [isAgentOpen, setIsAgentOpen] = useState(false);

  const view = useMemo(() => {
    const inUnit = rows.filter((r) => unit === ALL || String(r.plan.amc_unit) === unit);
    const active = inUnit.filter(isActive);
    return {
      active,
      kpis: computeKpis(active, inUnit),
      barriers: barriersByType(active),
      avoidable: avoidableDaysByUnit(rows.filter(isActive)),
    };
  }, [rows, unit]);

  // Look the selection up by id so the drawer shows fresh data after a write + reload.
  const selected = rows.find((r) => r.plan.amc_dischargeplanid === selectedId);

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <HeartPulseRegular fontSize={28} />
        <div className={styles.title}>
          <Text size={500} weight="semibold">Discharge Command Center</Text>
          <Text size={200}>Contoso University Health · house-wide discharge and barrier view</Text>
        </div>
        <Button appearance="primary" icon={<BotSparkleRegular />} onClick={() => setIsAgentOpen(true)}>
          Ask Discharge Navigator
        </Button>
        <Text size={200} className={styles.version}>v{APP_VERSION}</Text>
      </header>

      <div className={styles.toolbar}>
        <TabList selectedValue={unit} onTabSelect={(_, data) => setUnit(String(data.value))}>
          <Tab value={ALL}>All units</Tab>
          {Units.map((u) => (
            <Tab key={u.value} value={String(u.value)}>{u.text}</Tab>
          ))}
        </TabList>
        <div className={styles.spacer} />
        {loadedAt && <Text size={200} className={styles.muted}>Updated {loadedAt.toLocaleTimeString()}</Text>}
        <Button appearance="subtle" icon={<ArrowClockwiseRegular />} onClick={() => void refresh()} disabled={loading}>
          Refresh
        </Button>
      </div>

      <main className={styles.content}>
        {error && (
          <MessageBar intent="error">
            <MessageBarBody>Couldn't load Dataverse data: {error}</MessageBarBody>
          </MessageBar>
        )}
        {loading && rows.length === 0 ? (
          <Spinner className={styles.loading} label="Loading discharge plans..." />
        ) : (
          <>
            <KpiTiles kpis={view.kpis} />
            <div className={styles.panels}>
              <BarList title="Open barriers by type" subtitle="Barrier tasks not yet completed" bars={view.barriers} />
              <BarList
                title="Avoidable bed-days by unit"
                subtitle="Days since medically ready, patients still in house"
                bars={view.avoidable}
              />
            </div>
            <PlansTable rows={view.active} onSelect={(r) => setSelectedId(r.plan.amc_dischargeplanid)} />
          </>
        )}
      </main>

      <PlanDrawer
        row={selected}
        onClose={() => setSelectedId(undefined)}
        onCompleteTask={completeTask}
        refreshing={loading}
        onRefresh={() => void refresh()}
      />

      <AgentPanel open={isAgentOpen} onClose={() => setIsAgentOpen(false)} onReply={() => void refresh()} />
    </div>
  );
}
