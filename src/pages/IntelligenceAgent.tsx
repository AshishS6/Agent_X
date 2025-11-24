
import { Newspaper, Zap, Bookmark, Share2 } from 'lucide-react';

const IntelligenceAgent = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Intelligence Agent</h1>
                <p className="text-gray-400">Curated news, industry updates, and strategic insights.</p>
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
    );
};

export default IntelligenceAgent;
