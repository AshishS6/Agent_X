import React, { useMemo } from 'react';
import { Megaphone, PenTool, BarChart, Loader2, FileText } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber } from '../utils/formatting';

const MarketingAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 12,
        statusCounts: { completed: 10, failed: 1, processing: 1 },
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Megaphone className="text-pink-400" size={20} />
                                Active Campaigns
                            </h3>
                            <button className="text-sm text-blue-400 hover:text-blue-300">View All</button>
                        </div>
                        <div className="space-y-4">
                            {[
                                { name: 'Summer Sale Promo', status: 'Active', spend: '$1,200', roas: '3.5x' },
                                { name: 'New Feature Launch', status: 'Learning', spend: '$450', roas: '1.2x' },
                                { name: 'Retargeting Q3', status: 'Paused', spend: '$0', roas: '-' },
                            ].map((campaign, i) => (
                                <div key={i} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                                    <div>
                                        <p className="font-medium text-white">{campaign.name}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`w-2 h-2 rounded-full ${campaign.status === 'Active' ? 'bg-green-500' : campaign.status === 'Learning' ? 'bg-yellow-500' : 'bg-gray-500'}`} />
                                            <span className="text-xs text-gray-400">{campaign.status}</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm text-white">{campaign.spend}</p>
                                        <p className="text-xs text-gray-500">ROAS: {campaign.roas}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <PenTool className="text-purple-400" size={20} />
                            Content Generator
                        </h3>
                        <div className="space-y-3">
                            <textarea
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                                rows={3}
                                placeholder="Describe the content you need (e.g., 'LinkedIn post about our new AI features')..."
                            ></textarea>
                            <div className="flex justify-end">
                                <button className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                                    Generate Drafts
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <BarChart className="text-blue-400" size={20} />
                            Performance
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Total Impressions</p>
                                <p className="text-2xl font-bold text-white">1.2M</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Click-Through Rate</p>
                                <p className="text-2xl font-bold text-white">2.4%</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Cost Per Lead</p>
                                <p className="text-2xl font-bold text-white">$14.50</p>
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
                    icon={Megaphone}
                    title="No conversation history yet"
                    description="Marketing agent conversations will appear here once tasks are executed."
                    hint="Conversations show campaign management, ad optimization, and content generation results."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Campaign Management', desc: 'Creates and optimizes marketing campaigns across channels.', tools: ['Ad Platforms', 'Analytics'] },
                { title: 'Content Generation', desc: 'Generates marketing copy, social posts, and ad creatives.', tools: ['GPT-4', 'Claude'] },
                { title: 'A/B Testing', desc: 'Designs and analyzes A/B tests for campaigns and content.', tools: ['Statistical Analysis', 'Reporting'] },
                { title: 'Audience Targeting', desc: 'Identifies and segments target audiences for campaigns.', tools: ['Data Analysis', 'CRM Integration'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-pink-500/10 p-2 rounded-lg">
                            <Megaphone className="text-pink-400" size={20} />
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
                    {['Google Ads', 'Facebook Ads', 'LinkedIn Ads', 'Analytics Platform'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <BarChart size={20} className="text-gray-400" />
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
            name="Marketing Agent"
            description="Campaign management, ad optimization, and content generation."
            icon={Megaphone}
            color="bg-pink-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default MarketingAgent;
