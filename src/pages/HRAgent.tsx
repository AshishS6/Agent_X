
import { Users, FileText, Calendar } from 'lucide-react';

const HRAgent = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">HR Agent</h1>
                <p className="text-gray-400">Recruitment, onboarding, and employee management.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-white">Candidates</h3>
                        <Users className="text-purple-400" size={20} />
                    </div>
                    <div className="text-3xl font-bold text-white mb-2">24</div>
                    <p className="text-sm text-gray-400">Active applications in pipeline</p>
                    <div className="mt-6 flex gap-2">
                        <span className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded border border-purple-500/20">
                            8 Screening
                        </span>
                        <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded border border-blue-500/20">
                            4 Interview
                        </span>
                    </div>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-white">Documents</h3>
                        <FileText className="text-orange-400" size={20} />
                    </div>
                    <div className="text-3xl font-bold text-white mb-2">5</div>
                    <p className="text-sm text-gray-400">Pending signatures</p>
                    <button className="mt-6 w-full py-2 bg-gray-800 hover:bg-gray-700 text-sm text-white rounded transition-colors">
                        View Documents
                    </button>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-white">Interviews</h3>
                        <Calendar className="text-green-400" size={20} />
                    </div>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                            <span>10:00 AM - Frontend Dev</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                            <span>2:30 PM - Product Manager</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HRAgent;
