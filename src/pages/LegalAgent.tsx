import React, { useMemo } from 'react';
import { Scale, FileText, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber } from '../utils/formatting';

const LegalAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 8,
        statusCounts: { completed: 6, failed: 1, processing: 1 },
    };

    const overviewContent = useMemo(() => (
        <div className="space-y-6">
            {/* KPI Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Tasks', value: formatNumber(metrics.totalTasks || 0, { showThousands: true }), color: 'text-blue-400', bg: 'bg-blue-400/10' },
                    { label: 'Completed', value: formatNumber(metrics.statusCounts?.completed || 0, { showThousands: true }), color: 'text-green-400', bg: 'bg-green-400/10' },
                    { label: 'Failed', value: formatNumber(metrics.statusCounts?.failed || 0, { showThousands: true }), color: 'text-red-400', bg: 'bg-red-400/10' },
                    { label: 'In Progress', value: formatNumber(metrics.statusCounts?.processing || 0, { showThousands: true }), color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
                ].map((stat, i) => (
                    <div key={i} className="bg-gray-900 p-4 rounded-xl border border-gray-800">
                        <p className="text-sm text-gray-400">{stat.label}</p>
                        <div className="flex items-end justify-between mt-2">
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FileText className="text-blue-400" size={20} />
                        Contract Review Queue
                    </h3>
                    <div className="space-y-3">
                        {[
                            { name: 'Vendor Agreement - Acme Corp', status: 'Reviewing', risk: 'Low' },
                            { name: 'NDA - Project X', status: 'Pending', risk: 'Medium' },
                            { name: 'Service Level Agreement', status: 'Completed', risk: 'None' },
                        ].map((doc, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800">
                                <div>
                                    <p className="text-sm font-medium text-white">{doc.name}</p>
                                    <span className="text-xs text-gray-500">{doc.status}</span>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded font-medium ${doc.risk === 'Low' ? 'bg-green-500/10 text-green-400' : doc.risk === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-gray-700 text-gray-300'}`}>
                                    {doc.risk} Risk
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Scale className="text-purple-400" size={20} />
                        Compliance Status
                    </h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">GDPR Compliance</span>
                            <CheckCircle className="text-green-500" size={18} />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">SOC 2 Type II</span>
                            <CheckCircle className="text-green-500" size={18} />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">CCPA</span>
                            <div className="flex items-center gap-2 text-yellow-400">
                                <span className="text-xs">Review Needed</span>
                                <AlertTriangle size={18} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    ), []);

    const conversationsContent = useMemo(() => (
        <div className="w-full flex-1 min-h-0 flex flex-col bg-gray-900 rounded-xl border border-gray-800">
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                <EmptyState
                    icon={Scale}
                    title="No conversation history yet"
                    description="Legal agent conversations will appear here once tasks are executed."
                    hint="Conversations show contract reviews, compliance checks, and risk management results."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Contract Review', desc: 'Analyzes contracts for risks and compliance issues.', tools: ['NLP Analysis', 'Risk Scoring'] },
                { title: 'Compliance Checking', desc: 'Verifies compliance with regulations and standards.', tools: ['Regulatory DB', 'Rule Engine'] },
                { title: 'Risk Assessment', desc: 'Identifies and quantifies legal risks in documents.', tools: ['Risk Models', 'Historical Data'] },
                { title: 'Document Generation', desc: 'Generates legal documents and templates.', tools: ['Template Engine', 'Clause Library'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-purple-500/10 p-2 rounded-lg">
                            <Scale className="text-purple-400" size={20} />
                        </div>
                    </div>
                    <p className="text-gray-400 mb-4">{skill.desc}</p>
                    <div className="flex flex-wrap gap-2">
                        {skill.tools.map((tool) => (
                            <span key={tool} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-md border border-gray-700">
                                {tool}
                            </span>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    ), []);

    const logsContent = useMemo(() => (
        <div className="space-y-4">
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-4">Activity Logs</h3>
                <EmptyState
                    icon={FileText}
                    title="No logs available"
                    description="Task execution logs will appear here once tasks are processed."
                    hint="Logs show detailed execution information for debugging and monitoring."
                    variant="minimal"
                />
            </div>
        </div>
    ), []);

    const configContent = useMemo(() => (
        <div className="space-y-6">
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-6">Data Sources</h3>
                <div className="space-y-4">
                    {['Document Management', 'Regulatory Database', 'Case Law Database', 'Compliance Platform'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <FileText size={20} className="text-gray-400" />
                                </div>
                                <div>
                                    <p className="font-medium text-white">{source}</p>
                                    <p className="text-xs text-gray-500">Not connected</p>
                                </div>
                            </div>
                            <button className="text-sm text-blue-400 hover:text-blue-300">Connect</button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    ), []);

    return (
        <AgentLayout
            name="Legal Agent"
            description="Contract review, compliance checks, and risk management."
            icon={Scale}
            color="bg-purple-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default LegalAgent;
