import { dataSourcesInfo } from '../../.power/schemas/appschemas/dataSourcesInfo';
import { MicrosoftCopilotStudioService } from '../generated';

// Copilot Studio schema name of Discharge Navigator in og-svc.
export const AGENT_SCHEMA_NAME = 'amc_DischargeNavigator';

// Discharge Navigator runs on the GitHub Copilot harness, which ExecuteCopilotAsyncV2 rejects. Its
// Agentic Runtime flavor works (same pattern as the-agents repo). UNDOCUMENTED: the connector marks it
// internal, and Microsoft can change or remove it. An empty notificationUrl makes it complete inline.
//
// The generated schema types its 200 response as void, so the SDK would drop the reply. Widen it in
// place: the SDK keeps one dataSourcesInfo for the whole app, so a copy wouldn't take effect.
const agenticOperation = (dataSourcesInfo.microsoftcopilotstudio.apis as Record<string, { responseInfo?: unknown }>)
  .ExecuteCopilotAsyncV2OnAgenticRuntime;
agenticOperation.responseInfo = { '200': { type: 'object' }, '202': { type: 'object' }, default: { type: 'object' } };

// The connector's casing for the conversation id varies.
interface ExecuteResult {
  responses?: string[];
  lastResponse?: string;
  isExpectingInput?: boolean;
  conversationId?: string;
  ConversationId?: string;
  conversationID?: string;
}

export interface AgentReply {
  text: string;
  conversationId?: string;
  elapsedMs: number;
}

// Copilot Studio reports runtime failures as an ordinary reply, so treat that text as an error.
const PLATFORM_ERROR = /^\s*An error has occurred\.\s*Error code:/i;

// The SDK can return plain objects rather than Error instances; surface whatever detail they carry.
function describeError(error: unknown): string {
  if (!error) return 'The agent call failed.';
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === 'object') {
    const e = error as { message?: unknown; status?: unknown };
    if (typeof e.message === 'string' && e.message) return e.status ? `${e.status}: ${e.message}` : e.message;
    try {
      return JSON.stringify(error);
    } catch {
      /* fall through */
    }
  }
  return String(error);
}

/** Sends one turn to Discharge Navigator as the signed-in user. Pass the returned conversationId to continue. */
export async function askAgent(message: string, conversationId?: string): Promise<AgentReply> {
  const started = performance.now();
  const result = await MicrosoftCopilotStudioService.ExecuteCopilotAsyncV2OnAgenticRuntime(
    AGENT_SCHEMA_NAME,
    { message, notificationUrl: '' },
    conversationId,
  );
  const elapsedMs = Math.round(performance.now() - started);
  if (!result.success) throw new Error(describeError(result.error));

  const data = (result.data ?? {}) as ExecuteResult;
  const responses = (data.responses ?? []).filter((r) => typeof r === 'string' && r.trim());
  const text = responses.length ? responses.join('\n\n') : (data.lastResponse ?? '');
  if (PLATFORM_ERROR.test(text)) throw new Error(text.trim());
  // An empty reply that expects input is a sign-in or consent card, which this panel can't show.
  if (!text.trim() && data.isExpectingInput) {
    throw new Error('The agent is waiting for a sign-in or consent. Open Discharge Navigator once in Teams, allow the Dataverse connection, then try again.');
  }

  return {
    text: text || '(The agent returned an empty response.)',
    conversationId: data.conversationId ?? data.ConversationId ?? data.conversationID ?? conversationId,
    elapsedMs,
  };
}
