#!/usr/bin/env bash
# Provisions the Azure commercial side of the AMC Discharge Navigator demo:
# one resource group, one Foundry (AIServices) resource with a project,
# and two model deployments from different model families.
# Idempotent: re-running skips anything that already exists.
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash: keep /subscriptions/... scopes intact

set -a; source "$(dirname "$0")/../.env"; set +a   # tenant-specific values live in .env (runbook: new machine)
SUB="${AZURE_SUBSCRIPTION_ID:?set in .env}"
RG="${AZURE_RESOURCE_GROUP:?set in .env}"
LOC="${AZURE_LOCATION:?set in .env}"
ACCOUNT="${FOUNDRY_ACCOUNT:?set in .env}"     # Contoso University Health
PROJECT="amc-discharge-navigator"

az account set --subscription "$SUB"

az group show -n "$RG" >/dev/null 2>&1 || \
  az group create -n "$RG" -l "$LOC" --tags demo=amc-agent-demo owner=pogorman -o none

if ! az cognitiveservices account show -n "$ACCOUNT" -g "$RG" >/dev/null 2>&1; then
  az cognitiveservices account create -n "$ACCOUNT" -g "$RG" -l "$LOC" \
    --kind AIServices --sku S0 --custom-domain "$ACCOUNT" \
    --allow-project-management true --yes -o none
fi

az cognitiveservices account project show -n "$ACCOUNT" -g "$RG" --project-name "$PROJECT" >/dev/null 2>&1 || \
  az cognitiveservices account project create -n "$ACCOUNT" -g "$RG" --project-name "$PROJECT" -l "$LOC" -o none

# The signed-in maker can call the deployments directly (scripts/test_foundry.py without --apim).
ME=$(az ad signed-in-user show --query id -o tsv)
ACCOUNT_ID=$(az cognitiveservices account show -n "$ACCOUNT" -g "$RG" --query id -o tsv)
if [ -z "$(az role assignment list --assignee "$ME" --scope "$ACCOUNT_ID" --role "Cognitive Services User" --query "[].id" -o tsv)" ]; then
  az role assignment create --assignee-object-id "$ME" --assignee-principal-type User \
    --role "Cognitive Services User" --scope "$ACCOUNT_ID" -o none
fi

deploy() { # name model version format capacity
  az cognitiveservices account deployment show -n "$ACCOUNT" -g "$RG" --deployment-name "$1" >/dev/null 2>&1 && return 0
  az cognitiveservices account deployment create -n "$ACCOUNT" -g "$RG" \
    --deployment-name "$1" --model-name "$2" --model-version "$3" --model-format "$4" \
    --sku-name GlobalStandard --sku-capacity "$5" -o none
}

# Patient-facing plain-language summaries (multilingual) - Mistral
deploy "patient-summary" "Mistral-Large-3" "1" "Mistral AI" 50
# Prior-auth clinical justification (reasoning) - OpenAI
deploy "prior-auth" "gpt-5.5" "2026-04-24" "OpenAI" 50

az cognitiveservices account deployment list -n "$ACCOUNT" -g "$RG" \
  --query "[].{deployment:name, model:properties.model.name, version:properties.model.version, state:properties.provisioningState}" -o table
az cognitiveservices account show -n "$ACCOUNT" -g "$RG" --query "properties.endpoint" -o tsv
