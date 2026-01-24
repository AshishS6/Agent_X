import React, { useMemo } from 'react';
import { MessageCircle, AlertCircle, CheckCircle, LifeBuoy, FileText } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber, formatPercentage } from '../utils/formatting';

const SupportAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 45,
        statusCounts: { completed: 42, failed: 2, processing: 1 },
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                        <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                            <h3 className="text-lg font-bold text-white">Active Tickets</h3>
                            <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full border border-blue-500/20">
                                12 Open
                            </span>
                        </div>
                        <div className="divide-y divide-gray-800">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="p-4 hover:bg-gray-800/50 transition-colors flex items-start gap-4">
                                    <div className="p-2 bg-gray-800 rounded-lg text-gray-400">
                                        <MessageCircle size={18} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between mb-1">
                                            <h4 className="text-white font-medium text-sm">Login issue on mobile app</h4>
                                            <span className="text-xs text-gray-500">2h ago</span>
                                        </div>
                                        <p className="text-gray-400 text-sm line-clamp-1">
                                            Customer is unable to reset password via the magic link...
                                        </p>
                                    </div>
                                    <button className="px-3 py-1 text-xs font-medium text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded hover:bg-blue-500/10 transition-colors">
                                        View
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4">Performance</h3>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">Response Time</span>
                                    <span className="text-white font-medium">1.2m</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-green-500 h-1.5 rounded-full w-4/5"></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">Resolution Rate</span>
                                    <span className="text-white font-medium">94%</span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-1.5">
                                    <div className="bg-blue-500 h-1.5 rounded-full w-[94%]"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
                        <div className="space-y-2">
                            <button className="w-full text-left px-4 py-3 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-colors flex items-center gap-3">
                                <AlertCircle size={16} className="text-red-400" />
                                Escalate Ticket
                            </button>
                            <button className="w-full text-left px-4 py-3 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-colors flex items-center gap-3">
                                <CheckCircle size={16} className="text-green-400" />
                                Mark as Resolved
                            </button>
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
                    icon={MessageCircle}
                    title="No conversation history yet"
                    description="Support agent conversations will appear here once tasks are executed."
                    hint="Conversations show ticket interactions, customer inquiries, and resolution details."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Ticket Triage', desc: 'Automatically categorizes and prioritizes support tickets.', tools: ['NLP Classification', 'Priority Scoring'] },
                { title: 'Response Generation', desc: 'Generates personalized responses to customer inquiries.', tools: ['LLM', 'Knowledge Base'] },
                { title: 'Escalation Detection', desc: 'Identifies tickets that need human intervention.', tools: ['Sentiment Analysis', 'Complexity Scoring'] },
                { title: 'Knowledge Base Search', desc: 'Searches internal documentation for solutions.', tools: ['Vector Search', 'RAG'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-blue-500/10 p-2 rounded-lg">
                            <LifeBuoy className="text-blue-400" size={20} />
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
                    {['Zendesk', 'Intercom', 'Slack', 'Email System'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <MessageCircle size={20} className="text-gray-400" />
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
            name="Support Agent"
            description="Monitor tickets and customer inquiries."
            icon={LifeBuoy}
            color="bg-blue-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default SupportAgent;
