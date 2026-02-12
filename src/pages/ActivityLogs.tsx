import { useState, useEffect, useMemo, useRef } from 'react';
import {
    Search,
    Filter,
    Calendar,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Briefcase,
    LifeBuoy,
    Megaphone,
    Scale,
    Database,
    Info,
    Loader2,
    Clock,
    Activity,
    GitBranch,
    ChevronDown,
    ChevronUp,
    Zap
} from 'lucide-react';
import clsx from 'clsx';
import { MonitoringService, Task, Workflow, WorkflowRun, WorkflowService } from '../services/api';
import { EmptyState } from '../components/EmptyState';

// Helper to map agent type to icon
const getAgentIcon = (type: string) => {
    switch (type) {
        case 'sales': return Briefcase;
        case 'support': return LifeBuoy;
        case 'marketing': return Megaphone;
        case 'legal': return Scale;
        default: return Database;
    }
};

interface ActivityLog {
    entryId: string;
    id: string;
    type: 'task' | 'system' | 'workflow';
    status: 'success' | 'warning' | 'error' | 'pending' | 'processing';
    severity: 'info' | 'warning' | 'error';
    agent: string;
    agentIcon: any;
    message: string;
    actionLabel: string;
    timestamp: string;
    createdAt: string;
    summary: string;
    errorReason?: string;
    nextStepHint?: string;
    keyFacts: Array<{ label: string; value: string }>;
    details: {
        input: Record<string, any>;
        output?: Record<string, any>;
        raw: Record<string, any>;
        llmUsage?: {
            model_id: string;
            provider: string;
            steps: number;
            total_tokens: number;
            cost: number;
            latency: number;
        };
    };
}

const ERROR_KEYS = ['error', 'message', 'reason', 'detail', 'details', 'cause'];

const humanize = (value: string) =>
    value
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/[_-]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .replace(/^./, (c) => c.toUpperCase());

const formatDate = (isoDate?: string) => {
    if (!isoDate) return 'Unknown';
    const parsed = new Date(isoDate);
    if (Number.isNaN(parsed.getTime())) return 'Unknown';
    return parsed.toLocaleString();
};

const formatDuration = (times: { startedAt?: string; completedAt?: string; createdAt?: string }) => {
    const started = times.startedAt ?? times.createdAt;
    const ended = times.completedAt;
    if (!started || !ended) return 'In progress';
    const startMs = new Date(started).getTime();
    const endMs = new Date(ended).getTime();
    if (Number.isNaN(startMs) || Number.isNaN(endMs) || endMs < startMs) return 'Unknown';
    const seconds = Math.round((endMs - startMs) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remSeconds = seconds % 60;
    return remSeconds ? `${minutes}m ${remSeconds}s` : `${minutes}m`;
};

const valueToString = (value: unknown) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) return value.length ? `${value.length} items` : '0 items';
    return 'View details';
};

const getTopInputFacts = (input: Record<string, any>) => {
    const candidates = ['topic', 'title', 'query', 'url', 'email', 'company', 'industry', 'source', 'channel'];
    const facts = candidates
        .filter((key) => input[key] !== undefined && input[key] !== null && input[key] !== '')
        .slice(0, 4)
        .map((key) => ({ label: humanize(key), value: valueToString(input[key]) }));
    if (facts.length > 0) return facts;
    const firstKeys = Object.keys(input).slice(0, 3);
    return firstKeys.map((key) => ({ label: humanize(key), value: valueToString(input[key]) }));
};

const findErrorMessage = (value: unknown, depth = 0): string | undefined => {
    if (value === null || value === undefined || depth > 4) return undefined;
    if (typeof value === 'string' && value.trim()) return value.trim();
    if (Array.isArray(value)) {
        for (const item of value) {
            const nested = findErrorMessage(item, depth + 1);
            if (nested) return nested;
        }
        return undefined;
    }
    if (typeof value === 'object') {
        const record = value as Record<string, unknown>;
        for (const key of ERROR_KEYS) {
            const nested = findErrorMessage(record[key], depth + 1);
            if (nested) return nested;
        }
        for (const nestedValue of Object.values(record)) {
            const nested = findErrorMessage(nestedValue, depth + 1);
            if (nested) return nested;
        }
    }
    return undefined;
};

