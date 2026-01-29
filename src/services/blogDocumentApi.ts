import axios from 'axios';

// Types matching backend Go models
export interface BlogDocument {
    id: string;
    brand: 'OPEN' | 'Zwitch';
    topic: string;
    targetAudience: string;
    intent: string;
    createdBy?: string;
    createdAt: string;
    updatedAt: string;
}

export interface BlogOutlineVersion {
    id: string;
    documentId: string;
    version: number;
    structure: {
        title: string;
        outline: Array<{
            heading: string;
            intent: string;
            subsections?: Array<{
                heading: string;
                intent: string;
            }>;
        }>;
    };
    status: 'draft' | 'reviewed' | 'approved';
    createdAt: string;
}

export interface BlogDraftVersion {
    id: string;
    documentId: string;
    outlineVersionId?: string;
    version: number;
    content: string;
    metaDescription?: string;
    wordCount?: number;
    estimatedReadingTime?: number;
    status: 'draft' | 'reviewed' | 'approved';
    createdAt: string;
}

export interface BlogFeedback {
    id: string;
    documentId: string;
    targetType: 'outline' | 'draft';
    targetVersionId: string;
    scope: 'global' | 'section';
    targetSectionId?: string;
    comment: string;
    createdBy?: string;
    createdAt: string;
}

