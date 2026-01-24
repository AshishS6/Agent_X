import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Code, Calendar, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

interface ConversationCardProps {
    action: string;
    timestamp: string;
    status: 'completed' | 'failed' | 'processing' | 'pending';
    output: any;
    taskId: string;
    onActionClick?: () => void;
}

/**
 * ConversationCard component for displaying human-readable conversation data
 * with collapsible raw JSON access
 */
export const ConversationCard: React.FC<ConversationCardProps> = ({
    action,
    timestamp,
    status,
    output,
    taskId,
    onActionClick,
}) => {
    const [showRawData, setShowRawData] = useState(false);

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return isNaN(date.getTime()) ? 'Just now' : date.toLocaleString();
        } catch {
            return 'Just now';
        }
    };

    const getStatusIcon = () => {
        switch (status) {
            case 'completed':
                return <CheckCircle size={14} className="text-green-400" />;
            case 'failed':
                return <XCircle size={14} className="text-red-400" />;
            case 'processing':
                return <Clock size={14} className="text-blue-400 animate-pulse" />;
            default:
                return <AlertTriangle size={14} className="text-yellow-400" />;
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case 'completed':
                return 'bg-green-500/10 text-green-400 border-green-500/20';
            case 'failed':
                return 'bg-red-500/10 text-red-400 border-red-500/20';
            case 'processing':
                return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            default:
                return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
        }
    };

    // Parse output based on action type
    const renderHumanReadableContent = () => {
        if (!output) {
            return (
                <div className="text-gray-400 text-sm italic">
                    No output available
                </div>
            );
        }

        // Handle Sales Agent actions
        if (action === 'generate_email' && output.email) {
            return (
                <div className="space-y-3">
                    <div>
                        <p className="text-xs text-gray-500 mb-1">To:</p>
                        <p className="text-sm text-white font-medium">{output.email.recipient || 'Recipient'}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Subject:</p>
                        <p className="text-sm text-white">{output.email.subject || 'No subject'}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Body:</p>
                        <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700">
                            <p className="text-sm text-gray-300 whitespace-pre-wrap">{output.email.body || 'No content'}</p>
                        </div>
                    </div>
                    {output.metadata && (
                        <div className="text-xs text-gray-500">
                            Tone: {output.metadata.tone || 'professional'}
                        </div>
                    )}
                </div>
            );
        }

        if (action === 'qualify_lead' && output.qualification) {
            return (
                <div className="space-y-3">
                    <div className="flex items-center gap-3">
                        <div className={clsx(
                            "px-3 py-1.5 rounded-lg font-semibold text-lg",
                            output.qualification.score >= 70
                                ? "bg-green-500/20 text-green-400"
                                : output.qualification.score >= 40
                                ? "bg-yellow-500/20 text-yellow-400"
                                : "bg-red-500/20 text-red-400"
                        )}>
                            Score: {output.qualification.score || 'N/A'}
                        </div>
                        <div className="flex-1">
                            <p className="text-xs text-gray-500 mb-1">Recommendation:</p>
                            <p className="text-sm text-white font-medium capitalize">
                                {output.qualification.recommendation || 'Follow-up'}
                            </p>
                        </div>
                    </div>
                    {output.qualification.reasoning && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1">Reasoning:</p>
                            <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700">
                                <p className="text-sm text-gray-300 whitespace-pre-wrap">
                                    {output.qualification.reasoning}
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        // Handle Blog Agent actions
        if (action === 'generate_outline' && output.outline) {
            return (
                <div className="space-y-3">
                    {output.title && (
                        <h4 className="text-white font-semibold text-base mb-2">{output.title}</h4>
                    )}
                    <div className="space-y-2">
                        {Array.isArray(output.outline) && output.outline.map((section: any, idx: number) => (
                            <div key={idx} className="pl-4 border-l-2 border-gray-700">
                                <p className="font-medium text-white text-sm">## {section.heading || `Section ${idx + 1}`}</p>
                                {section.intent && (
                                    <p className="text-gray-400 text-xs mt-1">{section.intent}</p>
                                )}
                                {section.subsections && section.subsections.length > 0 && (
                                    <div className="mt-2 ml-4 space-y-1">
                                        {section.subsections.map((sub: any, subIdx: number) => (
                                            <div key={subIdx}>
                                                <p className="text-sm text-gray-300">### {sub.heading || `Subsection ${subIdx + 1}`}</p>
                                                {sub.intent && (
                                                    <p className="text-gray-400 text-xs">{sub.intent}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (action === 'generate_post_from_outline' && output.content) {
            return (
                <div className="space-y-3">
                    {output.title && (
                        <h4 className="text-white font-semibold text-base mb-2">{output.title}</h4>
                    )}
                    <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700 max-h-96 overflow-y-auto">
                        <p className="text-sm text-gray-300 whitespace-pre-wrap">
                            {output.content.substring(0, 500)}
                            {output.content.length > 500 && '...'}
                        </p>
                    </div>
                    {(output.word_count || output.estimated_reading_time) && (
                        <div className="flex gap-4 text-xs text-gray-500">
                            {output.word_count && (
                                <span>Word Count: {output.word_count}</span>
                            )}
                            {output.estimated_reading_time && (
                                <span>Reading Time: {output.estimated_reading_time} min</span>
                            )}
                        </div>
                    )}
                </div>
            );
        }

        // Generic fallback - try to extract meaningful fields
        if (typeof output === 'object') {
            const keys = Object.keys(output);
            if (keys.length > 0) {
                return (
                    <div className="space-y-2">
                        {keys.slice(0, 5).map((key) => {
                            const value = output[key];
                            if (value === null || value === undefined) return null;
                            
                            return (
                                <div key={key}>
                                    <p className="text-xs text-gray-500 mb-1 capitalize">{key.replace(/_/g, ' ')}:</p>
                                    <div className="bg-gray-800/50 p-2 rounded border border-gray-700">
                                        <p className="text-sm text-gray-300">
                                            {typeof value === 'string' 
                                                ? value.substring(0, 200) + (value.length > 200 ? '...' : '')
                                                : typeof value === 'object'
                                                ? JSON.stringify(value, null, 2).substring(0, 200) + '...'
                                                : String(value)
                                            }
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                        {keys.length > 5 && (
                            <p className="text-xs text-gray-500 italic">
                                +{keys.length - 5} more fields (view raw data to see all)
                            </p>
                        )}
                    </div>
                );
            }
        }

        // Ultimate fallback
        return (
            <div className="text-gray-400 text-sm italic">
                Output format not recognized. Use "View Raw Data" to see the full response.
            </div>
        );
    };

    return (
        <div className="mb-4 p-4 border border-gray-800 rounded-lg hover:bg-gray-800/50 transition-colors group w-full">
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="bg-blue-500/10 text-blue-400 text-xs font-medium px-2 py-1 rounded-full capitalize">
                        {action.replace(/_/g, ' ')}
                    </span>
                    <span className="text-gray-500 text-xs">ID: #{taskId.slice(0, 8)}</span>
                    <span className={clsx(
                        "text-xs px-2 py-1 rounded-full border flex items-center gap-1",
                        getStatusColor()
                    )}>
                        {getStatusIcon()}
                        <span className="capitalize">{status}</span>
                    </span>
                </div>
                <div className="flex items-center gap-2 text-gray-500 text-xs">
                    <Calendar size={12} />
                    <span>{formatDate(timestamp)}</span>
                </div>
            </div>

            {/* Human-readable content */}
            <div className="text-gray-300 text-sm mt-2 w-full min-w-0 mb-3">
                {renderHumanReadableContent()}
            </div>

            {/* Raw Data Toggle */}
            <div className="border-t border-gray-800 pt-3 mt-3">
                <button
                    onClick={() => setShowRawData(!showRawData)}
                    className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-300 transition-colors w-full"
                >
                    <Code size={14} />
                    <span>{showRawData ? 'Hide' : 'View'} Raw Data</span>
                    {showRawData ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showRawData && (
                    <div className="mt-3 bg-gray-950 p-3 rounded-lg border border-gray-800 overflow-x-auto">
                        <pre className="text-xs text-gray-400 font-mono whitespace-pre-wrap break-words">
                            {JSON.stringify(output, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
};
