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

    // MCC Management State
    const [mccList, setMccList] = useState<any[]>([]);
    const [selectedMccValue, setSelectedMccValue] = useState<string>('');
    const [overrideReason, setOverrideReason] = useState<string>('');
    const [isSavingMcc, setIsSavingMcc] = useState(false);
    const [saveMccSuccess, setSaveMccSuccess] = useState<string | null>(null);
    const [saveMccError, setSaveMccError] = useState<string | null>(null);

    useEffect(() => {
        if (activeTab === 'mcc') {
            fetchMccList();
        }
    }, [activeTab]);

    // Pre-select primary suggested MCC when task opens
    useEffect(() => {
        if (selectedTask && selectedTask.output) {
            try {
                // Determine source: task.output might be string or object
                const output = typeof selectedTask.output === 'string'
                    ? JSON.parse(selectedTask.output)
                    : selectedTask.output;

                // If already finalized, load that
                // TODO: Handle viewing existing final_mcc logic

                // Default to primary suggestion
                if (output?.comprehensive_site_scan?.mcc_codes?.primary_mcc?.mcc_code) {
                    setSelectedMccValue(output.comprehensive_site_scan.mcc_codes.primary_mcc.mcc_code);
                }
            } catch (e) { console.error("Error parsing task output for MCC default", e); }
        }
    }, [selectedTask]);

    const fetchMccList = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/mccs?active=true');
            const data = await response.json();
            if (data.success) {
                setMccList(data.data || []);
            }
        } catch (error) {
            console.error("Failed to fetch MCCs", error);
        }
    };

    const handleSaveMcc = async () => {
        if (!selectedTask) return;
        setIsSavingMcc(true);
        setSaveMccSuccess(null);
        setSaveMccError(null);

        try {
            const response = await fetch(`http://localhost:3001/api/tasks/${selectedTask.id}/mcc`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mcc_code: selectedMccValue,
                    override_reason: overrideReason,
                    source: 'manual', // Logic to determine if auto or manual can be refined
                    selected_by: 'admin'
                })
            });
            const result = await response.json();
            if (result.success) {
                setSaveMccSuccess("MCC Finalized Successfully");
                // Refresh task to see updated status (optional)
                fetchAgentAndTasks();
            } else {
                setSaveMccError(result.error || "Failed to save");
            }
        } catch (e) {
            setSaveMccError("Failed to save connection error");
        } finally {
            setIsSavingMcc(false);
        }
    };

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

            await AgentService.execute('market_research', researchType, input);

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
                                                { id: 'changes', label: 'Changes', icon: Activity },
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

                                                            {/* Phase E.1.1: Failure Gating & Compliance Dashboard */}
                                                            {siteScan.scan_status?.status === 'FAILED' ? (
                                                                <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-8 text-center animate-in fade-in slide-in-from-top-2">
                                                                    <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/20">
                                                                        <Lock className="text-red-400" size={32} />
                                                                    </div>
                                                                    <h3 className="text-xl font-bold text-white mb-2">Scan could not be completed</h3>
                                                                    <p className="text-gray-400 mb-6 max-w-md mx-auto">
                                                                        {siteScan.scan_status.message || "The website blocked access or could not be reached."}
                                                                        <br />
                                                                        <span className="text-sm text-gray-500 mt-2 block">
                                                                            Reason: {siteScan.scan_status.reason} (This does not indicate a compliance violation)
                                                                        </span>
                                                                    </p>

                                                                    {siteScan.scan_status.target_url && (
                                                                        <a
                                                                            href={siteScan.scan_status.target_url}
                                                                            target="_blank"
                                                                            rel="noreferrer"
                                                                            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors text-sm font-medium"
                                                                        >
                                                                            <ExternalLink size={16} />
                                                                            Visit Website Manually
                                                                        </a>
                                                                    )}
                                                                </div>
                                                            ) : siteScan.compliance_intelligence && (
                                                                <div className="space-y-6 animate-in fade-in slide-in-from-top-2">
                                                                    {/* Score Card */}
                                                                    <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-6 relative overflow-hidden">
                                                                        <div className="absolute top-0 right-0 p-4 opacity-10">
                                                                            <Shield size={120} className="text-white" />
                                                                        </div>

                                                                        <div className="flex flex-col md:flex-row gap-8 relative z-10">
                                                                            {/* Main Score */}
                                                                            <div className="flex flex-col items-center justify-center min-w-[200px]">
                                                                                <div className="relative w-32 h-32 flex items-center justify-center">
                                                                                    <svg className="w-full h-full" viewBox="0 0 36 36">
                                                                                        <path
                                                                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                                                                            fill="none"
                                                                                            stroke="#374151"
                                                                                            strokeWidth="3"
                                                                                        />
                                                                                        <path
                                                                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                                                                            fill="none"
                                                                                            stroke={
                                                                                                siteScan.compliance_intelligence.score >= 80 ? '#4ade80' :
                                                                                                    siteScan.compliance_intelligence.score >= 50 ? '#facc15' : '#f87171'
                                                                                            }
                                                                                            strokeWidth="3"
                                                                                            strokeDasharray={`${siteScan.compliance_intelligence.score}, 100`}
                                                                                            className="animate-[spin_1s_ease-out_reverse]"
                                                                                        />
                                                                                    </svg>
                                                                                    <div className="absolute flex flex-col items-center">
                                                                                        <span className="text-4xl font-bold text-white">{siteScan.compliance_intelligence.score}</span>
                                                                                        <span className={`text-sm font-semibold uppercase tracking-wider ${siteScan.compliance_intelligence.rating === 'Good' ? 'text-green-400' :
                                                                                            siteScan.compliance_intelligence.rating === 'Fair' ? 'text-yellow-400' : 'text-red-400'
                                                                                            }`}>{siteScan.compliance_intelligence.rating}</span>
                                                                                    </div>
                                                                                </div>
                                                                                <p className="text-xs text-gray-500 mt-2 text-center max-w-[150px] mb-2">
                                                                                    Compliance Score
                                                                                </p>
                                                                                {siteScan.business_context ? (
                                                                                    <div className="flex flex-col gap-2 items-center w-full">
                                                                                        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[10px] uppercase font-bold tracking-wider">
                                                                                            <Building size={10} />
                                                                                            {siteScan.business_context.primary.replace(/_/g, ' ')}
                                                                                        </div>

                                                                                        <div className="flex flex-wrap gap-1 justify-center">
                                                                                            {/* Low Confidence Warning */}
                                                                                            {(siteScan.business_context.status === 'LOW_CONFIDENCE' || siteScan.business_context.status === 'UNDETERMINED') && (
                                                                                                <span className="text-[9px] text-yellow-500 bg-yellow-500/10 px-1.5 rounded border border-yellow-500/20 flex items-center gap-1">
                                                                                                    <AlertTriangle size={8} />
                                                                                                    Low Confidence
                                                                                                </span>
                                                                                            )}

                                                                                            {/* Frontend Surface */}
                                                                                            {siteScan.business_context.frontend_surface &&
                                                                                                siteScan.business_context.frontend_surface !== 'UNKNOWN' &&
                                                                                                siteScan.business_context.frontend_surface !== 'MARKETING_SITE' && (
                                                                                                    <span className="text-[9px] text-purple-400 bg-purple-500/10 px-1.5 rounded border border-purple-500/20">
                                                                                                        {siteScan.business_context.frontend_surface.replace(/_/g, ' ')}
                                                                                                    </span>
                                                                                                )}
                                                                                        </div>
                                                                                    </div>
                                                                                ) : siteScan.compliance_intelligence.context && (
                                                                                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[10px] uppercase font-bold tracking-wider">
                                                                                        <Building size={10} />
                                                                                        {siteScan.compliance_intelligence.context.replace(/_/g, ' ')}
                                                                                    </div>
                                                                                )}
                                                                            </div>

                                                                            {/* Breakdown */}
                                                                            <div className="flex-1 space-y-5 justify-center flex flex-col">
                                                                                {/* Technical */}
                                                                                <div>
                                                                                    <div className="flex justify-between text-sm mb-1">
                                                                                        <span className="text-gray-300 font-medium">Technical Security</span>
                                                                                        <span className="text-gray-400">{siteScan.compliance_intelligence.breakdown.technical.score}/{siteScan.compliance_intelligence.breakdown.technical.max}</span>
                                                                                    </div>
                                                                                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                                                                        <div
                                                                                            className="h-full bg-blue-500 rounded-full transition-all duration-1000"
                                                                                            style={{ width: `${(siteScan.compliance_intelligence.breakdown.technical.score / siteScan.compliance_intelligence.breakdown.technical.max) * 100}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <div className="flex gap-2 mt-1 flex-wrap">
                                                                                        {siteScan.compliance_intelligence.breakdown.technical.details.map((d: any, i: number) => (
                                                                                            <span key={i} className={`text-[10px] px-1.5 py-0.5 rounded border ${d.status === 'pass' || d.status.includes('Good') ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-300 border-red-500/20'}`}>
                                                                                                {d.item}
                                                                                            </span>
                                                                                        ))}
                                                                                    </div>
                                                                                </div>

                                                                                {/* Policy */}
                                                                                <div>
                                                                                    <div className="flex justify-between text-sm mb-1">
                                                                                        <span className="text-gray-300 font-medium">Policy Completeness</span>
                                                                                        <span className="text-gray-400">{siteScan.compliance_intelligence.breakdown.policy.score}/{siteScan.compliance_intelligence.breakdown.policy.max}</span>
                                                                                    </div>
                                                                                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                                                                        <div
                                                                                            className="h-full bg-purple-500 rounded-full transition-all duration-1000 delay-100"
                                                                                            style={{ width: `${(siteScan.compliance_intelligence.breakdown.policy.score / siteScan.compliance_intelligence.breakdown.policy.max) * 100}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <div className="flex gap-2 mt-1 flex-wrap">
                                                                                        {siteScan.compliance_intelligence.breakdown.policy.details.map((d: any, i: number) => (
                                                                                            <span key={i} className={`text-[10px] px-1.5 py-0.5 rounded border ${d.status.includes('Found') ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                                                                d.status.includes('Optional') ? 'bg-yellow-500/10 text-yellow-300 border-yellow-500/20' :
                                                                                                    d.status.includes('N/A') ? 'bg-gray-500/10 text-gray-400 border-gray-500/20' :
                                                                                                        'bg-red-500/10 text-red-300 border-red-500/20'
                                                                                                }`}>
                                                                                                {d.item} {d.status.includes('N/A') && '(N/A)'}
                                                                                            </span>
                                                                                        ))}
                                                                                    </div>
                                                                                </div>

                                                                                {/* Trust */}
                                                                                <div>
                                                                                    <div className="flex justify-between text-sm mb-1">
                                                                                        <span className="text-gray-300 font-medium">Trust & Content Risk</span>
                                                                                        <span className="text-gray-400">{siteScan.compliance_intelligence.breakdown.trust.score}/{siteScan.compliance_intelligence.breakdown.trust.max}</span>
                                                                                    </div>
                                                                                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                                                                        <div
                                                                                            className="h-full bg-orange-500 rounded-full transition-all duration-1000 delay-200"
                                                                                            style={{ width: `${(siteScan.compliance_intelligence.breakdown.trust.score / siteScan.compliance_intelligence.breakdown.trust.max) * 100}%` }}
                                                                                        />
                                                                                    </div>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    </div>

                                                                    {/* Risk Flags Section */}
                                                                    {siteScan.compliance_intelligence.risk_flags.length > 0 && (
                                                                        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-5">
                                                                            <h3 className="text-red-400 font-bold flex items-center gap-2 mb-3">
                                                                                <AlertOctagon size={20} />
                                                                                Detected Risk Signals
                                                                            </h3>
                                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                                                {siteScan.compliance_intelligence.risk_flags.map((flag: any, idx: number) => (
                                                                                    <div key={idx} className="bg-black/30 border border-red-500/30 rounded p-3 flex justify-between items-start">
                                                                                        <div>
                                                                                            <span className="text-xs font-bold text-red-300 uppercase tracking-wider block mb-1">{flag.type.replace('_', ' ')}</span>
                                                                                            <p className="text-sm text-gray-300">{flag.message}</p>
                                                                                        </div>
                                                                                        <span className="text-xs font-bold bg-red-500/20 text-red-400 px-2 py-1 rounded">
                                                                                            -{flag.penalty} pts
                                                                                        </span>
                                                                                    </div>
                                                                                ))}
                                                                            </div>
                                                                        </div>
                                                                    )}
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
                                                    {/* System Suggestions */}
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">System Suggestions</h3>
                                                        <div className="grid grid-cols-1 gap-4">
                                                            {/* Primary Suggestion */}
                                                            {displayData.mcc_codes?.primary_mcc && (
                                                                <div className="bg-gray-800/50 border border-green-500/30 rounded-lg p-4 override-hidden">
                                                                    <div className="flex items-start gap-4">
                                                                        <div className="mt-1 flex-shrink-0">
                                                                            <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-500">
                                                                                <CheckCircle size={18} />
                                                                            </div>
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <h4 className="font-bold text-white text-lg break-words">
                                                                                {displayData.mcc_codes.primary_mcc.mcc_code} - {displayData.mcc_codes.primary_mcc.description}
                                                                            </h4>
                                                                            <div className="text-sm text-gray-400 mt-1">
                                                                                {displayData.mcc_codes.primary_mcc.category} / {displayData.mcc_codes.primary_mcc.subcategory}
                                                                            </div>
                                                                            <div className="mt-3 bg-gray-900/50 rounded p-3 text-sm border border-gray-700">
                                                                                <span className="text-gray-500 block mb-1 text-xs uppercase">Reasoning</span>
                                                                                {displayData.mcc_codes.primary_mcc.keywords_matched && Array.isArray(displayData.mcc_codes.primary_mcc.keywords_matched) ? (
                                                                                    <div className="flex flex-wrap gap-2">
                                                                                        {displayData.mcc_codes.primary_mcc.keywords_matched.map((kw: string, i: number) => (
                                                                                            <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">{kw}</span>
                                                                                        ))}
                                                                                    </div>
                                                                                ) : (
                                                                                    <span className="text-gray-400">High keyword match frequency on homepage.</span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        <div className="flex-shrink-0 flex flex-col items-end">
                                                                            <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-1 rounded border border-green-500/30 mb-2 whitespace-nowrap">Primary Match</span>
                                                                            <div className="text-3xl font-bold text-green-400">{displayData.mcc_codes.primary_mcc.confidence}%</div>
                                                                            <div className="text-xs text-gray-500">Confidence</div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {/* Secondary Suggestion */}
                                                            {displayData.mcc_codes?.secondary_mcc && (
                                                                <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-3 flex justify-between items-center">
                                                                    <div className="flex gap-3 items-center">
                                                                        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 font-mono text-xs">2nd</div>
                                                                        <div>
                                                                            <div className="font-bold text-gray-300">
                                                                                {displayData.mcc_codes.secondary_mcc.mcc_code} - {displayData.mcc_codes.secondary_mcc.description}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="text-sm text-gray-500 font-medium">{displayData.mcc_codes.secondary_mcc.confidence}% Conf.</div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    <div className="border-t border-gray-700 my-4"></div>

                                                    {/* Manual Selection & Override */}
                                                    <div className="bg-gray-900/40 border border-gray-700/50 rounded-lg p-6">
                                                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                                                            <Shield size={20} className="text-blue-500" />
                                                            Final Decision
                                                        </h3>

                                                        {saveMccSuccess && (
                                                            <div className="mb-4 p-3 bg-green-500/10 text-green-400 rounded border border-green-500/20 flex items-center gap-2">
                                                                <CheckCircle size={16} /> {saveMccSuccess}
                                                            </div>
                                                        )}
                                                        {saveMccError && (
                                                            <div className="mb-4 p-3 bg-red-500/10 text-red-400 rounded border border-red-500/20 flex items-center gap-2">
                                                                <AlertCircle size={16} /> {saveMccError}
                                                            </div>
                                                        )}

                                                        <div className="space-y-4">
                                                            <div>
                                                                <label className="block text-sm font-semibold text-gray-400 mb-1">Select Final MCC</label>
                                                                <div className="relative">
                                                                    <select
                                                                        className="w-full p-2.5 border border-gray-700 rounded bg-gray-800 text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                                        value={selectedMccValue}
                                                                        onChange={(e) => setSelectedMccValue(e.target.value)}
                                                                    >
                                                                        <option value="">-- Search and Select MCC --</option>
                                                                        {mccList.map((mcc) => (
                                                                            <option key={mcc.code} value={mcc.code}>
                                                                                {mcc.code} - {mcc.description} ({mcc.category})
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </div>
                                                            </div>

                                                            {selectedMccValue && displayData.mcc_codes?.primary_mcc?.mcc_code !== selectedMccValue && (
                                                                <div className="animate-in fade-in slide-in-from-top-2">
                                                                    <div className="flex items-start gap-2 p-3 bg-yellow-500/10 text-yellow-500 rounded border border-yellow-500/20 mb-3 text-sm">
                                                                        <AlertTriangle size={16} className="mt-0.5" />
                                                                        <div>
                                                                            <strong className="block mb-1">Override Warning:</strong>
                                                                            You are selecting an MCC that differs from the primary system suggestion.
                                                                            Please provide a valid reasoning for this override.
                                                                        </div>
                                                                    </div>
                                                                    <label className="block text-sm font-semibold text-gray-400 mb-1">Override Reason <span className="text-red-500">*</span></label>
                                                                    <textarea
                                                                        className="w-full p-2.5 border border-gray-700 rounded bg-gray-800 text-white focus:ring-2 focus:ring-blue-500 h-24 placeholder-gray-500"
                                                                        placeholder="Explain why the system suggestion was rejected..."
                                                                        value={overrideReason}
                                                                        onChange={(e) => setOverrideReason(e.target.value)}
                                                                    ></textarea>
                                                                </div>
                                                            )}

                                                            <div className="pt-2">
                                                                <button
                                                                    onClick={handleSaveMcc}
                                                                    disabled={isSavingMcc || !selectedMccValue || (selectedMccValue !== displayData.mcc_codes?.primary_mcc?.mcc_code && !overrideReason)}
                                                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                                                                >
                                                                    {isSavingMcc ? <Loader className="animate-spin" size={16} /> : <CheckCircle size={16} />}
                                                                    Confirm & Save Final MCC
                                                                </button>
                                                            </div>
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

                                                    {/* V2 Features - Feature Flagged */}
                                                    {FEATURES.ENABLE_MARKET_RESEARCH_V2_UI && (
                                                        <div className="p-6 space-y-4 bg-gray-900/30 border-t border-gray-700">
                                                            <TechStackCard techStack={displayData.tech_stack} />
                                                            <SEOHealthCard seoAnalysis={displayData.seo_analysis} />
                                                            <BusinessMetadataV2 businessDetails={displayData.business_details} />
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {activeTab === 'changes' && (
                                                <div className="space-y-6">
                                                    {/* Change Intelligence View */}
                                                    {displayData.change_intelligence ? (
                                                        <div className="space-y-6">
                                                            {/* Summary Banner */}
                                                            <div className={`p-6 rounded-lg border flex justify-between items-center ${displayData.change_intelligence.overall_severity === 'critical' ? 'bg-red-500/10 border-red-500/30' :
                                                                displayData.change_intelligence.overall_severity === 'moderate' ? 'bg-yellow-500/10 border-yellow-500/30' :
                                                                    displayData.change_intelligence.overall_severity === 'minor' ? 'bg-blue-500/10 border-blue-500/30' :
                                                                        'bg-gray-800/50 border-gray-700'
                                                                }`}>
                                                                <div>
                                                                    <div className="flex items-center gap-2 mb-2">
                                                                        {displayData.change_intelligence.overall_severity === 'critical' && <AlertOctagon className="text-red-500" size={24} />}
                                                                        {displayData.change_intelligence.overall_severity === 'moderate' && <AlertTriangle className="text-yellow-500" size={24} />}
                                                                        {displayData.change_intelligence.overall_severity === 'minor' && <Activity className="text-blue-500" size={24} />}
                                                                        {displayData.change_intelligence.overall_severity === 'none' && <CheckCircle className="text-gray-400" size={24} />}

                                                                        <h3 className={`text-lg font-bold capitalize ${displayData.change_intelligence.overall_severity === 'critical' ? 'text-red-400' :
                                                                            displayData.change_intelligence.overall_severity === 'moderate' ? 'text-yellow-400' :
                                                                                displayData.change_intelligence.overall_severity === 'minor' ? 'text-blue-400' :
                                                                                    'text-gray-300'
                                                                            }`}>
                                                                            {displayData.change_intelligence.overall_severity} Change Severity
                                                                        </h3>
                                                                    </div>
                                                                    <p className="text-white font-medium">{displayData.change_intelligence.summary}</p>
                                                                </div>

                                                                {/* Recommended Action Box */}
                                                                {displayData.change_intelligence.recommended_action && (
                                                                    <div className="bg-black/30 p-4 rounded-lg border border-white/10 max-w-md">
                                                                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">Recommended Action</label>
                                                                        <p className="text-sm text-gray-200 flex items-start gap-2">
                                                                            <ArrowRight size={16} className="mt-0.5 text-blue-400 flex-shrink-0" />
                                                                            {displayData.change_intelligence.recommended_action}
                                                                        </p>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            {/* Change List */}
                                                            <div>
                                                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                                                    <Activity className="text-blue-400" size={20} />
                                                                    Detected Changes
                                                                </h3>

                                                                {displayData.change_intelligence.changes && displayData.change_intelligence.changes.length > 0 ? (
                                                                    <div className="space-y-4">
                                                                        {displayData.change_intelligence.changes.map((change: any, idx: number) => (
                                                                            <div key={idx} className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-5 hover:border-blue-500/30 transition-colors">
                                                                                <div className="flex justify-between items-start mb-3">
                                                                                    <div className="flex items-center gap-3">
                                                                                        <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${change.severity === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
                                                                                            change.severity === 'moderate' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' :
                                                                                                'bg-blue-500/10 text-blue-400 border-blue-500/30'
                                                                                            }`}>
                                                                                            {change.severity}
                                                                                        </span>
                                                                                        <h4 className="font-bold text-gray-200 capitalize">
                                                                                            {change.type.replace(/_/g, ' ')}
                                                                                        </h4>
                                                                                    </div>
                                                                                    <div className="text-xs text-gray-500 font-mono">
                                                                                        Conf: {(change.confidence * 100).toFixed(0)}%
                                                                                    </div>
                                                                                </div>

                                                                                <p className="text-gray-400 text-sm mb-3">
                                                                                    {change.description}
                                                                                </p>

                                                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-black/20 p-3 rounded">
                                                                                    <div>
                                                                                        <span className="text-gray-500 text-xs block mb-1">Business Impact</span>
                                                                                        <span className="text-gray-300">{change.business_impact}</span>
                                                                                    </div>
                                                                                    <div>
                                                                                        <span className="text-gray-500 text-xs block mb-1">Recommended Action</span>
                                                                                        <span className="text-gray-300">{change.recommended_action}</span>
                                                                                    </div>
                                                                                </div>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <div className="text-center p-12 bg-gray-800/30 rounded-lg border border-gray-700/50 border-dashed">
                                                                        <CheckCircle className="mx-auto text-gray-600 mb-3" size={32} />
                                                                        <p className="text-gray-500">No significant changes detected in this scan.</p>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="text-center p-12">
                                                            <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-700">
                                                                <Activity size={24} className="text-gray-600" />
                                                            </div>
                                                            <h3 className="text-lg font-medium text-white mb-2">Change Detection Not Available</h3>
                                                            <p className="text-gray-500">Run a new scan to enable change intelligence.</p>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>
                    </div>

                    {/* Site Preview Modal */}
                    {
                        isPreviewOpen && previewUrl && (
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
                        )
                    }
                </div>
            )}
        </div>
    );
};

export default MarketResearchAgent;
