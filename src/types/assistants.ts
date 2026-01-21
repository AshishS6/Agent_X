/**
 * Assistant API Types
 * LOCKED CONTRACT - Do not change without frontend coordination
 */

export interface AssistantResponse {
  assistant: string;
  answer: string;        // Markdown-formatted
  citations: string[];   // Always array, never null
  metadata: {
    model: string;
    provider: string;
    rag_used: boolean;
    kb: string;
    latency_ms: number;
  };
}

export interface AssistantRequest {
  message: string;
  assistant: 'fintech' | 'code' | 'general';
  knowledge_base?: string;
}

export type AssistantName = 'fintech' | 'code' | 'general';

export interface AssistantConfig {
  name: AssistantName;
  title: string;
  description: string;
  knowledgeBase: string;
}
