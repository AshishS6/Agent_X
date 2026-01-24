import React, { useMemo } from 'react';
import { Newspaper, Zap, Bookmark, Share2, Loader2, FileText } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber } from '../utils/formatting';

const IntelligenceAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 18,
        statusCounts: { completed: 16, failed: 1, processing: 1 },
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
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Newspaper className="text-blue-400" size={20} />
                            Latest Briefings
                        </h3>
                        <div className="space-y-6">
                            {[
                                { title: 'The Future of Generative AI in Enterprise', source: 'TechCrunch', time: '1 hour ago', summary: 'New report suggests 85% of enterprises will adopt GenAI by 2026...' },
                                { title: 'Global Supply Chain Disruptions Ease', source: 'Bloomberg', time: '4 hours ago', summary: 'Shipping costs normalize as major ports clear backlogs...' },
                                { title: 'Competitor X Acquires Startup Y', source: 'Reuters', time: 'Yesterday', summary: 'Strategic acquisition to bolster their mobile capabilities...' },
                            ].map((news, i) => (
                                <div key={i} className="group">
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="text-white font-medium group-hover:text-blue-400 transition-colors cursor-pointer">{news.title}</h4>
                                        <span className="text-xs text-gray-500">{news.time}</span>
                                    </div>
                                    <p className="text-sm text-gray-400 mb-3">{news.summary}</p>
                                    <div className="flex items-center gap-4">
                                        <span className="text-xs font-medium text-gray-500 bg-gray-800 px-2 py-1 rounded">{news.source}</span>
                                        <div className="flex gap-2">
                                            <button className="text-gray-500 hover:text-white transition-colors"><Bookmark size={16} /></button>
                                            <button className="text-gray-500 hover:text-white transition-colors"><Share2 size={16} /></button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Zap className="text-yellow-400" size={20} />
                            Flash Insights
                        </h3>
                        <div className="space-y-4">
                            <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                <p className="text-sm text-yellow-200">Regulatory changes in EU may impact Q4 strategy. Review recommended.</p>
                            </div>
                            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                                <p className="text-sm text-blue-200">Emerging trend: "Green IT" mentions up 400% this month.</p>
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
                    icon={Newspaper}
                    title="No conversation history yet"
                    description="Intelligence agent conversations will appear here once tasks are executed."
                    hint="Conversations show curated news, industry updates, and strategic insights."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'News Curation', desc: 'Curates relevant news and industry updates.', tools: ['News APIs', 'Content Filtering'] },
                { title: 'Trend Analysis', desc: 'Identifies emerging trends and patterns.', tools: ['NLP', 'Sentiment Analysis'] },
                { title: 'Competitive Intelligence', desc: 'Monitors competitor activities and strategies.', tools: ['Web Scraping', 'Data Aggregation'] },
                { title: 'Strategic Insights', desc: 'Generates actionable strategic recommendations.', tools: ['Analysis Engine', 'Report Generation'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-blue-500/10 p-2 rounded-lg">
                            <Newspaper className="text-blue-400" size={20} />
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
                    {['News APIs', 'RSS Feeds', 'Social Media', 'Industry Databases'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <Newspaper size={20} className="text-gray-400" />
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
            name="Intelligence Agent"
            description="Curated news, industry updates, and strategic insights."
            icon={Newspaper}
            color="bg-blue-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default IntelligenceAgent;
