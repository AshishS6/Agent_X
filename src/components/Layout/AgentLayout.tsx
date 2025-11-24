import React, { useState } from 'react';
import {
    Settings,
    MessageSquare,
    Zap,
    BarChart2,
    Power,
    MoreVertical
} from 'lucide-react';
import clsx from 'clsx';

interface AgentLayoutProps {
    name: string;
    description: string;
    icon: React.ElementType;
    color: string;
    children?: React.ReactNode; // For custom content if needed
    // Tab content props
    overviewContent: React.ReactNode;
    conversationsContent: React.ReactNode;
    skillsContent: React.ReactNode;
    configContent: React.ReactNode;
}

const AgentLayout = ({
    name,
    description,
    icon: Icon,
    color,
    overviewContent,
    conversationsContent,
    skillsContent,
    configContent
}: AgentLayoutProps) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'conversations' | 'skills' | 'config'>('overview');
    const [isEnabled, setIsEnabled] = useState(true);

    const tabs = [
        { id: 'overview', label: 'Overview', icon: BarChart2 },
        { id: 'conversations', label: 'Conversations', icon: MessageSquare },
        { id: 'skills', label: 'Skills & Playbooks', icon: Zap },
        { id: 'config', label: 'Configuration', icon: Settings },
    ];

    return (
        <div className="space-y-6">
            {/* Agent Header */}
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 flex items-start justify-between">
                <div className="flex items-center gap-4">
                    <div className={`p-4 rounded-xl ${color} bg-opacity-10`}>
                        <Icon className={`w-8 h-8 ${color.replace('bg-', 'text-')}`} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                            {name}
                            <span className={clsx(
                                "text-xs px-2 py-1 rounded-full border",
                                isEnabled
                                    ? "bg-green-500/10 text-green-400 border-green-500/20"
                                    : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                            )}>
                                {isEnabled ? 'Active' : 'Disabled'}
                            </span>
                        </h1>
                        <p className="text-gray-400 mt-1">{description}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setIsEnabled(!isEnabled)}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                            isEnabled
                                ? "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                                : "bg-green-500/10 text-green-400 hover:bg-green-500/20"
                        )}
                    >
                        <Power size={18} />
                        {isEnabled ? 'Disable Agent' : 'Enable Agent'}
                    </button>
                    <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                        <MoreVertical size={20} />
                    </button>
                </div>
            </div>

            {/* Tabs Navigation */}
            <div className="border-b border-gray-800">
                <div className="flex gap-6">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={clsx(
                                "flex items-center gap-2 pb-4 px-2 text-sm font-medium transition-all relative",
                                activeTab === tab.id
                                    ? "text-blue-400"
                                    : "text-gray-400 hover:text-white"
                            )}
                        >
                            <tab.icon size={18} />
                            {tab.label}
                            {activeTab === tab.id && (
                                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-400 rounded-t-full" />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
                {activeTab === 'overview' && overviewContent}
                {activeTab === 'conversations' && conversationsContent}
                {activeTab === 'skills' && skillsContent}
                {activeTab === 'config' && configContent}
            </div>
        </div>
    );
};

export default AgentLayout;
