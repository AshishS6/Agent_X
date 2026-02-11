import { useEffect, useMemo, useState } from 'react';
import {
    Plus,
    Calendar,
    MoreVertical,
    Play,
    Pause,
    Clock,
    Zap,
    LifeBuoy,
    GitBranch
} from 'lucide-react';
import clsx from 'clsx';
import { formatNumber } from '../utils/formatting';
import { EmptyState } from '../components/EmptyState';
import { Workflow, WorkflowCase, WorkflowRun, WorkflowService, WorkflowStepRun } from '../services/api';
import api from '../services/api';

const Workflows = () => {
    const [workflows, setWorkflows] = useState<Workflow[]>([]);
    const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
    const [filter, setFilter] = useState('All');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [runs, setRuns] = useState<WorkflowRun[]>([]);
    const [runsLoading, setRunsLoading] = useState(false);
    const [cases, setCases] = useState<WorkflowCase[]>([]);
    const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
    const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
    const [runDetail, setRunDetail] = useState<{ run: WorkflowRun; steps: WorkflowStepRun[] } | null>(null);

    const filteredWorkflows = useMemo(() => {
        if (filter === 'All') return workflows;
        return workflows.filter((w) => w.status.toLowerCase() === filter.toLowerCase());
    }, [filter, workflows]);

    useEffect(() => {
        fetchWorkflows();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (!selectedWorkflow) return;
        fetchCases(selectedWorkflow.id);
        setSelectedRunId(null);
        setRunDetail(null);
        setSelectedCaseId(null);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedWorkflow?.id]);

    const fetchWorkflows = async () => {
        try {
            setLoading(true);
            const data = await WorkflowService.getAll();
            setWorkflows(data);
            setSelectedWorkflow((prev) => {
                if (prev) {
                    const match = data.find((w) => w.id === prev.id);
                    return match || data[0] || null;
                }
                return data[0] || null;
            });
            setError(null);
        } catch (e) {
            console.error('Failed to fetch workflows', e);
            setError('Failed to load workflows');
        } finally {
            setLoading(false);
        }
    };

    const fetchCases = async (workflowId: string) => {
        try {
            setRunsLoading(true);
            const { cases: data } = await WorkflowService.getCases(workflowId, { limit: 25, offset: 0 });
            setCases(data);
            // default select most recent case
            const first = data[0]?.id || null;
            setSelectedCaseId(first);
            if (first) {
                const { runs: r } = await WorkflowService.getRunsForCase(first, { limit: 25, offset: 0 });
                setRuns(r);
            } else {
                setRuns([]);
            }
        } catch (e) {
            console.error('Failed to fetch workflow cases', e);
            setCases([]);
            setRuns([]);
        } finally {
            setRunsLoading(false);
        }
    };

    const selectCase = async (caseId: string) => {
        setSelectedCaseId(caseId);
        setSelectedRunId(null);
        setRunDetail(null);
        try {
            setRunsLoading(true);
            const { runs: r } = await WorkflowService.getRunsForCase(caseId, { limit: 25, offset: 0 });
            setRuns(r);
        } catch (e) {
            console.error('Failed to fetch runs for case', e);
            setRuns([]);
        } finally {
            setRunsLoading(false);
        }
    };

    const fetchRunDetail = async (runId: string) => {
        try {
            setSelectedRunId(runId);
            const data = await WorkflowService.getRunById(runId);
            setRunDetail(data);
        } catch (e) {
            console.error('Failed to fetch run detail', e);
            setRunDetail(null);
        }
    };

    const generateSecret = () => {
        const bytes = new Uint8Array(24);
        crypto.getRandomValues(bytes);
        // base64url
        const str = btoa(String.fromCharCode(...bytes))
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/g, '');
        return str;
    };

    const createFreshdeskTriageWorkflow = async () => {
        const secret = generateSecret();
        const wf = await WorkflowService.create({
            name: 'Freshdesk Ticket Triage (MVP)',
            description: 'Freshdesk webhook → classify ticket + draft reply + next steps (human-in-the-loop).',
            status: 'active',
            triggerType: 'freshdesk',
            triggerConfig: {
                secret,
                header: 'X-AgentX-Webhook-Secret',
            },
            ownerTeam: 'support',
            steps: [
                {
                    type: 'load_context',
                    input_template: {
                        ticket_id: '{{ticket_id}}',
                    },
                },
                {
                    type: 'agent_task',
                    agent_type: 'support_ticket_triage',
                    action: 'triage_ticket',
                    input_template: {
                        ticket_id: '{{ticket_id}}',
                        subject: '{{subject}}',
                        description: '{{description}}',
                        requester_email: '{{requester_email}}',
                        priority: '{{priority}}',
                    },
                },
            ],
        });
        await fetchWorkflows();
        setSelectedWorkflow(wf);
    };

    const toggleWorkflowStatus = async () => {
        if (!selectedWorkflow) return;
        try {
            if (selectedWorkflow.status === 'active') {
                const updated = await WorkflowService.pause(selectedWorkflow.id);
                setSelectedWorkflow(updated);
                setWorkflows((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
            } else {
                const updated = await WorkflowService.activate(selectedWorkflow.id);
                setSelectedWorkflow(updated);
                setWorkflows((prev) => prev.map((w) => (w.id === updated.id ? updated : w)));
            }
        } catch (e) {
            console.error('Failed to toggle workflow status', e);
        }
    };

    const webhookInfo = useMemo(() => {
        if (!selectedWorkflow) return null;
        if (selectedWorkflow.triggerType !== 'freshdesk') return null;
        const url = `${api.defaults.baseURL}/triggers/freshdesk/${selectedWorkflow.id}`;
        const secretHeader = selectedWorkflow.triggerConfig?.header || 'X-AgentX-Webhook-Secret';
        const secret = selectedWorkflow.triggerConfig?.secret || '';
        return { url, secretHeader, secret };
    }, [selectedWorkflow]);

    const formatRelativeTime = (iso: string) => {
        const t = new Date(iso).getTime();
        const diff = Date.now() - t;
        const sec = Math.max(0, Math.floor(diff / 1000));
        if (sec < 60) return `${sec}s ago`;
        const min = Math.floor(sec / 60);
        if (min < 60) return `${min}m ago`;
        const hr = Math.floor(min / 60);
        if (hr < 24) return `${hr}h ago`;
        const day = Math.floor(hr / 24);
        return `${day}d ago`;
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-gray-400">
                Loading workflows...
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center text-gray-400">
                <span>{error}</span>
                <button onClick={fetchWorkflows} className="ml-4 text-blue-400 hover:underline">Retry</button>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <p className="text-gray-400 text-sm">Manage and monitor your multi-agent automations</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700 text-sm">
                        <Calendar size={14} />
                        <span>Last 7 Days</span>
                    </button>
                    <button
                        onClick={createFreshdeskTriageWorkflow}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium shadow-lg shadow-blue-500/20"
                    >
                        <Plus size={16} />
                        <span>New Workflow</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 min-h-0">
                {/* Workflow List (Left 2/3) */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Filters */}
                    <div className="flex items-center gap-2 mb-4">
                        {['All', 'Active', 'Paused', 'Draft'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-full text-xs font-medium transition-colors border",
                                    filter === f
                                        ? "bg-blue-600/10 text-blue-400 border-blue-600/20"
                                        : "bg-gray-800/50 text-gray-400 border-gray-700 hover:bg-gray-800 hover:text-gray-300"
                                )}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    {/* List */}
                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2">
                        {filteredWorkflows.length === 0 ? (
                            <EmptyState
                                icon={GitBranch}
                                title="No workflows yet"
                                description="Create your first workflow to automate multi-agent tasks and processes."
                                primaryAction={{
                                    label: 'Create Workflow',
                                    onClick: () => {
                                        createFreshdeskTriageWorkflow();
                                    },
                                    icon: Plus,
                                }}
                                hint="Workflows allow you to chain multiple agents together for complex automation."
                            />
                        ) : (
                            filteredWorkflows.map((workflow) => (
                            <div
                                key={workflow.id}
                                onClick={() => setSelectedWorkflow(workflow)}
                                className={clsx(
                                    "p-4 rounded-xl border transition-all cursor-pointer group",
                                    selectedWorkflow?.id === workflow.id
                                        ? "bg-blue-600/5 border-blue-500/50 ring-1 ring-blue-500/20"
                                        : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/50 hover:border-gray-600"
                                )}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "w-10 h-10 rounded-lg flex items-center justify-center",
                                            workflow.status === 'active' ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                                        )}>
                                            {workflow.status === 'active' ? <Play size={20} /> : <Pause size={20} />}
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">{workflow.name}</h3>
                                            <p className="text-xs text-gray-500">{workflow.triggerType}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={clsx(
                                            "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border",
                                            workflow.status === 'active'
                                                ? "bg-green-500/10 text-green-400 border-green-500/20"
                                                : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                                        )}>
                                            {workflow.status}
                                        </span>
                                        <button className="p-1 text-gray-500 hover:text-white rounded hover:bg-gray-700">
                                            <MoreVertical size={16} />
                                        </button>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-400 mb-4 line-clamp-1">{workflow.description || '—'}</p>

                                <div className="flex items-center justify-between pt-3 border-t border-gray-700/50">
                                    <div className="flex items-center -space-x-2">
                                        <div className="w-6 h-6 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400" title="Support">
                                            <LifeBuoy size={12} />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-gray-500">
                                        <div className="flex items-center gap-1">
                                            <Clock size={12} />
                                            <span>{workflow.updatedAt ? formatRelativeTime(workflow.updatedAt) : '—'}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-300">{formatNumber(0)}</span> runs
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                        )}
                    </div>
                </div>

                {/* Workflow Detail (Right 1/3) */}
                <div className="w-96 bg-gray-900 border border-gray-800 rounded-xl flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-800">
                        <div className="flex items-center justify-between mb-2">
                            <h2 className="font-semibold text-white">{selectedWorkflow?.name || 'Select a workflow'}</h2>
                            {selectedWorkflow && (
                                <button onClick={toggleWorkflowStatus} className="text-xs text-blue-400 hover:text-blue-300 font-medium">
                                    {selectedWorkflow.status === 'active' ? 'Pause' : 'Activate'}
                                </button>
                            )}
                        </div>
                        <p className="text-xs text-gray-400">{selectedWorkflow?.description || '—'}</p>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Workflow Steps</h3>

                        <div className="space-y-4 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-800">
                            {/* Trigger Step */}
                            <div className="relative pl-10">
                                <div className="absolute left-0 top-0 w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400 z-10">
                                    <Zap size={14} />
                                </div>
                                <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700">
                                    <div className="text-xs font-medium text-blue-400 mb-0.5">Trigger</div>
                                    <div className="text-sm text-gray-200">{selectedWorkflow?.triggerType || '—'}</div>
                                </div>
                            </div>

                            {/* Agent Steps (Mock) */}
                            {(selectedWorkflow?.steps || []).map((step, i) => (
                                <div key={i} className="relative pl-10">
                                    <div className="absolute left-0 top-0 w-7 h-7 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400 z-10">
                                        <LifeBuoy size={14} />
                                    </div>
                                    <div className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50">
                                        <div className="text-xs font-medium text-gray-500 mb-0.5">Step {i + 1}</div>
                                        <div className="text-sm text-gray-200">{step.type || 'step'} </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-6 mb-3">Recent Runs</h3>
                        {runsLoading ? (
                            <div className="text-xs text-gray-500">Loading runs...</div>
                        ) : (
                            <div className="space-y-2">
                                {cases.length > 0 && (
                                    <div className="mb-3">
                                        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Cases (tickets)</div>
                                        <div className="flex flex-wrap gap-2">
                                            {cases.slice(0, 8).map((c) => (
                                                <button
                                                    key={c.id}
                                                    onClick={() => selectCase(c.id)}
                                                    className={clsx(
                                                        "px-2 py-1 rounded-lg text-xs border transition-colors",
                                                        selectedCaseId === c.id
                                                            ? "bg-blue-600/10 text-blue-300 border-blue-500/30"
                                                            : "bg-gray-800/40 text-gray-400 border-gray-800 hover:bg-gray-800/70 hover:text-gray-300"
                                                    )}
                                                    title={`Ticket ${c.externalRefId}`}
                                                >
                                                    {c.externalRefId}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {runs.length === 0 ? (
                                    <div className="text-xs text-gray-500">No runs yet.</div>
                                ) : (
                                    runs.slice(0, 10).map((r) => (
                                        <div
                                            key={r.id}
                                            onClick={() => fetchRunDetail(r.id)}
                                            className={clsx(
                                                "flex items-center justify-between p-2 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer",
                                                selectedRunId === r.id && "bg-blue-600/5 border border-blue-500/20"
                                            )}
                                        >
                                            <div className="flex items-center gap-2">
                                                <div className={clsx(
                                                    "w-1.5 h-1.5 rounded-full",
                                                    r.status === 'completed' ? "bg-green-500" : r.status === 'failed' ? "bg-red-500" : "bg-blue-500"
                                                )}></div>
                                                <span className="text-sm text-gray-300">Run {r.id.slice(0, 8)}</span>
                                            </div>
                                            <span className="text-xs text-gray-500">{formatRelativeTime(r.startedAt)}</span>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {webhookInfo && (
                            <div className="mt-6">
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Webhook</h3>
                                <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 text-xs text-gray-300 space-y-2">
                                    <div className="text-gray-400">URL</div>
                                    <div className="font-mono break-all">{webhookInfo.url}</div>
                                    <div className="text-gray-400">Secret header</div>
                                    <div className="font-mono break-all">{webhookInfo.secretHeader}: {webhookInfo.secret || '—'}</div>
                                </div>
                            </div>
                        )}

                        {runDetail && (
                            <div className="mt-6">
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Run Detail</h3>
                                <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 text-xs text-gray-300 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="font-mono">Run {runDetail.run.id.slice(0, 8)}</span>
                                        <span className={clsx(
                                            "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border",
                                            runDetail.run.status === 'completed' && "bg-green-500/10 text-green-400 border-green-500/20",
                                            runDetail.run.status === 'failed' && "bg-red-500/10 text-red-400 border-red-500/20",
                                            runDetail.run.status === 'running' && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                        )}>
                                            {runDetail.run.status}
                                        </span>
                                    </div>

                                    <div>
                                        <div className="text-gray-400 mb-1">Trigger payload</div>
                                        <pre className="whitespace-pre-wrap break-words text-gray-200">{JSON.stringify(runDetail.run.triggerPayload, null, 2)}</pre>
                                    </div>

                                    <div>
                                        <div className="text-gray-400 mb-1">Step outputs</div>
                                        <div className="space-y-2">
                                            {runDetail.steps.map((s) => (
                                                <div key={s.id} className="border border-gray-800 rounded-lg p-2">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-gray-300">Step {s.stepIndex + 1}: {s.stepType}</span>
                                                        <span className="text-gray-500">{s.status}</span>
                                                    </div>
                                                    <pre className="whitespace-pre-wrap break-words text-gray-200">{JSON.stringify(s.output, null, 2)}</pre>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Workflows;
