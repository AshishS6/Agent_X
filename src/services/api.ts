import axios from 'axios';

// Types matching backend
export interface Agent {
    id: string;
    type: string;
    name: string;
    description: string;
    status: 'active' | 'paused' | 'error';
    config: Record<string, any>;
    createdAt: string;
    updatedAt: string;
}

export interface Task {
    id: string;
    agentId: string;
    userId?: string;
    action: string;
    input: Record<string, any>;
    output?: Record<string, any>;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    priority: 'high' | 'medium' | 'low';
    error?: string;
    startedAt?: string;
    completedAt?: string;
    createdAt: string;
}

export interface AgentMetrics {
    statusCounts: Record<string, number>;
    recentTasks: Task[];
    totalTasks: number;
}

export interface SystemMetrics {
    activeAgents: {
        value: string;
        count: number;
        total: number;
    };
    tasksCompleted: {
        value: number;
        trend: number;
    };
    timeSaved: {
        value: string;
        hours: number;
    };
    efficiencyScore: {
        value: string;
        score: number;
    };
    taskBreakdown: Record<string, number>;
    recentActivity: Task[];
}

// API Client
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Helper to map API response (snake_case) to Frontend types (camelCase)
const mapAgentFromApi = (data: any): Agent => ({
    ...data,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
});

const mapTaskFromApi = (data: any): Task => {
    // console.log('Raw task data:', data); 
    return {
        ...data,
        agentId: data.agent_id,
        userId: data.user_id,
        startedAt: data.started_at,
        completedAt: data.completed_at,
        createdAt: data.created_at,
    };
};

export const AgentService = {
    getAll: async (): Promise<Agent[]> => {
        const response = await api.get<{ data: any[] }>('/agents');
        return response.data.data.map(mapAgentFromApi);
    },

    getById: async (id: string): Promise<Agent> => {
        const response = await api.get<{ data: any }>(`/agents/${id}`);
        return mapAgentFromApi(response.data.data);
    },

    /**
     * Execute an agent task using agent type (e.g., "market_research", "sales")
     */
    execute: async (agentType: string, action: string, input: any, priority: string = 'medium'): Promise<Task> => {
        const response = await api.post<{ data: any }>(`/agents/${agentType}/execute`, {
            action,
            input,
            priority,
        });
        return mapTaskFromApi(response.data.data);
    },

    getMetrics: async (id: string): Promise<AgentMetrics> => {
        const response = await api.get<{ data: any }>(`/agents/${id}/metrics`);
        const data = response.data.data;
        return {
            ...data,
            recentTasks: (data.recentTasks || []).map(mapTaskFromApi)
        };
    },
};

export const TaskService = {
    getAll: async (params?: { agentId?: string; status?: string; limit?: number; offset?: number }): Promise<{ tasks: Task[], total: number }> => {
        const response = await api.get<{ data: any[], total: number }>('/tasks', { params });
        return {
            tasks: response.data.data.map(mapTaskFromApi),
            total: response.data.total
        };
    },

    getById: async (id: string): Promise<Task> => {
        const response = await api.get<{ data: any }>(`/tasks/${id}`);
        return mapTaskFromApi(response.data.data);
    },

    downloadReport: async (taskId: string, format: 'pdf' | 'json' | 'markdown'): Promise<void> => {
        const response = await api.get(`/tasks/${taskId}/report`, {
            params: { format },
            responseType: 'blob'
        });

        // Create blob URL and trigger download
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;

        // Extract filename from Content-Disposition header if available
        const contentDisposition = response.headers['content-disposition'];
        let filename = `report_${taskId}.${format === 'markdown' ? 'md' : format}`;
        if (contentDisposition) {
            // Try quoted filename first: filename="file.md"
            let filenameMatch = contentDisposition.match(/filename="([^"]+)"/i);
            if (!filenameMatch) {
                // Try unquoted: filename=file.md
                filenameMatch = contentDisposition.match(/filename=([^;]+)/i);
            }
            if (filenameMatch) {
                filename = filenameMatch[1].trim();
                // Ensure markdown files have .md extension
                if (format === 'markdown' && !filename.endsWith('.md')) {
                    filename = filename.replace(/\.[^.]+$/, '') + '.md';
                }
            }
        }

        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    },
};

