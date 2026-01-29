import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FileText, Play, Loader2, Plus, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import AgentLayout from '../components/Layout/AgentLayout';
import { AgentService, TaskService, Task, AgentMetrics } from '../services/api';
import { BlogDocumentService, BlogDocument } from '../services/blogDocumentApi';
import { formatNumber, formatPercentage } from '../utils/formatting';
import { EmptyState } from '../components/EmptyState';
import clsx from 'clsx';

const TASKS_PAGE_SIZE = 10;
const DOCS_PAGE_SIZE = 10;

const BlogAgent = () => {
    const navigate = useNavigate();
    const [agentId, setAgentId] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [tasksTotal, setTasksTotal] = useState(0);
    const [tasksPage, setTasksPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState<BlogDocument[]>([]);
    const [documentsTotal, setDocumentsTotal] = useState(0);
    const [documentsPage, setDocumentsPage] = useState(1);
    const [showNewDocForm, setShowNewDocForm] = useState(false);
    const [newDoc, setNewDoc] = useState({
        brand: 'OPEN' as 'OPEN' | 'Zwitch',
        topic: '',
        targetAudience: 'SME',
        intent: 'education',
    });

    const fetchTasks = useCallback(async (id: string, page: number = 1) => {
        const { tasks: agentTasks, total } = await TaskService.getAll({
            agentId: id,
            limit: TASKS_PAGE_SIZE,
            offset: (page - 1) * TASKS_PAGE_SIZE,
        });
        setTasks(agentTasks);
        setTasksTotal(total);
        setTasksPage(page);
    }, []);

    const fetchDocuments = useCallback(async (page: number = 1) => {
        try {
            const { documents: docs, total } = await BlogDocumentService.list({
                limit: DOCS_PAGE_SIZE,
                offset: (page - 1) * DOCS_PAGE_SIZE,
            });
            setDocuments(docs);
            setDocumentsTotal(total);
            setDocumentsPage(page);
        } catch (err) {
            console.error('Failed to fetch documents:', err);
        }
    }, []);

    const handleCreateDocument = async () => {
        try {
            const doc = await BlogDocumentService.create(newDoc);
            setShowNewDocForm(false);
            setNewDoc({ brand: 'OPEN', topic: '', targetAudience: 'SME', intent: 'education' });
            // Refresh list so the new doc appears immediately
            fetchDocuments(1);
            navigate(`/blog/${doc.id}`);
        } catch (err) {
            console.error('Failed to create document:', err);
            alert('Failed to create document');
        }
    };

    // Initial load: fetch agent ID once, then hydrate data.
    useEffect(() => {
        const init = async () => {
            try {
                const agents = await AgentService.getAll();
                const blogAgent = agents.find(a => a.type === 'blog');
                if (!blogAgent) {
                    console.error('Blog agent not found. Available agents:', agents.map(a => ({ type: a.type, name: a.name })));
                    return;
                }

                setAgentId(blogAgent.id);
                const [agentMetrics] = await Promise.all([
                    AgentService.getMetrics(blogAgent.id),
                    fetchTasks(blogAgent.id, tasksPage),
                    fetchDocuments(documentsPage),
                ]);
                setMetrics(agentMetrics);
            } catch (err) {
                console.error('Failed to fetch agent data:', err);
            } finally {
                setLoading(false);
            }
        };

        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Polling: keep the page fresh, but pause while the user is filling the New Blog form.
    useEffect(() => {
        if (!agentId) return;
        if (showNewDocForm) return; // avoid re-renders while typing

        const poll = async () => {
            try {
                const [agentMetrics] = await Promise.all([
                    AgentService.getMetrics(agentId),
                    fetchTasks(agentId, tasksPage),
                ]);
                setMetrics(agentMetrics);
            } catch (err) {
                console.error('Polling failed:', err);
            }
        };

        poll();
        const interval = setInterval(poll, 15000);
        return () => clearInterval(interval);
    }, [agentId, fetchTasks, tasksPage, showNewDocForm]);

    // Documents poll (lighter + less frequent). Also paused while typing.
    useEffect(() => {
        if (showNewDocForm) return;
        fetchDocuments(documentsPage);
        const interval = setInterval(() => fetchDocuments(documentsPage), 60000);
        return () => clearInterval(interval);
    }, [fetchDocuments, showNewDocForm, documentsPage]);


    // Safe date formatter
    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return isNaN(date.getTime()) ? 'Just now' : date.toLocaleTimeString();
        } catch {
            return 'Just now';
        }
    };

    const tasksTotalPages = Math.max(1, Math.ceil(tasksTotal / TASKS_PAGE_SIZE));
    const documentsTotalPages = Math.max(1, Math.ceil(documentsTotal / DOCS_PAGE_SIZE));

    // Get last activity from most recent task
    const lastActivity = useMemo(() => {
        if (tasks.length === 0) return undefined;
        const sortedTasks = [...tasks].sort((a, b) => 
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
        return sortedTasks[0]?.completedAt || sortedTasks[0]?.createdAt;
    }, [tasks]);

    // Tab Content
    // NOTE: Avoid memoizing this block; it contains controlled form inputs and
    // UI state (showNewDocForm/newDoc) that must re-render immediately.
    const headerStats = useMemo(() => (
        <div className="flex items-center gap-2">
            {[
                { label: 'Total Tasks', value: formatNumber(metrics?.totalTasks || 0, { showThousands: true }), trend: '+0%', color: 'text-blue-400', bg: 'bg-blue-400/10' },
                { label: 'Completed', value: formatNumber(metrics?.statusCounts?.completed || 0, { showThousands: true }), trend: '+0%', color: 'text-green-400', bg: 'bg-green-400/10' },
                { label: 'Failed', value: formatNumber(metrics?.statusCounts?.failed || 0, { showThousands: true }), trend: '0%', color: 'text-red-400', bg: 'bg-red-400/10' },
                { label: 'Success Rate', value: formatPercentage(metrics?.totalTasks ? ((metrics.statusCounts?.completed || 0) / metrics.totalTasks) * 100 : 100, 1, false), trend: '+0%', color: 'text-orange-400', bg: 'bg-orange-400/10' },
            ].map((stat, i) => (
                <div key={i} className="bg-gray-950/40 px-3 py-2 rounded-lg border border-gray-800 min-w-[140px]">
                    <div className="flex items-center justify-between gap-3">
                        <div>
                            <p className="text-[11px] text-gray-400 leading-tight">{stat.label}</p>
                            <p className="text-lg font-bold text-white leading-tight mt-1">{stat.value}</p>
                        </div>
                        <span className={`text-[10px] font-medium px-2 py-1 rounded-full ${stat.bg} ${stat.color}`}>
                            {stat.trend}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    ), [metrics]);

    const overviewContent = (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Blog Documents */}
                <div className="lg:col-span-2 bg-gray-900 p-6 rounded-xl border border-gray-800 flex flex-col min-h-0">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-white">Blog Documents</h3>
                        <button
                            onClick={() => setShowNewDocForm(true)}
                            className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            New Blog
                        </button>
                    </div>
                    {showNewDocForm && (
                        <div className="mb-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
                            <h4 className="text-sm font-semibold text-white mb-3">Create New Blog Document</h4>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Brand</label>
                                    <select
                                        value={newDoc.brand}
                                        onChange={(e) => setNewDoc({ ...newDoc, brand: e.target.value as 'OPEN' | 'Zwitch' })}
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white text-sm"
                                    >
                                        <option value="OPEN">OPEN</option>
                                        <option value="Zwitch">Zwitch</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Topic *</label>
                                    <input
                                        type="text"
                                        value={newDoc.topic}
                                        onChange={(e) => setNewDoc({ ...newDoc, topic: e.target.value })}
                                        placeholder="e.g., AI in Marketing"
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Target Audience</label>
                                    <select
                                        value={newDoc.targetAudience}
                                        onChange={(e) => setNewDoc({ ...newDoc, targetAudience: e.target.value })}
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white text-sm"
                                    >
                                        <option value="SME">SME</option>
                                        <option value="Developer">Developer</option>
                                        <option value="Founder">Founder</option>
                                        <option value="Enterprise">Enterprise</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Intent</label>
                                    <select
                                        value={newDoc.intent}
                                        onChange={(e) => setNewDoc({ ...newDoc, intent: e.target.value })}
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white text-sm"
                                    >
                                        <option value="education">Education</option>
                                        <option value="product">Product</option>
                                        <option value="announcement">Announcement</option>
                                    </select>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleCreateDocument}
                                        disabled={!newDoc.topic}
                                        className="flex-1 px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                                    >
                                        Create
                                    </button>
                                    <button
                                        onClick={() => setShowNewDocForm(false)}
                                        className="px-3 py-2 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                    <div className="flex-1 min-h-0 flex flex-col">
                        <div className="flex-1 min-h-[200px] max-h-[320px] overflow-y-auto space-y-3 pr-1">
                            {documents.length === 0 ? (
                                <EmptyState
                                    icon={FileText}
                                    title="No blog documents yet"
                                    description="Create your first blog document to get started with the new document-centric workflow."
                                    primaryAction={{
                                        label: 'Create Blog Document',
                                        onClick: () => setShowNewDocForm(true),
                                        icon: Plus,
                                    }}
                                    hint="Blog documents support outline → feedback → draft workflow with version tracking."
                                    variant="minimal"
                                />
                            ) : (
                                documents.map((doc) => (
                                    <div
                                        key={doc.id}
                                        onClick={() => navigate(`/blog/${doc.id}`)}
                                        className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 cursor-pointer transition-colors"
                                    >
                                        <div className="flex-1">
                                            <p className="text-sm font-medium text-white">{doc.topic}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                                                    {doc.brand}
                                                </span>
                                                <span className="text-xs text-gray-500">{doc.targetAudience}</span>
                                                <span className="text-xs text-gray-500">•</span>
                                                <span className="text-xs text-gray-500">{doc.intent}</span>
                                            </div>
                                        </div>
                                        <ArrowRight className="w-4 h-4 text-gray-400" />
                                    </div>
                                ))
                            )}
                        </div>
                        {documentsTotal > DOCS_PAGE_SIZE && (
                            <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800">
                                <p className="text-xs text-gray-500">
                                    Showing {(documentsPage - 1) * DOCS_PAGE_SIZE + 1}–{Math.min(documentsPage * DOCS_PAGE_SIZE, documentsTotal)} of {documentsTotal}
                                </p>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => fetchDocuments(documentsPage - 1)}
                                        disabled={documentsPage <= 1}
                                        className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                                    >
                                        Previous
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => fetchDocuments(documentsPage + 1)}
                                        disabled={documentsPage >= documentsTotalPages}
                                        className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Current Queue */}
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">Recent Tasks</h3>
                    <div className="flex-1 min-h-0 flex flex-col">
                        <div className="flex-1 min-h-[200px] max-h-[320px] overflow-y-auto space-y-3 pr-1">
                            {tasks.length === 0 ? (
                                <EmptyState
                                    icon={FileText}
                                    title="No tasks found"
                                    description="You haven't created any blog tasks yet. Start by generating an outline or draft."
                                    primaryAction={{
                                        label: 'Create Blog',
                                        onClick: () => {
                                            setShowNewDocForm(true);
                                        },
                                        icon: Play,
                                    }}
                                    hint="Use the document workflow: outline → feedback → draft."
                                    variant="minimal"
                                />
                            ) : (
                                tasks.map((task) => (
                                    <div key={task.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800 shrink-0">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2 h-2 rounded-full shrink-0 ${task.status === 'processing' ? 'bg-blue-500 animate-pulse' :
                                                task.status === 'completed' ? 'bg-green-500' :
                                                    task.status === 'failed' ? 'bg-red-500' : 'bg-gray-500'
                                                }`} />
                                            <div>
                                                <p className="text-sm font-medium text-white capitalize">{task.action.replace('_', ' ')}</p>
                                                <p className="text-xs text-gray-500">{formatDate(task.createdAt)}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3 shrink-0">
                                            <span className={`text-xs px-2 py-1 rounded-full ${task.priority === 'high' ? 'bg-red-500/10 text-red-400' :
                                                task.priority === 'medium' ? 'bg-yellow-500/10 text-yellow-400' :
                                                    'bg-blue-500/10 text-blue-400'
                                                }`}>
                                                {task.priority}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                        {tasksTotal > TASKS_PAGE_SIZE && (
                            <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800">
                                <p className="text-xs text-gray-500">
                                    Showing {(tasksPage - 1) * TASKS_PAGE_SIZE + 1}–{Math.min(tasksPage * TASKS_PAGE_SIZE, tasksTotal)} of {tasksTotal}
                                </p>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => agentId && fetchTasks(agentId, tasksPage - 1)}
                                        disabled={tasksPage <= 1}
                                        className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                                    >
                                        Previous
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => agentId && fetchTasks(agentId, tasksPage + 1)}
                                        disabled={tasksPage >= tasksTotalPages}
                                        className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );

    const logsContent = (
        <div className="space-y-4">
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-4">Activity Logs</h3>
                <div className="space-y-3">
                    {tasks.length === 0 ? (
                        <EmptyState
                            icon={FileText}
                            title="No logs available"
                            description="Task execution logs will appear here once tasks are processed."
                            hint="Logs show detailed execution information for debugging and monitoring."
                            variant="minimal"
                        />
                    ) : (
                        tasks.map((task) => (
                            <div key={task.id} className="p-3 bg-gray-800/50 rounded-lg border border-gray-800">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-medium text-gray-400 capitalize">
                                            {task.action.replace('_', ' ')}
                                        </span>
                                        <span className={clsx(
                                            "text-xs px-2 py-0.5 rounded-full",
                                            task.status === 'completed' ? "bg-green-500/10 text-green-400" :
                                                task.status === 'failed' ? "bg-red-500/10 text-red-400" :
                                                    "bg-blue-500/10 text-blue-400"
                                        )}>
                                            {task.status}
                                        </span>
                                    </div>
                                    <span className="text-xs text-gray-500">{formatDate(task.createdAt)}</span>
                                </div>
                                {task.error && (
                                    <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                                        Error: {task.error}
                                    </div>
                                )}
                                {task.completedAt && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        Completed: {formatDate(task.completedAt)}
                                    </p>
                                )}
                            </div>
                        ))
                    )}
                </div>
                {tasksTotal > TASKS_PAGE_SIZE && (
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800">
                        <p className="text-xs text-gray-500">
                            Showing {(tasksPage - 1) * TASKS_PAGE_SIZE + 1}–{Math.min(tasksPage * TASKS_PAGE_SIZE, tasksTotal)} of {tasksTotal}
                        </p>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => agentId && fetchTasks(agentId, tasksPage - 1)}
                                disabled={tasksPage <= 1}
                                className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                            >
                                Previous
                            </button>
                            <button
                                type="button"
                                onClick={() => agentId && fetchTasks(agentId, tasksPage + 1)}
                                disabled={tasksPage >= tasksTotalPages}
                                className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <AgentLayout
            name="Blog Agent"
            description="Generates structured blog outlines and drafts for marketing teams."
            icon={FileText}
            color="bg-purple-500"
            lastActivity={lastActivity}
            headerStats={headerStats}
            showEnableToggle={false}
            showOverflowMenu={false}
            showConversationsTab={false}
            showSkillsTab={false}
            showConfigTab={false}
            overviewContent={overviewContent}
            conversationsContent={null}
            skillsContent={null}
            logsContent={logsContent}
            configContent={null}
        />
    );
};

export default BlogAgent;
