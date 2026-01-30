# AgentX Migration Baseline - v0-flat-agents

**Date:** 2026-01-25  
**Status:** Pre-migration baseline (frozen state)

## Current Route Structure

### Overview
- `/` → DashboardHome

### Assistants
- `/assistants/fintech` → FintechAssistantPage
- `/assistants/code` → CodeAssistantPage
- `/assistants/general` → GeneralAssistantPage

### Agents (Flat Structure)
- `/sales` → SalesAgent (backend: `sales_agent`)
- `/support` → SupportAgent
- `/hr` → HRAgent
- `/market-research` → MarketResearchAgent (backend: `market_research_agent`, includes site scan)
- `/marketing` → MarketingAgent
- `/blog` → BlogAgent
- `/leads` → LeadSourcingAgent
- `/intelligence` → IntelligenceAgent
- `/legal` → LegalAgent
- `/finance` → FinanceAgent

### System Routes
- `/workflows` → Workflows
- `/activity` → ActivityLogs
- `/data` → Integrations
- `/settings` → Settings

## Sidebar Structure (v0-flat-agents)

Current sidebar has flat "Agents" section with 10 items:
1. Sales Agent
2. Support Agent
3. HR Agent
4. Market Research
5. Marketing
6. Blog Agent
7. Lead Sourcing
8. Intelligence
9. Legal
10. Finance

## Backend Agent Mappings

| Frontend Route | Backend Agent Type | Status |
|----------------|-------------------|--------|
| `/sales` | `sales` | ✅ Partial (has backend) |
| `/market-research` | `market_research_agent` | ✅ Full (includes site scan) |
| `/blog` | `blog` | ❌ UI only |
| `/leads` | N/A | ❌ UI only |
| `/marketing` | N/A | ❌ UI only |

## Site Scan Location

- **Current:** Part of Market Research Agent
- **Backend:** `backend/agents/market_research_agent/scan_engine.py`
- **Action:** `comprehensive_site_scan`
- **Route:** Accessible via `/market-research`

## Notes

- All routes are direct (no nesting)
- No domain-based organization
- Site scan is embedded in Market Research Agent
- Sales Agent and Market Research Agent have backend support
- Most agents are UI-only placeholders

---

**This baseline is frozen and serves as reference for migration validation.**
