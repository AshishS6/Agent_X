import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { DollarSign, Users, Filter, Search, Play, Loader2, FileText } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { AgentService, TaskService, Task, AgentMetrics } from '../services/api';
import { formatNumber, formatPercentage } from '../utils/formatting';
import { EmptyState } from '../components/EmptyState';
import { ConversationCard } from '../components/ConversationCard';
import clsx from 'clsx';

const TASKS_PAGE_SIZE = 10;

const SalesAgent = () => {
    const [agentId, setAgentId] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [tasksTotal, setTasksTotal] = useState(0);
    const [tasksPage, setTasksPage] = useState(1);
    const [loading, setLoading] = useState(true);

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

    // Fetch agent data
    useEffect(() => {
        const fetchAgentData = async () => {
            try {
                const agents = await AgentService.getAll();
                const salesAgent = agents.find(a => a.type === 'sales');

                if (salesAgent) {
                    setAgentId(salesAgent.id);
                    const [agentMetrics] = await Promise.all([
                        AgentService.getMetrics(salesAgent.id),
                        fetchTasks(salesAgent.id, tasksPage),
                    ]);
                    setMetrics(agentMetrics);
                }
            } catch (err) {
                console.error('Failed to fetch agent data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchAgentData();
        const interval = setInterval(fetchAgentData, 5000);
        return () => clearInterval(interval);
    }, [fetchTasks, tasksPage]);

    // --- Tab Content ---


    const handleTaskCreated = useCallback(() => {
        if (agentId) fetchTasks(agentId, 1);
    }, [agentId, fetchTasks]);

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

    // Get last activity from most recent task
    const lastActivity = useMemo(() => {
        if (tasks.length === 0) return undefined;
        const sortedTasks = [...tasks].sort((a, b) => 
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
        return sortedTasks[0]?.completedAt || sortedTasks[0]?.createdAt;
    }, [tasks]);

    const overviewContent = useMemo(() => (
        <div className="space-y-6">
            {/* KPI Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Tasks', value: formatNumber(metrics?.totalTasks || 0, { showThousands: true }), trend: '+0%', color: 'text-blue-400', bg: 'bg-blue-400/10' },
                    { label: 'Completed', value: formatNumber(metrics?.statusCounts?.completed || 0, { showThousands: true }), trend: '+0%', color: 'text-green-400', bg: 'bg-green-400/10' },
                    { label: 'Failed', value: formatNumber(metrics?.statusCounts?.failed || 0, { showThousands: true }), trend: '0%', color: 'text-red-400', bg: 'bg-red-400/10' },
                    { label: 'Success Rate', value: formatPercentage(metrics?.totalTasks ? ((metrics.statusCounts?.completed || 0) / metrics.totalTasks) * 100 : 100, 1, false), trend: '+0%', color: 'text-orange-400', bg: 'bg-orange-400/10' },
                ].map((stat, i) => (
                    <div key={i} className="bg-gray-900 p-4 rounded-xl border border-gray-800">
                        <p className="text-sm text-gray-400">{stat.label}</p>
                        <div className="flex items-end justify-between mt-2">
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${stat.bg} ${stat.color}`}>
                                {stat.trend}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Current Queue */}
                <div className="lg:col-span-2 bg-gray-900 p-6 rounded-xl border border-gray-800 flex flex-col min-h-0">
                    <h3 className="text-lg font-bold text-white mb-4">Recent Tasks</h3>
                    <div className="flex-1 min-h-0 flex flex-col">
                        <div className="flex-1 min-h-[200px] max-h-[320px] overflow-y-auto space-y-3 pr-1">
                            {tasks.length === 0 ? (
                                <EmptyState
                                    icon={DollarSign}
                                    title="No tasks found"
                                    description="You haven't created any tasks yet. Start by executing your first sales task."
                                    primaryAction={{
                                        label: 'Execute Task',
                                        onClick: () => {
                                            // Scroll to task form or focus it
                                            document.querySelector('form')?.scrollIntoView({ behavior: 'smooth' });
                                        },
                                        icon: Play,
                                    }}
                                    hint="Tasks help automate lead qualification, email outreach, and meeting scheduling."
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

                {/* Task Execution Form */}
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">Execute Task</h3>
                    <TaskForm
                        agentId={agentId}
                        onTaskCreated={handleTaskCreated}
                    />
                </div>
            </div>
        </div>
    ), [metrics, tasks, agentId, handleTaskCreated, fetchTasks, tasksPage, tasksTotal, tasksTotalPages]);

    const conversationsContent = useMemo(() => (
        <div className="w-full flex-1 min-h-0 flex flex-col bg-gray-900 rounded-xl border border-gray-800">
            {/* Toolbar */}
            <div className="p-4 border-b border-gray-800 flex justify-between items-center shrink-0">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search conversations..."
                        className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-blue-500"
                    />
                </div>
                <button className="flex items-center gap-2 text-gray-400 hover:text-white px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors shrink-0">
                    <Filter size={16} />
                    <span className="text-sm">Filter</span>
                </button>
            </div>

            {/* List */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                {tasks.filter(t => t.output).map((task) => (
                    <ConversationCard
                        key={task.id}
                        action={task.action}
                        timestamp={task.createdAt}
                        status={task.status}
                        output={task.output}
                        taskId={task.id}
                    />
                ))}
                {tasks.filter(t => t.output).length === 0 && (
                    <EmptyState
                        icon={Search}
                        title="No conversation history yet"
                        description="Completed tasks will appear here. Start by executing a task to see conversation results."
                        primaryAction={{
                            label: 'Execute Task',
                            onClick: () => {
                                // Navigate to overview tab or scroll to form
                                window.location.hash = '';
                            },
                        }}
                        hint="Conversations show the output and results from completed agent tasks."
                    />
                )}
            </div>
        </div>
    ), [tasks]);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Lead Qualification', desc: 'Analyzes company data to score leads.', tools: ['LinkedIn API', 'Clearbit', 'CRM'] },
                { title: 'Email Drafting', desc: 'Generates personalized outreach emails.', tools: ['OpenAI', 'Gmail API'] },
                { title: 'Meeting Scheduling', desc: 'Finds times and sends invites.', tools: ['Google Calendar', 'Calendly'] },
                { title: 'CRM Sync', desc: 'Updates deal stages and notes.', tools: ['Salesforce', 'HubSpot'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-blue-500/10 p-2 rounded-lg">
                            <Users className="text-blue-400" size={20} />
                        </div>
                    </div>
                    <p className="text-gray-400 mb-4">{skill.desc}</p>
                    <div className="flex flex-wrap gap-2">
                        {skill.tools.map((tool) => (
                            <span key={tool} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-md border border-gray-700">
                                {tool}
                            </span>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    ), []);

    const logsContent = useMemo(() => (
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
                        tasks.slice(0, 20).map((task) => (
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
            </div>
        </div>
    ), [tasks]);

    const configContent = useMemo(() => (
        <div className="space-y-6">
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-6">Data Sources</h3>
                <div className="space-y-4">
                    {['Salesforce', 'HubSpot', 'Gmail', 'LinkedIn Sales Nav'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <Users size={20} className="text-gray-400" />
                                </div>
                                <div>
                                    <p className="font-medium text-white">{source}</p>
                                    <p className="text-xs text-gray-500">Connected</p>
                                </div>
                            </div>
                            <button className="text-sm text-red-400 hover:text-red-300">Disconnect</button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    ), []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <AgentLayout
            name="Sales Agent"
            description="Automates lead qualification, email outreach, and meeting scheduling."
            icon={DollarSign}
            color="bg-blue-500"
            lastActivity={lastActivity}
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

// Task Execution Form Component
interface TaskFormProps {
    agentId: string | null;
    onTaskCreated: () => void;
}

const TaskForm = ({ agentId, onTaskCreated }: TaskFormProps) => {
    const [action, setAction] = useState('generate_email');
    const [input, setInput] = useState('');
    const [executing, setExecuting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agentId || !input) return;

        setExecuting(true);
        try {
            let parsedInput = {};
            try {
                // Try to parse as JSON first
                parsedInput = JSON.parse(input);
            } catch {
                // Fallback to simple object
                if (action === 'generate_email') {
                    parsedInput = { recipientName: 'Prospect', context: input };
                } else {
                    parsedInput = { input };
                }
            }

            await AgentService.execute('sales', action, parsedInput);
            setInput(''); // Only clear input on success
            onTaskCreated();
        } catch (err) {
            console.error('Failed to execute task:', err);
        } finally {
            setExecuting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Action</label>
                <select
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="generate_email">Generate Email</option>
                    <option value="qualify_lead">Qualify Lead</option>
                </select>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Input (JSON or Text)</label>
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={action === 'generate_email' ? 'Enter context for the email...' : 'Enter lead details...'}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent h-32 font-mono text-sm"
                />
            </div>
            <button
                type="submit"
                disabled={executing || !input}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {executing ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                Execute Task
            </button>
        </form>
    );
};

export default SalesAgent;