export interface BlogDocumentWithVersions {
    document: BlogDocument;
    outline?: BlogOutlineVersion;
    draft?: BlogDraftVersion;
    outlineFeedback?: BlogFeedback[];
    draftFeedback?: BlogFeedback[];
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
const mapDocumentFromApi = (data: any): BlogDocument => ({
    id: data.id,
    brand: data.brand,
    topic: data.topic,
    targetAudience: data.target_audience,
    intent: data.intent,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
});

const mapOutlineFromApi = (data: any): BlogOutlineVersion => ({
    id: data.id,
    documentId: data.document_id,
    version: data.version,
    structure: data.structure,
    status: data.status,
    createdAt: data.created_at,
});

const mapDraftFromApi = (data: any): BlogDraftVersion => ({
    id: data.id,
    documentId: data.document_id,
    outlineVersionId: data.outline_version_id,
    version: data.version,
    content: data.content,
    metaDescription: data.meta_description,
    wordCount: data.word_count,
    estimatedReadingTime: data.estimated_reading_time,
    status: data.status,
    createdAt: data.created_at,
});

const mapFeedbackFromApi = (data: any): BlogFeedback => ({
    id: data.id,
    documentId: data.document_id,
    targetType: data.target_type,
    targetVersionId: data.target_version_id,
    scope: data.scope,
    targetSectionId: data.target_section_id,
    comment: data.comment,
    createdBy: data.created_by,
    createdAt: data.created_at,
});

export const BlogDocumentService = {
    /**
     * Create a new blog document
     */
    create: async (data: {
        brand: 'OPEN' | 'Zwitch';
        topic: string;
        targetAudience: string;
        intent: string;
        createdBy?: string;
    }): Promise<BlogDocument> => {
        // Transform camelCase to snake_case for backend
        const requestBody = {
            brand: data.brand,
            topic: data.topic,
            target_audience: data.targetAudience,
            intent: data.intent,
            created_by: data.createdBy,
        };
        const response = await api.post<{ success: boolean; data: any }>('/blog/documents', requestBody);
        return mapDocumentFromApi(response.data.data);
    },

    /**
     * Get a blog document by ID with latest versions
     */
    getById: async (id: string): Promise<BlogDocumentWithVersions> => {
        const response = await api.get<{ success: boolean; data: any }>(`/blog/documents/${id}`);
        const data = response.data.data;
        return {
            document: mapDocumentFromApi(data.document),
            outline: data.outline ? mapOutlineFromApi(data.outline) : undefined,
            draft: data.draft ? mapDraftFromApi(data.draft) : undefined,
            outlineFeedback: data.outline_feedback?.map(mapFeedbackFromApi),
            draftFeedback: data.draft_feedback?.map(mapFeedbackFromApi),
        };
    },

    /**
     * List all blog documents
     */
    list: async (params?: { limit?: number; offset?: number }): Promise<{ documents: BlogDocument[]; total: number }> => {
        const response = await api.get<{ success: boolean; data: any[]; total: number }>('/blog/documents', { params });
        return {
            documents: response.data.data.map(mapDocumentFromApi),
            total: response.data.total,
        };
    },

    /**
     * Generate an outline for a document
     */
    generateOutline: async (documentId: string, options?: { useRAG?: boolean }): Promise<Task> => {
        const response = await api.post<{ success: boolean; data: any; message: string }>(
            `/blog/documents/${documentId}/outlines`,
            { use_rag: options?.useRAG || false }
        );
        // Return task info - the outline will be saved to DB by the agent
        return response.data.data;
    },

    /**
     * Update outline status
     */
    updateOutlineStatus: async (documentId: string, versionId: string, status: 'draft' | 'reviewed' | 'approved'): Promise<void> => {
        await api.put(`/blog/documents/${documentId}/outlines/${versionId}`, { status });
    },

    /**
     * Update outline structure
     */
    updateOutlineStructure: async (documentId: string, versionId: string, structure: any): Promise<void> => {
        await api.put(`/blog/documents/${documentId}/outlines/${versionId}/structure`, { structure });
    },

    /**
     * Add feedback to an outline
     */
    addFeedback: async (
        documentId: string,
        feedback: {
            targetType: 'outline' | 'draft';
            targetVersionId: string;
            scope: 'global' | 'section';
            targetSectionId?: string;
            comment: string;
            createdBy?: string;
        }
    ): Promise<BlogFeedback> => {
        const endpoint = feedback.targetType === 'outline'
            ? `/blog/documents/${documentId}/outlines/${feedback.targetVersionId}/feedback`
            : `/blog/documents/${documentId}/drafts/${feedback.targetVersionId}/feedback`;
        
        const response = await api.post<{ success: boolean; data: any }>(
            endpoint,
            {
                target_type: feedback.targetType,
                target_version_id: feedback.targetVersionId,
                scope: feedback.scope,
                target_section_id: feedback.targetSectionId,
                comment: feedback.comment,
                created_by: feedback.createdBy,
            }
        );
        return mapFeedbackFromApi(response.data.data);
    },

    /**
     * Add feedback to a draft
     */
    addDraftFeedback: async (
        documentId: string,
        feedback: {
            targetVersionId: string;
            scope: 'global' | 'section';
            targetSectionId?: string;
            comment: string;
            createdBy?: string;
        }
    ): Promise<BlogFeedback> => {
        const response = await api.post<{ success: boolean; data: any }>(
            `/blog/documents/${documentId}/drafts/${feedback.targetVersionId}/feedback`,
            {
                target_type: 'draft',
                target_version_id: feedback.targetVersionId,
                scope: feedback.scope,
                target_section_id: feedback.targetSectionId,
                comment: feedback.comment,
                created_by: feedback.createdBy,
            }
        );
        return mapFeedbackFromApi(response.data.data);
    },

    /**
     * Generate a draft from an approved outline
     */
    generateDraft: async (
        documentId: string,
        options?: {
            tone?: 'professional' | 'friendly' | 'explanatory';
            length?: 'short' | 'medium' | 'long';
            useRAG?: boolean;
        }
    ): Promise<Task> => {
        const response = await api.post<{ success: boolean; data: any; message: string }>(
            `/blog/documents/${documentId}/drafts`,
            {
                tone: options?.tone || 'professional',
                length: options?.length || 'medium',
                use_rag: options?.useRAG || false,
            }
        );
        // Return task info - the draft will be saved to DB by the agent
        return response.data.data;
    },
};

// Re-export Task type from api.ts
import { Task } from './api';
