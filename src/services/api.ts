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

    execute: async (id: string, action: string, input: any, priority: string = 'medium'): Promise<Task> => {
        const response = await api.post<{ data: any }>(`/agents/${id}/execute`, {
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
            recentActivity: (data.recentActivity || []).map(mapTaskFromApi)
        };
    },

    getActivity: async (limit: number = 20): Promise<Task[]> => {
        const response = await api.get<{ data: any[] }>('/monitoring/activity', {
            params: { limit },
        });
        return response.data.data.map(mapTaskFromApi);
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
        return response.data.data.map(mapIntegrationFromApi);
    },

    connect: async (data: Partial<Integration>): Promise<Integration> => {
        const response = await api.post<{ data: any }>('/integrations', data);
        return mapIntegrationFromApi(response.data.data);
    },

    disconnect: async (id: string): Promise<void> => {
        await api.delete(`/integrations/${id}`);
    },

    update: async (id: string, data: Partial<Integration>): Promise<Integration> => {
        const response = await api.put<{ data: any }>(`/integrations/${id}`, data);
        return mapIntegrationFromApi(response.data.data);
    }
};

export default api;