export const MonitoringService = {
    getHealth: async () => {
        const response = await api.get('/monitoring/health');
        return response.data;
    },

    getMetrics: async (): Promise<SystemMetrics> => {
        const response = await api.get<{ data: any }>('/monitoring/metrics');
        const data = response.data.data;
        return {
            ...data,
            recentActivity: (data.recentActivity?.tasks || []).map(mapTaskFromApi)
        };
    },

    getActivity: async (limit: number = 20, offset: number = 0): Promise<{ tasks: Task[], total: number }> => {
        const response = await api.get<{ data: any[], total: number }>('/monitoring/activity', {
            params: { limit, offset },
        });
        return {
            tasks: response.data.data.map(mapTaskFromApi),
            total: response.data.total
        };
    },
};

export interface Integration {
    id: string;
    name: string;
    type: string;
    status: 'connected' | 'error' | 'disconnected';
    config: Record<string, any>;
    lastSync?: string;
    createdAt: string;
}

// ... existing interfaces ...

// Helper to map API response (snake_case) to Frontend types (camelCase)
const mapIntegrationFromApi = (data: any): Integration => ({
    ...data,
    lastSync: data.last_sync,
    createdAt: data.created_at,
});

// ... existing helpers ...

export const IntegrationService = {
    getAll: async (): Promise<Integration[]> => {
        const response = await api.get<{ data: any[] }>('/integrations');
        return (response.data.data || []).map(mapIntegrationFromApi);
    },

    connect: async (data: Partial<Integration>): Promise<Integration> => {
        const response = await api.post<{ data: any }>('/integrations', data);
        return mapIntegrationFromApi(response.data.data);
    },

    disconnect: async (id: string): Promise<void> => {
        await api.delete(`/integrations/${id}`);
    },

    update: async (id: string, data: Partial<Integration>): Promise<Integration> => {
        // Accept both camelCase and snake_case on backend; keep frontend camelCase
        const response = await api.put<{ data: any }>(`/integrations/${id}`, data);
        return mapIntegrationFromApi(response.data.data);
    }
};

export default api;

// -------------------------
// Workflows (MVP)
// -------------------------

export interface Workflow {
    id: string;
    name: string;
    description?: string | null;
    status: 'active' | 'paused' | 'draft';
    triggerType: string;
    triggerConfig: Record<string, any>;
    steps: any[];
    ownerTeam?: string | null;
    createdBy?: string | null;
    createdAt: string;
    updatedAt: string;
}

export interface WorkflowRun {
    id: string;
    workflowId: string;
    status: 'running' | 'completed' | 'failed';
    caseId?: string | null;
    providerEventId?: string | null;
    idempotencyKey?: string | null;
    triggerPayload: Record<string, any>;
    startedAt: string;
    completedAt?: string | null;
    error?: string | null;
}

export interface WorkflowCase {
    id: string;
    workflowId: string;
    provider: string;
    externalRefId: string;
    status?: string | null;
    latestState: Record<string, any>;
    createdAt: string;
    updatedAt: string;
}

export interface WorkflowStepRun {
    id: string;
    workflowRunId: string;
    stepIndex: number;
    stepType: string;
    status: 'running' | 'completed' | 'failed' | 'skipped';
    input: Record<string, any>;
    output: Record<string, any>;
    taskId?: string | null;
    error?: string | null;
    startedAt: string;
    completedAt?: string | null;
}

const mapWorkflowFromApi = (data: any): Workflow => ({
    id: data.id,
    name: data.name,
    description: data.description ?? null,
    status: data.status,
    triggerType: data.trigger_type,
    triggerConfig: data.trigger_config || {},
    steps: data.steps || [],
    ownerTeam: data.owner_team ?? null,
    createdBy: data.created_by ?? null,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
});

