import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { DollarSign, Users, Filter, Search, Play, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { AgentService, TaskService, Task, AgentMetrics } from '../services/api';

const SalesAgent = () => {
    const [agentId, setAgentId] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);



    // Fetch agent data
    useEffect(() => {
        const fetchAgentData = async () => {
            try {
                // Find sales agent ID
                const agents = await AgentService.getAll();
                const salesAgent = agents.find(a => a.type === 'sales');

                if (salesAgent) {
                    setAgentId(salesAgent.id);
                    const [agentMetrics, { tasks: agentTasks }] = await Promise.all([
                        AgentService.getMetrics(salesAgent.id),
                        TaskService.getAll({ agentId: salesAgent.id, limit: 10 })
                    ]);
                    setMetrics(agentMetrics);
                    setTasks(agentTasks);
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
    }, []);

    // --- Tab Content ---

    // Safe date formatter
    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return isNaN(date.getTime()) ? 'Just now' : date.toLocaleTimeString();
        } catch {
            return 'Just now';
        }
    };

    const handleTaskCreated = useCallback(() => {
        if (agentId) {
            TaskService.getAll({ agentId, limit: 10 }).then(({ tasks }) => setTasks(tasks));
        }
    }, [agentId]);

    // --- Tab Content ---

    const overviewContent = useMemo(() => (
        <div className="space-y-6">
            {/* KPI Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Tasks', value: metrics?.totalTasks || 0, trend: '+0%', color: 'text-blue-400', bg: 'bg-blue-400/10' },
                    { label: 'Completed', value: metrics?.statusCounts?.completed || 0, trend: '+0%', color: 'text-green-400', bg: 'bg-green-400/10' },
                    { label: 'Failed', value: metrics?.statusCounts?.failed || 0, trend: '0%', color: 'text-red-400', bg: 'bg-red-400/10' },
                    { label: 'Success Rate', value: `${metrics?.totalTasks ? Math.round(((metrics.statusCounts?.completed || 0) / metrics.totalTasks) * 100) : 100}%`, trend: '+0%', color: 'text-orange-400', bg: 'bg-orange-400/10' },
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
                <div className="lg:col-span-2 bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4">Recent Tasks</h3>
                    <div className="space-y-3">
                        {tasks.length === 0 ? (
                            <div className="text-center text-gray-500 py-8">No tasks found</div>
                        ) : (
                            tasks.map((task) => (
                                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${task.status === 'processing' ? 'bg-blue-500 animate-pulse' :
                                            task.status === 'completed' ? 'bg-green-500' :
                                                task.status === 'failed' ? 'bg-red-500' : 'bg-gray-500'
                                            }`} />
                                        <div>
                                            <p className="text-sm font-medium text-white capitalize">{task.action.replace('_', ' ')}</p>
                                            <p className="text-xs text-gray-500">{formatDate(task.createdAt)}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
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
    ), [metrics, tasks, agentId, handleTaskCreated]);

    const conversationsContent = useMemo(() => (
        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col h-[600px]">
            {/* Toolbar */}
            <div className="p-4 border-b border-gray-800 flex justify-between items-center">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search conversations..."
                        className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-blue-500"
                    />
                </div>
                <button className="flex items-center gap-2 text-gray-400 hover:text-white px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors">
                    <Filter size={16} />
                    <span className="text-sm">Filter</span>
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4">
                {tasks.filter(t => t.output).map((task) => (
                    <div key={task.id} className="mb-4 p-4 border border-gray-800 rounded-lg hover:bg-gray-800/50 cursor-pointer transition-colors group">
                        <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                                <span className="bg-blue-500/10 text-blue-400 text-xs font-medium px-2 py-1 rounded-full capitalize">{task.action.replace('_', ' ')}</span>
                                <span className="text-gray-500 text-xs">ID: #{task.id.slice(0, 8)}</span>
                            </div>
                            <span className="text-gray-500 text-xs">{formatDate(task.createdAt)}</span>
                        </div>
                        <div className="text-gray-300 text-sm mt-2">
                            <pre className="whitespace-pre-wrap font-sans text-gray-400">
                                {JSON.stringify(task.output, null, 2)}
                            </pre>
                        </div>
                    </div>
                ))}
                {tasks.filter(t => t.output).length === 0 && (
                    <div className="text-center text-gray-500 mt-10">No conversation history yet</div>
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
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
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
