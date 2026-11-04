# Discharge Command Center — Memory Bank
(Machine-facing file for the code-apps plugin. Human docs live in ../docs/*.html.)

## Project
- Path: C:\Users\pogorman\source\repos\amc-agent-demo\code-app
- App name: Discharge Command Center
- App ID: a1951694-de5a-4196-a0b9-8145e3e4645c (demo tenant since 2026-11-01; was 3f3c4872-... in og-ai-dev)
- Environment: og-svc (<environment-id>), https://og-svc.crm.dynamics.com
- Solution: AMCDischargeNavigator (5f595ff8-09d6-f111-a05d-000d3a34d653). The app came in with the solution import.
- App URL: https://apps.powerapps.com/play/e/<environment-id>/app/a1951694-de5a-4196-a0b9-8145e3e4645c?tenantId=<tenant-id>
- CLI Binary: pa (npx --no-install pa). Installed locally via devDependency @microsoft/power-apps-cli; the template didn't include it.
- pa auth account: admin@<tenant>.onmicrosoft.com (back on the demo tenant since 2026-11-01; was admin@<previous-tenant> from 2026-10-15)

## Completed Steps
- [x] Prerequisites (Node v22.22.0)
- [x] Scaffold (npx degit templates/vite)
- [x] Init (pa app init)
- [x] Baseline deploy (in solution)
- [x] Add Dataverse: amc_dischargeplan, amc_dischargetask, amc_patient (src/generated/*)
- [x] Implement (Fluent UI v9, light theme): src/data/{choices,useDischargeData,metrics}.ts, src/components/{KpiTiles,BarList,PlansTable,PlanDrawer}.tsx, format.ts
- [x] Build clean (bundle ~620 KB / 180 KB gzip; Fluent)
- [x] Final deploy v1.0.0 (2026-10-15, approved by O'G). Redeploy: bump version, npm run build && npx --no-install pa app push --solution-id cfa98fc2-d2c8-f111-aaaf-000d3a367aeb --non-interactive
- [x] Deploy v1.1.0 (2026-10-19, O'G: "ship it"). `--solution-id` failed with a token error even after `pa auth login -e`, so I pushed with `npx --no-install pa app push --non-interactive` (it updates by appId). The app is still only in AMCDischargeNavigator.

## Features
- KPI tiles: expected discharges today, medically ready still here (+avoidable bed-days), open barriers, prior-auth median turnaround (14d), high readmission risk
- Bars: open barriers by type; avoidable bed-days by unit (house-wide)
- Active plans table sorted by avoidable days; row -> drawer with facts, hospital course, tasks
- Write: "Mark complete" on a task (status Completed + completedon now), then reload
- v1.1.0 (deployed 2026-10-19 13:48 UTC): "Agent drafts" section in the drawer (src/components/DraftViewer.tsx). It shows amc_patientsummary (with the amc_summarystatus badge) and amc_priorauthpacket, rendered as Markdown with react-markdown 10.1.0, in an Accordion, with a Reload button because the OverlayDrawer covers the toolbar Refresh. Bundle is about 222 KB gzip.
- v1.2.1 (deployed 2026-11-01 after O'G's "ship it"): fixes the v1.2.0 white screen when a reply arrived. The scroll effect was a concise arrow returning scrollIntoView's value (Chrome 156 returns an object); React called it as cleanup ("destroy is not a function"). Effects now use braces (KI-34). Verified in local play: `npm run dev`, open the printed Local Play URL in Chrome (allow local network access once).
- v1.2.0 (deployed 2026-11-01 ~20:57 UTC with `pac code push --solutionName AMCDischargeNavigator`, after O'G's "go for it"; the npm pa CLI was still signed in to the old tenant, KI-33): "Ask Discharge Navigator" button in the header opens src/components/AgentPanel.tsx, a chat drawer with the Copilot Studio agent. Connector: Microsoft Copilot Studio (`pac code add-data-source -a microsoftcopilotstudio -c shared-microsoftcopi-2f0d4f27-4622-4782-9e06-419a318ff16a`, O'G's connection in og-svc). src/data/agentClient.ts calls ExecuteCopilotAsyncV2OnAgenticRuntime (GitHub Copilot harness agents reject ExecuteCopilotAsyncV2; same pattern as the-agents repo) with schema amc_DischargeNavigator and notificationUrl "", widening the generated 200 response from void to object in place. Data refreshes after each reply (the agent can save drafts).
- Version label in header from src/version.ts (bump with package.json on each deploy)

## Preferences
- Light theme (Fluent webLightTheme) to match Teams/Power Apps on camera; overrides the plugin's dark default.
- Human-facing docs are HTML only.
