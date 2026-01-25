import React, { useState, useEffect } from 'react';
import { Globe, Plus, Loader, AlertCircle, CheckCircle, XCircle, AlertTriangle, Eye, Download, Shield, CreditCard, ShoppingBag, Building, ExternalLink, Activity, ArrowRight, AlertOctagon, Info, Lock, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { AgentService, TaskService, Task, Agent } from '../services/api';
import { FEATURES } from '../config/features';
import TechStackCard from '../components/market-research/TechStackCard';
import SEOHealthCard from '../components/market-research/SEOHealthCard';
import BusinessMetadataV2 from '../components/market-research/BusinessMetadataV2';
import ReportDownloadButton from '../components/market-research/ReportDownloadButton';

/**
 * Site Scan - Operations Domain
 * 
 * Dedicated single-purpose UI for site scanning.
 * Supports:
 * - Site Scan (comprehensive website analysis)
 * - KYC Site Scan (merchant KYC screening with decision rules)
 */
const SiteScanAgent = () => {
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
    const [activeTab, setActiveTab] = useState('crawl');
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);

    const handleViewReport = (task: Task) => {
        setSelectedTask(task);
        setActiveTab('crawl');
        setIsReportModalOpen(true);
    };

    // Form State - Site Scan only
    const [url, setUrl] = useState('');
    const [businessName, setBusinessName] = useState('');
    const [scanType, setScanType] = useState<'site_scan' | 'kyc_site_scan'>('site_scan');
    
    // KYC-specific form fields
    const [kycMerchantName, setKycMerchantName] = useState('');
    const [kycAddress, setKycAddress] = useState('');
    const [kycBusinessType, setKycBusinessType] = useState('E-commerce');
    const [kycProducts, setKycProducts] = useState('');

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

    useEffect(() => {
        if (selectedTask && selectedTask.output) {
            try {
                const output = typeof selectedTask.output === 'string'
                    ? JSON.parse(selectedTask.output)
                    : selectedTask.output;

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
                    source: 'manual',
                    selected_by: 'admin'
                })
            });
            const result = await response.json();
            if (result.success) {
                setSaveMccSuccess("MCC Finalized Successfully");
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
    }, [page]);

    const fetchAgentAndTasks = async () => {
        try {
            setLoading(true);
            const agents = await AgentService.getAll();
            const marketAgent = agents.find(a => a.type === 'market_research');

            if (marketAgent) {
                setAgent(marketAgent);
                // Fetch a larger batch to ensure we have enough for filtering and pagination
                // In a production system, this filtering would ideally be done on the backend
                const { tasks: allTasks, total } = await TaskService.getAll({
                    agentId: marketAgent.id,
                    limit: 500, // Fetch more to account for filtering
                    offset: 0
                });
                
                // Filter for site scan tasks only (including KYC)
                const scanTasks = allTasks.filter(task => 
                    task.action === 'site_scan' || task.action === 'comprehensive_site_scan' || task.action === 'kyc_site_scan'
                );
                
                // Sort by creation date (newest first)
                scanTasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
                
                // Apply pagination
                const start = (page - 1) * limit;
                const end = start + limit;
                setTasks(scanTasks.slice(start, end));
                setTotalTasks(scanTasks.length);
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
        if (!agent || !url.trim()) return;

        try {
            setSubmitting(true);

            if (scanType === 'kyc_site_scan') {
                // KYC scan requires additional fields
                if (!kycMerchantName.trim()) {
                    alert('Merchant name is required for KYC scan');
                    return;
                }
                if (!kycAddress.trim()) {
                    alert('Registered address is required for KYC scan');
                    return;
                }
                
                const input = {
                    url: url,
                    merchant_legal_name: kycMerchantName,
                    registered_address: kycAddress,
                    declared_business_type: kycBusinessType,
                    declared_products_services: kycProducts.split(',').map(p => p.trim()).filter(p => p),
                    merchant_display_name: businessName.trim() || kycMerchantName.split(' ')[0],
                    website_url: url
                };
                
                // For now, we'll use market_research agent with kyc_site_scan action
                // TODO: Integrate with KYC agent when available
                await AgentService.execute('market_research', 'kyc_site_scan', input);
            } else {
                // Regular site scan
                const input: any = {
                    topic: url,
                    url: url
                };

                if (businessName.trim()) {
                    input.business_name = businessName;
                }

                // Use 'comprehensive_site_scan' backend action but display as 'site_scan'
                await AgentService.execute('market_research', 'comprehensive_site_scan', input);
            }

            setIsModalOpen(false);
            setUrl('');
            setBusinessName('');
            setKycMerchantName('');
            setKycAddress('');
            setKycBusinessType('E-commerce');
            setKycProducts('');
            
            // Reset to first page and refresh task list to show new scan
            setPage(1);
            fetchAgentAndTasks();
        } catch (err: any) {
            alert('Failed to create site scan: ' + err.message);
        } finally {
            setSubmitting(false);
        }
    };

    // Helper function to extract site scan details from task
    const getSiteScanDetails = (task: Task) => {
        let url = '';
        let businessName = '';
        let scanType = 'Site Scan';
        
        // Determine scan type label
        if (task.action === 'kyc_site_scan') {
            scanType = 'KYC Site Scan';
        } else if (task.action === 'comprehensive_site_scan' || task.action === 'site_scan') {
            scanType = 'Site Scan';
        }

        // Try to get URL from input first
        if (task.input?.url) {
            url = task.input.url;
        } else if (task.input?.topic) {
            // Sometimes URL might be in topic field
            url = task.input.topic;
        }

        // Try to get business name from input
        if (task.input?.business_name) {
            businessName = task.input.business_name;
        } else if (task.input?.merchant_display_name) {
            businessName = task.input.merchant_display_name;
        } else if (task.input?.merchant_legal_name) {
            businessName = task.input.merchant_legal_name;
        }

        // If task is completed, try to extract from output
        if (task.status === 'completed' && task.output) {
            try {
                const output = typeof task.output === 'string' 
                    ? JSON.parse(task.output) 
                    : task.output;

                // Extract URL from output
                if (output?.comprehensive_site_scan?.url && !url) {
                    url = output.comprehensive_site_scan.url;
                }

                // Extract business name from output
                if (output?.comprehensive_site_scan?.business_details?.extracted_business_name && !businessName) {
                    businessName = output.comprehensive_site_scan.business_details.extracted_business_name;
                } else if (output?.comprehensive_site_scan?.business_name && !businessName) {
                    businessName = output.comprehensive_site_scan.business_name;
                }
            } catch (e) {
                // Silently fail if output parsing fails
            }
        }

        return { url, businessName, scanType };
    };

    // Report rendering will be done inline in the modal JSX below

    if (loading && tasks.length === 0) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-400">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Site Scan</h1>
                    <p className="text-gray-400 text-sm">Comprehensive website analysis for compliance, risk assessment, and structural insights</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                >
                    <Plus size={16} />
                    New Site Scan
                </button>
            </div>

            {/* Task List */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <div className="p-6 border-b border-gray-800">
                    <h3 className="text-lg font-bold text-white">Recent Site Scans</h3>
                </div>
                <div className="p-6">
                    {tasks.length === 0 ? (
                        <div className="text-center py-12 text-gray-400">
                            <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>No site scans yet. Create your first scan to get started.</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {tasks.map((task) => {
                                const { url, businessName, scanType } = getSiteScanDetails(task);
                                const displayUrl = url || 'URL not available';
                                const displayBusinessName = businessName || 'Business name not available';
                                
                                return (
                                    <div
                                        key={task.id}
                                        className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                                        onClick={() => handleViewReport(task)}
                                    >
                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                                                task.status === 'completed' ? 'bg-green-500' :
                                                task.status === 'failed' ? 'bg-red-500' :
                                                'bg-blue-500 animate-pulse'
                                            }`} />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <p className="text-sm font-medium text-white truncate">
                                                        {displayUrl}
                                                    </p>
                                                    <span className="text-xs text-gray-500 flex-shrink-0">
                                                        {scanType}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 text-xs text-gray-400">
                                                    <span className="truncate">{displayBusinessName}</span>
                                                    <span>•</span>
                                                    <span className="flex-shrink-0">{new Date(task.createdAt).toLocaleString()}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <span className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ml-3 ${
                                            task.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                                            task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                            'bg-blue-500/10 text-blue-400'
                                        }`}>
                                            {task.status}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                    
                    {/* Pagination Controls */}
                    {totalTasks > limit && (
                        <div className="mt-6 pt-6 border-t border-gray-800 flex items-center justify-between">
                            <div className="text-sm text-gray-400">
                                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, totalTasks)} of {totalTasks} scans
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setPage(prev => Math.max(1, prev - 1))}
                                    disabled={page === 1}
                                    className={`px-3 py-2 rounded-lg border transition-colors flex items-center gap-1 ${
                                        page === 1
                                            ? 'border-gray-800 text-gray-600 cursor-not-allowed'
                                            : 'border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                                    }`}
                                >
                                    <ChevronLeft size={16} />
                                    Previous
                                </button>
                                
                                {/* Page Numbers */}
                                <div className="flex items-center gap-1">
                                    {Array.from({ length: Math.min(5, Math.ceil(totalTasks / limit)) }, (_, i) => {
                                        let pageNum: number;
                                        const totalPages = Math.ceil(totalTasks / limit);
                                        
                                        if (totalPages <= 5) {
                                            pageNum = i + 1;
                                        } else if (page <= 3) {
                                            pageNum = i + 1;
                                        } else if (page >= totalPages - 2) {
                                            pageNum = totalPages - 4 + i;
                                        } else {
                                            pageNum = page - 2 + i;
                                        }
                                        
                                        return (
                                            <button
                                                key={pageNum}
                                                onClick={() => setPage(pageNum)}
                                                className={`w-8 h-8 rounded-lg border transition-colors ${
                                                    page === pageNum
                                                        ? 'bg-blue-500 border-blue-500 text-white'
                                                        : 'border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                                                }`}
                                            >
                                                {pageNum}
                                            </button>
                                        );
                                    })}
                                </div>
                                
                                <button
                                    onClick={() => setPage(prev => Math.min(Math.ceil(totalTasks / limit), prev + 1))}
                                    disabled={page >= Math.ceil(totalTasks / limit)}
                                    className={`px-3 py-2 rounded-lg border transition-colors flex items-center gap-1 ${
                                        page >= Math.ceil(totalTasks / limit)
                                            ? 'border-gray-800 text-gray-600 cursor-not-allowed'
                                            : 'border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                                    }`}
                                >
                                    Next
                                    <ChevronRight size={16} />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Create Task Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 w-full max-w-md">
                        <h3 className="text-lg font-bold text-white mb-4">New Site Scan</h3>
                        <form onSubmit={handleCreateTask} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Scan Type</label>
                                <select
                                    value={scanType}
                                    onChange={(e) => setScanType(e.target.value as 'site_scan' | 'kyc_site_scan')}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                >
                                    <option value="site_scan">Site Scan</option>
                                    <option value="kyc_site_scan">KYC Site Scan</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Website URL</label>
                                <input
                                    type="url"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="https://example.com"
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                    required
                                />
                            </div>
                            
                            {scanType === 'site_scan' && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Business Name (Optional)</label>
                                    <input
                                        type="text"
                                        value={businessName}
                                        onChange={(e) => setBusinessName(e.target.value)}
                                        placeholder="Example Inc"
                                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                    />
                                </div>
                            )}
                            
                            {scanType === 'kyc_site_scan' && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Merchant Legal Name <span className="text-red-400">*</span></label>
                                        <input
                                            type="text"
                                            value={kycMerchantName}
                                            onChange={(e) => setKycMerchantName(e.target.value)}
                                            placeholder="Acme Corporation Pvt Ltd"
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Registered Address <span className="text-red-400">*</span></label>
                                        <textarea
                                            value={kycAddress}
                                            onChange={(e) => setKycAddress(e.target.value)}
                                            placeholder="123 Business Park, Suite 400, Mumbai, MH 400001, India"
                                            rows={3}
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Business Type</label>
                                        <select
                                            value={kycBusinessType}
                                            onChange={(e) => setKycBusinessType(e.target.value)}
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        >
                                            <option value="E-commerce">E-commerce</option>
                                            <option value="SaaS">SaaS</option>
                                            <option value="Financial Services">Financial Services</option>
                                            <option value="Retail">Retail</option>
                                            <option value="Other">Other</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Products/Services (comma-separated)</label>
                                        <input
                                            type="text"
                                            value={kycProducts}
                                            onChange={(e) => setKycProducts(e.target.value)}
                                            placeholder="Clothing, Accessories, Shoes"
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Display Name (Optional)</label>
                                        <input
                                            type="text"
                                            value={businessName}
                                            onChange={(e) => setBusinessName(e.target.value)}
                                            placeholder="Acme Shop"
                                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>
                                </>
                            )}
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50"
                                >
                                    {submitting ? 'Scanning...' : 'Start Scan'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Enhanced Report View Modal - Full implementation from MarketResearchAgent */}
            {isReportModalOpen && selectedTask && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl">
                        {/* Header */}
                        <div className="flex justify-between items-center p-6 border-b border-gray-800 bg-gradient-to-r from-blue-900/20 to-purple-900/20">
                            <div className="flex-1">
                                <h2 className="text-2xl font-bold text-white mb-1">{selectedTask.input?.topic || selectedTask.input?.url || 'Site Scan Report'}</h2>
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

                        {/* Content - Full report rendering from MarketResearchAgent */}
                        <div className="flex-1 overflow-hidden flex flex-col">
                            {(() => {
                                // Try to parse as JSON first
                                let crawlData: any = null;
                                try {
                                    // Try multiple possible locations for the response
                                    let response = selectedTask.output?.response || selectedTask.output?.raw_output || selectedTask.output;

                                    // Handle string response
                                    if (typeof response === 'string') {
                                        // 1. Strip Markdown code blocks
                                        response = response.replace(/```json\n|```/g, '').trim();

                                        // 2. Try parsing entire string
                                        try {
                                            crawlData = JSON.parse(response);
                                        } catch (e) {
                                            // 3. Fallback: try to find JSON object if mixed with text
                                            const jsonMatch = (response as string).match(/\{[\s\S]*\}/);
                                            if (jsonMatch && jsonMatch[0]) {
                                                crawlData = JSON.parse(jsonMatch[0]);
                                            }
                                        }
                                    } else if (typeof response === 'object') {
                                        crawlData = response;
                                    }
                                    
                                    // If crawlData is still null, try parsing the entire output
                                    if (!crawlData && selectedTask.output) {
                                        const output = selectedTask.output;
                                        if (typeof output === 'string') {
                                            try {
                                                crawlData = JSON.parse(output);
                                            } catch (e) {
                                                // Last resort: try to extract JSON from string
                                                const outputStr: string = output;
                                                const jsonMatch = outputStr.match(/\{[\s\S]*\}/);
                                                if (jsonMatch && jsonMatch[0]) {
                                                    crawlData = JSON.parse(jsonMatch[0]);
                                                }
                                            }
                                        } else if (typeof output === 'object' && output !== null) {
                                            crawlData = output;
                                        }
                                    }
                                } catch (e) {
                                    console.error("Failed to parse crawl data", e);
                                }

                                // Debug: Log what we received for KYC scans
                                if (selectedTask.action === 'kyc_site_scan') {
                                    console.log("KYC Scan - Raw output:", selectedTask.output);
                                    console.log("KYC Scan - Parsed crawlData:", crawlData);
                                    console.log("KYC Scan - Output keys:", selectedTask.output ? Object.keys(selectedTask.output) : []);
                                }

                                // Check if this is a KYC scan result
                                // KYC data has decision, reason_codes, summary, confidence_score, etc.
                                // Also check nested structures (response might wrap the KYC data)
                                const hasKycFields = crawlData?.decision !== undefined || 
                                                    crawlData?.reason_codes !== undefined || 
                                                    crawlData?.confidence_score !== undefined ||
                                                    crawlData?.audit_trail !== undefined ||
                                                    (crawlData?.response && (crawlData.response.decision || crawlData.response.reason_codes));
                                
                                // If KYC data is nested in response, extract it
                                let kycData = crawlData;
                                if (crawlData?.response) {
                                    // Check if response is a string that needs parsing
                                    if (typeof crawlData.response === 'string') {
                                        try {
                                            const parsedResponse = JSON.parse(crawlData.response);
                                            if (parsedResponse.decision || parsedResponse.reason_codes || parsedResponse.confidence_score !== undefined) {
                                                kycData = parsedResponse;
                                            }
                                        } catch (e) {
                                            // Response is not JSON, keep original
                                            console.warn("Failed to parse KYC response string:", e);
                                        }
                                    } else if (crawlData.response && (crawlData.response.decision || crawlData.response.reason_codes)) {
                                        kycData = crawlData.response;
                                    }
                                }
                                
                                // Also check if the entire output is the KYC data (not wrapped)
                                if (!kycData || (Object.keys(kycData).length === 0 && selectedTask.output)) {
                                    // Try parsing the entire output directly
                                    const directOutput = selectedTask.output;
                                    if (directOutput && typeof directOutput === 'object') {
                                        if (directOutput.decision || directOutput.reason_codes || directOutput.confidence_score !== undefined) {
                                            kycData = directOutput;
                                        }
                                    }
                                }
                                
                                const isKycScan = selectedTask.action === 'kyc_site_scan' || hasKycFields;
                                
                                if (isKycScan) {
                                    // Render KYC-specific UI
                                    // Use the extracted kycData (might be nested)
                                    
                                    // Handle decision enum - it might be an object with 'value' property or a string
                                    let decision = 'UNKNOWN';
                                    if (kycData?.decision) {
                                        if (typeof kycData.decision === 'object' && kycData.decision.value) {
                                            decision = kycData.decision.value;
                                        } else if (typeof kycData.decision === 'string') {
                                            decision = kycData.decision;
                                        }
                                    }
                                    
                                    // Normalize decision to uppercase for consistency
                                    decision = decision.toUpperCase();
                                    
                                    // If we still don't have data, show a helpful message
                                    if (!kycData || Object.keys(kycData).length === 0) {
                                        // Check if there's an error in the output
                                        const errorMessage = selectedTask.output?.error || selectedTask.error;
                                        const taskStatus = selectedTask.status;
                                        
                                        return (
                                            <div className="flex-1 overflow-y-auto p-6">
                                                <div className={`rounded-lg p-6 ${
                                                    taskStatus === 'failed' ? 'bg-red-500/10 border border-red-500/50' :
                                                    'bg-yellow-500/10 border border-yellow-500/50'
                                                }`}>
                                                    <h3 className={`text-lg font-bold mb-2 ${
                                                        taskStatus === 'failed' ? 'text-red-400' : 'text-yellow-400'
                                                    }`}>
                                                        {taskStatus === 'failed' ? 'KYC Scan Failed' : 'KYC Scan In Progress'}
                                                    </h3>
                                                    {errorMessage ? (
                                                        <div className="mb-4">
                                                            <p className="text-gray-300 mb-2">Error:</p>
                                                            <p className="text-red-400 font-mono text-sm">{errorMessage}</p>
                                                        </div>
                                                    ) : (
                                                        <p className="text-gray-300 mb-4">
                                                            {taskStatus === 'processing' 
                                                                ? 'The KYC scan is still processing. Please wait...'
                                                                : 'The KYC scan results are not yet available or the scan may have failed.'}
                                                        </p>
                                                    )}
                                                    <details className="mt-4">
                                                        <summary className="text-sm text-gray-400 cursor-pointer">View Raw Output</summary>
                                                        <pre className="mt-2 text-xs text-gray-400 overflow-x-auto max-h-96">
                                                            {JSON.stringify(selectedTask.output, null, 2)}
                                                        </pre>
                                                    </details>
                                                </div>
                                            </div>
                                        );
                                    }
                                    
                                    return (
                                        <div className="flex-1 overflow-y-auto p-6">
                                            <div className="space-y-6">
                                                {/* KYC Decision Card */}
                                                <div className={`rounded-lg p-6 ${
                                                    decision === 'PASS' ? 'bg-green-500/10 border border-green-500/50' :
                                                    decision === 'FAIL' ? 'bg-red-500/10 border border-red-500/50' :
                                                    'bg-yellow-500/10 border border-yellow-500/50'
                                                }`}>
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h3 className="text-xl font-bold text-white">KYC Decision</h3>
                                                        <span className={`px-4 py-2 rounded-full text-sm font-bold ${
                                                            decision === 'PASS' ? 'bg-green-500/20 text-green-400' :
                                                            decision === 'FAIL' ? 'bg-red-500/20 text-red-400' :
                                                            'bg-yellow-500/20 text-yellow-400'
                                                        }`}>
                                                            {decision}
                                                        </span>
                                                    </div>
                                                    {kycData?.summary && (
                                                        <p className="text-gray-300 mb-2">{kycData.summary}</p>
                                                    )}
                                                    {kycData?.confidence_score !== undefined && (
                                                        <div className="mt-4">
                                                            <div className="flex items-center justify-between mb-1">
                                                                <span className="text-sm text-gray-400">Confidence Score</span>
                                                                <span className="text-sm font-medium text-white">{(kycData.confidence_score * 100).toFixed(1)}%</span>
                                                            </div>
                                                            <div className="w-full bg-gray-700 rounded-full h-2">
                                                                <div 
                                                                    className={`h-2 rounded-full ${
                                                                        decision === 'PASS' ? 'bg-green-500' :
                                                                        decision === 'FAIL' ? 'bg-red-500' :
                                                                        'bg-yellow-500'
                                                                    }`}
                                                                    style={{ width: `${kycData.confidence_score * 100}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Compliance Score */}
                                                {kycData?.compliance_score && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Compliance Score</h4>
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <div>
                                                                <div className="text-3xl font-bold text-blue-400 mb-1">
                                                                    {kycData.compliance_score.overall_score}/100
                                                                </div>
                                                                <div className="text-sm text-gray-400">{kycData.compliance_score.rating}</div>
                                                            </div>
                                                            <div className="space-y-2">
                                                                <div className="flex justify-between text-sm">
                                                                    <span className="text-gray-400">Technical</span>
                                                                    <span className="text-white">{kycData.compliance_score.technical_score}/30</span>
                                                                </div>
                                                                <div className="flex justify-between text-sm">
                                                                    <span className="text-gray-400">Policy</span>
                                                                    <span className="text-white">{kycData.compliance_score.policy_score}/40</span>
                                                                </div>
                                                                <div className="flex justify-between text-sm">
                                                                    <span className="text-gray-400">Trust</span>
                                                                    <span className="text-white">{kycData.compliance_score.trust_score}/30</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Reason Codes */}
                                                {kycData?.reason_codes && kycData.reason_codes.length > 0 && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Reason Codes</h4>
                                                        <div className="space-y-2">
                                                            {kycData.reason_codes.map((rc: any, idx: number) => (
                                                                <div key={idx} className={`p-3 rounded-lg ${
                                                                    rc.is_auto_fail ? 'bg-red-500/10 border border-red-500/30' :
                                                                    rc.is_auto_escalate ? 'bg-yellow-500/10 border border-yellow-500/30' :
                                                                    'bg-blue-500/10 border border-blue-500/30'
                                                                }`}>
                                                                    <div className="flex items-center gap-2 mb-1">
                                                                        <span className="text-xs font-mono text-gray-400">[{rc.code}]</span>
                                                                        {rc.is_auto_fail && <span className="text-xs text-red-400">AUTO-FAIL</span>}
                                                                        {rc.is_auto_escalate && <span className="text-xs text-yellow-400">ESCALATE</span>}
                                                                    </div>
                                                                    <p className="text-sm text-gray-300">{rc.message}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Policy Checks */}
                                                {kycData?.policy_checks && kycData.policy_checks.length > 0 && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Policy Checks</h4>
                                                        <div className="space-y-2">
                                                            {kycData.policy_checks.map((pc: any, idx: number) => (
                                                                <div key={idx} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                                                                    <span className="text-sm text-gray-300 capitalize">{pc.policy_type?.replace('_', ' ')}</span>
                                                                    <div className="flex items-center gap-2">
                                                                        {pc.found ? (
                                                                            <>
                                                                                <CheckCircle className="text-green-400" size={16} />
                                                                                <span className="text-xs text-green-400">Found</span>
                                                                                {pc.url && (
                                                                                    <a href={pc.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline">
                                                                                        View
                                                                                    </a>
                                                                                )}
                                                                            </>
                                                                        ) : (
                                                                            <>
                                                                                <XCircle className="text-red-400" size={16} />
                                                                                <span className="text-xs text-red-400">Not Found</span>
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Entity Match */}
                                                {kycData?.entity_match && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Entity Match</h4>
                                                        <div className="space-y-3">
                                                            <div>
                                                                <span className="text-sm text-gray-400">Declared Name:</span>
                                                                <p className="text-white">{kycData.entity_match.declared_name}</p>
                                                            </div>
                                                            {kycData.entity_match.best_match && (
                                                                <div>
                                                                    <span className="text-sm text-gray-400">Best Match:</span>
                                                                    <p className="text-white">{kycData.entity_match.best_match}</p>
                                                                </div>
                                                            )}
                                                            {kycData.entity_match.match_score !== undefined && (
                                                                <div>
                                                                    <span className="text-sm text-gray-400">Match Score:</span>
                                                                    <p className="text-white">{kycData.entity_match.match_score.toFixed(1)}%</p>
                                                                </div>
                                                            )}
                                                            {kycData.entity_match.match_status && (
                                                                <div>
                                                                    <span className={`px-2 py-1 rounded text-xs ${
                                                                        kycData.entity_match.match_status === 'MATCH' ? 'bg-green-500/20 text-green-400' :
                                                                        kycData.entity_match.match_status === 'PARTIAL' ? 'bg-yellow-500/20 text-yellow-400' :
                                                                        'bg-red-500/20 text-red-400'
                                                                    }`}>
                                                                        {kycData.entity_match.match_status}
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Checkout Flow */}
                                                {kycData?.checkout_flow && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Checkout Flow Validation</h4>
                                                        <div className="grid grid-cols-2 gap-3">
                                                            {Object.entries(kycData.checkout_flow).map(([key, value]: [string, any]) => (
                                                                <div key={key} className="flex items-center justify-between p-2 bg-gray-900/50 rounded">
                                                                    <span className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                                                                    {value ? (
                                                                        <CheckCircle className="text-green-400" size={16} />
                                                                    ) : (
                                                                        <XCircle className="text-red-400" size={16} />
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Audit Trail */}
                                                {kycData?.audit_trail && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Audit Trail</h4>
                                                        <div className="space-y-2 text-sm">
                                                            {kycData.audit_trail.scan_id && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Scan ID:</span>
                                                                    <span className="text-white font-mono text-xs">{kycData.audit_trail.scan_id}</span>
                                                                </div>
                                                            )}
                                                            {kycData.audit_trail.scan_duration_seconds !== undefined && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Duration:</span>
                                                                    <span className="text-white">{kycData.audit_trail.scan_duration_seconds.toFixed(2)}s</span>
                                                                </div>
                                                            )}
                                                            {kycData.audit_trail.pages_scanned !== undefined && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Pages Scanned:</span>
                                                                    <span className="text-white">{kycData.audit_trail.pages_scanned}</span>
                                                                </div>
                                                            )}
                                                            {kycData.audit_trail.checks_performed && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Checks Performed:</span>
                                                                    <span className="text-white">{kycData.audit_trail.checks_performed.length}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Business Context */}
                                                {(kycData?.detected_business_type || kycData?.detected_mcc || kycData?.product_match_status) && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Business Context</h4>
                                                        <div className="space-y-2 text-sm">
                                                            {kycData.detected_business_type && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Detected Business Type:</span>
                                                                    <span className="text-white">{kycData.detected_business_type}</span>
                                                                </div>
                                                            )}
                                                            {kycData.detected_mcc && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Detected MCC:</span>
                                                                    <span className="text-white">{kycData.detected_mcc}</span>
                                                                </div>
                                                            )}
                                                            {kycData.product_match_status && (
                                                                <div className="flex justify-between">
                                                                    <span className="text-gray-400">Product Match Status:</span>
                                                                    <span className="text-white capitalize">{kycData.product_match_status}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Content Risk Summary */}
                                                {kycData?.content_risk_summary && (
                                                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-4">Content Risk Summary</h4>
                                                        <div className="space-y-2">
                                                            {kycData.content_risk_summary.risk_level && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm text-gray-400">Risk Level:</span>
                                                                    <span className={`px-2 py-1 rounded text-xs ${
                                                                        kycData.content_risk_summary.risk_level === 'LOW' ? 'bg-green-500/20 text-green-400' :
                                                                        kycData.content_risk_summary.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                                                                        'bg-red-500/20 text-red-400'
                                                                    }`}>
                                                                        {kycData.content_risk_summary.risk_level}
                                                                    </span>
                                                                </div>
                                                            )}
                                                            {kycData.content_risk_summary.dummy_words_detected !== undefined && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm text-gray-400">Dummy Words Detected:</span>
                                                                    {kycData.content_risk_summary.dummy_words_detected ? (
                                                                        <span className="text-red-400 text-sm">Yes</span>
                                                                    ) : (
                                                                        <span className="text-green-400 text-sm">No</span>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Raw Data (for debugging) */}
                                                <details className="bg-gray-800/30 border border-gray-700 rounded-lg p-4">
                                                    <summary className="text-sm font-medium text-gray-400 cursor-pointer">View Raw Data</summary>
                                                    <pre className="mt-4 text-xs text-gray-400 overflow-x-auto">
                                                        {JSON.stringify(kycData, null, 2)}
                                                    </pre>
                                                </details>
                                            </div>
                                        </div>
                                    );
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
                                
                                // Extract crawl summary per PRD V2.1.1
                                const crawlSummary = siteScan?.crawl_summary || {};
                                
                                // RDAP from backend with fallback to compliance intelligence
                                const rdap = siteScan?.rdap || {};
                                const techDetails = siteScan?.compliance_intelligence?.breakdown?.technical?.details || [];
                                const domainAgeDetail = Array.isArray(techDetails) ? techDetails.find((d: any) => d.item === 'Domain Age') : null;
                                const lowVintageAlert = siteScan?.compliance?.general?.alerts?.find((a: any) => a.code === 'LOW_VINTAGE');
                                const domainAgeDays = typeof rdap.age_days === 'number' ? rdap.age_days : (() => {
                                    const m = lowVintageAlert?.description?.match(/(\d+)\s+days/i);
                                    return m ? parseInt(m[1], 10) : undefined;
                                })();

                                // Render Tabbed Interface for Crawler Results
                                return (
                                    <div className="flex flex-col h-full">
                                        {/* Tabs */}
                                        <div className="flex border-b border-gray-800 px-6 overflow-x-auto">
                                            {[
                                                { id: 'crawl', label: 'Crawl summary' },
                                                { id: 'compliance', label: 'Compliance checks' },
                                                { id: 'policy', label: 'Policy details' },
                                                { id: 'mcc', label: 'MCC codes' },
                                                { id: 'product', label: 'Product details' },
                                                { id: 'business', label: 'Business details' },
                                                { id: 'content-risk', label: 'Content Risk' },
                                                { id: 'changes', label: 'Changes' },
                                            ].map((tab) => (
                                                <button
                                                    key={tab.id}
                                                    onClick={() => setActiveTab(tab.id)}
                                                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === tab.id
                                                        ? 'border-blue-500 text-blue-400'
                                                        : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700'
                                                        }`}
                                                >
                                                    {tab.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Tab Content */}
                                        <div className="flex-1 overflow-y-auto p-6 bg-gray-900/50">
                                            {activeTab === 'crawl' && (

                                                                                        <div className="space-y-6">

                                                                                            {/* Crawl Summary Tab */}

                                                                                            <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-6">

                                                                                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">

                                                                                                    <Activity size={20} />

                                                                                                    Crawl Summary

                                                                                                </h3>

                                                                                                {/* Stats */}

                                                                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

                                                                                                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">

                                                                                                        <div className="text-xs text-gray-400 mb-1">Pages Discovered</div>

                                                                                                        <div className="text-2xl font-bold text-white">{crawlSummary.pages_discovered ?? 0}</div>

                                                                                                    </div>

                                                                                                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">

                                                                                                        <div className="text-xs text-gray-400 mb-1">Pages Fetched</div>

                                                                                                        <div className="text-2xl font-bold text-green-400">{crawlSummary.pages_fetched ?? 0}</div>

                                                                                                    </div>

                                                                                                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">

                                                                                                        <div className="text-xs text-gray-400 mb-1">Pages Skipped</div>

                                                                                                        <div className="text-2xl font-bold text-yellow-400">{crawlSummary.pages_skipped ?? 0}</div>

                                                                                                    </div>

                                                                                                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">

                                                                                                        <div className="text-xs text-gray-400 mb-1">Crawl Time</div>

                                                                                                        <div className="text-lg font-bold text-white">

                                                                                                            {crawlSummary.crawl_time_ms ? `${(crawlSummary.crawl_time_ms / 1000).toFixed(1)}s` : 'N/A'}

                                                                                                        </div>

                                                                                                    </div>

                                                                                                </div>

                                                                                                {/* Early Exit */}

                                                                                                {(crawlSummary.early_exit || crawlSummary.early_exit_reason) && (

                                                                                                    <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">

                                                                                                        <div className="flex items-center gap-2 text-blue-400 font-medium mb-2">

                                                                                                            <Info size={16} />

                                                                                                            Early Exit

                                                                                                        </div>

                                                                                                        <div className="text-sm text-gray-300">

                                                                                                            {crawlSummary.early_exit_reason || 'Crawl completed early'}

                                                                                                        </div>

                                                                                                    </div>

                                                                                                )}

                                                                                                {/* Robots / Sitemap */}

                                                                                                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">

                                                                                                    <div className="flex items-center gap-2">

                                                                                                        <span className="text-gray-400">Robots.txt Checked:</span>

                                                                                                        <span className={crawlSummary.robots_checked ? 'text-green-400' : 'text-gray-500'}>

                                                                                                            {crawlSummary.robots_checked ? 'Yes' : 'No'}

                                                                                                        </span>

                                                                                                    </div>

                                                                                                    <div className="flex items-center gap-2">

                                                                                                        <span className="text-gray-400">Sitemap Found:</span>

                                                                                                        <span className={crawlSummary.sitemap_found ? 'text-green-400' : 'text-gray-500'}>

                                                                                                            {crawlSummary.sitemap_found ? 'Yes' : 'No'}

                                                                                                        </span>

                                                                                                    </div>

                                                                                                    <div className="flex items-center gap-2">

                                                                                                        <span className="text-gray-400">Sitemap URLs:</span>

                                                                                                        <span className="text-gray-300">{crawlSummary.sitemap_urls_count ?? 0}</span>

                                                                                                    </div>

                                                                                                </div>

                                                                                            </div>

                                                                                            {/* Found Key Pages (from Policy Details) */}

                                                                                            {siteScan?.policy_details && (

                                                                                                <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-6">

                                                                                                    <h3 className="text-lg font-bold text-white mb-4">Discovered Key Pages</h3>

                                                                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">

                                                                                                        {Object.entries(siteScan.policy_details).map(([key, val]: any, idx) => {

                                                                                                            // Check if this is an e-commerce site

                                                                                                            const productPage = siteScan.policy_details?.product;

                                                                                                            const isEcommerce = productPage?.found && 

                                                                                                                (productPage.url?.includes('/shop') || 

                                                                                                                 productPage.url?.includes('/store') ||

                                                                                                                 productPage.url?.includes('/cart') ||

                                                                                                                 productPage.url?.includes('/checkout'));
                                                                    

                                                                                                            // For shipping_delivery on non-e-commerce sites, show as N/A

                                                                                                            const isShippingOrReturns = key === 'shipping_delivery' || key === 'returns_refund';

                                                                                                            const showAsNotApplicable = isShippingOrReturns && !val?.found && !isEcommerce;
                                                                    

                                                                                                            return (

                                                                                                                <div key={idx} className="bg-gray-900/40 rounded-lg p-3 border border-gray-800">

                                                                                                                    <div className="flex items-center justify-between">

                                                                                                                        <span className="text-sm text-gray-300 capitalize">{key.replace(/_/g, ' ')}</span>

                                                                                                                        {val?.found ? (

                                                                                                                            <CheckCircle size={16} className="text-green-400" />

                                                                                                                        ) : showAsNotApplicable ? (

                                                                                                                            <Info size={16} className="text-gray-500" />

                                                                                                                        ) : (

                                                                                                                            <XCircle size={16} className="text-gray-600" />

                                                                                                                        )}

                                                                                                                    </div>

                                                                                                                    {val?.found && val?.url && (

                                                                                                                        <a href={val.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline break-all">

                                                                                                                            {val.url}

                                                                                                                        </a>

                                                                                                                    )}

                                                                                                                    {showAsNotApplicable && (

                                                                                                                        <span className="text-xs text-gray-500">N/A for service business</span>

                                                                                                                    )}

                                                                                                                </div>

                                                                                                            );

                                                                                                        })}

                                                                                                    </div>

                                                                                                </div>

                                                                                            )}

                                                                                            {/* Failed Scan Notice (if scan failed) */}

                                                                                            {siteScan?.scan_status?.status === 'FAILED' && (

                                                                                                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">

                                                                                                    <div className="flex items-start gap-4">

                                                                                                        <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center border border-red-500/20 flex-shrink-0">

                                                                                                            <Lock className="text-red-400" size={24} />

                                                                                                        </div>

                                                                                                        <div className="flex-1">

                                                                                                            <h3 className="text-lg font-bold text-red-400 mb-1">Scan Failed</h3>

                                                                                                            <p className="text-gray-300 mb-2">

                                                                                                                {siteScan.scan_status.message || "The website blocked access or could not be reached."}

                                                                                                            </p>

                                                                                                            <div className="flex items-center gap-4 text-sm">

                                                                                                                <span className="bg-red-500/20 text-red-300 px-2 py-0.5 rounded text-xs font-mono">

                                                                                                                    {siteScan.scan_status.reason}

                                                                                                                </span>

                                                                                                                {siteScan.scan_status.retryable && (

                                                                                                                    <span className="text-yellow-400 text-xs">Retryable</span>

                                                                                                                )}

                                                                                                            </div>

                                                                                                            {siteScan.scan_status.target_url && (

                                                                                                                <a

                                                                                                                    href={siteScan.scan_status.target_url}

                                                                                                                    target="_blank"

                                                                                                                    rel="noreferrer"

                                                                                                                    className="inline-flex items-center gap-2 mt-3 text-blue-400 hover:underline text-sm"

                                                                                                                >

                                                                                                                    <ExternalLink size={14} />

                                                                                                                    Visit Website Manually

                                                                                                                </a>

                                                                                                            )}

                                                                                                        </div>

                                                                                                    </div>

                                                                                                </div>

                                                                                            )}

                                                                                            {/* Domain Registration (RDAP) - shown here for all scans including failed ones */}

                                                                                            {(siteScan?.rdap || rdap) && (

                                                                                                <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-6">

                                                                                                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">

                                                                                                        <Globe size={20} className="text-blue-400" />

                                                                                                        Domain Registration (RDAP)

                                                                                                    </h3>

                                                                                                    <div className="text-sm text-gray-300 space-y-3">

                                                                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

                                                                                                            <div className="bg-gray-900/50 rounded-lg p-3">

                                                                                                                <div className="text-gray-400 text-xs mb-1">Status</div>

                                                                                                                <div className={

                                                                                                                    domainAgeDetail?.status?.startsWith('Good') ? 'text-green-400 font-semibold' :

                                                                                                                    domainAgeDetail?.status?.startsWith('Moderate') ? 'text-yellow-400 font-semibold' :

                                                                                                                    domainAgeDetail?.status?.startsWith('Low') ? 'text-yellow-400 font-semibold' :

                                                                                                                    domainAgeDetail?.status?.startsWith('Critical') ? 'text-red-400 font-semibold' :

                                                                                                                    'text-gray-400'

                                                                                                                }>

                                                                                                                    {domainAgeDetail?.status || (typeof domainAgeDays === 'number' ? (domainAgeDays > (3*365) ? 'Good (> 3yr)' : domainAgeDays > 365 ? 'Moderate (1-3yr)' : 'Low (< 1yr)') : 'Unknown')}

                                                                                                                </div>

                                                                                                            </div>

                                                                                                            {typeof domainAgeDays === 'number' && (

                                                                                                                <div className="bg-gray-900/50 rounded-lg p-3">

                                                                                                                    <div className="text-gray-400 text-xs mb-1">Age</div>

                                                                                                                    <div className="text-white font-semibold">{domainAgeDays} days</div>

                                                                                                                </div>

                                                                                                            )}

                                                                                                            {((siteScan?.rdap || rdap)?.registrar?.name || (siteScan?.rdap || rdap)?.registrar?.iana_id) && (

                                                                                                                <div className="bg-gray-900/50 rounded-lg p-3">

                                                                                                                    <div className="text-gray-400 text-xs mb-1">Registrar</div>

                                                                                                                    <div className="text-white truncate">{(siteScan?.rdap || rdap)?.registrar?.name || 'Unknown'}</div>

                                                                                                                </div>

                                                                                                            )}

                                                                                                            {(siteScan?.rdap || rdap)?.registrar?.iana_id && (

                                                                                                                <div className="bg-gray-900/50 rounded-lg p-3">

                                                                                                                    <div className="text-gray-400 text-xs mb-1">IANA ID</div>

                                                                                                                    <div className="text-white">{(siteScan?.rdap || rdap)?.registrar?.iana_id}</div>

                                                                                                                </div>

                                                                                                            )}

                                                                                                        </div>
                                                                

                                                                                                        {/* Dates Row */}

                                                                                                        {((siteScan?.rdap || rdap)?.created_on || (siteScan?.rdap || rdap)?.updated_on || (siteScan?.rdap || rdap)?.expires_on) && (

                                                                                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-gray-700/50">

                                                                                                                <div><span className="text-gray-400">Created:</span> <span className="text-white">{(siteScan?.rdap || rdap)?.created_on || 'N/A'}</span></div>

                                                                                                                <div><span className="text-gray-400">Updated:</span> <span className="text-white">{(siteScan?.rdap || rdap)?.updated_on || 'N/A'}</span></div>

                                                                                                                <div><span className="text-gray-400">Expires:</span> <span className="text-white">{(siteScan?.rdap || rdap)?.expires_on || 'N/A'}</span></div>

                                                                                                            </div>

                                                                                                        )}
                                                                

                                                                                                        {/* Status codes */}

                                                                                                        {Array.isArray((siteScan?.rdap || rdap)?.status) && (siteScan?.rdap || rdap)?.status.length > 0 && (

                                                                                                            <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-700/50">

                                                                                                                {(siteScan?.rdap || rdap)?.status.slice(0, 8).map((st: string, i: number) => (

                                                                                                                    <span key={i} className="text-[10px] px-1.5 py-0.5 rounded border bg-gray-700/40 text-gray-300 border-gray-600">

                                                                                                                        {st}

                                                                                                                    </span>

                                                                                                                ))}

                                                                                                            </div>

                                                                                                        )}
                                                                

                                                                                                        {/* Nameservers */}

                                                                                                        {Array.isArray((siteScan?.rdap || rdap)?.nameservers) && (siteScan?.rdap || rdap)?.nameservers.length > 0 && (

                                                                                                            <div className="text-xs text-gray-400 pt-2 border-t border-gray-700/50">

                                                                                                                <span className="mr-2">Nameservers:</span>

                                                                                                                <span className="text-gray-300">{(siteScan?.rdap || rdap)?.nameservers.slice(0, 5).join(', ')}{(siteScan?.rdap || rdap)?.nameservers.length > 5 ? '…' : ''}</span>

                                                                                                            </div>

                                                                                                        )}

                                                                                                    </div>

                                                                                                </div>

                                                                                            )}

                                                                                            {/* Crawl Errors - only show for partial failures (not when whole scan failed) */}

                                                                                            {crawlSummary?.errors && crawlSummary.errors.length > 0 && siteScan?.scan_status?.status !== 'FAILED' && (

                                                                                                <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-6">

                                                                                                    <h3 className="text-lg font-bold text-white mb-4">Crawl Errors</h3>

                                                                                                    <div className="space-y-3">

                                                                                                        {crawlSummary.errors.slice(0, 8).map((err: any, i: number) => (

                                                                                                            <div key={i} className="bg-black/30 rounded border border-red-500/20 p-3 text-sm">

                                                                                                                <div className="flex items-center justify-between mb-1">

                                                                                                                    <span className="text-red-300 font-medium uppercase">{err.type}</span>

                                                                                                                    {err.status_code && <span className="text-gray-400">HTTP {err.status_code}</span>}

                                                                                                                </div>

                                                                                                                <div className="text-gray-300 break-all">{err.url}</div>

                                                                                                                {err.message && <div className="text-gray-500 mt-1">{err.message}</div>}

                                                                                                            </div>

                                                                                                        ))}

                                                                                                    </div>

                                                                                                </div>

                                                                                            )}

                                                                                        </div>

                                                                                    )}

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

                                                                                                                <div className="flex flex-col md:flex-row gap-8">

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

                                                                                                                            {siteScan.compliance_intelligence?.label || 'Advisory Score'}

                                                                                                                            {siteScan.compliance_intelligence?.signal_type === 'advisory' && (

                                                                                                                                <span className="block text-[10px] text-yellow-400 mt-0.5">(Advisory)</span>

                                                                                                                            )}

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

                                                                                                                                <div className="flex-1">

                                                                                                                                    <span className="text-xs font-bold text-red-300 uppercase tracking-wider block mb-1">{flag.type.replace('_', ' ')}</span>

                                                                                                                                    <p className="text-sm text-gray-300">{flag.message}</p>

                                                                                                                                    {flag.signal_reference && (

                                                                                                                                        <div className="mt-2 text-xs text-gray-500">

                                                                                                                                            Signal: {flag.signal_reference} ({flag.signal_type || 'advisory'})

                                                                                                                                        </div>

                                                                                                                                    )}

                                                                                                                                    {flag.triggering_keyword && (

                                                                                                                                        <div className="mt-1 text-xs text-gray-500">

                                                                                                                                            Keyword: {flag.triggering_keyword}

                                                                                                                                        </div>

                                                                                                                                    )}

                                                                                                                                </div>

                                                                                                                                <span className="text-xs font-bold bg-red-500/20 text-red-400 px-2 py-1 rounded">

                                                                                                                                    -{flag.penalty} pts

                                                                                                                                </span>

                                                                                                                            </div>

                                                                                                                        ))}

                                                                                                                    </div>

                                                                                                                </div>

                                                                                                            )}
                                                                    

                                                                                                            {/* Content Risk Section - PRD V2.1.1 with Intent Awareness */}

                                                                                                            {siteScan.content_risk && (

                                                                                                                <div className={`rounded-lg p-5 mt-4 ${

                                                                                                                    siteScan.content_risk.risk_score >= 50 

                                                                                                                        ? 'bg-yellow-500/5 border border-yellow-500/20' 

                                                                                                                        : 'bg-gray-800/30 border border-gray-700/30'

                                                                                                                }`}>

                                                                                                                    <h3 className={`font-bold flex items-center gap-2 mb-3 ${

                                                                                                                        siteScan.content_risk.risk_score >= 50 ? 'text-yellow-400' : 'text-gray-300'

                                                                                                                    }`}>

                                                                                                                        <AlertTriangle size={20} />

                                                                                                                        Content Risk Detection

                                                                                                                        <span className="text-xs text-gray-400 ml-2">(Rule-based, non-semantic)</span>

                                                                                                                        {siteScan.content_risk.policy_mentions_count > 0 && (

                                                                                                                            <span className="text-xs text-green-400 ml-2 bg-green-500/10 px-2 py-0.5 rounded">

                                                                                                                                {siteScan.content_risk.policy_mentions_count} policy mention(s) excluded

                                                                                                                            </span>

                                                                                                                        )}

                                                                                                                    </h3>

                                                                                                                    {siteScan.content_risk.detection_method && (

                                                                                                                        <p className="text-xs text-gray-400 mb-3">{siteScan.content_risk.detection_method}</p>

                                                                                                                    )}

                                                                                                                    {siteScan.content_risk.restricted_keywords_found && siteScan.content_risk.restricted_keywords_found.length > 0 && (

                                                                                                                        <div className="space-y-2">

                                                                                                                            {siteScan.content_risk.restricted_keywords_found.slice(0, 5).map((risk: any, idx: number) => {

                                                                                                                                const isProhibitive = risk.intent === 'prohibitive' && 

                                                                                                                                    ['privacy_policy', 'terms_conditions', 'terms_condition', 'refund_policy'].includes(risk.page_type);

                                                                                                                                return (

                                                                                                                                    <div key={idx} className={`rounded p-3 ${

                                                                                                                                        isProhibitive 

                                                                                                                                            ? 'bg-green-500/10 border border-green-500/30' 

                                                                                                                                            : 'bg-black/30 border border-yellow-500/30'

                                                                                                                                    }`}>

                                                                                                                                        <div className="flex justify-between items-start mb-2">

                                                                                                                                            <div className="flex items-center gap-2">

                                                                                                                                                <span className={`text-xs font-bold uppercase ${

                                                                                                                                                    isProhibitive ? 'text-green-300' : 'text-yellow-300'

                                                                                                                                                }`}>{risk.category}</span>

                                                                                                                                                {risk.page_type && (

                                                                                                                                                    <span className="text-xs text-gray-500 bg-black/30 px-1.5 py-0.5 rounded">

                                                                                                                                                        {risk.page_type.replace(/_/g, ' ')}

                                                                                                                                                    </span>

                                                                                                                                                )}

                                                                                                                                            </div>

                                                                                                                                            <span className={`text-xs ${

                                                                                                                                                isProhibitive ? 'text-green-400' : 'text-gray-400'

                                                                                                                                            }`}>

                                                                                                                                                {isProhibitive ? 'prohibitive (no penalty)' : risk.evidence?.severity || 'moderate'}

                                                                                                                                            </span>

                                                                                                                                        </div>

                                                                                                                                        <p className="text-sm text-gray-300 mb-2">Keyword: {risk.keyword}</p>

                                                                                                                                        {risk.intent_context && isProhibitive && (

                                                                                                                                            <div className="text-xs text-green-400/80 bg-green-500/5 p-2 rounded mb-2 font-mono">

                                                                                                                                                "{risk.intent_context}"

                                                                                                                                            </div>

                                                                                                                                        )}

                                                                                                                                        {risk.evidence && !isProhibitive && (

                                                                                                                                            <div className="text-xs text-gray-500 space-y-1">

                                                                                                                                                <div>Source: <a href={risk.evidence.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{risk.evidence.source_url}</a></div>

                                                                                                                                                <div>Snippet: {risk.evidence.evidence_snippet?.substring(0, 100)}...</div>

                                                                                                                                            </div>

                                                                                                                                        )}

                                                                                                                                    </div>

                                                                                                                                );

                                                                                                                            })}

                                                                                                                            {siteScan.content_risk.restricted_keywords_found.length > 5 && (

                                                                                                                                <p className="text-xs text-gray-500 text-center mt-2">

                                                                                                                                    + {siteScan.content_risk.restricted_keywords_found.length - 5} more keywords (see Content Risk tab)

                                                                                                                                </p>

                                                                                                                            )}

                                                                                                                        </div>

                                                                                                                    )}

                                                                                                                    {siteScan.content_risk.dummy_words_detected && (

                                                                                                                        <div className="mt-3 bg-black/30 border border-yellow-500/30 rounded p-3">

                                                                                                                            <span className="text-xs font-bold text-yellow-300 uppercase block mb-1">Dummy Text Detected</span>

                                                                                                                            <p className="text-sm text-gray-300">Lorem ipsum or placeholder text found</p>

                                                                                                                        </div>

                                                                                                                    )}

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

                                                                                                                            <span>SSL Certificate detected (HTTPS)</span>

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

                                                                                                                        {crawlData.compliance_checks?.ssl_certificate?.valid ? "Detected" : "Not Detected"}

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

                                                                                                {Object.entries(displayData.policy_details || {}).map(([key, value]: [string, any]) => {

                                                                                                    // Check if this is an e-commerce site (has shop/store in product URL)

                                                                                                    const productPage = displayData.policy_details?.product;

                                                                                                    const isEcommerce = productPage?.found && 

                                                                                                        (productPage.url?.includes('/shop') || 

                                                                                                         productPage.url?.includes('/store') ||

                                                                                                         productPage.url?.includes('/cart') ||

                                                                                                         productPage.url?.includes('/checkout'));
                                                            

                                                                                                    // For shipping_delivery and returns_refund on non-e-commerce sites, show as N/A

                                                                                                    const isShippingOrReturns = key === 'shipping_delivery' || key === 'returns_refund';

                                                                                                    const showAsNotApplicable = isShippingOrReturns && !value.found && !isEcommerce;
                                                            

                                                                                                    return (

                                                                                                        <div key={key} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 flex flex-col justify-between">

                                                                                                            <div>

                                                                                                                <div className="flex items-center gap-2 mb-2">

                                                                                                                    {value.found

                                                                                                                        ? <CheckCircle className="text-green-500" size={18} />

                                                                                                                        : showAsNotApplicable

                                                                                                                            ? <Info className="text-gray-400" size={18} />

                                                                                                                            : <XCircle className="text-gray-500" size={18} />

                                                                                                                    }

                                                                                                                    <h4 className="font-medium text-white capitalize">{key.replace(/_/g, ' ')}</h4>

                                                                                                                </div>

                                                                                                                <p className="text-xs text-gray-400 mb-3">

                                                                                                                    {showAsNotApplicable 

                                                                                                                        ? 'N/A (not applicable for service business)'

                                                                                                                        : value.status || (value.found ? 'Detected' : 'Not detected')

                                                                                                                    }

                                                                                                                </p>

                                                                                                                {value.evidence && (

                                                                                                                    <div className="mt-2 text-[10px] text-gray-500">

                                                                                                                        <span className="text-gray-600">Source: </span>

                                                                                                                        <a href={value.evidence.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">

                                                                                                                            {value.evidence.source_url}

                                                                                                                        </a>

                                                                                                                    </div>

                                                                                                                )}

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

                                                                                                    );

                                                                                                })}

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

                                                                                                                        <span className="text-gray-500 block mb-1 text-xs uppercase">Evidence</span>

                                                                                                                        {displayData.mcc_codes.primary_mcc.keywords_matched && Array.isArray(displayData.mcc_codes.primary_mcc.keywords_matched) ? (

                                                                                                                            <div className="flex flex-wrap gap-2">

                                                                                                                                {displayData.mcc_codes.primary_mcc.keywords_matched.map((kw: string, i: number) => (

                                                                                                                                    <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">{kw}</span>

                                                                                                                                ))}

                                                                                                                            </div>

                                                                                                                        ) : (

                                                                                                                            <span className="text-gray-400">High keyword match frequency on homepage.</span>

                                                                                                                        )}

                                                                                                                        {displayData.mcc_codes.primary_mcc.evidence && (

                                                                                                                            <div className="mt-2 text-[10px] text-gray-500">

                                                                                                                                <div>Pages: {displayData.mcc_codes.primary_mcc.evidence.additional_context?.pages_matched?.join(', ') || 'Unknown'}</div>

                                                                                                                            </div>

                                                                                                                        )}

                                                                                                                        {displayData.mcc_codes.primary_mcc.low_confidence && (

                                                                                                                            <div className="mt-2 text-xs text-yellow-400">

                                                                                                                                Low confidence classification (below 30% threshold)

                                                                                                                            </div>

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

                                                                                    {activeTab === 'content-risk' && (

                                                                                        <div className="space-y-6">

                                                                                            {/* Content Risk Analysis */}

                                                                                            {siteScan?.content_risk ? (

                                                                                                <div className="space-y-6">

                                                                                                    {/* Risk Score Summary */}

                                                                                                    <div className={`p-6 rounded-lg border ${

                                                                                                        siteScan.content_risk.risk_score >= 100 

                                                                                                            ? 'bg-red-500/10 border-red-500/30' 

                                                                                                            : siteScan.content_risk.risk_score >= 50 

                                                                                                            ? 'bg-yellow-500/10 border-yellow-500/30' 

                                                                                                            : 'bg-green-500/10 border-green-500/30'

                                                                                                    }`}>

                                                                                                        <div className="flex items-center justify-between mb-4">

                                                                                                            <div className="flex items-center gap-3">

                                                                                                                <AlertOctagon className={

                                                                                                                    siteScan.content_risk.risk_score >= 100 

                                                                                                                        ? 'text-red-400' 

                                                                                                                        : siteScan.content_risk.risk_score >= 50 

                                                                                                                        ? 'text-yellow-400' 

                                                                                                                        : 'text-green-400'

                                                                                                                } size={24} />

                                                                                                                <h3 className="text-lg font-bold text-white">Content Risk Score</h3>

                                                                                                            </div>

                                                                                                            <div className="text-right">

                                                                                                                <div className={`text-3xl font-bold ${

                                                                                                                    siteScan.content_risk.risk_score >= 100 

                                                                                                                        ? 'text-red-400' 

                                                                                                                        : siteScan.content_risk.risk_score >= 50 

                                                                                                                        ? 'text-yellow-400' 

                                                                                                                        : 'text-green-400'

                                                                                                                }`}>

                                                                                                                    {siteScan.content_risk.risk_score}

                                                                                                                </div>

                                                                                                                <div className="text-sm text-gray-400 mt-1">

                                                                                                                    {siteScan.content_risk.risk_contributing_count || siteScan.content_risk.restricted_keywords_found?.length || 0} risk keywords

                                                                                                                    {siteScan.content_risk.policy_mentions_count > 0 && (

                                                                                                                        <span className="text-green-400 ml-2">

                                                                                                                            + {siteScan.content_risk.policy_mentions_count} policy mentions

                                                                                                                        </span>

                                                                                                                    )}

                                                                                                                </div>

                                                                                                            </div>

                                                                                                        </div>

                                                                                                        <div className="text-sm text-gray-300">

                                                                                                            {siteScan.content_risk.risk_score >= 100 

                                                                                                                ? 'High risk content detected. Multiple prohibited keywords found.' 

                                                                                                                : siteScan.content_risk.risk_score >= 50 

                                                                                                                ? 'Moderate risk content detected. Some restricted keywords found.' 

                                                                                                                : siteScan.content_risk.policy_mentions_count > 0

                                                                                                                ? 'Low risk. Keywords found in policy pages with prohibitive intent (legal boilerplate).'

                                                                                                                : 'Low risk. Minimal or no restricted content detected.'}

                                                                                                        </div>

                                                                                                        {siteScan.content_risk.policy_mentions_count > 0 && (

                                                                                                            <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded text-sm">

                                                                                                                <span className="text-green-400 font-medium">Intent-Aware Detection:</span>

                                                                                                                <span className="text-gray-300 ml-2">

                                                                                                                    {siteScan.content_risk.policy_mentions_count} keyword(s) found in prohibitive context 

                                                                                                                    (e.g., "we do not allow...") and excluded from risk score.

                                                                                                                </span>

                                                                                                            </div>

                                                                                                        )}

                                                                                                    </div>

                                                                                                    {/* Dummy Words Detection */}

                                                                                                    {siteScan.content_risk.dummy_words_detected && (

                                                                                                        <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-5">

                                                                                                            <div className="flex items-center gap-2 mb-3">

                                                                                                                <AlertTriangle className="text-orange-400" size={20} />

                                                                                                                <h3 className="text-lg font-bold text-orange-400">Dummy Content Detected</h3>

                                                                                                            </div>

                                                                                                            <p className="text-sm text-gray-300 mb-3">

                                                                                                                Lorem ipsum or placeholder text was found on the website, indicating incomplete content.

                                                                                                            </p>

                                                                                                            {siteScan.content_risk.dummy_words && siteScan.content_risk.dummy_words.length > 0 && (

                                                                                                                <div className="flex flex-wrap gap-2">

                                                                                                                    {siteScan.content_risk.dummy_words.map((pattern: string, idx: number) => (

                                                                                                                        <span key={idx} className="px-3 py-1 bg-orange-500/20 text-orange-300 text-xs font-mono rounded border border-orange-500/30">

                                                                                                                            {pattern}

                                                                                                                        </span>

                                                                                                                    ))}

                                                                                                                </div>

                                                                                                            )}

                                                                                                        </div>

                                                                                                    )}

                                                                                                    {/* Restricted Keywords by Category */}

                                                                                                    {siteScan.content_risk.restricted_keywords_found && siteScan.content_risk.restricted_keywords_found.length > 0 ? (

                                                                                                        <div className="space-y-6">

                                                                                                            {/* Risk Contributing Keywords Section */}

                                                                                                            {(() => {

                                                                                                                // Separate risk keywords from policy mentions

                                                                                                                const riskKeywords = siteScan.content_risk.restricted_keywords_found.filter(

                                                                                                                    (item: any) => item.intent !== 'prohibitive' || 

                                                                                                                    !['privacy_policy', 'terms_conditions', 'terms_condition', 'refund_policy', 'returns_refund'].includes(item.page_type)

                                                                                                                );

                                                                                                                const policyMentions = siteScan.content_risk.restricted_keywords_found.filter(

                                                                                                                    (item: any) => item.intent === 'prohibitive' && 

                                                                                                                    ['privacy_policy', 'terms_conditions', 'terms_condition', 'refund_policy', 'returns_refund'].includes(item.page_type)

                                                                                                                );
                                                                        

                                                                                                                return (

                                                                                                                    <>

                                                                                                                        {riskKeywords.length > 0 && (

                                                                                                                            <div>

                                                                                                                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">

                                                                                                                                    <AlertOctagon className="text-red-400" size={20} />

                                                                                                                                    Risk-Contributing Keywords

                                                                                                                                    <span className="text-xs text-gray-400 font-normal ml-2">({riskKeywords.length} detected)</span>

                                                                                                                                </h3>

                                                                                                                                <div className="space-y-4">

                                                                                                                                    {(() => {

                                                                                                                                        // Group keywords by category

                                                                                                                                        const grouped: { [key: string]: { keyword: string; page_type: string; intent: string }[] } = {};

                                                                                                                                        riskKeywords.forEach((item: any) => {

                                                                                                                                            if (!grouped[item.category]) {

                                                                                                                                                grouped[item.category] = [];

                                                                                                                                            }

                                                                                                                                            if (!grouped[item.category].some((k: any) => k.keyword === item.keyword)) {

                                                                                                                                                grouped[item.category].push({ 

                                                                                                                                                    keyword: item.keyword, 

                                                                                                                                                    page_type: item.page_type,

                                                                                                                                                    intent: item.intent 

                                                                                                                                                });

                                                                                                                                            }

                                                                                                                                        });

                                                                                                                                        // Category severity mapping

                                                                                                                                        const categorySeverity: { [key: string]: { color: string; bg: string; border: string; label: string } } = {

                                                                                                                                            'child_pornography': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Child Pornography' },

                                                                                                                                            'adult': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Adult Content' },

                                                                                                                                            'gambling': { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'Gambling' },

                                                                                                                                            'weapons': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Weapons' },

                                                                                                                                            'drugs': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Illegal Drugs' },

                                                                                                                                            'pharmacy': { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'Prescription Drugs' },

                                                                                                                                            'crypto': { color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', label: 'Cryptocurrency' },

                                                                                                                                            'forex': { color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', label: 'Forex Trading' },

                                                                                                                                            'binary': { color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', label: 'Binary Options' },

                                                                                                                                            'alcohol': { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'Alcohol' },

                                                                                                                                            'tobacco': { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', label: 'Tobacco' },

                                                                                                                                            'counterfeit': { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'Counterfeit Goods' },

                                                                                                                                            'copyright': { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', label: 'Copyright Infringement' },

                                                                                                                                            'hacking': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Hacking Tools' },

                                                                                                                                            'illegal_goods': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Illegal Goods' },

                                                                                                                                        };

                                                                                                                                        return Object.entries(grouped).map(([category, keywords]) => {

                                                                                                                                            const severity = categorySeverity[category] || { 

                                                                                                                                                color: 'text-gray-400', 

                                                                                                                                                bg: 'bg-gray-500/10', 

                                                                                                                                                border: 'border-gray-500/30', 

                                                                                                                                                label: category.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())

                                                                                                                                            };

                                                                                                                                            return (

                                                                                                                                                <div key={category} className={`${severity.bg} ${severity.border} border rounded-lg p-5`}>

                                                                                                                                                    <div className="flex items-center justify-between mb-3">

                                                                                                                                                        <h4 className={`font-bold ${severity.color} flex items-center gap-2`}>

                                                                                                                                                            <AlertOctagon size={18} />

                                                                                                                                                            {severity.label}

                                                                                                                                                        </h4>

                                                                                                                                                        <span className="text-xs text-gray-400 bg-black/30 px-2 py-1 rounded">

                                                                                                                                                            {keywords.length} {keywords.length === 1 ? 'keyword' : 'keywords'}

                                                                                                                                                        </span>

                                                                                                                                                    </div>

                                                                                                                                                    <div className="flex flex-wrap gap-2">

                                                                                                                                                        {keywords.map((kw, idx) => (

                                                                                                                                                            <span key={idx} className="px-3 py-1.5 bg-black/30 text-gray-300 text-sm rounded border border-gray-700/50 font-mono flex items-center gap-2">

                                                                                                                                                                {kw.keyword}

                                                                                                                                                                {kw.page_type && (

                                                                                                                                                                    <span className="text-xs text-gray-500">

                                                                                                                                                                        ({kw.page_type.replace(/_/g, ' ')})

                                                                                                                                                                    </span>

                                                                                                                                                                )}

                                                                                                                                                            </span>

                                                                                                                                                        ))}

                                                                                                                                                    </div>

                                                                                                                                                </div>

                                                                                                                                            );

                                                                                                                                        });

                                                                                                                                    })()}

                                                                                                                                </div>

                                                                                                                            </div>

                                                                                                                        )}

                                                                                                                        {/* Policy Mentions Section (Prohibitive Intent) */}

                                                                                                                        {policyMentions.length > 0 && (

                                                                                                                            <div>

                                                                                                                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">

                                                                                                                                    <CheckCircle className="text-green-400" size={20} />

                                                                                                                                    Policy Mentions (Prohibitive Intent)

                                                                                                                                    <span className="text-xs text-gray-400 font-normal ml-2">({policyMentions.length} - excluded from risk score)</span>

                                                                                                                                </h3>

                                                                                                                                <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-5">

                                                                                                                                    <p className="text-sm text-gray-400 mb-4">

                                                                                                                                        These keywords were found on policy pages in prohibitive context 

                                                                                                                                        (e.g., "we do not allow gambling"). They indicate compliance awareness, not actual risk.

                                                                                                                                    </p>

                                                                                                                                    <div className="flex flex-wrap gap-2">

                                                                                                                                        {policyMentions.map((item: any, idx: number) => (

                                                                                                                                            <span key={idx} className="px-3 py-1.5 bg-green-500/10 text-green-300 text-sm rounded border border-green-500/30 font-mono flex items-center gap-2">

                                                                                                                                                <CheckCircle size={12} />

                                                                                                                                                {item.keyword}

                                                                                                                                                <span className="text-xs text-green-400/60">

                                                                                                                                                    ({item.page_type?.replace(/_/g, ' ') || 'policy'})

                                                                                                                                                </span>

                                                                                                                                            </span>

                                                                                                                                        ))}

                                                                                                                                    </div>

                                                                                                                                    {policyMentions[0]?.intent_context && (

                                                                                                                                        <div className="mt-3 p-3 bg-black/20 rounded text-xs text-gray-400 font-mono">

                                                                                                                                            Example context: "{policyMentions[0].intent_context}"

                                                                                                                                        </div>

                                                                                                                                    )}

                                                                                                                                </div>

                                                                                                                            </div>

                                                                                                                        )}

                                                                                                                    </>

                                                                                                                );

                                                                                                            })()}

                                                                                                        </div>

                                                                                                    ) : (

                                                                                                        <div className="text-center p-12 bg-gray-800/30 rounded-lg border border-gray-700/50 border-dashed">

                                                                                                            <CheckCircle className="mx-auto text-green-500 mb-3" size={32} />

                                                                                                            <h3 className="text-lg font-medium text-white mb-2">No Restricted Keywords Detected</h3>

                                                                                                            <p className="text-gray-500">No prohibited or restricted content keywords were found on this website.</p>

                                                                                                        </div>

                                                                                                    )}

                                                                                                </div>

                                                                                            ) : (

                                                                                                <div className="text-center p-12">

                                                                                                    <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-700">

                                                                                                        <AlertOctagon size={24} className="text-gray-600" />

                                                                                                    </div>

                                                                                                    <h3 className="text-lg font-medium text-white mb-2">Content Risk Analysis Not Available</h3>

                                                                                                    <p className="text-gray-500">Content risk data was not found in this scan report.</p>

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

export default SiteScanAgent;
