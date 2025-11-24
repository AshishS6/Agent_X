
import { Megaphone, PenTool, BarChart } from 'lucide-react';

const MarketingAgent = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Marketing Agent</h1>
                <p className="text-gray-400">Campaign management, ad optimization, and content generation.</p>
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
    );
};

export default MarketingAgent;
