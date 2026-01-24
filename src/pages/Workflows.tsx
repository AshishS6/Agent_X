import { useState } from 'react';
import {
    Plus,
    Calendar,
    MoreVertical,
    Play,
    Pause,
    Clock,
    CheckCircle2,
    Zap,
    Briefcase,
    LifeBuoy,
    Megaphone,
    GitBranch
} from 'lucide-react';
import clsx from 'clsx';
import { formatNumber, formatPercentage } from '../utils/formatting';
import { EmptyState } from '../components/EmptyState';

// Mock Data
const workflows = [
    {
        id: '1',
        name: 'New Lead Nurture',
        description: 'Enrich new leads from CRM and start outreach sequence.',
        trigger: 'New CRM Deal',
        agents: [
            { name: 'Lead Sourcing', icon: Zap },
            { name: 'Sales', icon: Briefcase },
            { name: 'Marketing', icon: Megaphone }
        ],
        status: 'active',
        metrics: {
            runs: 1240,
            successRate: 98.5,
            avgDuration: '45s'
        },
        lastRun: '2 mins ago'
    },
    {
        id: '2',
        name: 'Support Ticket Triage',
        description: 'Analyze incoming tickets, tag them, and draft initial replies.',
        trigger: 'New Zendesk Ticket',
        agents: [
            { name: 'Support', icon: LifeBuoy },
            { name: 'Intelligence', icon: Zap }
        ],
        status: 'active',
        metrics: {
            runs: 856,
            successRate: 92.1,
            avgDuration: '1m 20s'
        },
        lastRun: '15 mins ago'
    },
    {
        id: '3',
        name: 'Competitor Alert',
        description: 'Monitor competitor news and update strategy docs.',
        trigger: 'News Alert',
        agents: [
            { name: 'Market Research', icon: Zap },
            { name: 'Sales', icon: Briefcase }
        ],
        status: 'paused',
        metrics: {
            runs: 45,
            successRate: 100,
            avgDuration: '3m 10s'
        },
        lastRun: '2 days ago'
    }
];

const Workflows = () => {
    const [selectedWorkflow, setSelectedWorkflow] = useState(workflows[0]);
    const [filter, setFilter] = useState('All');

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Workflows</h1>
                    <p className="text-gray-400 text-sm">Manage and monitor your multi-agent automations</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg border border-gray-700 hover:bg-gray-700 text-sm">
                        <Calendar size={14} />
                        <span>Last 7 Days</span>
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium shadow-lg shadow-blue-500/20">
                        <Plus size={16} />
                        <span>New Workflow</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 min-h-0">
                {/* Workflow List (Left 2/3) */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Filters */}
                    <div className="flex items-center gap-2 mb-4">
                        {['All', 'Active', 'Paused', 'Draft'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-full text-xs font-medium transition-colors border",
                                    filter === f
                                        ? "bg-blue-600/10 text-blue-400 border-blue-600/20"
                                        : "bg-gray-800/50 text-gray-400 border-gray-700 hover:bg-gray-800 hover:text-gray-300"
                                )}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    {/* List */}
                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2">
                        {workflows.length === 0 ? (
                            <EmptyState
                                icon={GitBranch}
                                title="No workflows yet"
                                description="Create your first workflow to automate multi-agent tasks and processes."
                                primaryAction={{
                                    label: 'Create Workflow',
                                    onClick: () => {
                                        // TODO: Open workflow creation modal
                                        console.log('Create workflow');
                                    },
                                    icon: Plus,
                                }}
                                hint="Workflows allow you to chain multiple agents together for complex automation."
                            />
                        ) : (
                            workflows.map((workflow) => (
                            <div
                                key={workflow.id}
                                onClick={() => setSelectedWorkflow(workflow)}
                                className={clsx(
                                    "p-4 rounded-xl border transition-all cursor-pointer group",
                                    selectedWorkflow.id === workflow.id
                                        ? "bg-blue-600/5 border-blue-500/50 ring-1 ring-blue-500/20"
                                        : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/50 hover:border-gray-600"
                                )}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "w-10 h-10 rounded-lg flex items-center justify-center",
                                            workflow.status === 'active' ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                                        )}>
                                            {workflow.status === 'active' ? <Play size={20} /> : <Pause size={20} />}
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">{workflow.name}</h3>
                                            <p className="text-xs text-gray-500">{workflow.trigger}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={clsx(
                                            "px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider border",
                                            workflow.status === 'active'
                                                ? "bg-green-500/10 text-green-400 border-green-500/20"
                                                : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                                        )}>
                                            {workflow.status}
                                        </span>
                                        <button className="p-1 text-gray-500 hover:text-white rounded hover:bg-gray-700">
                                            <MoreVertical size={16} />
                                        </button>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-400 mb-4 line-clamp-1">{workflow.description}</p>

                                <div className="flex items-center justify-between pt-3 border-t border-gray-700/50">
                                    <div className="flex items-center -space-x-2">
                                        {workflow.agents.map((agent, i) => (
                                            <div key={i} className="w-6 h-6 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400" title={agent.name}>
                                                <agent.icon size={12} />
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-gray-500">
                                        <div className="flex items-center gap-1">
                                            <Clock size={12} />
                                            <span>{workflow.lastRun}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <CheckCircle2 size={12} className="text-green-500" />
                                            <span className="text-gray-300">{formatPercentage(workflow.metrics.successRate, 1)}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-300">{formatNumber(workflow.metrics.runs)}</span> runs
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                        )}
                    </div>
                </div>

                {/* Workflow Detail (Right 1/3) */}
                <div className="w-96 bg-gray-900 border border-gray-800 rounded-xl flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-800">
                        <div className="flex items-center justify-between mb-2">
                            <h2 className="font-semibold text-white">{selectedWorkflow.name}</h2>
                            <button className="text-xs text-blue-400 hover:text-blue-300 font-medium">Edit Workflow</button>
                        </div>
                        <p className="text-xs text-gray-400">{selectedWorkflow.description}</p>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Workflow Steps</h3>

                        <div className="space-y-4 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-800">
                            {/* Trigger Step */}
                            <div className="relative pl-10">
                                <div className="absolute left-0 top-0 w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-400 z-10">
                                    <Zap size={14} />
                                </div>
                                <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700">
                                    <div className="text-xs font-medium text-blue-400 mb-0.5">Trigger</div>
                                    <div className="text-sm text-gray-200">{selectedWorkflow.trigger}</div>
                                </div>
                            </div>

                            {/* Agent Steps (Mock) */}
                            {selectedWorkflow.agents.map((agent, i) => (
                                <div key={i} className="relative pl-10">
                                    <div className="absolute left-0 top-0 w-7 h-7 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-400 z-10">
                                        <agent.icon size={14} />
                                    </div>
                                    <div className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50">
                                        <div className="text-xs font-medium text-gray-500 mb-0.5">Step {i + 1}</div>
                                        <div className="text-sm text-gray-200">{agent.name} Action</div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-6 mb-3">Recent Runs</h3>
                        <div className="space-y-2">
                            {[1, 2, 3].map((run) => (
                                <div key={run} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-800/50 transition-colors cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                                        <span className="text-sm text-gray-300">Run #{1000 + run}</span>
                                    </div>
                                    <span className="text-xs text-gray-500">2m ago</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Workflows;
