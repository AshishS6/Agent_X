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
import { MonitoringService, SystemMetrics, Task, AgentService, Agent, IntegrationService, Integration } from '../services/api';
import { formatNumber, formatPercentage, formatDuration } from '../utils/formatting';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

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
                    {formatPercentage(Math.abs(trend), 1)}
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
    const [agents, setAgents] = useState<Agent[]>([]);
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [metricsData, agentsData, integrationsData] = await Promise.all([
                    MonitoringService.getMetrics(),
                    AgentService.getAll(),
                    IntegrationService.getAll().catch(() => []), // Gracefully handle integration fetch errors
                ]);
                setMetrics(metricsData);
                setAgents(agentsData);
                setIntegrations(integrationsData);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch data:', err);
                setError('Failed to load system metrics. Is the backend running?');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        // Poll every 5 seconds for real-time updates
        const interval = setInterval(fetchData, 5000);
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
                    value={formatNumber(metrics?.tasksCompleted.value || 0, { showThousands: true })}
                    subLabel="Est. human hours saved this period"
                    trend={metrics?.tasksCompleted.trend}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
                <StatCard
                    title="Time Saved"
                    value={formatDuration(metrics?.timeSaved.value || metrics?.timeSaved.hours)}
                    subLabel="Est. hours saved (5 min per completed task)"
                    trend={metrics?.tasksCompleted.trend}
                    icon={Clock}
                    color="bg-purple-500"
                />
                <StatCard
                    title="Efficiency Score"
                    value={formatPercentage(metrics?.efficiencyScore.value || metrics?.efficiencyScore.score, 1, false)}
                    subLabel="Completed vs total tasks"
                    trend={undefined}
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
                                    <EmptyState
                                        icon={Activity}
                                        title="No recent activity"
                                        description="System activity will appear here as agents process tasks."
                                        hint="Activity includes task executions, completions, and system events."
                                        variant="minimal"
                                    />
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
                            <EmptyState
                                icon={CheckCircle}
                                title="No open tasks requiring review"
                                description="All tasks are either completed or in progress. Check back later for tasks needing attention."
                                hint="Tasks requiring manual review or approval will appear here."
                            />
                        )}
                        {activeTab === 'alerts' && (
                            <EmptyState
                                icon={CheckCircle}
                                title="System healthy. No active alerts."
                                description="All systems are operating normally. You'll be notified if any issues arise."
                                hint="Alerts include agent failures, integration errors, and system warnings."
                            />
                        )}
                    </div>
                </div>

                {/* Right Column: System Health (1/3) */}
                <div className="space-y-6">
                    {/* Agent Status */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">Agent Status</h3>
                            {agents.length > 0 && agents.length < 10 && (
                                <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                                    {10 - agents.length} missing
                                </span>
                            )}
                        </div>
                        {agents.length === 0 ? (
                            <div className="text-center text-gray-500 py-4 text-sm">
                                No agents found
                            </div>
                        ) : (
                            <div className="space-y-4 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                                {agents.map((agent) => {
                                    // Map backend status to UI status
                                    const getStatusDisplay = (status: string) => {
                                        switch (status) {
                                            case 'active':
                                                return { label: 'Operational', color: 'green' };
                                            case 'paused':
                                                return { label: 'Degraded', color: 'yellow' };
                                            case 'error':
                                                return { label: 'Offline', color: 'red' };
                                            default:
                                                return { label: 'Unknown', color: 'gray' };
                                        }
                                    };

                                    const statusDisplay = getStatusDisplay(agent.status);

                                    return (
                                        <div key={agent.id} className="flex items-center justify-between">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <div className={clsx(
                                                        "w-2 h-2 rounded-full shrink-0",
                                                        statusDisplay.color === 'green' ? "bg-green-500" :
                                                            statusDisplay.color === 'yellow' ? "bg-yellow-500" :
                                                                "bg-red-500"
                                                    )} />
                                                    <p className="text-sm font-medium text-white truncate">{agent.name}</p>
                                                </div>
                                            </div>
                                            <div className="text-right shrink-0 ml-2">
                                                <span className={clsx(
                                                    "text-xs px-2 py-1 rounded-full border",
                                                    statusDisplay.color === 'green'
                                                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                                                        : statusDisplay.color === 'yellow'
                                                        ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                                                        : "bg-red-500/10 text-red-400 border-red-500/20"
                                                )}>
                                                    {statusDisplay.label}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })}
                                {/* Show degraded state explanation if any agents are degraded/offline */}
                                {agents.some(a => a.status === 'paused' || a.status === 'error') && (() => {
                                    const getStatusDisplay = (status: string) => {
                                        switch (status) {
                                            case 'active':
                                                return { label: 'Operational', color: 'green' };
                                            case 'paused':
                                                return { label: 'Degraded', color: 'yellow' };
                                            case 'error':
                                                return { label: 'Offline', color: 'red' };
                                            default:
                                                return { label: 'Unknown', color: 'gray' };
                                        }
                                    };
                                    return (
                                        <div className="mt-4 pt-4 border-t border-gray-800">
                                            {agents.filter(a => a.status === 'paused' || a.status === 'error').map((agent) => {
                                                const statusDisplay = getStatusDisplay(agent.status);
                                            return (
                                                <ErrorState
                                                    key={agent.id}
                                                    title={`${agent.name} - ${statusDisplay.label}`}
                                                    message={
                                                        agent.status === 'paused'
                                                            ? 'This agent has been paused and is not processing tasks.'
                                                            : 'This agent is experiencing errors and may not function correctly.'
                                                    }
                                                    failureReason={
                                                        agent.status === 'paused'
                                                            ? 'Agent was manually paused or automatically paused due to configuration issues.'
                                                            : 'Agent encountered errors during task execution. Check logs for details.'
                                                    }
                                                    impact={
                                                        agent.status === 'paused'
                                                            ? `Tasks for ${agent.name} will be queued but not processed until the agent is resumed.`
                                                            : `Tasks for ${agent.name} may fail or timeout. Some features may be unavailable.`
                                                    }
                                                    primaryAction={{
                                                        label: agent.status === 'paused' ? 'Resume Agent' : 'View Logs',
                                                        onClick: () => {
                                                            // TODO: Navigate to agent page or logs
                                                            console.log('Action for', agent.id);
                                                        },
                                                    }}
                                                    variant={agent.status === 'paused' ? 'degraded' : 'error'}
                                                />
                                            );
                                            })}
                                        </div>
                                    );
                                })()}
                            </div>
                        )}
                        {/* Show degraded state explanation if any agents are degraded/offline - moved outside scrollable area */}
                        {agents.some(a => a.status === 'paused' || a.status === 'error') && (() => {
                            const getStatusDisplay = (status: string) => {
                                switch (status) {
                                    case 'active':
                                        return { label: 'Operational', color: 'green' };
                                    case 'paused':
                                        return { label: 'Degraded', color: 'yellow' };
                                    case 'error':
                                        return { label: 'Offline', color: 'red' };
                                    default:
                                        return { label: 'Unknown', color: 'gray' };
                                }
                            };
                            return (
                                <div className="mt-4 pt-4 border-t border-gray-800 space-y-3">
                                    {agents.filter(a => a.status === 'paused' || a.status === 'error').slice(0, 1).map((agent) => {
                                        const statusDisplay = getStatusDisplay(agent.status);
                                    return (
                                        <ErrorState
                                            key={agent.id}
                                            title={`${agent.name} - ${statusDisplay.label}`}
                                            message={
                                                agent.status === 'paused'
                                                    ? 'This agent has been paused and is not processing tasks.'
                                                    : 'This agent is experiencing errors and may not function correctly.'
                                            }
                                            failureReason={
                                                agent.status === 'paused'
                                                    ? 'Agent was manually paused or automatically paused due to configuration issues.'
                                                    : 'Agent encountered errors during task execution. Check logs for details.'
                                            }
                                            impact={
                                                agent.status === 'paused'
                                                    ? `Tasks for ${agent.name} will be queued but not processed until the agent is resumed.`
                                                    : `Tasks for ${agent.name} may fail or timeout. Some features may be unavailable.`
                                            }
                                            primaryAction={{
                                                label: agent.status === 'paused' ? 'Resume Agent' : 'View Logs',
                                                onClick: () => {
                                                    // TODO: Navigate to agent page or logs
                                                    console.log('Action for', agent.id);
                                                },
                                            }}
                                            variant={agent.status === 'paused' ? 'degraded' : 'error'}
                                        />
                                    );
                                    })}
                                    {agents.filter(a => a.status === 'paused' || a.status === 'error').length > 1 && (
                                        <p className="text-xs text-gray-500 text-center">
                                            +{agents.filter(a => a.status === 'paused' || a.status === 'error').length - 1} more agents with issues
                                        </p>
                                    )}
                                </div>
                            );
                        })()}
                        {agents.length > 0 && agents.length < 10 && (
                            <div className="mt-4 pt-4 border-t border-gray-800">
                                <div className="flex items-start gap-2 text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
                                    <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-medium mb-1">Some agents not reporting status</p>
                                        <p className="text-yellow-300/70">
                                            Expected {10} agents, but only {agents.length} found. Check backend configuration.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Integrations Status */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4">Integrations</h3>
                        {integrations.length === 0 ? (
                            <div className="text-center text-gray-500 py-4 text-sm">
                                No integrations configured
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {integrations.slice(0, 4).map((integration) => {
                                    const getTimeDisplay = () => {
                                        if (!integration.lastSync) return 'Never synced';
                                        const lastSync = new Date(integration.lastSync);
                                        const now = new Date();
                                        const diffMs = now.getTime() - lastSync.getTime();
                                        const diffMins = Math.floor(diffMs / 60000);
                                        
                                        if (diffMins < 1) return 'Just now';
                                        if (diffMins < 60) return `${diffMins}m ago`;
                                        const diffHours = Math.floor(diffMins / 60);
                                        if (diffHours < 24) return `${diffHours}h ago`;
                                        const diffDays = Math.floor(diffHours / 24);
                                        return `${diffDays}d ago`;
                                    };

                                    return (
                                        <div key={integration.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div className={clsx(
                                                    "w-2 h-2 rounded-full",
                                                    integration.status === 'connected' ? "bg-green-500" : 
                                                        integration.status === 'error' ? "bg-red-500" : "bg-gray-500"
                                                )} />
                                                <span className="text-sm font-medium text-white">{integration.name}</span>
                                            </div>
                                            <span className={clsx(
                                                "text-xs",
                                                integration.status === 'error' ? "text-red-400" : "text-gray-500"
                                            )}>
                                                {integration.status === 'error' ? 'Failed' : getTimeDisplay()}
                                            </span>
                                        </div>
                                    );
                                })}
                                {integrations.length > 4 && (
                                    <div className="text-center pt-2">
                                        <button
                                            onClick={() => {
                                                // TODO: Navigate to integrations page
                                                window.location.href = '/data';
                                            }}
                                            className="text-xs text-blue-400 hover:text-blue-300"
                                        >
                                            View all {integrations.length} integrations →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                        {/* Show error state for failed integrations */}
                        {integrations.filter(i => i.status === 'error').length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-800">
                                {integrations.filter(i => i.status === 'error').slice(0, 1).map((integration) => (
                                    <ErrorState
                                        key={integration.id}
                                        title={`${integration.name} - Connection Failed`}
                                        message={`${integration.name} is not connected and may be experiencing issues.`}
                                        failureReason={
                                            integration.config?.error || 
                                            (integration.lastSync 
                                                ? `Last sync failed at ${new Date(integration.lastSync).toLocaleString()}`
                                                : 'Connection failed. Check your credentials and network connection.') || undefined
                                        }
                                        impact={
                                            integration.type === 'notion' 
                                                ? 'Blog content cannot be synced to Notion.'
                                                : integration.type === 'salesforce' || integration.type === 'hubspot'
                                                ? 'CRM data synchronization is paused.'
                                                : integration.type === 'slack'
                                                ? 'Notifications will not be sent to Slack.'
                                                : integration.type === 'gmail'
                                                ? 'Email automation features are unavailable.'
                                                : 'Some features may be limited.'
                                        }
                                        primaryAction={{
                                            label: 'Reconnect',
                                            onClick: () => {
                                                window.location.href = '/data';
                                            },
                                        }}
                                        variant="error"
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default DashboardHome;
