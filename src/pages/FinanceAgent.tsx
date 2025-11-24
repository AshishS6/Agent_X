
import { DollarSign, PieChart, FileText, CreditCard } from 'lucide-react';

const FinanceAgent = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Finance Agent</h1>
                <p className="text-gray-400">Expense tracking, invoice processing, and financial forecasting.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-green-500/10 rounded-lg text-green-400">
                            <DollarSign size={20} />
                        </div>
                        <h3 className="text-lg font-bold text-white">Monthly Spend</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">$45,230</p>
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
                    <p className="text-sm text-gray-400">Total value: $12,400</p>
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
                        { category: 'Software Subscriptions', amount: '$15,200', pct: 35 },
                        { category: 'Marketing & Ads', amount: '$12,500', pct: 28 },
                        { category: 'Office & Infrastructure', amount: '$8,400', pct: 18 },
                        { category: 'Travel & Events', amount: '$5,100', pct: 12 },
                    ].map((item, i) => (
                        <div key={i}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-300">{item.category}</span>
                                <span className="text-white font-medium">{item.amount}</span>
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
    );
};

export default FinanceAgent;
