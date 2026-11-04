/*!
 * Copyright (C) Microsoft Corporation. All rights reserved.
 * This file is auto-generated. Do not modify it manually.
 * Changes to this file may be overwritten.
 */

export const dataSourcesInfo = {
  "amc_dischargeplans": {
    "tableId": "",
    "version": "",
    "primaryKey": "amc_dischargeplanid",
    "dataSourceType": "Dataverse",
    "apis": {}
  },
  "amc_dischargetasks": {
    "tableId": "",
    "version": "",
    "primaryKey": "amc_dischargetaskid",
    "dataSourceType": "Dataverse",
    "apis": {}
  },
  "amc_patients": {
    "tableId": "",
    "version": "",
    "primaryKey": "amc_patientid",
    "dataSourceType": "Dataverse",
    "apis": {}
  },
  "microsoftcopilotstudio": {
    "tableId": "",
    "version": "",
    "primaryKey": "",
    "dataSourceType": "Connector",
    "apis": {
      "ExecuteCopilotAsyncV2": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/authenticated/bots/{Copilot}/proactivecopilot/executeAsyncV2",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "x-ms-conversation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "201": {
            "type": "void"
          },
          "default": {
            "type": "object"
          }
        }
      },
      "ExecuteCopilotAsync": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/authenticated/bots/{Copilot}/proactivecopilot/executeAsync",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "x-ms-conversation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "ExecuteCopilot": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/authenticated/bots/{Copilot}/proactivecopilot/execute",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "x-ms-conversation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "ListCopilots": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/copilots",
        "method": "GET",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "ExecuteDataverseCopilotToStart": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/authenticated/bots/{Copilot}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ContinueExecuteDataverseCopilot": {
        "path": "/{connectionId}/powervirtualagents/dataverse-backed/authenticated/bots/{Copilot}/conversations/{ConversationId}/continue",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ContinueExecuteDataverseCopilotOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/dataverse-backed/authenticated/bots/{Copilot}/conversations/{ConversationId}/continue",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ExecuteCopilotAsyncV2OnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/dataverse-backed/authenticated/bots/{Copilot}/proactivecopilot/executeAsyncV2",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "x-ms-conversation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-correlation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-run-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-operation-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-action-tracking-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-cf-design-mode",
            "in": "header",
            "required": false,
            "type": "boolean"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          },
          "202": {
            "type": "object"
          },
          "default": {
            "type": "object"
          }
        }
      },
      "ExecuteDataverseCopilotToStartOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/dataverse-backed/authenticated/bots/{Copilot}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "Accept",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-cci-streaming-supported",
            "in": "header",
            "required": false,
            "type": "boolean"
          },
          {
            "name": "x-ms-correlation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-run-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-operation-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-action-tracking-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-cf-design-mode",
            "in": "header",
            "required": false,
            "type": "boolean"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ExecuteInlineAgenticTurnOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/inline-agentic/bots/{BotIdentifier}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "BotIdentifier",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "Accept",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-cci-streaming-supported",
            "in": "header",
            "required": false,
            "type": "boolean"
          },
          {
            "name": "x-ms-correlation-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-run-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-operation-name",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-action-tracking-id",
            "in": "header",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-cf-design-mode",
            "in": "header",
            "required": false,
            "type": "boolean"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ExecuteFirstPartyCopilot": {
        "path": "/{connectionId}/powervirtualagents/prebuilt/authenticated/bots/{Copilot}/conversations/{ConversationId}/execute/trigger/{TriggerId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "TriggerId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ExecuteFirstPartyCopilotToStart": {
        "path": "/{connectionId}/powervirtualagents/prebuilt/authenticated/bots/{Copilot}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "ContinueExecuteFirstPartyCopilot": {
        "path": "/{connectionId}/powervirtualagents/prebuilt/authenticated/bots/{Copilot}/conversations/{ConversationId}/continue",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "InvokeConnectorCallback": {
        "path": "/{connectionId}/powervirtualagents/bots/{Copilot}/channels/{channelId}/user-triggers/users/{userId}/triggers/{triggerId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "channelId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "userId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "triggerId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "conversationId",
            "in": "query",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "InvokeTriggerOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/bots/{Copilot}/triggers/{triggerId}/invoke",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "triggerId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-cds-bot-id",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-resourcegroup-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-connection-mode",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-purpose",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-component-schema-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-component-version",
            "in": "header",
            "required": true,
            "type": "integer"
          },
          {
            "name": "x-ms-trigger-bot-version",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "inputs",
            "in": "body",
            "required": false,
            "type": "object"
          },
          {
            "name": "conversationId",
            "in": "query",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-pva-bot-id",
            "in": "header",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "InvokeTrigger": {
        "path": "/{connectionId}/powervirtualagents/bots/{Copilot}/triggers/{triggerId}/invoke",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Copilot",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "triggerId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-cds-bot-id",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-resourcegroup-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-workflow-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-connection-mode",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-purpose",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-component-schema-name",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "x-ms-trigger-component-version",
            "in": "header",
            "required": true,
            "type": "integer"
          },
          {
            "name": "x-ms-trigger-bot-version",
            "in": "header",
            "required": true,
            "type": "string"
          },
          {
            "name": "inputs",
            "in": "body",
            "required": false,
            "type": "object"
          },
          {
            "name": "conversationId",
            "in": "query",
            "required": false,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          },
          {
            "name": "x-ms-pva-bot-id",
            "in": "header",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestStartNewConversation": {
        "path": "/{connectionId}/powervirtualagents/evaluation-test/authenticated/bots/{CdsBotId}/conversations",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestExecuteTurn": {
        "path": "/{connectionId}/powervirtualagents/evaluation-test/authenticated/bots/{CdsBotId}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestContinueTurn": {
        "path": "/{connectionId}/powervirtualagents/evaluation-test/authenticated/bots/{CdsBotId}/conversations/{ConversationId}/continue",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestStartNewConversationOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/evaluation-test/authenticated/bots/{CdsBotId}/conversations",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestExecuteTurnOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/evaluation-test/authenticated/bots/{CdsBotId}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "EvaluationTestContinueTurnOnAgenticRuntime": {
        "path": "/{connectionId}/copilotstudio/agenticruntime/evaluation-test/authenticated/bots/{CdsBotId}/conversations/{ConversationId}/continue",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "DeclarativeAgentEvaluationTestStartNewConversation": {
        "path": "/{connectionId}/powervirtualagents/evaluation-test/authenticated/declarative-bots/{CdsBotId}/conversations",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "DeclarativeAgentEvaluationTestExecuteTurn": {
        "path": "/{connectionId}/powervirtualagents/evaluation-test/authenticated/declarative-bots/{CdsBotId}/conversations/{ConversationId}",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "CdsBotId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "ConversationId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "void"
          }
        }
      },
      "BindUserConnections": {
        "path": "/{connectionId}/powervirtualagents/bots/{botSchemaName}/channels/{channelId}/user-connections",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "botSchemaName",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "channelId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "stateId",
            "in": "query",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": true,
            "type": "object"
          }
        ],
        "responseInfo": {
          "204": {
            "type": "void"
          }
        }
      },
      "RunAgentMakerEvaluationTestSet": {
        "path": "/{connectionId}/copilotstudio/bots/{Agent}/api/makerevaluation/testsets/{TestSetId}/run",
        "method": "POST",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Agent",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "TestSetId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "required": false,
            "type": "object"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "202": {
            "type": "object"
          }
        }
      },
      "GetAgentMakerEvaluationTestSets": {
        "path": "/{connectionId}/copilotstudio/bots/{Agent}/api/makerevaluation/testsets",
        "method": "GET",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Agent",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "GetAgentMakerEvaluationTestSetDetails": {
        "path": "/{connectionId}/copilotstudio/bots/{Agent}/api/makerevaluation/testsets/{TestSetId}",
        "method": "GET",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Agent",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "TestSetId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "GetAgentMakerEvaluationTestRuns": {
        "path": "/{connectionId}/copilotstudio/bots/{Agent}/api/makerevaluation/testruns",
        "method": "GET",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Agent",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      },
      "GetAgentMakerEvaluationTestRunDetails": {
        "path": "/{connectionId}/copilotstudio/bots/{Agent}/api/makerevaluation/testruns/{EvaluationRunId}",
        "method": "GET",
        "parameters": [
          {
            "name": "connectionId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "Agent",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "EvaluationRunId",
            "in": "path",
            "required": true,
            "type": "string"
          },
          {
            "name": "environmentId",
            "in": "query",
            "required": false,
            "type": "string"
          }
        ],
        "responseInfo": {
          "200": {
            "type": "object"
          }
        }
      }
    }
  }
};
