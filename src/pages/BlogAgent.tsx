import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FileText, BookOpen, Search, Play, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { AgentService, TaskService, Task, AgentMetrics } from '../services/api';
import { formatNumber, formatPercentage } from '../utils/formatting';
import { EmptyState } from '../components/EmptyState';
import { ConversationCard } from '../components/ConversationCard';
import clsx from 'clsx';

const TASKS_PAGE_SIZE = 10;

const BlogAgent = () => {
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
                const blogAgent = agents.find(a => a.type === 'blog');

                if (blogAgent) {
                    setAgentId(blogAgent.id);
                    const [agentMetrics] = await Promise.all([
                        AgentService.getMetrics(blogAgent.id),
                        fetchTasks(blogAgent.id, tasksPage),
                    ]);
                    setMetrics(agentMetrics);
                } else {
                    console.error('Blog agent not found. Available agents:', agents.map(a => ({ type: a.type, name: a.name })));
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

    // Tab Content
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
                                    icon={FileText}
                                    title="No tasks found"
                                    description="You haven't created any blog tasks yet. Start by generating an outline or draft."
                                    primaryAction={{
                                        label: 'Generate Outline',
                                        onClick: () => {
                                            // Scroll to task form
                                            document.querySelector('form')?.scrollIntoView({ behavior: 'smooth' });
                                        },
                                        icon: Play,
                                    }}
                                    hint="Create blog outlines or generate full posts from approved outlines."
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
                    <BlogTaskForm
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
                    <Search size={16} />
                    <span className="text-sm">Filter</span>
                </button>
            </div>

            {/* List */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                {tasks.filter(t => t.output).map((task) => {
                    const output = task.output as any;
                    // Handle both direct output and nested response structure
                    const normalizedOutput = output?.response || output;
                    
                    return (
                        <ConversationCard
                            key={task.id}
                            action={task.action}
                            timestamp={task.createdAt}
                            status={task.status}
                            output={normalizedOutput}
                            taskId={task.id}
                        />
                    );
                })}
                {tasks.filter(t => t.output).length === 0 && (
                    <EmptyState
                        icon={BookOpen}
                        title="No conversation history yet"
                        description="Completed blog tasks will appear here. Generate an outline or post to see results."
                        primaryAction={{
                            label: 'Generate Content',
                            onClick: () => {
                                // Navigate to overview tab
                                window.location.hash = '';
                            },
                        }}
                        hint="Conversations show generated outlines, blog posts, and other content from completed tasks."
                    />
                )}
            </div>
        </div>
    ), [tasks]);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Outline Generation', desc: 'Creates structured blog outlines with clear sections and intent.', tools: ['GPT-4', 'Claude'] },
                { title: 'Draft Generation', desc: 'Generates full blog drafts from approved outlines.', tools: ['GPT-4', 'Claude'] },
                { title: 'Brand Consistency', desc: 'Maintains OPEN and Zwitch brand voices.', tools: ['Brand Guidelines'] },
                { title: 'Audience Targeting', desc: 'Tailors content for SME, Developer, Founder, and Enterprise audiences.', tools: ['Audience Analysis'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-blue-500/10 p-2 rounded-lg">
                            <BookOpen className="text-blue-400" size={20} />
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
                <h3 className="text-lg font-bold text-white mb-6">Brand Settings</h3>
                <div className="space-y-4">
                    {['OPEN', 'Zwitch'].map((brand) => (
                        <div key={brand} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <FileText size={20} className="text-gray-400" />
                                </div>
                                <div>
                                    <p className="font-medium text-white">{brand}</p>
                                    <p className="text-xs text-gray-500">
                                        {brand === 'OPEN' ? 'Technical, detailed, developer-focused' : 'Friendly, accessible, business-focused'}
                                    </p>
                                </div>
                            </div>
                            <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-400">Active</span>
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
            name="Blog Agent"
            description="Generates structured blog outlines and drafts for marketing teams."
            icon={FileText}
            color="bg-purple-500"
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
interface BlogTaskFormProps {
    agentId: string | null;
    onTaskCreated: () => void;
}

const BlogTaskForm = ({ agentId, onTaskCreated }: BlogTaskFormProps) => {
    const [action, setAction] = useState<'generate_outline' | 'generate_post_from_outline'>('generate_outline');
    const [brand, setBrand] = useState('OPEN');
    const [topic, setTopic] = useState('');
    const [targetAudience, setTargetAudience] = useState('SME');
    const [intent, setIntent] = useState('education');
    const [tone, setTone] = useState('professional');
    const [length, setLength] = useState('medium');
    const [outlineInput, setOutlineInput] = useState('');
    const [executing, setExecuting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        // Check if agent is loaded
        if (!agentId) {
            alert('Agent is not loaded yet. Please wait a moment and try again.');
            console.error('Agent ID is null. Agent may not be loaded yet.');
            return;
        }

        if (action === 'generate_outline' && !topic) {
            alert('Please enter a topic');
            return;
        }

        if (action === 'generate_post_from_outline' && !outlineInput) {
            alert('Please provide an outline (JSON format)');
            return;
        }

        setExecuting(true);
        try {
            let parsedInput: any = {
                brand,
            };

            if (action === 'generate_outline') {
                parsedInput = {
                    brand,
                    topic,
                    target_audience: targetAudience,
                    intent,
                };
            } else {
                // Parse outline JSON
                let outline;
                try {
                    outline = JSON.parse(outlineInput);
                } catch {
                    alert('Invalid JSON format for outline');
                    setExecuting(false);
                    return;
                }
                parsedInput = {
                    brand,
                    outline,
                    tone,
                    length,
                };
            }

            console.log('Executing task:', { agentType: 'blog', action, input: parsedInput });
            const task = await AgentService.execute('blog', action, parsedInput);
            console.log('Task created successfully:', task);
            
            // Reset form on success
            if (action === 'generate_outline') {
                setTopic('');
            } else {
                setOutlineInput('');
            }
            
            onTaskCreated();
        } catch (err: any) {
            console.error('Failed to execute task:', err);
            const errorMessage = err?.response?.data?.error || err?.message || 'Unknown error occurred';
            alert(`Failed to execute task: ${errorMessage}`);
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
                    onChange={(e) => setAction(e.target.value as any)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="generate_outline">Generate Outline</option>
                    <option value="generate_post_from_outline">Generate Post from Outline</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Brand</label>
                <select
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="OPEN">OPEN</option>
                    <option value="Zwitch">Zwitch</option>
                </select>
            </div>

            {action === 'generate_outline' ? (
                <>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Topic *</label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="e.g., AI in Marketing"
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Target Audience</label>
                        <select
                            value={targetAudience}
                            onChange={(e) => setTargetAudience(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="SME">SME</option>
                            <option value="Developer">Developer</option>
                            <option value="Founder">Founder</option>
                            <option value="Enterprise">Enterprise</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Intent</label>
                        <select
                            value={intent}
                            onChange={(e) => setIntent(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="education">Education</option>
                            <option value="product">Product</option>
                            <option value="announcement">Announcement</option>
                        </select>
                    </div>
                </>
            ) : (
                <>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Outline (JSON) *</label>
                        <textarea
                            value={outlineInput}
                            onChange={(e) => setOutlineInput(e.target.value)}
                            placeholder='{"title": "...", "outline": [...]}'
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent h-32 font-mono text-sm"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Tone</label>
                        <select
                            value={tone}
                            onChange={(e) => setTone(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="professional">Professional</option>
                            <option value="friendly">Friendly</option>
                            <option value="explanatory">Explanatory</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Length</label>
                        <select
                            value={length}
                            onChange={(e) => setLength(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="short">Short (~800 words)</option>
                            <option value="medium">Medium (~1200 words)</option>
                            <option value="long">Long (~2000 words)</option>
                        </select>
                    </div>
                </>
            )}

            <button
                type="submit"
                disabled={executing || !agentId || (action === 'generate_outline' ? !topic : !outlineInput)}
                className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {executing ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                {!agentId ? 'Loading Agent...' : executing ? 'Executing...' : 'Execute Task'}
            </button>
        </form>
    );
};

export default BlogAgent;
