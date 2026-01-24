import React, { useMemo } from 'react';
import { DollarSign, PieChart, FileText, CreditCard, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber, formatCurrency } from '../utils/formatting';

const FinanceAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 15,
        statusCounts: { completed: 12, failed: 1, processing: 2 },
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

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-green-500/10 rounded-lg text-green-400">
                            <DollarSign size={20} />
                        </div>
                        <h3 className="text-lg font-bold text-white">Monthly Spend</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">{formatCurrency(45230)}</p>
                    <p className="text-sm text-green-400">-5% vs last month</p>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                            <FileText size={20} />
                        </div>
                        <h3 className="text-lg font-bold text-white">Pending Invoices</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">8</p>
                    <p className="text-sm text-gray-400">Total value: {formatCurrency(12400)}</p>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                            <CreditCard size={20} />
                        </div>
                        <h3 className="text-lg font-bold text-white">Corporate Cards</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">Active</p>
                    <p className="text-sm text-gray-400">Next billing: Nov 25</p>
                </div>
            </div>

            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <PieChart className="text-orange-400" size={20} />
                    Expense Breakdown
                </h3>
                <div className="space-y-4">
                    {[
                        { category: 'Software Subscriptions', amount: 15200, pct: 35 },
                        { category: 'Marketing & Ads', amount: 12500, pct: 28 },
                        { category: 'Office & Infrastructure', amount: 8400, pct: 18 },
                        { category: 'Travel & Events', amount: 5100, pct: 12 },
                    ].map((item, i) => (
                        <div key={i}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-300">{item.category}</span>
                                <span className="text-white font-medium">{formatCurrency(item.amount)}</span>
                            </div>
                            <div className="w-full bg-gray-800 rounded-full h-2">
                                <div
                                    className="bg-blue-500 h-2 rounded-full"
                                    style={{ width: `${item.pct}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    ), []);

    const conversationsContent = useMemo(() => (
        <div className="w-full flex-1 min-h-0 flex flex-col bg-gray-900 rounded-xl border border-gray-800">
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                <EmptyState
                    icon={DollarSign}
                    title="No conversation history yet"
                    description="Finance agent conversations will appear here once tasks are executed."
                    hint="Conversations show expense tracking, invoice processing, and financial forecasting results."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Expense Tracking', desc: 'Automatically categorizes and tracks business expenses.', tools: ['Receipt OCR', 'Category AI'] },
                { title: 'Invoice Processing', desc: 'Processes and validates invoices for payment.', tools: ['Document Parsing', 'Approval Workflow'] },
                { title: 'Financial Forecasting', desc: 'Generates financial forecasts and budget projections.', tools: ['Data Analysis', 'ML Models'] },
                { title: 'Compliance Monitoring', desc: 'Monitors financial transactions for compliance issues.', tools: ['Rule Engine', 'Alert System'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-green-500/10 p-2 rounded-lg">
                            <DollarSign className="text-green-400" size={20} />
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
                    {['Accounting Software', 'Banking API', 'Credit Card Provider', 'Expense Management'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <CreditCard size={20} className="text-gray-400" />
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
            name="Finance Agent"
            description="Expense tracking, invoice processing, and financial forecasting."
            icon={DollarSign}
            color="bg-green-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default FinanceAgent;
