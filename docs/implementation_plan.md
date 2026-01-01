# [ARCHIVED] Cleanup Tasks and Implement Pagination

> **Note**: This document is archived. The features described here have been completed. This is kept for historical reference only.

## Goal Description
Clean up "stuck" tasks that are in "processing" state for too long and implement pagination for the Market Research Agent's history table to handle large numbers of tasks.

**Status**: ✅ Completed

## Proposed Changes

### Cleanup Script
#### [NEW] [agents/cleanup_tasks.py](file:///Users/ashish/Agent_X/agents/cleanup_tasks.py)
- Create a Python script to mark tasks as "failed" if they are in "processing" state and created more than 1 hour ago.
- Use `db_utils.py` for database connection.

### Backend
#### [MODIFY] [backend/src/models/Task.ts](file:///Users/ashish/Agent_X/backend/src/models/Task.ts)
- Update `findAll` method to return `{ tasks: Task[], total: number }`.
- Execute two queries: one for data with limit/offset, one for total count (or use window function).

#### [MODIFY] [backend/src/routes/tasks.ts](file:///Users/ashish/Agent_X/backend/src/routes/tasks.ts)
- Update `GET /` handler to return the new structure `{ tasks: ..., total: ... }` in the response data.

### Frontend
#### [MODIFY] [src/services/api.ts](file:///Users/ashish/Agent_X/src/services/api.ts)
- Update `TaskService.getAll` to return `Promise<{ tasks: Task[], total: number }>`.
- Update the mapping logic to handle the new response structure.

#### [MODIFY] [src/pages/MarketResearchAgent.tsx](file:///Users/ashish/Agent_X/src/pages/MarketResearchAgent.tsx)
- Add state for `page` (default 1) and `limit` (default 10).
- Update `fetchAgentAndTasks` to call `TaskService.getAll` with pagination params.
- Render pagination controls (Previous, Next, Page Info) below the table.
- Use `total` to calculate total pages.

#### [MODIFY] [src/pages/SalesAgent.tsx](file:///Users/ashish/Agent_X/src/pages/SalesAgent.tsx)
- Update usage of `TaskService.getAll` to access `.tasks` property from the response.

## Verification Plan

### Automated Tests
- None (Manual verification preferred for UI/DB changes).

### Manual Verification
1.  **Run Cleanup Script**:
    - Run `python3 agents/cleanup_tasks.py`.
    - Verify in DB that old "processing" tasks are now "failed".
2.  **Verify Pagination**:
    - Open Market Research Agent dashboard.
    - Check if "Research History" shows 10 items per page.
    - Click "Next" and "Previous" buttons to verify navigation.
    - Verify "Total" count is displayed correctly.
3.  **Verify Sales Agent**:
    - Open Sales Agent dashboard.
    - Verify that tasks still load correctly (regression test).
