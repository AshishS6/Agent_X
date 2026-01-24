# Phase 0: Codebase Orientation Summary

**Date:** 2026-01-25  
**Purpose:** Internal summary of UI architecture before Phase 1 improvements

---

## 1. Dashboard & Main Components

### Dashboard Page
- **Location:** `src/pages/DashboardHome.tsx`
- **Structure:**
  - KPI Cards Row (4 cards: Active Agents, Tasks Completed, Time Saved, Efficiency Score)
  - Main Content Split (2/3 + 1/3 layout)
    - Left: Recent Activity / Open Tasks / Alerts tabs
    - Right: Agent Status + Integrations Status

### Key Issues Identified:
1. **Agent Status (lines 242-247):** Hardcoded array of 4 agents
   - Only shows: Sales Agent, Support Agent, Market Research, Legal Agent
   - Missing: Blog, HR, Marketing, Finance, Intelligence, Lead Sourcing, Support (duplicate?)
   - Should fetch from backend dynamically

2. **Integrations Status (lines 278-283):** Hardcoded array
   - Shows: Salesforce, Slack, Gmail, Notion
   - Should use `IntegrationService.getAll()` from `src/services/api.ts`

3. **KPI Values:** Raw numbers without formatting
   - `metrics?.timeSaved.value` (line 129) - may contain raw floats
   - `metrics?.efficiencyScore.value` (line 137) - may contain raw floats
   - `metrics?.tasksCompleted.value` (line 121) - raw number

---

## 2. Agent Detail Pages

### Shared Layout Component
- **Location:** `src/components/Layout/AgentLayout.tsx`
- **Structure:**
  - Agent Header (icon, name, status badge, enable/disable button)
  - Tabs: Overview | Conversations | Skills & Playbooks | Configuration
  - Tab content passed as props

### Agent Pages Using AgentLayout:
1. **SalesAgent** (`src/pages/SalesAgent.tsx`)
   - Overview: KPI strip (4 cards), Recent Tasks list, Task Execution Form
   - Conversations: **RAW JSON displayed** (line 198: `JSON.stringify(task.output, null, 2)`)
   - Skills: Static cards
   - Config: Static data sources

2. **BlogAgent** (`src/pages/BlogAgent.tsx`)
   - Similar structure to SalesAgent
   - Conversations: **Partially parsed** (lines 202-244)
     - `generate_outline` action: Renders structured outline
     - `generate_post_from_outline` action: Renders content preview
     - **Fallback: Still shows raw JSON** (line 242: `JSON.stringify(response, null, 2)`)

3. **MarketResearchAgent** (`src/pages/MarketResearchAgent.tsx`)
   - Large file (2213 lines)
   - Has specialized components in `src/components/market-research/`
   - Conversations: Uses structured rendering for site scans, **but fallback shows raw JSON** (line 584)

### Inconsistencies:
- **SalesAgent:** Always shows raw JSON in conversations
- **BlogAgent:** Conditional rendering (some actions parsed, others raw JSON)
- **MarketResearchAgent:** Complex parsing for site scans, raw JSON fallback
- **Other agents:** Need to check (HR, Marketing, Finance, etc. are likely UI-only)

---

## 3. Shared UI Components

### Existing Components:
- `AgentLayout.tsx` - Reusable agent page wrapper
- `StatCard` - Defined inline in DashboardHome (not exported)
- `src/components/market-research/` - Specialized components for Market Research Agent

### Missing:
- **No shared formatting utilities** (formatNumber, formatPercentage, formatDuration, formatCurrency)
- **No shared conversation card component**
- **No breadcrumb component**

---

## 4. Data Formatting Issues

### Locations with Raw Numbers:
1. **DashboardHome.tsx:**
   - Line 121: `metrics?.tasksCompleted.value` (raw number)
   - Line 129: `metrics?.timeSaved.value` (may be "0h" or raw float)
   - Line 137: `metrics?.efficiencyScore.value` (may be "0%" or raw float)

2. **SalesAgent.tsx:**
   - Line 80: Success Rate calculation: `Math.round(...)` - may produce raw percentages
   - Line 77-80: KPI cards show raw numbers

3. **BlogAgent.tsx:**
   - Line 81: Same Success Rate calculation issue
   - Line 78-81: KPI cards show raw numbers

### Expected Problems:
- Floating point leaks: `14.583333333333334`, `86.20689655172413`
- Missing units (hours, %, currency)
- Inconsistent precision

---

## 5. Agent Status Visibility

