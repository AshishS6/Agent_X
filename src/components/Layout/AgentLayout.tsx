import React, { useState } from 'react';
import {
    Settings,
    MessageSquare,
    Zap,
    BarChart2,
    Power,
    FileText,
    Clock
} from 'lucide-react';
import clsx from 'clsx';

interface AgentLayoutProps {
    name: string;
    description: string;
    icon: React.ElementType;
    color: string;
    children?: React.ReactNode; // For custom content if needed
    lastActivity?: string; // Last activity timestamp
    headerStats?: React.ReactNode; // Optional KPI/stats block inside header card
    // Header / tabs controls (optional per agent page)
    showEnableToggle?: boolean; // hides "Disable Agent" button when false
    showOverflowMenu?: boolean; // hides 3-dot menu when false
    showConversationsTab?: boolean;
    showSkillsTab?: boolean;
    showConfigTab?: boolean;
    // Tab content props
    overviewContent: React.ReactNode;
    conversationsContent: React.ReactNode;
    skillsContent: React.ReactNode;
    logsContent?: React.ReactNode; // Optional logs tab
    configContent: React.ReactNode;
}

const AgentLayout = ({
    name,
    description,
    icon: Icon,
    color,
    lastActivity,
    headerStats,
    showEnableToggle = true,
    showOverflowMenu = true,
    showConversationsTab = true,
    showSkillsTab = true,
    showConfigTab = true,
    overviewContent,
    conversationsContent,
    skillsContent,
    logsContent,
    configContent
}: AgentLayoutProps) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'conversations' | 'skills' | 'logs' | 'config'>('overview');
    const [isEnabled, setIsEnabled] = useState(true);

    const formatLastActivity = (timestamp?: string) => {
        if (!timestamp) return 'No activity yet';
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return 'No activity yet';
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffMins = Math.floor(diffMs / 60000);
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours}h ago`;
            const diffDays = Math.floor(diffHours / 24);
            return `${diffDays}d ago`;
        } catch {
            return 'No activity yet';
        }
    };

    const tabs = [
        { id: 'overview', label: 'Overview', icon: BarChart2 },
        ...(showConversationsTab ? [{ id: 'conversations' as const, label: 'Conversations', icon: MessageSquare }] : []),
        ...(showSkillsTab ? [{ id: 'skills' as const, label: 'Skills & Playbooks', icon: Zap }] : []),
        ...(logsContent ? [{ id: 'logs' as const, label: 'Logs', icon: FileText }] : []),
        ...(showConfigTab ? [{ id: 'config' as const, label: 'Configuration', icon: Settings }] : []),
    ];

    return (
        <div className="flex flex-col gap-6 min-h-full">
            {/* Agent Header */}
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 shrink-0">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`p-4 rounded-xl ${color} bg-opacity-10`}>
                            <Icon className={`w-8 h-8 ${color.replace('bg-', 'text-')}`} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className={clsx(
                                    "text-xs px-2 py-1 rounded-full border",
                                    isEnabled
                                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                                        : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                                )}>
                                    {isEnabled ? 'Active' : 'Disabled'}
                                </span>
                                <span className="text-xs text-gray-500">Agent</span>
                            </div>
                            <p className="text-gray-300 mt-2">{description}</p>
                            {lastActivity && (
                                <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-500">
                                    <Clock size={12} />
                                    <span>Last activity: {formatLastActivity(lastActivity)}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {headerStats && (
                            <div className="hidden xl:flex items-center gap-2">
                                {headerStats}
                            </div>
                        )}
                        {showEnableToggle && (
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
                        )}
                        {showOverflowMenu && (
                            <button
                                aria-label="More"
                                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
                            >
                                <span className="text-xl leading-none">⋮</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Tabs Navigation */}
            <div className="border-b border-gray-800 shrink-0">
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
            <div className={clsx(
                activeTab === 'conversations'
                    ? 'flex-1 min-h-0 flex flex-col w-full'
                    : 'min-h-[400px]'
            )}>
                {activeTab === 'overview' && overviewContent}
                {activeTab === 'conversations' && conversationsContent}
                {activeTab === 'skills' && skillsContent}
                {activeTab === 'logs' && logsContent}
                {activeTab === 'config' && configContent}
            </div>
        </div>
    );
};

export default AgentLayout;
