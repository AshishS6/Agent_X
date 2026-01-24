import { useState, useEffect } from 'react';
import {
    Search,
    Filter,
    Calendar,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Briefcase,
    LifeBuoy,
    Megaphone,
    Scale,
    Database,
    Info,
    Loader2,
    Clock,
    Activity
} from 'lucide-react';
import clsx from 'clsx';
import { MonitoringService, Task } from '../services/api';
import { EmptyState } from '../components/EmptyState';

// Helper to map agent type to icon
const getAgentIcon = (type: string) => {
    switch (type) {
        case 'sales': return Briefcase;
        case 'support': return LifeBuoy;
        case 'marketing': return Megaphone;
        case 'legal': return Scale;
        default: return Database;
    }
};

interface ActivityLog {
    id: string;
    type: 'task' | 'system' | 'workflow';
    status: 'success' | 'warning' | 'error' | 'pending' | 'processing';
    severity: 'info' | 'warning' | 'error';
    agent: string;
    agentIcon: any;
    message: string;
    timestamp: string;
    details: {
        input: string;
        output: string;
        raw: string;
    };
}

const ActivityLogs = () => {
    const [logs, setLogs] = useState<ActivityLog[]>([]);
    const [selectedLog, setSelectedLog] = useState<ActivityLog | null>(null);
    const [filterType, setFilterType] = useState('All');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLogs();
        // Poll for updates every 10 seconds
        const interval = setInterval(fetchLogs, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchLogs = async () => {
        try {
            const tasks = await MonitoringService.getActivity(50);
            const mappedLogs = tasks.map(mapTaskToLog);
            setLogs(mappedLogs);
            setLoading(false);
        } catch (err) {
            console.error('Failed to fetch activity logs:', err);
            setLoading(false);
        }
    };

    const mapTaskToLog = (task: Task): ActivityLog => {
        const isError = task.status === 'failed';

        return {
            id: task.id,
            type: 'task',
            status: task.status === 'failed' ? 'error' : task.status === 'completed' ? 'success' : 'processing',
            severity: isError ? 'error' : 'info',
            agent: task.agentId ? 'Agent Task' : 'System', // We might want to fetch agent name if possible, or use type
            agentIcon: getAgentIcon('sales'), // Defaulting to sales for now, ideally we get agent type
            message: `${task.action} - ${task.status}`,
            timestamp: task.createdAt ? new Date(task.createdAt).toLocaleString() : 'Unknown',
            details: {
                input: JSON.stringify(task.input, null, 2),
                output: task.output ? JSON.stringify(task.output, null, 2) : 'No output',
                raw: JSON.stringify(task)
            }
        };
    };

    const filteredLogs = filterType === 'All'
        ? logs
        : logs.filter(log => log.type.toLowerCase() === filterType.toLowerCase());

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Activity & Logs</h1>
                    <p className="text-gray-400 text-sm">Audit trail of all agent and system activities</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-4 py-1.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-64"
                        />
                    </div>
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700 text-sm">
                        <Calendar size={14} />
                        <span>Last 24 Hours</span>
                    </button>
                    <button className="p-2 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700">
                        <Filter size={16} />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 min-h-0">
                {/* Activity List (Left 2/3) */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Filter Chips */}
                    <div className="flex items-center gap-2 mb-4">
                        {['All', 'Tasks', 'Workflows', 'System'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilterType(f)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-full text-xs font-medium transition-colors border",
                                    filterType === f
                                        ? "bg-blue-600/10 text-blue-400 border-blue-600/20"
                                        : "bg-gray-800/50 text-gray-400 border-gray-700 hover:bg-gray-800 hover:text-gray-300"
                                )}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-800">
                        <div className="col-span-3">Time</div>
                        <div className="col-span-4">Activity</div>
                        <div className="col-span-3">Agent</div>
                        <div className="col-span-2 text-right">Status</div>
                    </div>

                    {/* List */}
                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        {filteredLogs.map((log) => (
                            <div
                                key={log.id}
                                onClick={() => setSelectedLog(log)}
                                className={clsx(
                                    "grid grid-cols-12 gap-4 px-4 py-3 border-b border-gray-800/50 items-center cursor-pointer transition-colors",
                                    selectedLog?.id === log.id
                                        ? "bg-blue-600/5 border-blue-500/20"
                                        : "hover:bg-gray-800/30"
                                )}
                            >
                                <div className="col-span-3 text-xs text-gray-400 font-mono">{log.timestamp}</div>
                                <div className="col-span-4 text-sm text-gray-200 font-medium truncate">{log.message}</div>
                                <div className="col-span-3 flex items-center gap-2">
                                    <div className="w-6 h-6 rounded bg-gray-800 flex items-center justify-center text-gray-400">
                                        <log.agentIcon size={12} />
                                    </div>
                                    <span className="text-xs text-gray-400">{log.agent}</span>
                                </div>
                                <div className="col-span-2 flex justify-end">
                                    <span className={clsx(
                                        "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border flex items-center gap-1",
                                        log.status === 'success' && "bg-green-500/10 text-green-400 border-green-500/20",
                                        log.status === 'warning' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                                        log.status === 'error' && "bg-red-500/10 text-red-400 border-red-500/20",
                                        (log.status === 'pending' || log.status === 'processing') && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                    )}>
                                        {log.status === 'success' && <CheckCircle2 size={10} />}
                                        {log.status === 'warning' && <AlertTriangle size={10} />}
                                        {log.status === 'error' && <XCircle size={10} />}
                                        {(log.status === 'pending' || log.status === 'processing') && <Clock size={10} />}
                                        {log.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {filteredLogs.length === 0 && (
                            <EmptyState
                                icon={Activity}
                                title="No activity logs found"
                                description={
                                    filterType === 'All'
                                        ? "Activity logs will appear here as agents process tasks and workflows execute."
                                        : `No ${filterType.toLowerCase()} logs found. Try adjusting your filters or time range.`
                                }
                                hint="Activity includes task executions, workflow runs, and system events."
                                variant="minimal"
                            />
                        )}
                    </div>
                </div>

                {/* Log Detail Drawer (Right 1/3) */}
                {selectedLog ? (
                    <div className="w-96 bg-gray-900 border border-gray-800 rounded-xl flex flex-col overflow-hidden animate-fade-in">
                        <div className="p-4 border-b border-gray-800 bg-gray-800/30">
                            <div className="flex items-center gap-2 mb-2">
                                <span className={clsx(
                                    "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border",
                                    selectedLog.status === 'success' && "bg-green-500/10 text-green-400 border-green-500/20",
                                    selectedLog.status === 'warning' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                                    selectedLog.status === 'error' && "bg-red-500/10 text-red-400 border-red-500/20",
                                    (selectedLog.status === 'pending' || selectedLog.status === 'processing') && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                )}>
                                    {selectedLog.status}
                                </span>
                                <span className="text-xs text-gray-500 font-mono">{selectedLog.timestamp}</span>
                            </div>
                            <h2 className="font-semibold text-white mb-1">{selectedLog.message}</h2>
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                                <selectedLog.agentIcon size={12} />
                                <span>{selectedLog.agent}</span>
                                <span>•</span>
                                <span className="capitalize">{selectedLog.type}</span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
                            <div>
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Context</h3>
                                <div className="space-y-3">
                                    <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                                        <div className="text-xs text-gray-400 mb-1">Input</div>
                                        <div className="text-sm text-gray-200 break-words whitespace-pre-wrap">{selectedLog.details.input}</div>
                                    </div>
                                    <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                                        <div className="text-xs text-gray-400 mb-1">Output</div>
                                        <div className="text-sm text-gray-200 break-words whitespace-pre-wrap">{selectedLog.details.output}</div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Raw Log</h3>
                                <pre className="bg-gray-950 p-3 rounded-lg border border-gray-800 text-xs text-gray-400 font-mono overflow-x-auto custom-scrollbar">
                                    {selectedLog.details.raw}
                                </pre>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="w-96 bg-gray-900/50 border border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500">
                        <Info size={48} className="mb-4 opacity-20" />
                        <p className="text-sm">Select a log entry to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ActivityLogs;
