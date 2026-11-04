import {
  Accordion,
  AccordionHeader,
  AccordionItem,
  AccordionPanel,
  Badge,
  Button,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ArrowClockwiseRegular } from '@fluentui/react-icons';
import Markdown from 'react-markdown';
import { SummaryStatus, summaryStatusLabel } from '../data/choices';
import type { Plan } from '../data/useDischargeData';

const useStyles = makeStyles({
  top: { display: 'flex', alignItems: 'center', gap: tokens.spacingHorizontalS },
  grow: { flexGrow: 1 },
  header: { display: 'flex', alignItems: 'center', gap: tokens.spacingHorizontalS },
  empty: { color: tokens.colorNeutralForeground3 },
  caption: { display: 'block', color: tokens.colorNeutralForeground3, marginBottom: tokens.spacingVerticalS },
  // The agent saves Markdown; keep its headings in proportion to the drawer.
  doc: {
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalM}`,
    backgroundColor: tokens.colorNeutralBackground2,
    fontSize: tokens.fontSizeBase300,
    lineHeight: tokens.lineHeightBase300,
    '& h1': { fontSize: tokens.fontSizeBase400, margin: `${tokens.spacingVerticalM} 0 ${tokens.spacingVerticalXS}` },
    '& h2': { fontSize: tokens.fontSizeBase400, margin: `${tokens.spacingVerticalM} 0 ${tokens.spacingVerticalXS}` },
    '& h3': { fontSize: tokens.fontSizeBase300, margin: `${tokens.spacingVerticalS} 0 ${tokens.spacingVerticalXXS}` },
    '& p': { margin: `${tokens.spacingVerticalXS} 0` },
    '& ul': { margin: `${tokens.spacingVerticalXS} 0`, paddingLeft: tokens.spacingHorizontalXL },
    '& ol': { margin: `${tokens.spacingVerticalXS} 0`, paddingLeft: tokens.spacingHorizontalXL },
  },
});

function Draft({ text, empty }: { text?: string; empty: string }) {
  const styles = useStyles();
  if (!text?.trim()) return <Text className={styles.empty}>{empty}</Text>;
  return (
    <>
      <Text size={200} className={styles.caption}>Saved by Discharge Navigator. Draft for clinician review and signature.</Text>
      <div className={styles.doc}>
        <Markdown>{text}</Markdown>
      </div>
    </>
  );
}

interface Props {
  plan: Plan;
  refreshing: boolean;
  onRefresh: () => void;
}

/** Shows the drafts the agent saved to the plan. Reload pulls in a draft saved from Teams while the drawer is open. */
export function DraftViewer({ plan, refreshing, onRefresh }: Props) {
  const styles = useStyles();
  const hasSummary = !!plan.amc_patientsummary?.trim();
  const hasPacket = !!plan.amc_priorauthpacket?.trim();
  const ask = 'No draft yet. Ask Discharge Navigator in Teams or Microsoft 365 Copilot to draft it, then reload.';

  return (
    <>
      <div className={styles.top}>
        <Text weight="semibold" className={styles.grow}>Agent drafts</Text>
        <Button size="small" appearance="subtle" icon={<ArrowClockwiseRegular />} disabled={refreshing} onClick={onRefresh}>
          Reload
        </Button>
      </div>
      <Accordion multiple collapsible>
        <AccordionItem value="summary">
          <AccordionHeader>
            <span className={styles.header}>
              Patient instructions
              {hasSummary && (
                <Badge appearance="tint" color={plan.amc_summarystatus === SummaryStatus.Signed ? 'success' : 'warning'}>
                  {summaryStatusLabel(plan.amc_summarystatus) || 'Draft'}
                </Badge>
              )}
            </span>
          </AccordionHeader>
          <AccordionPanel>
            <Draft text={plan.amc_patientsummary} empty={ask} />
          </AccordionPanel>
        </AccordionItem>
        <AccordionItem value="packet">
          <AccordionHeader>
            <span className={styles.header}>
              Prior auth packet
              {hasPacket && <Badge appearance="tint" color="warning">Draft</Badge>}
            </span>
          </AccordionHeader>
          <AccordionPanel>
            <Draft text={plan.amc_priorauthpacket} empty={ask} />
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </>
  );
}
