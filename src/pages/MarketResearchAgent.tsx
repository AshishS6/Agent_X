import React, { useState, useEffect } from 'react';
import { TrendingUp, Globe, Search, BarChart2, Plus, Loader, AlertCircle, FileText, CheckCircle, XCircle } from 'lucide-react';
import { AgentService, TaskService, Task, Agent } from '../services/api';

const MarketResearchAgent = () => {
    const [agent, setAgent] = useState<Agent | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
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
    }, []);

    const fetchAgentAndTasks = async () => {
        try {
            setLoading(true);
            const agents = await AgentService.getAll();
            const marketAgent = agents.find(a => a.type === 'market_research');

            if (marketAgent) {
                setAgent(marketAgent);
                const agentTasks = await TaskService.getAll({ agentId: marketAgent.id, limit: 10 });
                setTasks(agentTasks);
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
                filters,
                depth: 'comprehensive'
            };

            await AgentService.execute(agent.id, researchType, input);

            setIsModalOpen(false);
            setTopic('');
            // Refresh tasks
            const agentTasks = await TaskService.getAll({ agentId: agent.id, limit: 10 });
            setTasks(agentTasks);
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
                                    <p className="text-xs text-gray-500">{new Date(task.createdAt).toLocaleDateString()}</p>
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
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Search className="text-purple-400" size={20} />
                    Research History
                </h3>
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
                                    <td className="py-3 text-gray-500">{new Date(task.createdAt).toLocaleDateString()}</td>
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
                                    <option value="compliance_check">Compliance Check</option>
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
                                    placeholder={researchType === 'competitor_research' ? 'e.g. Acme Corp' : 'e.g. AI in Healthcare'}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                    required
                                />
                            </div>

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

            {/* Report View Modal */}
            {isReportModalOpen && selectedTask && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl">
                        <div className="flex justify-between items-center p-6 border-b border-gray-800">
                            <div>
                                <h2 className="text-xl font-bold text-white">{selectedTask.input.topic || 'Research Report'}</h2>
                                <p className="text-sm text-gray-400 capitalize">{selectedTask.action.replace('_', ' ')} • {new Date(selectedTask.createdAt).toLocaleString()}</p>
                            </div>
                            <button onClick={() => setIsReportModalOpen(false)} className="text-gray-400 hover:text-white">
                                <XCircle size={24} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="prose prose-invert max-w-none">
                                {/* Display structured output if available, otherwise raw response */}
                                {selectedTask.output ? (
                                    <>
                                        {/* Market Analysis View */}
                                        {selectedTask.output.analysis && (
                                            <div className="whitespace-pre-wrap font-mono text-sm text-gray-300">
                                                {typeof selectedTask.output.analysis === 'string'
                                                    ? selectedTask.output.analysis
                                                    : selectedTask.output.analysis.findings || JSON.stringify(selectedTask.output.analysis, null, 2)}
                                            </div>
                                        )}

                                        {/* Competitor Intelligence View */}
                                        {selectedTask.output.intelligence && (
                                            <div className="whitespace-pre-wrap font-mono text-sm text-gray-300">
                                                {selectedTask.output.intelligence.analysis || JSON.stringify(selectedTask.output.intelligence, null, 2)}
                                            </div>
                                        )}

                                        {/* Compliance View */}
                                        {selectedTask.output.compliance && (
                                            <div className="whitespace-pre-wrap font-mono text-sm text-gray-300">
                                                {selectedTask.output.compliance.findings || JSON.stringify(selectedTask.output.compliance, null, 2)}
                                            </div>
                                        )}

                                        {/* Trend View */}
                                        {selectedTask.output.trends && (
                                            <div className="whitespace-pre-wrap font-mono text-sm text-gray-300">
                                                {selectedTask.output.trends.analysis || JSON.stringify(selectedTask.output.trends, null, 2)}
                                            </div>
                                        )}

                                        {/* Fallback for generic response */}
                                        {selectedTask.output.response && !selectedTask.output.analysis && !selectedTask.output.intelligence && !selectedTask.output.compliance && !selectedTask.output.trends && (
                                            <div className="whitespace-pre-wrap font-mono text-sm text-gray-300">
                                                {selectedTask.output.response}
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <p className="text-gray-500 italic">No report content available.</p>
                                )}
                            </div>
                        </div>

                        <div className="p-4 border-t border-gray-800 flex justify-end">
                            <button
                                onClick={() => setIsReportModalOpen(false)}
                                className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MarketResearchAgent;