### Current State:
- **DashboardHome.tsx lines 242-247:** Hardcoded 4 agents
- **Backend:** Returns all agents via `AgentService.getAll()`
- **Sidebar:** Lists 11 agents (need to verify exact count)

### Missing:
- Dynamic agent status fetching
- Scroll/pagination for agent list
- Warning if backend returns fewer agents than sidebar

---

## 6. Integrations Display

### Current State:
- **DashboardHome.tsx lines 278-283:** Hardcoded integration list
- **Integrations.tsx:** Full page with proper `IntegrationService.getAll()` usage
- **Issue:** Dashboard shows static data, not real integration status

### Missing:
- Error reason display
- Impact statements
- Action buttons (Reconnect/Retry)
- Secondary actions (View Logs/Disable)

---

## 7. Raw JSON in Conversations

### Locations:
1. **SalesAgent.tsx line 198:**
   ```tsx
   <pre>{JSON.stringify(task.output, null, 2)}</pre>
   ```

2. **BlogAgent.tsx line 242:**
   ```tsx
   <pre>{JSON.stringify(response, null, 2)}</pre>
   ```
   (Fallback for non-outline/non-post actions)

3. **MarketResearchAgent.tsx line 584:**
   ```tsx
   <pre>{JSON.stringify(content, null, 2)}</pre>
   ```
   (Fallback for non-crawler tasks)

### Impact:
- High cognitive load
- Zero scannability
- Unprofessional appearance

---

## 8. Empty States

### Current State:
- **SalesAgent line 204:** "No conversation history yet" (text only)
- **BlogAgent line 250:** "No conversation history yet" (text only)
- **DashboardHome line 182:** "No recent activity" (text only)
- **DashboardHome line 224:** "No open tasks requiring review" (icon + text)
- **DashboardHome line 230:** "System healthy. No active alerts." (icon + text)

### Missing:
- Reassurance messages
- CTAs (Call-to-Action buttons)
- Instructional hints

---

## 9. Navigation & Orientation

### Current State:
- **No breadcrumbs** anywhere
- **Sidebar navigation** exists (`src/components/Layout/Sidebar.tsx`)
- **Header** exists (`src/components/Layout/Header.tsx`)

### Missing:
- Breadcrumb component
- Breadcrumb integration in agent pages
- Breadcrumb integration in system pages

---

## 10. Agent Page Structure Consistency

### Reference Implementation:
- **SalesAgent** follows AgentLayout pattern correctly
- **BlogAgent** follows same pattern
- **MarketResearchAgent** - needs verification (large file, may have custom structure)

### Required Standard Structure (from Phase 5):
1. Agent Header ✅ (via AgentLayout)
2. Tabs (consistent order) ✅ (via AgentLayout)
3. Overview Tab ✅ (3-4 KPI cards + Recent activity + Quick actions)
4. Conversations Tab ⚠️ (needs ConversationCard component)
5. Skills & Playbooks Tab ✅ (static cards)
6. Configuration Tab ✅ (static for now)

---

## 11. Reusable vs Agent-Specific Components

### Reusable:
- `AgentLayout` - Used by SalesAgent, BlogAgent
- `StatCard` - Inline in DashboardHome (should be extracted)

### Agent-Specific:
- `src/components/market-research/` - Specialized for Market Research Agent
- Task forms (TaskForm in SalesAgent, BlogTaskForm in BlogAgent)

### Recommendation:
- Extract `StatCard` to shared component
- Create `ConversationCard` as shared component
- Create formatting utilities in `src/utils/formatting.ts`

---

## 12. Data Flow

### API Services (`src/services/api.ts`):
- `AgentService.getAll()` - Returns all agents
- `AgentService.getMetrics(id)` - Returns agent metrics
- `MonitoringService.getMetrics()` - Returns system metrics
- `IntegrationService.getAll()` - Returns all integrations
- `TaskService.getAll(params)` - Returns tasks with pagination

### Data Structures:
- `SystemMetrics` - Dashboard KPIs
- `AgentMetrics` - Agent-specific KPIs
- `Task` - Task data with `output` field (contains JSON)
- `Integration` - Integration data with `status`, `lastSync`

---

## Next Steps (Phase 1):
1. Create `src/utils/formatting.ts` with formatting functions
2. Apply formatting to DashboardHome KPI cards
3. Apply formatting to SalesAgent KPI cards
4. Apply formatting to BlogAgent KPI cards
5. Check MarketResearchAgent for formatting needs

---

**Status:** ✅ Phase 0 Complete  
**Ready for:** Phase 1 - Data Formatting & Credibility Fixes
