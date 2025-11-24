
import { Scale, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

const LegalAgent = () => {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Legal Agent</h1>
                    <p className="text-gray-400">Contract review, compliance checks, and risk management.</p>
                </div>
                <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                    Upload Contract
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FileText className="text-blue-400" size={20} />
                        Contract Review Queue
                    </h3>
                    <div className="space-y-3">
                        {[
                            { name: 'Vendor Agreement - Acme Corp', status: 'Reviewing', risk: 'Low' },
                            { name: 'NDA - Project X', status: 'Pending', risk: 'Medium' },
                            { name: 'Service Level Agreement', status: 'Completed', risk: 'None' },
                        ].map((doc, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800">
                                <div>
                                    <p className="text-sm font-medium text-white">{doc.name}</p>
                                    <span className="text-xs text-gray-500">{doc.status}</span>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded font-medium ${doc.risk === 'Low' ? 'bg-green-500/10 text-green-400' : doc.risk === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-gray-700 text-gray-300'}`}>
                                    {doc.risk} Risk
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Scale className="text-purple-400" size={20} />
                        Compliance Status
                    </h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">GDPR Compliance</span>
                            <CheckCircle className="text-green-500" size={18} />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">SOC 2 Type II</span>
                            <CheckCircle className="text-green-500" size={18} />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">CCPA</span>
                            <div className="flex items-center gap-2 text-yellow-400">
                                <span className="text-xs">Review Needed</span>
                                <AlertTriangle size={18} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LegalAgent;
