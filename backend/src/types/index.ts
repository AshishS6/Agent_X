// Agent Types
export type AgentType =
    | 'sales'
    | 'support'
    | 'hr'
    | 'market-research'
    | 'marketing'
    | 'leads'
    | 'intelligence'
    | 'legal'
    | 'finance';

export type AgentStatus = 'active' | 'paused' | 'error';

export interface Agent {
    id: string;
    type: AgentType;
    name: string;
    description: string;
    status: AgentStatus;
    config: Record<string, any>;
    createdAt: Date;
    updatedAt: Date;
}

// Task Types
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type TaskPriority = 'high' | 'medium' | 'low';

export interface Task {
    id: string;
    agentId: string;
    userId?: string;
    action: string;
    input: Record<string, any>;
    output?: Record<string, any>;
    status: TaskStatus;
    priority: TaskPriority;
    error?: string;
    startedAt?: Date;
    completedAt?: Date;
    createdAt: Date;
}

// Conversation Types
export type ConversationRole = 'system' | 'user' | 'assistant' | 'tool';

export interface ConversationMessage {
    id: string;
    agentId: string;
    taskId: string;
    role: ConversationRole;
    content: string;
    metadata?: Record<string, any>;
    createdAt: Date;
}

// Integration Types
export type IntegrationStatus = 'connected' | 'error' | 'disconnected';

export interface Integration {
    id: string;
    name: string;
    type: string;
    status: IntegrationStatus;
    config: Record<string, any>;
    lastSync?: Date;
    createdAt: Date;
}

// Metrics Types
export interface AgentMetric {
    id: string;
    agentId: string;
    metricType: string;
    value: number;
    timestamp: Date;
}

// Queue Message Types
export interface QueueMessage {
    taskId: string;
    agentType: AgentType;
    action: string;
    input: Record<string, any>;
    userId?: string;
    timestamp: string;
    priority: TaskPriority;
}

// API Response Types
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
    total?: number;
}

// WebSocket Event Types
export interface WebSocketEvent {
    type: 'task_update' | 'agent_status' | 'new_activity' | 'metric_update';
    payload: any;
    timestamp: string;
}
