import React, { useState, useEffect } from 'react';
import {
    Activity,
    TrendingUp,
    Clock,
    CheckCircle,
    AlertTriangle,
    Filter,
    ArrowUpRight,
    ArrowDownRight,
    Loader2
} from 'lucide-react';
import clsx from 'clsx';
import { MonitoringService, SystemMetrics, Task } from '../services/api';

// --- Components ---

interface StatCardProps {
    title: string;
    value: string | number;
    subLabel: string;
    trend?: number;
    icon: React.ElementType;
    color: string;
    onClick?: () => void;
}

const StatCard = ({ title, value, subLabel, trend, icon: Icon, color, onClick }: StatCardProps) => (
    <div
        onClick={onClick}
        className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-all cursor-pointer group relative overflow-hidden"
    >
        <div className="flex justify-between items-start mb-4 relative z-10">
            <div className={`p-3 rounded-lg ${color} bg-opacity-10 group-hover:scale-110 transition-transform`}>
                <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
            </div>
            {trend !== undefined && (
                <div className={clsx(
                    "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
                    trend >= 0 ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                )}>
                    {trend >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {Math.abs(trend)}%
                </div>
            )}
        </div>

        <div className="relative z-10">
            <h3 className="text-gray-400 text-sm font-medium mb-1">{title}</h3>
            <p className="text-2xl font-bold text-white mb-1">{value}</p>
            <p className="text-xs text-gray-500">{subLabel}</p>
        </div>

        {/* Sparkline Background Effect (Simplified) */}
        <div className="absolute bottom-0 right-0 w-32 h-16 opacity-5 group-hover:opacity-10 transition-opacity">
            <svg viewBox="0 0 100 50" className="w-full h-full fill-current text-white">
                <path d="M0 50 L10 40 L20 45 L30 30 L40 35 L50 20 L60 25 L70 10 L80 15 L90 5 L100 0 V50 H0 Z" />
            </svg>
        </div>
    </div>
);

const DashboardHome = () => {
    const [activeTab, setActiveTab] = useState<'activity' | 'tasks' | 'alerts'>('activity');
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const data = await MonitoringService.getMetrics();
                setMetrics(data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch metrics:', err);
                setError('Failed to load system metrics. Is the backend running?');
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
        // Poll every 5 seconds for real-time updates
        const interval = setInterval(fetchMetrics, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading && !metrics) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (error && !metrics) {
        return (
            <div className="flex flex-col items-center justify-center h-96 text-red-400">
                <AlertTriangle className="w-12 h-12 mb-4" />
                <p>{error}</p>
                <p className="text-sm text-gray-500 mt-2">Make sure Docker services are running</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Active Agents"
                    value={metrics?.activeAgents.value || "0/0"}
                    subLabel="Agents currently running"
                    trend={0}
                    icon={Activity}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Tasks Completed"
                    value={metrics?.tasksCompleted.value || 0}
                    subLabel="In this period"
                    trend={metrics?.tasksCompleted.trend}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
                <StatCard
                    title="Time Saved"
                    value={metrics?.timeSaved.value || "0h"}
                    subLabel="Est. human hours saved"
                    trend={15}
                    icon={Clock}
                    color="bg-purple-500"
                />
                <StatCard
                    title="Efficiency Score"
                    value={metrics?.efficiencyScore.value || "0%"}
                    subLabel="Weighted across agents"
                    trend={2.5}
                    icon={TrendingUp}
                    color="bg-orange-500"
                />
            </div>

            {/* Main Content Split */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: Live Operations (2/3) */}
                <div className="lg:col-span-2 bg-gray-900 rounded-xl border border-gray-800 flex flex-col h-[600px]">
                    {/* Tabs Header */}
                    <div className="flex items-center justify-between p-4 border-b border-gray-800">
                        <div className="flex gap-2">
                            {[
                                { id: 'activity', label: 'Recent Activity' },
                                { id: 'tasks', label: 'Open Tasks' },
                                { id: 'alerts', label: 'Alerts & Errors' }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={clsx(
                                        "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                                        activeTab === tab.id
                                            ? "bg-gray-800 text-white"
                                            : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                                    )}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                        <button className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
                            <Filter size={18} />
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                        {activeTab === 'activity' && (
                            <div className="space-y-4">
                                {metrics?.recentActivity.length === 0 ? (
                                    <div className="text-center text-gray-500 py-8">No recent activity</div>
                                ) : (
                                    metrics?.recentActivity.map((task: Task) => (
                                        <div key={task.id} className="flex items-center gap-4 p-3 hover:bg-gray-800/50 rounded-lg transition-colors group cursor-pointer">
                                            <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700 group-hover:border-gray-600">
                                                {task.status === 'completed' ? (
                                                    <CheckCircle size={18} className="text-green-400" />
                                                ) : task.status === 'failed' ? (
                                                    <AlertTriangle size={18} className="text-red-400" />
                                                ) : (
                                                    <Activity size={18} className="text-blue-400" />
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm text-white">
                                                    <span className="font-medium text-gray-200 capitalize">{task.action.replace('_', ' ')}</span>
                                                    <span className="text-gray-400 mx-2">•</span>
                                                    <span className="text-xs bg-gray-800 px-2 py-0.5 rounded text-gray-300">{task.agentId}</span>
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {new Date(task.createdAt).toLocaleString()}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <span className={clsx(
                                                    "text-xs px-2 py-1 rounded-full border",
                                                    task.status === 'completed' ? "bg-green-500/10 text-green-400 border-green-500/20" :
                                                        task.status === 'failed' ? "bg-red-500/10 text-red-400 border-red-500/20" :
                                                            "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                                )}>
                                                    {task.status}
                                                </span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                        {/* Placeholders for other tabs */}
                        {activeTab === 'tasks' && (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                <CheckCircle size={48} className="mb-4 opacity-20" />
                                <p>No open tasks requiring review</p>
                            </div>
                        )}
                        {activeTab === 'alerts' && (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                <CheckCircle size={48} className="mb-4 opacity-20" />
                                <p>System healthy. No active alerts.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: System Health (1/3) */}
                <div className="space-y-6">
                    {/* Agent Status */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4">Agent Status</h3>
                        <div className="space-y-4">
                            {[
                                { name: 'Sales Agent', status: 'Operational', latency: '120ms', error: '0.1%' },
                                { name: 'Support Agent', status: 'Operational', latency: '85ms', error: '0.0%' },
                                { name: 'Market Research', status: 'Degraded', latency: '450ms', error: '2.4%' },
                                { name: 'Legal Agent', status: 'Operational', latency: '200ms', error: '0.0%' },
                            ].map((agent, i) => (
                                <div key={i} className="flex items-center justify-between">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <div className={clsx(
                                                "w-2 h-2 rounded-full",
                                                agent.status === 'Operational' ? "bg-green-500" : "bg-yellow-500"
                                            )} />
                                            <p className="text-sm font-medium text-white">{agent.name}</p>
                                        </div>
                                        <p className="text-xs text-gray-500 pl-4">{agent.latency} latency</p>
                                    </div>
                                    <div className="text-right">
                                        <span className={clsx(
                                            "text-xs px-2 py-1 rounded-full border",
                                            agent.status === 'Operational'
                                                ? "bg-green-500/10 text-green-400 border-green-500/20"
                                                : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                                        )}>
                                            {agent.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Integrations Status */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4">Integrations</h3>
                        <div className="space-y-3">
                            {[
                                { name: 'Salesforce', status: 'Connected', time: 'Synced 2m ago' },
                                { name: 'Slack', status: 'Connected', time: 'Real-time' },
                                { name: 'Gmail', status: 'Connected', time: 'Synced 5m ago' },
                                { name: 'Notion', status: 'Error', time: 'Failed 1h ago' },
                            ].map((integration, i) => (
                                <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "w-2 h-2 rounded-full",
                                            integration.status === 'Connected' ? "bg-green-500" : "bg-red-500"
                                        )} />
                                        <span className="text-sm font-medium text-white">{integration.name}</span>
                                    </div>
                                    <span className="text-xs text-gray-500">{integration.time}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default DashboardHome;
