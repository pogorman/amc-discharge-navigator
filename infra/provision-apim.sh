#!/usr/bin/env bash
# APIM (Consumption) in front of Foundry. The original tenant enforced disableLocalAuth=true
# on Cognitive Services, so Foundry API keys were unavailable. APIM's system-assigned managed
# identity authenticates to Foundry with Entra ID; the Power Platform connector authenticates
# to APIM with a subscription key (same pattern as Permitting Wingman / mcp-apim).
# Idempotent: re-running skips anything that already exists.
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash: keep /subscriptions/... scopes intact
export PYTHONIOENCODING=utf-8 # az rest on Windows chokes on BOM-prefixed responses under cp1252

set -a; source "$(dirname "$0")/../.env"; set +a   # tenant-specific values live in .env (runbook: new machine)
SUB="${AZURE_SUBSCRIPTION_ID:?set in .env}"
RG="${AZURE_RESOURCE_GROUP:?set in .env}"
LOC="${AZURE_LOCATION:?set in .env}"
APIM="${APIM_NAME:?set in .env}"
FOUNDRY="${FOUNDRY_ACCOUNT:?set in .env}"
API_ID="foundry"
SUBSCRIPTION_ID="discharge-navigator"
PUBLISHER_EMAIL="${APIM_PUBLISHER_EMAIL:?set in .env}"

az account set --subscription "$SUB"
ARM="https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.ApiManagement/service/$APIM"
V="api-version=2024-05-01"

if ! az apim show -n "$APIM" -g "$RG" >/dev/null 2>&1; then
  echo "creating APIM (Consumption)..."
  az apim create -n "$APIM" -g "$RG" -l "$LOC" --sku-name Consumption \
    --publisher-email "$PUBLISHER_EMAIL" --publisher-name "Contoso University Health (demo)" \
    --enable-managed-identity true -o none
fi

PRINCIPAL=$(az apim show -n "$APIM" -g "$RG" --query identity.principalId -o tsv)
FOUNDRY_ID=$(az cognitiveservices account show -n "$FOUNDRY" -g "$RG" --query id -o tsv)
if [ -z "$(az role assignment list --assignee "$PRINCIPAL" --scope "$FOUNDRY_ID" --role "Cognitive Services User" --query "[].id" -o tsv)" ]; then
  az role assignment create --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
    --role "Cognitive Services User" --scope "$FOUNDRY_ID" -o none
fi

# API + operation
az apim api show -g "$RG" --service-name "$APIM" --api-id "$API_ID" >/dev/null 2>&1 || \
  az apim api create -g "$RG" --service-name "$APIM" --api-id "$API_ID" --path "foundry" \
    --display-name "Foundry Deployments" --protocols https --subscription-required true \
    --service-url "https://$FOUNDRY.openai.azure.com/openai/v1" -o none

az apim api operation show -g "$RG" --service-name "$APIM" --api-id "$API_ID" --operation-id chat-completion >/dev/null 2>&1 || \
  az apim api operation create -g "$RG" --service-name "$APIM" --api-id "$API_ID" --operation-id chat-completion \
    --display-name "Chat completion" --method POST --url-template "/chat/completions" -o none

# API policy (managed identity to Foundry) + connector subscription. Python helper,
# because `az rest` crashes on Windows printing APIM's BOM-prefixed policy XML.
python "$(dirname "$0")/apim_config.py" "$SUB" "$RG" "$APIM" "$API_ID" "$SUBSCRIPTION_ID"

echo "gateway: $(az apim show -n "$APIM" -g "$RG" --query gatewayUrl -o tsv)/foundry"
echo "subscription key: az rest --method post --url \"$ARM/subscriptions/$SUBSCRIPTION_ID/listSecrets?$V\" --query primaryKey -o tsv"