const getFailureHint = (reason?: string) => {
    if (!reason) return 'Open technical details to inspect request and response payloads.';
    const lower = reason.toLowerCase();
    if (lower.includes('timeout') || lower.includes('timed out')) {
        return 'The request likely took too long. Try a smaller input or rerun.';
    }
    if (lower.includes('rate') || lower.includes('429')) {
        return 'A provider limit was hit. Retry in a few moments.';
    }
    if (
        lower.includes('auth') ||
        lower.includes('token') ||
        lower.includes('permission') ||
        lower.includes('unauthorized') ||
        lower.includes('forbidden') ||
        lower.includes('401') ||
        lower.includes('403')
    ) {
        return 'This looks like an access issue. Check credentials and integration permissions.';
    }
    if (lower.includes('missing') || lower.includes('required') || lower.includes('invalid') || lower.includes('validation')) {
        return 'The input is likely incomplete or invalid. Review required fields in the request.';
    }
    if (lower.includes('not found') || lower.includes('404')) {
        return 'A referenced resource could not be found. Validate IDs, URLs, or linked records.';
    }
    return 'Review task input/output below to isolate what step failed.';
};

const ActivityLogs = () => {
    const [logs, setLogs] = useState<ActivityLog[]>([]);
    const [selectedLog, setSelectedLog] = useState<ActivityLog | null>(null);
    const [filterType, setFilterType] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(0);
    const [totalPages, setTotalPages] = useState(0);
    const PAGE_SIZE = 20;

    // Use ref to track selected log for interval updates without stale closures
    const selectedLogRef = useRef<ActivityLog | null>(null);

    // Keep ref in sync with state
    useEffect(() => {
        selectedLogRef.current = selectedLog;
    }, [selectedLog]);

    useEffect(() => {
        fetchLogs(false);
        const interval = setInterval(() => fetchLogs(true), 5000);
        return () => clearInterval(interval);
    }, [page]);

    useEffect(() => {
        setShowTechnicalDetails(false);
    }, [selectedLog?.id]);

    const fetchLogs = async (isBackground = false) => {
        try {
            if (!isBackground) setLoading(true);
            const offset = page * PAGE_SIZE;

            const [taskData, runData, workflows] = await Promise.all([
                MonitoringService.getActivity(PAGE_SIZE, offset),
                WorkflowService.getAllRuns({ limit: PAGE_SIZE, offset }),
                WorkflowService.getAll()
            ]);

            const tasks = taskData.tasks;
            const totalTasks = taskData.total;
            const totalRuns = runData.total;

            const maxItems = Math.max(totalTasks, totalRuns);
            setTotalPages(Math.ceil(maxItems / PAGE_SIZE) || 1);

            const workflowMap = new Map(workflows.map(w => [w.id, w]));

            const workflowRuns = runData.runs
                .map(run => {
                    const workflow = workflowMap.get(run.workflowId);
                    return workflow ? { run, workflow } : null;
                })
                .filter((item): item is { run: WorkflowRun, workflow: Workflow } => item !== null);

            const mappedLogs = [
                ...tasks.map(mapTaskToLog),
                ...workflowRuns.map(({ run, workflow }) => mapWorkflowRunToLog(run, workflow))
            ].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

            setLogs(mappedLogs);

            // Only auto-select if nothing is currently selected (checking ref for up-to-date value)
            if (!selectedLogRef.current && mappedLogs.length > 0) {
                setSelectedLog(mappedLogs[0]);
            }
            if (!isBackground) setLoading(false);
        } catch (err) {
            console.error('Failed to fetch activity logs:', err);
            if (!isBackground) setLoading(false);
        }
    };

    const mapTaskToLog = (task: Task): ActivityLog => {
        const isError = task.status === 'failed';
        const actionLabel = humanize(task.action || 'Task');
        const errorReason = isError
            ? task.error || findErrorMessage(task.output) || 'Task failed before returning a clear error message.'
            : undefined;
        const topFacts = getTopInputFacts(task.input || {});

        return {
            entryId: `task:${task.id}`,
            id: task.id,
            type: 'task',
            status: task.status === 'failed' ? 'error' : task.status === 'completed' ? 'success' : 'processing',
            severity: isError ? 'error' : 'info',
            agent: task.agentId ? 'Agent Task' : 'System', // We might want to fetch agent name if possible, or use type
            agentIcon: getAgentIcon('sales'), // Defaulting to sales for now, ideally we get agent type
            message: `${actionLabel} - ${task.status}`,
            actionLabel,
            timestamp: formatDate(task.createdAt),
            createdAt: task.createdAt,
            summary: isError ? 'Task failed and needs attention.' : task.status === 'completed' ? 'Task completed successfully.' : 'Task is still running.',
            errorReason,
            nextStepHint: isError ? getFailureHint(errorReason) : undefined,
            keyFacts: [
                { label: 'Task ID', value: task.id.slice(0, 8) },
                { label: 'Priority', value: humanize(task.priority || 'medium') },
                { label: 'Duration', value: formatDuration(task) },
                ...topFacts
            ],
            details: {
                input: task.input || {},
                output: task.output,
                raw: task as unknown as Record<string, any>,
                llmUsage: task.output?.llm_usage ? {
                    model_id: task.output.llm_usage.model_id || 'unknown',
                    provider: task.output.llm_usage.provider || 'unknown',
                    steps: 1, // basic implementation for single step
                    total_tokens: (task.output.llm_usage.input_tokens || 0) + (task.output.llm_usage.output_tokens || 0),
                    cost: task.output.llm_usage.estimated_cost_usd || 0,
                    latency: task.output.llm_usage.latency_ms || 0
                } : undefined
            }
        };
    };

    const mapWorkflowRunToLog = (run: WorkflowRun, workflow: Workflow): ActivityLog => {
        const isError = run.status === 'failed';
        const actionLabel = `${workflow.name} (Workflow)`;
        const errorReason = isError
            ? run.error || 'Workflow run failed before returning a detailed error.'
            : undefined;

        return {
            entryId: `workflow:${run.id}`,
            id: run.id,
            type: 'workflow',
            status: run.status === 'failed' ? 'error' : run.status === 'completed' ? 'success' : 'processing',
            severity: isError ? 'error' : 'info',
            agent: 'Workflow Engine',
            agentIcon: GitBranch,
            message: `${workflow.name} - ${run.status}`,
            actionLabel,
            timestamp: formatDate(run.startedAt),
            createdAt: run.startedAt,
            summary: isError
                ? `Workflow "${workflow.name}" failed and needs attention.`
                : run.status === 'completed'
                    ? `Workflow "${workflow.name}" completed successfully.`
                    : `Workflow "${workflow.name}" is currently running.`,
            errorReason,
            nextStepHint: isError ? getFailureHint(errorReason) : undefined,
            keyFacts: [
                { label: 'Workflow', value: workflow.name },
                { label: 'Run ID', value: run.id.slice(0, 8) },
                { label: 'Trigger', value: humanize(workflow.triggerType || 'workflow') },
                { label: 'Case ID', value: run.caseId ? run.caseId.slice(0, 8) : '-' },
                {
                    label: 'Duration',
                    value: formatDuration({
                        startedAt: run.startedAt,
                        completedAt: run.completedAt || undefined,
                        createdAt: run.startedAt
                    })
                }
            ],
            details: {
                input: run.triggerPayload || {},
                output: {
                    status: run.status,
                    error: run.error || null,
                    providerEventId: run.providerEventId || null,
                    idempotencyKey: run.idempotencyKey || null
                },
                raw: {
                    run,
                    workflow
                }
            }
        };
    };

    const filteredLogs = useMemo(() => {
        const byType = filterType === 'All'
            ? logs
            : logs.filter((log) => {
                if (filterType === 'Tasks') return log.type === 'task';
                if (filterType === 'Workflows') return log.type === 'workflow';
                if (filterType === 'System') return log.type === 'system';
                return true;
            });

        if (!searchQuery.trim()) return byType;
        const query = searchQuery.toLowerCase();
        return byType.filter((log) =>
            [
                log.message,
                log.actionLabel,
                log.status,
                log.agent,
                log.errorReason || ''
            ].some((text) => text.toLowerCase().includes(query))
        );
    }, [filterType, logs, searchQuery]);

    const failureCount = logs.filter((log) => log.status === 'error').length;
    const successCount = logs.filter((log) => log.status === 'success').length;
    const runningCount = logs.filter((log) => log.status === 'processing' || log.status === 'pending').length;

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <p className="text-gray-400 text-sm">Track task outcomes with plain-language diagnostics and optional technical details.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                        <input
                            type="text"
                            placeholder="Search by action, status, or failure reason..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-4 py-1.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-64"
                        />
                    </div>
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700 text-sm">
                        <Calendar size={14} />
                        <span>Last 24 Hours</span>
                    </button>
                    <button className="p-2 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700">
                        <Filter size={16} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="rounded-lg border border-gray-800 bg-gray-900/40 px-3 py-2">
                    <p className="text-[11px] uppercase tracking-wider text-gray-500">Successful</p>
                    <p className="text-lg font-semibold text-green-400">{successCount}</p>
                </div>
                <div className="rounded-lg border border-gray-800 bg-gray-900/40 px-3 py-2">
                    <p className="text-[11px] uppercase tracking-wider text-gray-500">Needs Attention</p>
                    <p className="text-lg font-semibold text-red-400">{failureCount}</p>
                </div>
                <div className="rounded-lg border border-gray-800 bg-gray-900/40 px-3 py-2">
                    <p className="text-[11px] uppercase tracking-wider text-gray-500">In Progress</p>
                    <p className="text-lg font-semibold text-blue-400">{runningCount}</p>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 min-h-0">
                {/* Activity List (Left 2/3) */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Filter Chips */}
                    <div className="flex items-center gap-2 mb-4">
                        {['All', 'Tasks', 'Workflows', 'System'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilterType(f)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-full text-xs font-medium transition-colors border",
                                    filterType === f
                                        ? "bg-blue-600/10 text-blue-400 border-blue-600/20"
                                        : "bg-gray-800/50 text-gray-400 border-gray-700 hover:bg-gray-800 hover:text-gray-300"
                                )}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-800">
                        <div className="col-span-3">Time</div>
                        <div className="col-span-4">Activity</div>
                        <div className="col-span-3">Agent</div>
                        <div className="col-span-2 text-right">Status</div>
                    </div>

                    {/* List */}
                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        {filteredLogs.map((log) => (
                            <div
                                key={log.entryId}
                                onClick={() => setSelectedLog(log)}
                                className={clsx(
                                    "grid grid-cols-12 gap-4 px-4 py-3 border-b border-gray-800/50 items-center cursor-pointer transition-colors",
                                    selectedLog?.entryId === log.entryId
                                        ? "bg-blue-600/5 border-blue-500/20"
                                        : "hover:bg-gray-800/30"
                                )}
                            >
                                <div className="col-span-3 text-xs text-gray-400 font-mono">{log.timestamp}</div>
                                <div className="col-span-4 min-w-0">
                                    <div className="text-sm text-gray-200 font-medium truncate">{log.actionLabel}</div>
                                    {log.status === 'error' && log.errorReason && (
                                        <div className="text-xs text-red-300/80 truncate">{log.errorReason}</div>
                                    )}
                                </div>
                                <div className="col-span-3 flex items-center gap-2">
                                    <div className="w-6 h-6 rounded bg-gray-800 flex items-center justify-center text-gray-400">
                                        <log.agentIcon size={12} />
                                    </div>
                                    <span className="text-xs text-gray-400">{log.agent}</span>
                                </div>
                                <div className="col-span-2 flex justify-end">
                                    <span className={clsx(
                                        "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border flex items-center gap-1",
                                        log.status === 'success' && "bg-green-500/10 text-green-400 border-green-500/20",
                                        log.status === 'warning' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                                        log.status === 'error' && "bg-red-500/10 text-red-400 border-red-500/20",
                                        (log.status === 'pending' || log.status === 'processing') && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                    )}>
                                        {log.status === 'success' && <CheckCircle2 size={10} />}
                                        {log.status === 'warning' && <AlertTriangle size={10} />}
                                        {log.status === 'error' && <XCircle size={10} />}
                                        {(log.status === 'pending' || log.status === 'processing') && <Clock size={10} />}
                                        {log.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {filteredLogs.length === 0 && (
                            <EmptyState
                                icon={Activity}
                                title="No activity logs found"
                                description={
                                    filterType === 'All'
                                        ? "Activity logs will appear here as agents process tasks and workflows execute."
                                        : `No ${filterType.toLowerCase()} logs found. Try adjusting your filters or time range.`
                                }
                                hint="Activity includes task executions, workflow runs, and system events."
                                variant="minimal"
                            />
                        )}
                    </div>

                    {/* Pagination Controls */}
                    <div className="flex justify-between items-center p-4 border-t border-gray-800 bg-gray-900/40">
                        <button
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            disabled={page === 0 || loading}
                            className="px-3 py-1.5 text-xs font-medium text-gray-300 bg-gray-800 border border-gray-700 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Previous
                        </button>
                        <div className="text-xs text-gray-500 font-mono">
                            Page {page + 1} of {totalPages}
                        </div>
                        <button
                            onClick={() => setPage(p => p + 1)}
                            disabled={page >= totalPages - 1 || loading}
                            className="px-3 py-1.5 text-xs font-medium text-gray-300 bg-gray-800 border border-gray-700 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                        </button>
                    </div>
                </div>

                {/* Log Detail Drawer (Right 1/3) */}
                {selectedLog ? (
                    <div className="w-96 bg-gray-900 border border-gray-800 rounded-xl flex flex-col overflow-hidden animate-fade-in">
                        <div className="p-4 border-b border-gray-800 bg-gray-800/30">
                            <div className="flex items-center gap-2 mb-2">
                                <span className={clsx(
                                    "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border",
                                    selectedLog.status === 'success' && "bg-green-500/10 text-green-400 border-green-500/20",
                                    selectedLog.status === 'warning' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                                    selectedLog.status === 'error' && "bg-red-500/10 text-red-400 border-red-500/20",
                                    (selectedLog.status === 'pending' || selectedLog.status === 'processing') && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                )}>
                                    {selectedLog.status}
                                </span>
                                <span className="text-xs text-gray-500 font-mono">{selectedLog.timestamp}</span>
                            </div>
                            <h2 className="font-semibold text-white mb-1">{selectedLog.actionLabel}</h2>
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                                <selectedLog.agentIcon size={12} />
                                <span>{selectedLog.agent}</span>
                                <span>•</span>
                                <span className="capitalize">{selectedLog.type}</span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
                            <div>
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">What Happened</h3>
                                <div className={clsx(
                                    'rounded-lg border p-3',
                                    selectedLog.status === 'error'
                                        ? 'bg-red-500/5 border-red-500/20'
                                        : selectedLog.status === 'success'
                                            ? 'bg-green-500/5 border-green-500/20'
                                            : 'bg-blue-500/5 border-blue-500/20'
                                )}>
                                    <p className="text-sm text-gray-200">{selectedLog.summary}</p>
                                    {selectedLog.errorReason && (
                                        <p className="text-sm text-red-300 mt-2">
                                            <span className="text-red-200 font-medium">Reason: </span>
                                            {selectedLog.errorReason}
                                        </p>
                                    )}
                                    {selectedLog.nextStepHint && (
                                        <p className="text-xs text-gray-300 mt-2">{selectedLog.nextStepHint}</p>
                                    )}
                                </div>
                            </div>

                            <div>
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Key Details</h3>
                                <div className="space-y-2">
                                    {selectedLog.keyFacts.map((fact) => (
                                        <div key={`${fact.label}-${fact.value}`} className="bg-gray-800/40 p-2.5 rounded-lg border border-gray-700/50 flex items-start justify-between gap-4">
                                            <span className="text-xs text-gray-400">{fact.label}</span>
                                            <span className="text-xs text-gray-200 text-right break-all">{fact.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {selectedLog.details.llmUsage && (
                                <div>
                                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                                        <Zap size={12} className="text-yellow-500" />
                                        <span>LLM Metrics</span>
                                    </h3>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="bg-gray-800/40 p-2.5 rounded-lg border border-gray-700/50">
                                            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Model</div>
                                            <div className="text-xs text-gray-200 font-mono truncate" title={selectedLog.details.llmUsage.model_id}>
                                                {selectedLog.details.llmUsage.model_id.split(':').pop()}
                                            </div>
                                        </div>
                                        <div className="bg-gray-800/40 p-2.5 rounded-lg border border-gray-700/50">
                                            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Tokens</div>
                                            <div className="text-xs text-gray-200 font-mono">
                                                {selectedLog.details.llmUsage.total_tokens.toLocaleString()}
                                            </div>
                                        </div>
                                        <div className="bg-gray-800/40 p-2.5 rounded-lg border border-gray-700/50">
                                            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Cost</div>
                                            <div className="text-xs text-gray-200 font-mono">
                                                ${selectedLog.details.llmUsage.cost.toFixed(6)}
                                            </div>
                                        </div>
                                        <div className="bg-gray-800/40 p-2.5 rounded-lg border border-gray-700/50">
                                            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Latency</div>
                                            <div className="text-xs text-gray-200 font-mono">
                                                {Math.round(selectedLog.details.llmUsage.latency)}ms
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div>
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Task Input</h3>
                                <div className="space-y-2">
                                    {Object.keys(selectedLog.details.input || {}).length === 0 && (
                                        <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50 text-sm text-gray-400">
                                            No input captured.
                                        </div>
                                    )}
                                    {Object.entries(selectedLog.details.input || {}).slice(0, 8).map(([key, value]) => (
                                        <div key={key} className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                                            <div className="text-xs text-gray-400 mb-1">{humanize(key)}</div>
                                            <div className="text-sm text-gray-200 break-words whitespace-pre-wrap">{valueToString(value)}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="border border-gray-800 rounded-lg overflow-hidden">
                                <button
                                    type="button"
                                    onClick={() => setShowTechnicalDetails((current) => !current)}
                                    className="w-full px-3 py-2 text-xs text-gray-300 bg-gray-800/40 hover:bg-gray-800/70 transition-colors flex items-center justify-between"
                                >
                                    <span>Technical Details (for debugging)</span>
                                    {showTechnicalDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </button>

                                {showTechnicalDetails && (
                                    <div className="p-3 space-y-3 bg-gray-950/50">
                                        <div>
                                            <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Output</div>
                                            <pre className="bg-gray-950 p-3 rounded-lg border border-gray-800 text-xs text-gray-400 font-mono overflow-x-auto custom-scrollbar">
                                                {selectedLog.details.output ? JSON.stringify(selectedLog.details.output, null, 2) : 'No output returned.'}
                                            </pre>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Raw Task Payload</div>
                                            <pre className="bg-gray-950 p-3 rounded-lg border border-gray-800 text-xs text-gray-400 font-mono overflow-x-auto custom-scrollbar">
                                                {JSON.stringify(selectedLog.details.raw, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="w-96 bg-gray-900/50 border border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500">
                        <Info size={48} className="mb-4 opacity-20" />
                        <p className="text-sm">Select a log entry to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ActivityLogs;
