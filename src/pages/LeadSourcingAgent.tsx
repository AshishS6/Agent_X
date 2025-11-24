
import { Target, Filter, UserPlus, Download } from 'lucide-react';

const LeadSourcingAgent = () => {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Lead Sourcing Agent</h1>
                    <p className="text-gray-400">Find and enrich potential leads for your sales team.</p>
                </div>
                <div className="flex gap-3">
                    <button className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2">
                        <Filter size={18} />
                        Filters
                    </button>
                    <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2">
                        <UserPlus size={18} />
                        Find Leads
                    </button>
                </div>
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
    );
};

export default LeadSourcingAgent;
