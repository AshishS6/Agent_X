import React, { useState, useEffect } from 'react';
import { TrendingUp, Globe, Search, Plus, Loader, AlertCircle, FileText, CheckCircle, XCircle, AlertTriangle, Eye, Download, Shield, CreditCard, ShoppingBag, Building, ExternalLink, Activity, ArrowRight, AlertOctagon, Info, Lock } from 'lucide-react';
import { AgentService, TaskService, Task, Agent } from '../services/api';
import { FEATURES } from '../config/features';
import TechStackCard from '../components/market-research/TechStackCard';
import SEOHealthCard from '../components/market-research/SEOHealthCard';
import BusinessMetadataV2 from '../components/market-research/BusinessMetadataV2';
import ReportDownloadButton from '../components/market-research/ReportDownloadButton';

const MarketResearchAgent = () => {
    const [agent, setAgent] = useState<Agent | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Pagination State
    const [page, setPage] = useState(1);
    const [limit] = useState(10);
    const [totalTasks, setTotalTasks] = useState(0);

    // Report View State
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    const [isReportModalOpen, setIsReportModalOpen] = useState(false);

    const handleViewReport = (task: Task) => {
        setSelectedTask(task);
        setIsReportModalOpen(true);
    };

    // Form State
    const [researchType, setResearchType] = useState('market_analysis');
    const [topic, setTopic] = useState('');
    const [filters, setFilters] = useState({
        date_range: 'last_month',
        geography: '',
        industry: ''
    });


    useEffect(() => {
        fetchAgentAndTasks();
    }, [page]); // Refresh when page changes

    const fetchAgentAndTasks = async () => {
        try {
            setLoading(true);
            const agents = await AgentService.getAll();
            const marketAgent = agents.find(a => a.type === 'market_research');

            if (marketAgent) {
                setAgent(marketAgent);
                const { tasks: agentTasks, total } = await TaskService.getAll({
                    agentId: marketAgent.id,
                    limit,
                    offset: (page - 1) * limit
                });
                // Filter out site scan tasks - they belong to Operations domain
                const marketResearchTasks = agentTasks.filter(
                    task => task.action !== 'site_scan' && task.action !== 'comprehensive_site_scan'
                );
                setTasks(marketResearchTasks);
                // Adjust total count (approximate, as we're filtering client-side)
                setTotalTasks(marketResearchTasks.length);
            } else {
                setError('Market Research Agent not found in the system.');
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load agent data');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTask = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agent) return;

        try {
            setSubmitting(true);

            const input = {
                topic,
                filters
            };

            await AgentService.execute('market_research', researchType, input);

            setIsModalOpen(false);
            setTopic('');
            
            // Refresh tasks using the same function that ensures proper filtering
            await fetchAgentAndTasks();
        } catch (err: any) {
            alert('Failed to create task: ' + err.message);
        } finally {
            setSubmitting(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-400';
            case 'processing': return 'text-blue-400';
            case 'failed': return 'text-red-400';
            default: return 'text-gray-400';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle size={16} />;
            case 'processing': return <Loader size={16} className="animate-spin" />;
            case 'failed': return <XCircle size={16} />;
            default: return <AlertCircle size={16} />;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 bg-red-900/20 border border-red-800 rounded-xl text-red-200 flex items-center gap-3">
                <AlertCircle size={24} />
                <p>{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Market Research Agent</h1>
                    <p className="text-gray-400">Competitor analysis, trend tracking, and market insights.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                    <Plus size={18} />
                    New Research Report
                </button>
            </div>

            {/* Stats / Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <TrendingUp className="text-green-400" size={20} />
                        Active Research
                    </h3>
                    <div className="space-y-3">
                        {tasks.filter(t => t.status === 'processing').length === 0 ? (
                            <p className="text-gray-500 text-sm">No active research tasks.</p>
                        ) : (
                            tasks.filter(t => t.status === 'processing').map(task => (
                                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-200">{task.input.topic || 'Unknown Topic'}</span>
                                    <span className="text-blue-400 text-sm font-medium flex items-center gap-1">
                                        <Loader size={12} className="animate-spin" /> Processing
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Globe className="text-blue-400" size={20} />
                        Recent Reports
                    </h3>
                    <div className="space-y-4">
                        {tasks.filter(t => t.status === 'completed').slice(0, 3).map(task => (
                            <div key={task.id} className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-blue-500/20 flex items-center justify-center text-blue-500">
                                    <FileText size={16} />
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-white">{task.input.topic || 'Research Report'}</p>
                                    <p className="text-xs text-gray-500">{new Date(task.createdAt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
                                </div>
                                <button
                                    onClick={() => handleViewReport(task)}
                                    className="text-xs text-blue-400 hover:text-blue-300"
                                >
                                    View
                                </button>
                            </div>
                        ))}
                        {tasks.filter(t => t.status === 'completed').length === 0 && (
                            <p className="text-gray-500 text-sm">No completed reports yet.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Task History */}
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Search className="text-purple-400" size={20} />
                        Research History
                    </h3>
                    <div className="text-sm text-gray-400">
                        Total: {totalTasks}
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-gray-800 text-gray-400 text-sm">
                                <th className="pb-3 pl-2">Topic</th>
                                <th className="pb-3">Type</th>
                                <th className="pb-3">Status</th>
                                <th className="pb-3">Date</th>
                                <th className="pb-3">Result</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {tasks.map(task => (
                                <tr key={task.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                                    <td className="py-3 pl-2 text-white font-medium">{task.input.topic || 'N/A'}</td>
                                    <td className="py-3 text-gray-400 capitalize">{task.action.replace('_', ' ')}</td>
                                    <td className={`py-3 ${getStatusColor(task.status)} flex items-center gap-2`}>
                                        {getStatusIcon(task.status)}
                                        <span className="capitalize">{task.status}</span>
                                    </td>
                                    <td className="py-3 text-gray-500">{new Date(task.createdAt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</td>
                                    <td className="py-3">
                                        {task.status === 'completed' && (
                                            <button
                                                onClick={() => handleViewReport(task)}
                                                className="text-blue-400 hover:text-blue-300"
                                            >
                                                View Report
                                            </button>
                                        )}
                                        {task.status === 'failed' && (
                                            <span className="text-red-400 text-xs truncate max-w-[150px] block" title={task.error}>
                                                {task.error}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {tasks.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="py-8 text-center text-gray-500">
                                        No research tasks found. Start a new research project!
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination Controls */}
                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-800">
                    <div className="text-sm text-gray-400">
                        Showing {tasks.length > 0 ? (page - 1) * limit + 1 : 0} to {Math.min(page * limit, totalTasks)} of {totalTasks} results
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage(p => p + 1)}
                            disabled={page * limit >= totalTasks}
                            className="px-3 py-1 bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {/* New Research Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-lg p-6 shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-white">New Research Project</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white">
                                <XCircle size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleCreateTask} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Research Type</label>
                                <select
                                    value={researchType}
                                    onChange={(e) => setResearchType(e.target.value)}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                >
                                    <option value="market_analysis">Market Analysis</option>
                                    <option value="competitor_research">Competitor Research</option>
                                    <option value="trend_monitoring">Trend Monitoring</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">
                                    {researchType === 'competitor_research' ? 'Competitor Name' : 'Topic / Keywords'}
                                </label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder={
                                        researchType === 'competitor_research' ? 'e.g. Acme Corp' : 'e.g. AI in Healthcare, Fintech trends, E-commerce growth'
                                    }
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                    required
                                />
                            </div>

                            {(
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Date Range</label>
                                        <select
                                            value={filters.date_range}
                                            onChange={(e) => setFilters({ ...filters, date_range: e.target.value })}
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        >
                                            <option value="last_week">Last Week</option>
                                            <option value="last_month">Last Month</option>
                                            <option value="last_year">Last Year</option>
                                            <option value="any_time">Any Time</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Geography</label>
                                        <input
                                            type="text"
                                            value={filters.geography}
                                            onChange={(e) => setFilters({ ...filters, geography: e.target.value })}
                                            placeholder="e.g. US, Europe"
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="pt-4 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                                >
                                    {submitting && <Loader size={16} className="animate-spin" />}
                                    Start Research
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Enhanced Report View Modal */}
            {isReportModalOpen && selectedTask && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl">
                        {/* Header */}
                        <div className="flex justify-between items-center p-6 border-b border-gray-800 bg-gradient-to-r from-blue-900/20 to-purple-900/20">
                            <div className="flex-1">
                                <h2 className="text-2xl font-bold text-white mb-1">{selectedTask.input?.topic || 'Research Report'}</h2>
                                <div className="flex items-center gap-4 text-sm text-gray-400">
                                    <span className="capitalize flex items-center gap-1">
                                        <Globe size={14} />
                                        {selectedTask.action.replace('_', ' ')}
                                    </span>
                                    <span>•</span>
                                    <span>{new Date(selectedTask.createdAt).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <ReportDownloadButton 
                                    taskId={selectedTask.id}
                                    taskStatus={selectedTask.status}
                                />
                                <button onClick={() => setIsReportModalOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                                    <XCircle size={28} />
                                </button>
                            </div>
                        </div>

                        {/* Content - Simple Market Research Report */}
                        <div className="flex-1 overflow-y-auto p-6">
                            {(() => {
                                // Parse task output for market research
                                let reportData: any = null;
                                try {
                                    const output = selectedTask.output;
                                    if (typeof output === 'string') {
                                        try {
                                            reportData = JSON.parse(output);
                                        } catch (e) {
                                            reportData = { text: output };
                                        }
                                    } else if (typeof output === 'object') {
                                        reportData = output;
                                    }
                                } catch (e) {
                                    console.error("Failed to parse report data", e);
                                }

                                const response = reportData?.response || reportData?.analysis || reportData?.text || reportData;
                                const content = typeof response === 'string' 
                                    ? response 
                                    : JSON.stringify(response, null, 2);

                                return (
                                    <div className="space-y-6">
                                        {/* Report Header */}
                                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                            <div className="flex items-center gap-3 mb-4">
                                                <FileText className="text-blue-400" size={24} />
                                                <div>
                                                    <h3 className="text-lg font-bold text-white">
                                                        {selectedTask.action.replace('_', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                                                    </h3>
                                                    <p className="text-sm text-gray-400">
                                                        {selectedTask.input?.topic || 'Market Research Report'}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-gray-400">
                                                <span>Status: <span className="text-green-400 capitalize">{selectedTask.status}</span></span>
                                                <span>•</span>
                                                <span>Completed: {new Date(selectedTask.updatedAt || selectedTask.createdAt).toLocaleString()}</span>
                                            </div>
                                        </div>

                                        {/* Report Content */}
                                        <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-6">
                                            <h4 className="text-md font-semibold text-white mb-4">Research Findings</h4>
                                            <div className="prose prose-invert max-w-none">
                                                {typeof content === 'string' && content.includes('\n') ? (
                                                    <div className="whitespace-pre-wrap text-gray-300 leading-relaxed">
                                                        {content}
                                                    </div>
                                                ) : (
                                                    <pre className="whitespace-pre-wrap font-mono text-sm text-gray-300 leading-relaxed overflow-x-auto">
                                                        {content}
                                                    </pre>
                                                )}
                                            </div>
                                        </div>

                                        {/* Additional Metadata if available */}
                                        {reportData && typeof reportData === 'object' && Object.keys(reportData).length > 1 && (
                                            <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-6">
                                                <h4 className="text-md font-semibold text-white mb-4">Additional Data</h4>
                                                <pre className="whitespace-pre-wrap font-mono text-xs text-gray-400 leading-relaxed overflow-x-auto">
                                                    {JSON.stringify(reportData, null, 2)}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                );
                            })()}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MarketResearchAgent;
