import React, { useMemo } from 'react';
import { Target, Filter, UserPlus, Download, Loader2, FileText } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber, formatPercentage } from '../utils/formatting';

const LeadSourcingAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 32,
        statusCounts: { completed: 28, failed: 2, processing: 2 },
    };

    const overviewContent = useMemo(() => (
        <div className="space-y-6">
            {/* KPI Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Tasks', value: formatNumber(metrics.totalTasks || 0, { showThousands: true }), color: 'text-blue-400', bg: 'bg-blue-400/10' },
                    { label: 'Completed', value: formatNumber(metrics.statusCounts?.completed || 0, { showThousands: true }), color: 'text-green-400', bg: 'bg-green-400/10' },
                    { label: 'Failed', value: formatNumber(metrics.statusCounts?.failed || 0, { showThousands: true }), color: 'text-red-400', bg: 'bg-red-400/10' },
                    { label: 'Success Rate', value: formatPercentage(metrics.totalTasks ? ((metrics.statusCounts?.completed || 0) / metrics.totalTasks) * 100 : 100, 1, false), color: 'text-orange-400', bg: 'bg-orange-400/10' },
                ].map((stat, i) => (
                    <div key={i} className="bg-gray-900 p-4 rounded-xl border border-gray-800">
                        <p className="text-sm text-gray-400">{stat.label}</p>
                        <div className="flex items-end justify-between mt-2">
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Target className="text-red-400" size={20} />
                        New Prospects
                    </h3>
                    <button className="text-gray-400 hover:text-white transition-colors">
                        <Download size={18} />
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="bg-gray-800/50 text-gray-200 uppercase font-medium">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Title</th>
                                <th className="px-6 py-3">Company</th>
                                <th className="px-6 py-3">Location</th>
                                <th className="px-6 py-3">Match Score</th>
                                <th className="px-6 py-3">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {[
                                { name: 'Sarah Jenkins', title: 'VP of Engineering', company: 'TechFlow', loc: 'San Francisco', score: 98 },
                                { name: 'Michael Chen', title: 'CTO', company: 'DataSphere', loc: 'New York', score: 95 },
                                { name: 'Jessica Wu', title: 'Head of Product', company: 'Innovate Inc', loc: 'Austin', score: 88 },
                                { name: 'David Miller', title: 'Director of IT', company: 'Global Corp', loc: 'London', score: 82 },
                            ].map((lead, i) => (
                                <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                                    <td className="px-6 py-4 font-medium text-white">{lead.name}</td>
                                    <td className="px-6 py-4">{lead.title}</td>
                                    <td className="px-6 py-4">{lead.company}</td>
                                    <td className="px-6 py-4">{lead.loc}</td>
                                    <td className="px-6 py-4">
                                        <span className="text-green-400 font-medium">{lead.score}%</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button className="text-blue-400 hover:text-blue-300 font-medium">Enrich</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    ), []);

    const conversationsContent = useMemo(() => (
        <div className="w-full flex-1 min-h-0 flex flex-col bg-gray-900 rounded-xl border border-gray-800">
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                <EmptyState
                    icon={Target}
                    title="No conversation history yet"
                    description="Lead sourcing agent conversations will appear here once tasks are executed."
                    hint="Conversations show lead discovery, enrichment, and qualification results."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Lead Discovery', desc: 'Finds potential leads based on criteria and signals.', tools: ['Data Sources', 'Signal Detection'] },
                { title: 'Lead Enrichment', desc: 'Enriches lead data with additional information.', tools: ['Data APIs', 'Company DB'] },
                { title: 'Lead Scoring', desc: 'Scores leads based on fit and engagement signals.', tools: ['ML Models', 'Scoring Engine'] },
                { title: 'CRM Integration', desc: 'Syncs qualified leads to CRM systems.', tools: ['Salesforce', 'HubSpot'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-red-500/10 p-2 rounded-lg">
                            <Target className="text-red-400" size={20} />
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
                    {['LinkedIn', 'Clearbit', 'ZoomInfo', 'CRM System'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <UserPlus size={20} className="text-gray-400" />
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
            name="Lead Sourcing Agent"
            description="Find and enrich potential leads for your sales team."
            icon={Target}
            color="bg-red-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default LeadSourcingAgent;
