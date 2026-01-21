import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FileText, BookOpen, Search, Play, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { AgentService, TaskService, Task, AgentMetrics } from '../services/api';

const BlogAgent = () => {
    const [agentId, setAgentId] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    // Fetch agent data
    useEffect(() => {
        const fetchAgentData = async () => {
            try {
                // Find blog agent ID
                const agents = await AgentService.getAll();
                const blogAgent = agents.find(a => a.type === 'blog');

                if (blogAgent) {
                    console.log('Blog agent found:', blogAgent);
                    setAgentId(blogAgent.id);
                    const [agentMetrics, { tasks: agentTasks }] = await Promise.all([
                        AgentService.getMetrics(blogAgent.id),
                        TaskService.getAll({ agentId: blogAgent.id, limit: 10 })
                    ]);
                    setMetrics(agentMetrics);
                    setTasks(agentTasks);
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
    }, []);

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

    // Tab Content
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
                    <BlogTaskForm
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
                    <Search size={16} />
                    <span className="text-sm">Filter</span>
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4">
                {tasks.filter(t => t.output).map((task) => {
                    const output = task.output as any;
                    const response = output?.response || output;
                    
                    return (
                        <div key={task.id} className="mb-4 p-4 border border-gray-800 rounded-lg hover:bg-gray-800/50 cursor-pointer transition-colors group">
                            <div className="flex justify-between items-start mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="bg-blue-500/10 text-blue-400 text-xs font-medium px-2 py-1 rounded-full capitalize">{task.action.replace('_', ' ')}</span>
                                    <span className="text-gray-500 text-xs">ID: #{task.id.slice(0, 8)}</span>
                                </div>
                                <span className="text-gray-500 text-xs">{formatDate(task.createdAt)}</span>
                            </div>
                            
                            {task.action === 'generate_outline' && response?.outline ? (
                                <div className="text-gray-300 text-sm mt-2">
                                    <h4 className="text-white font-semibold mb-2">{response.title}</h4>
                                    <div className="space-y-2">
                                        {response.outline.map((section: any, idx: number) => (
                                            <div key={idx} className="pl-4 border-l-2 border-gray-700">
                                                <p className="font-medium text-white">## {section.heading}</p>
                                                <p className="text-gray-400 text-xs mt-1">{section.intent}</p>
                                                {section.subsections && section.subsections.length > 0 && (
                                                    <div className="mt-2 ml-4 space-y-1">
                                                        {section.subsections.map((sub: any, subIdx: number) => (
                                                            <div key={subIdx}>
                                                                <p className="text-sm text-gray-300">### {sub.heading}</p>
                                                                <p className="text-gray-400 text-xs">{sub.intent}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : task.action === 'generate_post_from_outline' && response?.content ? (
                                <div className="text-gray-300 text-sm mt-2">
                                    <h4 className="text-white font-semibold mb-2">{response.title}</h4>
                                    <div className="bg-gray-800/50 p-3 rounded-lg max-h-96 overflow-y-auto">
                                        <pre className="whitespace-pre-wrap font-sans text-gray-300 text-xs">
                                            {response.content.substring(0, 500)}
                                            {response.content.length > 500 && '...'}
                                        </pre>
                                    </div>
                                    {response.word_count && (
                                        <div className="mt-2 text-xs text-gray-500">
                                            Word Count: {response.word_count} | Reading Time: {response.estimated_reading_time || Math.ceil(response.word_count / 200)} min
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-gray-300 text-sm mt-2">
                                    <pre className="whitespace-pre-wrap font-sans text-gray-400">
                                        {JSON.stringify(response, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    );
                })}
                {tasks.filter(t => t.output).length === 0 && (
                    <div className="text-center text-gray-500 mt-10">No conversation history yet</div>
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
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
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
