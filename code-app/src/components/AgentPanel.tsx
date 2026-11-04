import { useEffect, useRef, useState } from 'react';
import {
  Button,
  DrawerBody,
  DrawerFooter,
  DrawerHeader,
  DrawerHeaderTitle,
  MessageBar,
  MessageBarBody,
  OverlayDrawer,
  Spinner,
  Text,
  Textarea,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { ArrowResetRegular, DismissRegular, SendRegular } from '@fluentui/react-icons';
import Markdown from 'react-markdown';
import { askAgent } from '../data/agentClient';

const useStyles = makeStyles({
  body: { display: 'flex', flexDirection: 'column', gap: tokens.spacingVerticalM },
  intro: { color: tokens.colorNeutralForeground3 },
  suggestions: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: tokens.spacingVerticalS },
  user: {
    alignSelf: 'flex-end',
    maxWidth: '85%',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalM}`,
    borderRadius: tokens.borderRadiusLarge,
    backgroundColor: tokens.colorBrandBackground2,
    whiteSpace: 'pre-wrap',
  },
  // The agent answers in Markdown; keep its headings in proportion to the panel.
  agent: {
    alignSelf: 'flex-start',
    maxWidth: '95%',
    padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalM}`,
    borderRadius: tokens.borderRadiusLarge,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground2,
    fontSize: tokens.fontSizeBase300,
    lineHeight: tokens.lineHeightBase300,
    '& h1': { fontSize: tokens.fontSizeBase400, margin: `${tokens.spacingVerticalM} 0 ${tokens.spacingVerticalXS}` },
    '& h2': { fontSize: tokens.fontSizeBase400, margin: `${tokens.spacingVerticalM} 0 ${tokens.spacingVerticalXS}` },
    '& h3': { fontSize: tokens.fontSizeBase300, margin: `${tokens.spacingVerticalS} 0 ${tokens.spacingVerticalXXS}` },
    '& p': { margin: `${tokens.spacingVerticalXS} 0` },
    '& ul': { margin: `${tokens.spacingVerticalXS} 0`, paddingLeft: tokens.spacingHorizontalXL },
    '& ol': { margin: `${tokens.spacingVerticalXS} 0`, paddingLeft: tokens.spacingHorizontalXL },
    '& table': { borderCollapse: 'collapse', fontSize: tokens.fontSizeBase200 },
    '& th, & td': { border: `1px solid ${tokens.colorNeutralStroke2}`, padding: `2px ${tokens.spacingHorizontalS}` },
  },
  meta: { color: tokens.colorNeutralForeground3, alignSelf: 'flex-start' },
  footer: { display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: tokens.spacingVerticalS },
  actions: { display: 'flex', justifyContent: 'space-between' },
});

const SUGGESTIONS = [
  "What's still blocking Miguel Reyes?",
  'Which of my patients are medically ready but still here?',
  'Which barriers are due today?',
];

interface Turn {
  role: 'user' | 'agent';
  text: string;
  elapsedMs?: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
  /** Called after each reply, because the agent can save drafts to the plan. */
  onReply: () => void;
}

/** Chat with Discharge Navigator, the same Copilot Studio agent as in Teams, as the signed-in user. */
export function AgentPanel({ open, onClose, onReply }: Props) {
  const styles = useStyles();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState('');
  const [conversationId, setConversationId] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const endRef = useRef<HTMLDivElement>(null);

  // Braces matter: newer Chrome returns a value from scrollIntoView, and React would take a returned value as
  // the effect's cleanup and crash calling it ("destroy is not a function").
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, busy]);

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    setTurns((t) => [...t, { role: 'user', text: message }]);
    setDraft('');
    setError(undefined);
    setBusy(true);
    try {
      const reply = await askAgent(message, conversationId);
      setConversationId(reply.conversationId);
      setTurns((t) => [...t, { role: 'agent', text: reply.text, elapsedMs: reply.elapsedMs }]);
      onReply();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setTurns([]);
    setConversationId(undefined);
    setError(undefined);
  };

  return (
    <OverlayDrawer open={open} onOpenChange={(_, data) => !data.open && onClose()} position="end" size="medium">
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <>
              <Button appearance="subtle" icon={<ArrowResetRegular />} onClick={reset} disabled={busy || turns.length === 0}>
                New chat
              </Button>
              <Button appearance="subtle" aria-label="Close" icon={<DismissRegular />} onClick={onClose} />
            </>
          }
        >
          Discharge Navigator
        </DrawerHeaderTitle>
      </DrawerHeader>

      <DrawerBody className={styles.body}>
        {turns.length === 0 && (
          <>
            <Text className={styles.intro}>
              The same agent as in Teams and Microsoft 365 Copilot. It reads the discharge plans with your permissions.
              Anything it writes is a draft for clinician review and signature.
            </Text>
            <div className={styles.suggestions}>
              {SUGGESTIONS.map((s) => (
                <Button key={s} size="small" onClick={() => void send(s)} disabled={busy}>
                  {s}
                </Button>
              ))}
            </div>
          </>
        )}
        {turns.map((turn, i) =>
          turn.role === 'user' ? (
            <div key={i} className={styles.user}>{turn.text}</div>
          ) : (
            <div key={i} className={styles.agent}>
              <Markdown>{turn.text}</Markdown>
            </div>
          ),
        )}
        {busy && <Spinner size="tiny" labelPosition="after" label="Discharge Navigator is working..." className={styles.meta} />}
        {error && (
          <MessageBar intent="error">
            <MessageBarBody>{error}</MessageBarBody>
          </MessageBar>
        )}
        <div ref={endRef} />
      </DrawerBody>

      <DrawerFooter className={styles.footer}>
        <Textarea
          value={draft}
          onChange={(_, data) => setDraft(data.value)}
          placeholder="Ask about a patient, a barrier or a draft"
          resize="vertical"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void send(draft);
            }
          }}
        />
        <div className={styles.actions}>
          <Text size={200} className={styles.intro}>Enter to send, Shift+Enter for a new line</Text>
          <Button appearance="primary" icon={<SendRegular />} onClick={() => void send(draft)} disabled={busy || !draft.trim()}>
            Send
          </Button>
        </div>
      </DrawerFooter>
    </OverlayDrawer>
  );
}