const mapWorkflowRunFromApi = (data: any): WorkflowRun => ({
    id: data.id,
    workflowId: data.workflow_id,
    status: data.status,
    caseId: data.case_id ?? null,
    providerEventId: data.provider_event_id ?? null,
    idempotencyKey: data.idempotency_key ?? null,
    triggerPayload: data.trigger_payload || {},
    startedAt: data.started_at,
    completedAt: data.completed_at ?? null,
    error: data.error ?? null,
});

const mapWorkflowCaseFromApi = (data: any): WorkflowCase => ({
    id: data.id,
    workflowId: data.workflow_id,
    provider: data.provider,
    externalRefId: data.external_ref_id,
    status: data.status ?? null,
    latestState: data.latest_state || {},
    createdAt: data.created_at,
    updatedAt: data.updated_at,
});

const mapWorkflowStepRunFromApi = (data: any): WorkflowStepRun => ({
    id: data.id,
    workflowRunId: data.workflow_run_id,
    stepIndex: data.step_index,
    stepType: data.step_type,
    status: data.status,
    input: data.input || {},
    output: data.output || {},
    taskId: data.task_id ?? null,
    error: data.error ?? null,
    startedAt: data.started_at,
    completedAt: data.completed_at ?? null,
});

export const WorkflowService = {
    getAll: async (): Promise<Workflow[]> => {
        const response = await api.get<{ data: any[] }>('/workflows');
        return (response.data.data || []).map(mapWorkflowFromApi);
    },
    create: async (data: Partial<Workflow> & { name: string; triggerType: string; steps: any[] }): Promise<Workflow> => {
        const response = await api.post<{ data: any }>('/workflows', {
            name: data.name,
            description: data.description,
            status: data.status || 'draft',
            trigger_type: data.triggerType,
            trigger_config: data.triggerConfig || {},
            steps: data.steps || [],
            owner_team: data.ownerTeam,
            created_by: data.createdBy,
        });
        return mapWorkflowFromApi(response.data.data);
    },
    update: async (id: string, updates: any): Promise<Workflow> => {
        const response = await api.put<{ data: any }>(`/workflows/${id}`, updates);
        return mapWorkflowFromApi(response.data.data);
    },
    pause: async (id: string): Promise<Workflow> => {
        const response = await api.post<{ data: any }>(`/workflows/${id}/pause`);
        return mapWorkflowFromApi(response.data.data);
    },
    activate: async (id: string): Promise<Workflow> => {
        const response = await api.post<{ data: any }>(`/workflows/${id}/activate`);
        return mapWorkflowFromApi(response.data.data);
    },
    getRuns: async (workflowId: string, params?: { limit?: number; offset?: number }) => {
        const response = await api.get<{ data: any[]; total: number }>(`/workflows/${workflowId}/runs`, { params });
        return { runs: (response.data.data || []).map(mapWorkflowRunFromApi), total: response.data.total || 0 };
    },
    getCases: async (workflowId: string, params?: { limit?: number; offset?: number }) => {
        const response = await api.get<{ data: any[]; total: number }>(`/workflows/${workflowId}/cases`, { params });
        return { cases: (response.data.data || []).map(mapWorkflowCaseFromApi), total: response.data.total || 0 };
    },
    getRunsForCase: async (caseId: string, params?: { limit?: number; offset?: number }) => {
        const response = await api.get<{ data: any[]; total: number }>(`/workflow-cases/${caseId}/runs`, { params });
        return { runs: (response.data.data || []).map(mapWorkflowRunFromApi), total: response.data.total || 0 };
    },
    getAllRuns: async (params?: { limit?: number; offset?: number }) => {
        const response = await api.get<{ data: any[]; total: number }>('/workflow-runs', { params });
        return { runs: (response.data.data || []).map(mapWorkflowRunFromApi), total: response.data.total || 0 };
    },
    getRunById: async (runId: string): Promise<{ run: WorkflowRun; steps: WorkflowStepRun[] }> => {
        const response = await api.get<{ data: { run: any; steps: any[] } }>(`/workflow-runs/${runId}`);
        return {
            run: mapWorkflowRunFromApi(response.data.data.run),
            steps: (response.data.data.steps || []).map(mapWorkflowStepRunFromApi),
        };
    },
};
