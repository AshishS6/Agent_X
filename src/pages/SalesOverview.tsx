import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, ArrowRight, Loader2, CheckCircle, Mail, MessageSquare, Clock } from 'lucide-react';
import { AgentService, TaskService, Agent, Task } from '../services/api';
import { EmptyState } from '../components/EmptyState';

const SalesOverview = () => {
    const navigate = useNavigate();
    const [recentTasks, setRecentTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const agents = await AgentService.getAll();
            const agent = agents.find(a => a.type === 'sales');
            
            if (agent) {
                const tasksData = await TaskService.getAll({ agentId: agent.id, limit: 5, offset: 0 });
                setRecentTasks(tasksData.tasks);
            }
        } catch (err) {
            console.error('Failed to fetch sales data:', err);
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

    const tasks = [
        {
            id: 'qualify',
            title: 'Lead Qualification',
            description: 'Score and qualify leads based on company data and fit signals',
            icon: CheckCircle,
            color: 'bg-green-500',
            available: true,
            onClick: () => navigate('/sales')
        },
        {
            id: 'outreach',
            title: 'Outreach Email',
            description: 'Generate personalized outreach emails for prospects',
            icon: Mail,
            color: 'bg-blue-500',
            available: true,
            onClick: () => navigate('/sales')
        },
        {
            id: 'followup',
            title: 'Follow-up Generation',
            description: 'Create follow-up emails based on previous interactions',
            icon: MessageSquare,
            color: 'bg-purple-500',
            available: false,
            comingSoon: true,
            onClick: () => {}
        }
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white mb-2">Sales</h1>
                <p className="text-gray-400 text-sm max-w-2xl">
                    Acquire, qualify, and convert leads. Use the tasks below to qualify prospects, generate outreach emails, and manage follow-ups.
                </p>
            </div>

            {/* Task Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {tasks.map((task) => (
                    <div
                        key={task.id}
                        onClick={task.available ? task.onClick : undefined}
                        className={`bg-gray-900 p-6 rounded-xl border border-gray-800 transition-all ${
                            task.available 
                                ? 'hover:border-gray-700 cursor-pointer hover:shadow-lg' 
                                : 'opacity-60 cursor-not-allowed'
                        }`}
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className={`p-3 rounded-lg ${task.color} bg-opacity-10`}>
                                <task.icon className={`w-6 h-6 ${task.color.replace('bg-', 'text-')}`} />
                            </div>
                            {task.comingSoon && (
                                <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                                    Coming soon
                                </span>
                            )}
                        </div>
                        <h3 className="text-lg font-bold text-white mb-2">{task.title}</h3>
                        <p className="text-sm text-gray-400">{task.description}</p>
                        {task.available && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    task.onClick();
                                }}
                                className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
                            >
                                Get started
                                <ArrowRight size={14} />
                            </button>
                        )}
                    </div>
                ))}
            </div>

            {/* Recent Tasks */}
            {recentTasks.length > 0 && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <Clock className="text-blue-400" size={20} />
                            Recent Tasks
                        </h3>
                        <button
                            onClick={() => navigate('/sales')}
                            className="text-sm text-blue-400 hover:text-blue-300"
                        >
                            View all
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-3">
                            {recentTasks.map((task) => (
                                <div
                                    key={task.id}
                                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                                    onClick={() => navigate('/sales')}
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

export default SalesOverview;
