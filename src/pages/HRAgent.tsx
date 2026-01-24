import React, { useMemo } from 'react';
import { Users, FileText, Calendar, Loader2 } from 'lucide-react';
import AgentLayout from '../components/Layout/AgentLayout';
import { EmptyState } from '../components/EmptyState';
import { formatNumber } from '../utils/formatting';

const HRAgent = () => {
    // Mock data - will be replaced when backend is implemented
    const metrics = {
        totalTasks: 24,
        statusCounts: { completed: 18, failed: 2, processing: 4 },
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
                <div className="lg:col-span-2 bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Users className="text-purple-400" size={20} />
                        Candidates
                    </h3>
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

                <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <FileText className="text-orange-400" size={20} />
                            Documents
                        </h3>
                        <div className="text-3xl font-bold text-white mb-2">5</div>
                        <p className="text-sm text-gray-400">Pending signatures</p>
                        <button className="mt-6 w-full py-2 bg-gray-800 hover:bg-gray-700 text-sm text-white rounded transition-colors">
                            View Documents
                        </button>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Calendar className="text-green-400" size={20} />
                            Interviews
                        </h3>
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
        </div>
    ), []);

    const conversationsContent = useMemo(() => (
        <div className="w-full flex-1 min-h-0 flex flex-col bg-gray-900 rounded-xl border border-gray-800">
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
                <EmptyState
                    icon={Users}
                    title="No conversation history yet"
                    description="HR agent conversations will appear here once tasks are executed."
                    hint="Conversations show recruitment, onboarding, and employee management interactions."
                />
            </div>
        </div>
    ), []);

    const skillsContent = useMemo(() => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
                { title: 'Resume Screening', desc: 'Automatically screens resumes and ranks candidates.', tools: ['AI Scoring', 'Keyword Matching'] },
                { title: 'Interview Scheduling', desc: 'Coordinates interview times with candidates and interviewers.', tools: ['Calendar API', 'Email Automation'] },
                { title: 'Onboarding Automation', desc: 'Streamlines new employee onboarding workflows.', tools: ['Document Generation', 'Task Management'] },
                { title: 'Compliance Checks', desc: 'Verifies candidate eligibility and documentation.', tools: ['Background Checks', 'Document Verification'] },
            ].map((skill, i) => (
                <div key={i} className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-white">{skill.title}</h3>
                        <div className="bg-purple-500/10 p-2 rounded-lg">
                            <Users className="text-purple-400" size={20} />
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
                    {['ATS System', 'LinkedIn', 'Job Boards', 'Background Check Service'].map((source) => (
                        <div key={source} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                    <Users size={20} className="text-gray-400" />
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
            name="HR Agent"
            description="Recruitment, onboarding, and employee management."
            icon={Users}
            color="bg-purple-500"
            overviewContent={overviewContent}
            conversationsContent={conversationsContent}
            skillsContent={skillsContent}
            logsContent={logsContent}
            configContent={configContent}
        />
    );
};

export default HRAgent;
