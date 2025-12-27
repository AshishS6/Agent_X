import React, { useState, useEffect } from 'react';
import { TrendingUp, Globe, Search, Plus, Loader, AlertCircle, FileText, CheckCircle, XCircle, AlertTriangle, Eye, Download, Shield, CreditCard, ShoppingBag, Building, ExternalLink } from 'lucide-react';
import { AgentService, TaskService, Task, Agent } from '../services/api';

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
    const [activeTab, setActiveTab] = useState('compliance');
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);

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
    // Web Crawler specific state
    const [crawlerConfig, setCrawlerConfig] = useState({
        max_pages: 0,
        depth: 1
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
                setTasks(agentTasks);
                setTotalTasks(total);
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
                depth: 'comprehensive',
                // Add crawler config for web_crawler type
                ...(researchType === 'web_crawler' && {
                    max_pages: crawlerConfig.max_pages,
                    crawl_depth: crawlerConfig.depth
                })
            };

            await AgentService.execute(agent.id, researchType, input);

            setIsModalOpen(false);
            setTopic('');
            setCrawlerConfig({ max_pages: 5, depth: 1 }); // Reset crawler config
            // Refresh tasks
            const { tasks: agentTasks, total } = await TaskService.getAll({
                agentId: agent.id,
                limit,
                offset: (page - 1) * limit
            });
            setTasks(agentTasks);
            setTotalTasks(total);
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
                                    <option value="site_scan">Site Scan (Comprehensive)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">
                                    {researchType === 'competitor_research' ? 'Competitor Name' :
                                        (researchType === 'web_crawler' || researchType === 'site_scan') ? 'Target URL' : 'Topic / Keywords'}
                                </label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder={
                                        researchType === 'competitor_research' ? 'e.g. Acme Corp' :
                                            (researchType === 'web_crawler' || researchType === 'site_scan') ? 'https://example.com' : 'e.g. AI in Healthcare'
                                    }
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                    required
                                />
                            </div>

                            {researchType === 'web_crawler' && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Keywords to Track</label>
                                        <input
                                            type="text"
                                            value={filters.industry}
                                            onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
                                            placeholder="e.g. pricing, launch, error"
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Max Pages</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={crawlerConfig.max_pages}
                                                onChange={(e) => {
                                                    const val = parseInt(e.target.value);
                                                    setCrawlerConfig({ ...crawlerConfig, max_pages: isNaN(val) ? 0 : val });
                                                }}
                                                placeholder="0 for unlimited"
                                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            />
                                            <p className="text-xs text-gray-500 mt-1">0 = crawl all pages in domain</p>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Crawl Depth</label>
                                            <input
                                                type="number"
                                                min="1"
                                                max="3"
                                                value={crawlerConfig.depth}
                                                onChange={(e) => setCrawlerConfig({ ...crawlerConfig, depth: parseInt(e.target.value) || 1 })}
                                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            />
                                            <p className="text-xs text-gray-500 mt-1">1 = page only, 2+ = follow links</p>
                                        </div>
                                    </div>
                                </>
                            )}

                            {researchType !== 'web_crawler' && (
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
                                <h2 className="text-2xl font-bold text-white mb-1">{selectedTask.input.topic || 'Research Report'}</h2>
                                <div className="flex items-center gap-4 text-sm text-gray-400">
                                    <span className="capitalize flex items-center gap-1">
                                        <Globe size={14} />
                                        {selectedTask.action.replace('_', ' ')}
                                    </span>
                                    <span>•</span>
                                    <span>{new Date(selectedTask.createdAt).toLocaleString()}</span>
                                </div>
                            </div>
                            <button onClick={() => setIsReportModalOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                                <XCircle size={28} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-hidden flex flex-col">
                            {(() => {
                                // Try to parse as JSON first
                                let crawlData: any = null;
                                try {
                                    let response = selectedTask.output?.response;

                                    // Handle string response
                                    if (typeof response === 'string') {
                                        // 1. Strip Markdown code blocks
                                        response = response.replace(/```json\n|```/g, '').trim();

                                        // 2. Try parsing entire string
                                        try {
                                            crawlData = JSON.parse(response);
                                        } catch (e) {
                                            // 3. Fallback: try to find JSON object if mixed with text
                                            const jsonMatch = response.match(/\{[\s\S]*\}/);
                                            if (jsonMatch) {
                                                crawlData = JSON.parse(jsonMatch[0]);
                                            }
                                        }
                                    } else if (typeof response === 'object') {
                                        crawlData = response;
                                    }
                                } catch (e) {
                                    console.error("Failed to parse crawl data", e);
                                }

                                if (!crawlData || (!crawlData.comprehensive_site_scan && !crawlData.compliance_checks && !crawlData.base_url)) {
                                    // Fallback for non-crawler tasks or failed parsing
                                    const output = selectedTask.output;
                                    const content = output?.response || output?.analysis || JSON.stringify(output, null, 2);
                                    return (
                                        <div className="p-6 overflow-y-auto">
                                            <div className="bg-gray-800/30 rounded-lg p-6">
                                                <pre className="whitespace-pre-wrap font-mono text-sm text-gray-300 leading-relaxed">
                                                    {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                                                </pre>
                                            </div>
                                        </div>
                                    );
                                }

                                // Normalize data if needed
                                const siteScan = crawlData.comprehensive_site_scan;
                                const displayData = siteScan || crawlData;

                                // Render Tabbed Interface for Crawler Results
                                return (
                                    <div className="flex flex-col h-full">
                                        {/* Tabs */}
                                        <div className="flex border-b border-gray-800 px-6">
                                            {[
                                                { id: 'compliance', label: 'Compliance checks', icon: Shield },
                                                { id: 'policy', label: 'Policy details', icon: FileText },
                                                { id: 'mcc', label: 'MCC codes', icon: CreditCard },
                                                { id: 'product', label: 'Product details', icon: ShoppingBag },
                                                { id: 'business', label: 'Business details', icon: Building },
                                            ].map((tab) => (
                                                <button
                                                    key={tab.id}
                                                    onClick={() => setActiveTab(tab.id)}
                                                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === tab.id
                                                        ? 'border-blue-500 text-blue-400'
                                                        : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700'
                                                        }`}
                                                >
                                                    <tab.icon size={16} />
                                                    {tab.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Tab Content */}
                                        <div className="flex-1 overflow-y-auto p-6 bg-gray-900/50">
                                            {activeTab === 'compliance' && (
                                                <div className="space-y-6">
                                                    {/* NEW: Comprehensive Site Scan View */}
                                                    {siteScan ? (
                                                        <div className="space-y-6">
                                                            {siteScan.error && (
                                                                <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-2">
                                                                    <div className="flex items-center gap-3 text-red-500">
                                                                        <AlertCircle size={18} />
                                                                        <div className="text-sm">
                                                                            <span className="font-bold">Scan Error: </span>
                                                                            {siteScan.error}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* General Compliance Status */}
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                                {/* General */}
                                                                <div className={`p-6 rounded-lg border ${siteScan.compliance?.general?.pass
                                                                    ? 'bg-green-500/10 border-green-500/30'
                                                                    : 'bg-red-500/10 border-red-500/30'
                                                                    }`}>
                                                                    <div className="flex items-center gap-3 mb-4">
                                                                        {siteScan.compliance?.general?.pass
                                                                            ? <CheckCircle className="text-green-500" size={24} />
                                                                            : <AlertTriangle className="text-red-500" size={24} />
                                                                        }
                                                                        <h3 className="text-lg font-bold text-white">General Compliance</h3>
                                                                    </div>

                                                                    {/* Alerts */}
                                                                    {siteScan.compliance?.general?.alerts?.length > 0 && (
                                                                        <div className="space-y-3 mb-4">
                                                                            {siteScan.compliance.general.alerts.map((alert: any, idx: number) => (
                                                                                <div key={idx} className="bg-black/30 p-3 rounded border border-red-500/20">
                                                                                    <div className="flex gap-2 text-red-300 font-medium mb-1">
                                                                                        <AlertTriangle size={14} className="mt-0.5" />
                                                                                        {alert.code}: {alert.type}
                                                                                    </div>
                                                                                    <p className="text-sm text-gray-400">{alert.description}</p>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}

                                                                    {/* Actions Needed */}
                                                                    {siteScan.compliance?.general?.actions_needed?.length > 0 && (
                                                                        <div>
                                                                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Actions Needed:</h4>
                                                                            <ul className="space-y-2">
                                                                                {siteScan.compliance.general.actions_needed.map((action: any, idx: number) => (
                                                                                    <li key={idx} className="text-sm text-gray-400 flex gap-2">
                                                                                        <span className="text-blue-400">•</span>
                                                                                        <span>{action.description}</span>
                                                                                    </li>
                                                                                ))}
                                                                            </ul>
                                                                        </div>
                                                                    )}

                                                                    {siteScan.compliance?.general?.pass && !siteScan.compliance?.general?.alerts?.length && (
                                                                        <div className="space-y-3">
                                                                            <p className="text-green-400 font-medium pb-2 border-b border-green-500/20">All general compliance checks passed.</p>
                                                                            <ul className="space-y-2 text-sm text-gray-300">
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>Website is live and accessible (Status: 200)</span>
                                                                                </li>
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>SSL Certificate is valid (HTTPS)</span>
                                                                                </li>
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>Domain vintage meets requirements</span>
                                                                                </li>
                                                                            </ul>
                                                                        </div>
                                                                    )}
                                                                </div>

                                                                {/* Payment Terms */}
                                                                <div className={`p-6 rounded-lg border ${siteScan.compliance?.payment_terms?.pass
                                                                    ? 'bg-green-500/10 border-green-500/30'
                                                                    : 'bg-yellow-500/10 border-yellow-500/30'
                                                                    }`}>
                                                                    <div className="flex items-center gap-3 mb-4">
                                                                        {siteScan.compliance?.payment_terms?.pass
                                                                            ? <CheckCircle className="text-green-500" size={24} />
                                                                            : <AlertTriangle className="text-yellow-500" size={24} />
                                                                        }
                                                                        <h3 className="text-lg font-bold text-white">Payment Terms</h3>
                                                                    </div>

                                                                    {siteScan.compliance?.payment_terms?.pass ? (
                                                                        <div className="space-y-3">
                                                                            <p className="text-green-400 font-medium pb-2 border-b border-green-500/20">Payment policies validate successfully.</p>
                                                                            <ul className="space-y-2 text-sm text-gray-300">
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>Refund/Return Policy detected</span>
                                                                                </li>
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>Terms & Conditions detected</span>
                                                                                </li>
                                                                                <li className="flex items-center gap-2">
                                                                                    <CheckCircle size={14} className="text-green-400" />
                                                                                    <span>Privacy Policy detected</span>
                                                                                </li>
                                                                            </ul>
                                                                        </div>
                                                                    ) : (
                                                                        <p className="text-yellow-400">Review payment terms for potential issues.</p>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        // OLD: Legacy Compliance View
                                                        <div className="space-y-6">
                                                            {/* Status Cards */}
                                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                                {/* Liveness */}
                                                                <div className={`p-4 rounded-lg border ${crawlData.compliance_checks?.liveness?.status === 'pass'
                                                                    ? 'bg-green-500/10 border-green-500/30'
                                                                    : 'bg-red-500/10 border-red-500/30'
                                                                    }`}>
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        {crawlData.compliance_checks?.liveness?.status === 'pass'
                                                                            ? <CheckCircle className="text-green-500" size={20} />
                                                                            : <AlertTriangle className="text-red-500" size={20} />
                                                                        }
                                                                        <h3 className="font-semibold text-white">Liveness</h3>
                                                                    </div>
                                                                    <p className="text-sm text-gray-300">{crawlData.compliance_checks?.liveness?.message || 'Status unknown'}</p>
                                                                </div>

                                                                {/* Redirection */}
                                                                <div className={`p-4 rounded-lg border ${crawlData.compliance_checks?.redirection?.status === 'pass'
                                                                    ? 'bg-green-500/10 border-green-500/30'
                                                                    : 'bg-yellow-500/10 border-yellow-500/30'
                                                                    }`}>
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        {crawlData.compliance_checks?.redirection?.status === 'pass'
                                                                            ? <CheckCircle className="text-green-500" size={20} />
                                                                            : <AlertTriangle className="text-yellow-500" size={20} />
                                                                        }
                                                                        <h3 className="font-semibold text-white">Redirection</h3>
                                                                    </div>
                                                                    <p className="text-sm text-gray-300">{crawlData.compliance_checks?.redirection?.message || 'No redirects detected'}</p>
                                                                </div>

                                                                {/* Vintage */}
                                                                <div className={`p-4 rounded-lg border ${crawlData.compliance_checks?.vintage?.status === 'pass'
                                                                    ? 'bg-green-500/10 border-green-500/30'
                                                                    : 'bg-red-500/10 border-red-500/30'
                                                                    }`}>
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        {crawlData.compliance_checks?.vintage?.status === 'pass'
                                                                            ? <CheckCircle className="text-green-500" size={20} />
                                                                            : <AlertTriangle className="text-red-500" size={20} />
                                                                        }
                                                                        <h3 className="font-semibold text-white">Vintage of Website</h3>
                                                                    </div>
                                                                    <p className="text-sm text-gray-300">{crawlData.compliance_checks?.vintage?.message || 'Age unknown'}</p>
                                                                </div>
                                                            </div>

                                                            {/* Details Tables */}
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                                <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
                                                                    <h3 className="text-lg font-semibold text-white mb-4">URL & Domain details</h3>
                                                                    <div className="space-y-3 text-sm">
                                                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                                                            <span className="text-gray-400">Link</span>
                                                                            <a href={crawlData.url} target="_blank" className="text-blue-400 hover:underline truncate max-w-[200px]">{crawlData.url}</a>
                                                                        </div>
                                                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                                                            <span className="text-gray-400">Domain Provider</span>
                                                                            <span className="text-white">{crawlData.compliance_checks?.url_details?.domain_provider || 'Unknown'}</span>
                                                                        </div>
                                                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                                                            <span className="text-gray-400">Registered On</span>
                                                                            <span className="text-white">{crawlData.compliance_checks?.url_details?.domain_registered_on || 'Unknown'}</span>
                                                                        </div>
                                                                        <div className="flex justify-between py-2">
                                                                            <span className="text-gray-400">Vintage Days</span>
                                                                            <span className="text-white">{crawlData.compliance_checks?.url_details?.vintage_days || 'N/A'}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
                                                                    <h3 className="text-lg font-semibold text-white mb-4">SSL Certificate</h3>
                                                                    <div className="space-y-3 text-sm">
                                                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                                                            <span className="text-gray-400">Status</span>
                                                                            <span className={crawlData.compliance_checks?.ssl_certificate?.valid ? "text-green-400" : "text-red-400"}>
                                                                                {crawlData.compliance_checks?.ssl_certificate?.valid ? "Valid" : "Invalid"}
                                                                            </span>
                                                                        </div>
                                                                        <div className="flex justify-between py-2 border-b border-gray-700">
                                                                            <span className="text-gray-400">Hostname</span>
                                                                            <span className="text-white">{crawlData.compliance_checks?.ssl_certificate?.server_hostname || 'N/A'}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {activeTab === 'policy' && (
                                                <div className="space-y-6">
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                        {Object.entries(displayData.policy_details || {}).map(([key, value]: [string, any]) => (
                                                            <div key={key} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 flex flex-col justify-between">
                                                                <div>
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        {value.found
                                                                            ? <CheckCircle className="text-green-500" size={18} />
                                                                            : <XCircle className="text-gray-500" size={18} />
                                                                        }
                                                                        <h4 className="font-medium text-white capitalize">{key.replace(/_/g, ' ')}</h4>
                                                                    </div>
                                                                    <p className="text-xs text-gray-400 mb-3">{value.status || 'Not found'}</p>
                                                                </div>
                                                                {value.found && value.url && (
                                                                    <button
                                                                        onClick={() => {
                                                                            setPreviewUrl(value.url);
                                                                            setIsPreviewOpen(true);
                                                                        }}
                                                                        className="text-xs bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 py-1.5 px-3 rounded border border-blue-500/30 flex items-center justify-center gap-1 transition-colors"
                                                                    >
                                                                        <Eye size={12} /> Preview
                                                                    </button>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {activeTab === 'mcc' && (
                                                <div className="space-y-6">
                                                    {/* MCC Selection */}
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                        {[displayData.mcc_codes?.primary_mcc, displayData.mcc_codes?.secondary_mcc].filter(Boolean).map((mcc: any, idx: number) => (
                                                            <div key={idx} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 relative overflow-hidden">
                                                                <div className="flex items-start gap-3">
                                                                    <div className="mt-1">
                                                                        <CheckCircle className="text-green-500" size={20} />
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="font-bold text-white mb-1">MCC Number: {mcc.mcc_code}</h4>
                                                                        <p className="text-sm text-gray-400">Found MCC code is matching with website content.</p>
                                                                        <div className="mt-2 text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded inline-block">
                                                                            {mcc.confidence}% Confidence
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Detailed Description */}
                                                    {displayData.mcc_codes?.primary_mcc && (
                                                        <div className="bg-white text-gray-900 rounded-lg p-6 border border-gray-200">
                                                            <div className="flex items-center gap-3 mb-4">
                                                                <div className="w-4 h-4 rounded-full border-[5px] border-blue-600"></div>
                                                                <h3 className="text-lg font-bold">{displayData.mcc_codes.primary_mcc.mcc_code} - {displayData.mcc_codes.primary_mcc.description}</h3>
                                                            </div>

                                                            <div className="grid grid-cols-[150px_1fr] gap-y-4 text-sm">
                                                                <div className="text-gray-500 font-medium">Category</div>
                                                                <div className="font-medium">{displayData.mcc_codes.primary_mcc.category || 'Retail'}</div>

                                                                <div className="text-gray-500 font-medium">Subcategory</div>
                                                                <div className="font-medium">{displayData.mcc_codes.primary_mcc.subcategory || 'General'}</div>

                                                                <div className="text-gray-500 font-medium">Description</div>
                                                                <div className="text-gray-700">
                                                                    Merchants classified with this MCC sell {displayData.mcc_codes.primary_mcc.description.toLowerCase()}.
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Feedback Section */}
                                                    <div className="bg-blue-50/5 border border-blue-100/10 rounded-lg p-4">
                                                        <div className="flex items-center gap-2 mb-3">
                                                            <input type="radio" name="mcc_feedback" id="incorrect" className="text-blue-600" />
                                                            <label htmlFor="incorrect" className="text-sm text-gray-300">Above MCCs are incorrect, please select the correct category and subcategory.</label>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {activeTab === 'product' && (
                                                <div className="space-y-6">
                                                    {/* Summary Cards */}
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5 flex items-start gap-4">
                                                            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 flex-shrink-0">
                                                                <CreditCard size={20} />
                                                            </div>
                                                            <div>
                                                                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pricing Model</label>
                                                                <p className="text-lg font-bold text-white mt-1">{displayData.product_details?.pricing_model || 'Not identified'}</p>
                                                            </div>
                                                        </div>
                                                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5 flex items-start gap-4">
                                                            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 flex-shrink-0">
                                                                <Building size={20} />
                                                            </div>
                                                            <div>
                                                                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Target Audience</label>
                                                                <p className="text-lg font-bold text-white mt-1">{displayData.product_details?.target_audience || 'General'}</p>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Extracted Product List */}
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg overflow-hidden">
                                                        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
                                                            <h3 className="font-bold text-white flex items-center gap-2">
                                                                <ShoppingBag size={18} className="text-blue-400" />
                                                                Products & Services
                                                            </h3>
                                                            <div className="flex gap-2">
                                                                {displayData.product_details?.source_pages?.product_page && (
                                                                    <button
                                                                        onClick={() => { setPreviewUrl(displayData.product_details.source_pages.product_page); setIsPreviewOpen(true); }}
                                                                        className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded flex items-center gap-1 transition-colors"
                                                                    >
                                                                        <Eye size={10} /> Product Page
                                                                    </button>
                                                                )}
                                                                {displayData.product_details?.source_pages?.pricing_page && (
                                                                    <button
                                                                        onClick={() => { setPreviewUrl(displayData.product_details.source_pages.pricing_page); setIsPreviewOpen(true); }}
                                                                        className="text-[10px] px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded flex items-center gap-1 transition-colors"
                                                                    >
                                                                        <Eye size={10} /> Pricing Page
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {displayData.product_details?.extracted_products?.length > 0 ? (
                                                            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                {displayData.product_details.extracted_products.map((product: any, idx: number) => (
                                                                    <div key={idx} className="bg-gray-900/40 border border-gray-700/50 rounded-lg p-4 hover:border-blue-500/30 transition-colors">
                                                                        <div className="flex justify-between items-start mb-2">
                                                                            <h4 className="font-bold text-blue-400">{product.name}</h4>
                                                                            {product.price_if_found && (
                                                                                <span className="text-xs font-bold text-green-400 bg-green-400/10 px-2 py-0.5 rounded">
                                                                                    {product.price_if_found}
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                        <p className="text-sm text-gray-400 leading-relaxed">
                                                                            {product.brief_description}
                                                                        </p>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (
                                                            <div className="p-12 text-center">
                                                                <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-700">
                                                                    <Search size={24} className="text-gray-600" />
                                                                </div>
                                                                <p className="text-gray-500">No specific products were extracted from the main pages.</p>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Audit Indicators */}
                                                    <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-6">
                                                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Quick Audit Analysis</h4>
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                            {[
                                                                { label: 'Products', val: displayData.product_details?.has_products },
                                                                { label: 'Pricing', val: displayData.product_details?.has_pricing },
                                                                { label: 'Checkout', val: displayData.product_details?.has_cart },
                                                                { label: 'E-commerce', val: displayData.product_details?.ecommerce_platform }
                                                            ].map((item, idx) => (
                                                                <div key={idx} className="flex flex-col gap-1">
                                                                    <span className="text-[10px] text-gray-500 uppercase tracking-tighter">{item.label}</span>
                                                                    <div className="flex items-center gap-1.5">
                                                                        {item.val ? <CheckCircle size={14} className="text-green-500" /> : <XCircle size={14} className="text-gray-600" />}
                                                                        <span className={`text-xs font-medium ${item.val ? 'text-gray-300' : 'text-gray-500'}`}>
                                                                            {item.val ? 'Detected' : 'Not Found'}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {activeTab === 'business' && (
                                                <div className="space-y-6">
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                                            <Building className="text-blue-400" size={20} />
                                                            Business Information
                                                        </h3>

                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                            <div className="space-y-6">
                                                                <div>
                                                                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Business Name</label>
                                                                    <p className="text-xl font-bold text-white mt-1">{displayData.business_details?.extracted_business_name || 'Not found'}</p>
                                                                </div>

                                                                <div>
                                                                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Company Summary</label>
                                                                    <p className="text-sm text-gray-300 mt-2 leading-relaxed bg-black/20 p-4 rounded-lg border border-gray-700/50">
                                                                        {displayData.business_details?.company_summary || 'No summary available.'}
                                                                    </p>
                                                                </div>

                                                                <div>
                                                                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Mission & Vision</label>
                                                                    <p className="text-sm italic text-gray-400 mt-2 border-l-2 border-blue-500/50 pl-4 py-1">
                                                                        {displayData.business_details?.mission_vision || 'Mission/Vision statement not found.'}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-6">
                                                                <div>
                                                                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Key Offerings</label>
                                                                    <p className="text-sm text-white mt-2 bg-blue-500/10 p-4 rounded-lg border border-blue-500/20">
                                                                        {displayData.business_details?.key_offerings || 'Product/Service details not found.'}
                                                                    </p>
                                                                </div>

                                                                <div>
                                                                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 block">Contact Information</label>
                                                                    <div className="space-y-3">
                                                                        <div className="flex items-center gap-3 text-sm">
                                                                            <div className="w-8 h-8 rounded bg-gray-700/50 flex items-center justify-center text-gray-400">
                                                                                <Globe size={14} />
                                                                            </div>
                                                                            <span className="text-gray-300">{displayData.business_details?.contact_info?.email || 'Email not found'}</span>
                                                                        </div>
                                                                        <div className="flex items-center gap-3 text-sm">
                                                                            <div className="w-8 h-8 rounded bg-gray-700/50 flex items-center justify-center text-gray-400">
                                                                                <Plus size={14} />
                                                                            </div>
                                                                            <span className="text-gray-300">{displayData.business_details?.contact_info?.phone || 'Phone not found'}</span>
                                                                        </div>
                                                                        <div className="flex items-center gap-3 text-sm">
                                                                            <div className="w-8 h-8 rounded bg-gray-700/50 flex items-center justify-center text-gray-400">
                                                                                <Building size={14} />
                                                                            </div>
                                                                            <span className="text-gray-300">{displayData.business_details?.contact_info?.address || 'Address not found'}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Sources & Verification Section */}
                                                        <div className="mt-10 pt-6 border-t border-gray-700/50">
                                                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                                <Globe size={14} />
                                                                Sources & Verification
                                                            </h4>
                                                            <div className="flex flex-wrap gap-4">
                                                                {displayData.business_details?.source_urls?.home && (
                                                                    <a
                                                                        href={displayData.business_details.source_urls.home}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-xs text-blue-400 transition-colors border border-gray-700"
                                                                    >
                                                                        Home Page
                                                                        <ExternalLink size={12} />
                                                                    </a>
                                                                )}
                                                                {displayData.business_details?.source_urls?.about_us && (
                                                                    <a
                                                                        href={displayData.business_details.source_urls.about_us}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-xs text-blue-400 transition-colors border border-gray-700"
                                                                    >
                                                                        About Us
                                                                        <ExternalLink size={12} />
                                                                    </a>
                                                                )}
                                                                {displayData.business_details?.source_urls?.contact_us && (
                                                                    <a
                                                                        href={displayData.business_details.source_urls.contact_us}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-xs text-blue-400 transition-colors border border-gray-700"
                                                                    >
                                                                        Contact Us
                                                                        <ExternalLink size={12} />
                                                                    </a>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-gray-800 flex justify-end gap-3 bg-gray-900/50">
                            <button
                                onClick={() => setIsReportModalOpen(false)}
                                className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                            >
                                Close
                            </button>
                            <button
                                onClick={() => {
                                    const content = JSON.stringify(selectedTask.output, null, 2);
                                    navigator.clipboard.writeText(content);
                                    alert('Report copied to clipboard!');
                                }}
                                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                            >
                                <Download size={16} />
                                Download Report
                            </button>
                        </div>
                    </div>

                    {/* Site Preview Modal */}
                    {isPreviewOpen && previewUrl && (
                        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4">
                            <div className="bg-white w-full max-w-5xl h-[85vh] rounded-xl flex flex-col overflow-hidden shadow-2xl">
                                <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-bold text-gray-800">Preview Site</h3>
                                            <span className="text-sm text-gray-500 px-2 py-0.5 bg-gray-200 rounded truncate max-w-[300px]">{previewUrl}</span>
                                        </div>
                                        <a
                                            href={previewUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-1.5 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
                                        >
                                            <ExternalLink size={12} />
                                            Open in New Tab
                                        </a>
                                    </div>
                                    <button onClick={() => setIsPreviewOpen(false)} className="text-gray-500 hover:text-gray-800">
                                        <XCircle size={24} />
                                    </button>
                                </div>
                                <div className="flex-1 bg-gray-100 relative">
                                    <iframe
                                        src={`http://localhost:3001/api/monitoring/proxy?url=${encodeURIComponent(previewUrl)}`}
                                        className="w-full h-full border-0"
                                        title="Site Preview"
                                        sandbox="allow-same-origin allow-scripts"
                                    />
                                    {/* Troubleshooting info for blocked iframes */}
                                    <div className="absolute inset-0 -z-10 flex flex-col items-center justify-center p-8 text-center bg-gray-50">
                                        <AlertTriangle size={48} className="text-yellow-500 mb-4" />
                                        <h4 className="text-lg font-bold text-gray-800 mb-2">Preview Blocked by Site</h4>
                                        <p className="text-gray-600 max-w-md mb-6">
                                            Some websites (like Razorpay) prevent themselves from being embedded for security reasons.
                                        </p>
                                        <a
                                            href={previewUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-6 py-2 bg-gray-800 hover:bg-gray-900 text-white rounded-lg transition-colors flex items-center gap-2"
                                        >
                                            <ExternalLink size={16} />
                                            Open in Browser to View
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MarketResearchAgent;
