import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Megaphone, ArrowRight, Loader2, FileText, TrendingUp, Search, BarChart, Clock } from 'lucide-react';
import { AgentService, TaskService, Agent, Task } from '../services/api';
import { EmptyState } from '../components/EmptyState';

const MarketingOverview = () => {
    const navigate = useNavigate();
    const [recentTasks, setRecentTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const agents = await AgentService.getAll();
            const blog = agents.find(a => a.type === 'blog');
            const research = agents.find(a => a.type === 'market_research');

            // Get recent tasks from both agents
            const allTasks: Task[] = [];
            if (blog) {
                const blogTasks = await TaskService.getAll({ agentId: blog.id, limit: 3, offset: 0 });
                allTasks.push(...blogTasks.tasks);
            }
            if (research) {
                const researchTasks = await TaskService.getAll({ agentId: research.id, limit: 3, offset: 0 });
                allTasks.push(...researchTasks.tasks);
            }
            
            // Sort by creation date and take most recent 5
            allTasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
            setRecentTasks(allTasks.slice(0, 5));
        } catch (err) {
            console.error('Failed to fetch marketing data:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    const contentTasks = [
        {
            id: 'blog',
            title: 'Blog / Content Generation',
            description: 'Generate blog outlines and drafts for your marketing content',
            icon: FileText,
            color: 'bg-blue-500',
            onClick: () => navigate('/blog')
        }
    ];

    const researchTasks = [
        {
            id: 'market-analysis',
            title: 'Market Analysis',
            description: 'Analyze industry trends, market size, and competitive landscape',
            icon: BarChart,
            color: 'bg-green-500',
            onClick: () => navigate('/market-research')
        },
        {
            id: 'competitor-research',
            title: 'Competitor Research',
            description: 'Research and compare competitor strategies, products, and positioning',
            icon: Search,
            color: 'bg-purple-500',
            onClick: () => navigate('/market-research')
        },
        {
            id: 'trend-monitoring',
            title: 'Trend Monitoring',
            description: 'Monitor industry trends and emerging opportunities',
            icon: TrendingUp,
            color: 'bg-orange-500',
            onClick: () => navigate('/market-research')
        }
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white mb-2">Marketing</h1>
                <p className="text-gray-400 text-sm max-w-2xl">
                    Generate content and market intelligence. Create blog posts and conduct market research to inform your marketing strategy.
                </p>
            </div>

            {/* Content Tasks */}
            <div>
                <h2 className="text-lg font-semibold text-white mb-4">Content</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {contentTasks.map((task) => (
                        <div
                            key={task.id}
                            onClick={task.onClick}
                            className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-all cursor-pointer hover:shadow-lg"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className={`p-3 rounded-lg ${task.color} bg-opacity-10`}>
                                    <task.icon className={`w-6 h-6 ${task.color.replace('bg-', 'text-')}`} />
                                </div>
                            </div>
                            <h3 className="text-lg font-bold text-white mb-2">{task.title}</h3>
                            <p className="text-sm text-gray-400 mb-4">{task.description}</p>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    task.onClick();
                                }}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
                            >
                                Get started
                                <ArrowRight size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Market Research Tasks */}
            <div>
                <h2 className="text-lg font-semibold text-white mb-4">Market Research</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {researchTasks.map((task) => (
                        <div
                            key={task.id}
                            onClick={task.onClick}
                            className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-all cursor-pointer hover:shadow-lg"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className={`p-3 rounded-lg ${task.color} bg-opacity-10`}>
                                    <task.icon className={`w-6 h-6 ${task.color.replace('bg-', 'text-')}`} />
                                </div>
                            </div>
                            <h3 className="text-lg font-bold text-white mb-2">{task.title}</h3>
                            <p className="text-sm text-gray-400 mb-4">{task.description}</p>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    task.onClick();
                                }}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
                            >
                                Get started
                                <ArrowRight size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recent Tasks */}
            {recentTasks.length > 0 && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <Clock className="text-blue-400" size={20} />
                            Recent Tasks
                        </h3>
                    </div>
                    <div className="p-6">
                        <div className="space-y-3">
                            {recentTasks.map((task) => (
                                <div
                                    key={task.id}
                                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                                    onClick={() => {
                                        // Navigate to appropriate page based on agent type
                                        if (task.action.includes('outline') || task.action.includes('post')) {
                                            navigate('/blog');
                                        } else {
                                            navigate('/market-research');
                                        }
                                    }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${
                                            task.status === 'completed' ? 'bg-green-500' :
                                            task.status === 'failed' ? 'bg-red-500' :
                                            'bg-blue-500 animate-pulse'
                                        }`} />
                                        <div>
                                            <p className="text-sm font-medium text-white capitalize">
                                                {task.action.replace('_', ' ')}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {new Date(task.createdAt).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <span className={`text-xs px-2 py-1 rounded-full ${
                                        task.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                                        task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                        'bg-blue-500/10 text-blue-400'
                                    }`}>
                                        {task.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MarketingOverview;
