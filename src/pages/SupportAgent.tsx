
import { MessageCircle, AlertCircle, CheckCircle } from 'lucide-react';

const SupportAgent = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Support Agent</h1>
                <p className="text-gray-400">Monitor tickets and customer inquiries.</p>
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
    );
};

export default SupportAgent;
