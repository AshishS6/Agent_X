import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Briefcase,
    LifeBuoy,
    Users,
    TrendingUp,
    Megaphone,
    FileText,
    Target,
    Newspaper,
    Scale,
    DollarSign,
    GitBranch,
    Activity,
    Database,
    Settings,
    ChevronRight,
    ChevronDown,
    X,
    MessageSquare,
    Code,
    Sparkles,
    Globe
} from 'lucide-react';
import clsx from 'clsx';

interface NavItem {
    path: string;
    label: string;
    icon: React.ElementType;
}

interface NavSection {
    title: string;
    items: NavItem[];
    collapsible?: boolean;
}

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
    const location = useLocation();
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['Sales', 'Marketing', 'Operations']));

    const toggleSection = (sectionTitle: string) => {
        setExpandedSections(prev => {
            const next = new Set(prev);
            if (next.has(sectionTitle)) {
                next.delete(sectionTitle);
            } else {
                next.add(sectionTitle);
            }
            return next;
        });
    };

    // Check if any item in a section is active
    const isSectionActive = (items: NavItem[]) => {
        return items.some(item => location.pathname === item.path || location.pathname.startsWith(item.path + '/'));
    };

    const navSections: NavSection[] = [
        {
            title: 'Overview',
            items: [
                { path: '/', label: 'Dashboard', icon: LayoutDashboard },
            ]
        },
        {
            title: 'Assistants',
            items: [
                { path: '/assistants/fintech', label: 'Fintech Assistant', icon: DollarSign },
                { path: '/assistants/code', label: 'Code Assistant', icon: Code },
                { path: '/assistants/general', label: 'General Assistant', icon: Sparkles },
            ]
        },
        {
            title: 'Sales',
            collapsible: true,
            items: [
                { path: '/sales/overview', label: 'Overview', icon: LayoutDashboard },
                { path: '/sales', label: 'Lead qualification & outreach', icon: Target },
            ]
        },
        {
            title: 'Marketing',
            collapsible: true,
            items: [
                { path: '/marketing/overview', label: 'Overview', icon: LayoutDashboard },
                { path: '/blog', label: 'Blog / Content Generation', icon: FileText },
                { path: '/market-research', label: 'Market Research', icon: TrendingUp },
            ]
        },
        {
            title: 'Operations',
            collapsible: true,
            items: [
                { path: '/operations/overview', label: 'Overview', icon: LayoutDashboard },
                { path: '/operations/site-scan', label: 'Site Scan', icon: Globe },
            ]
        },
        {
            title: 'Other Agents',
            collapsible: true,
            items: [
                { path: '/support', label: 'Support Agent', icon: LifeBuoy },
                { path: '/hr', label: 'HR Agent', icon: Users },
                { path: '/intelligence', label: 'Intelligence', icon: Newspaper },
                { path: '/legal', label: 'Legal', icon: Scale },
                { path: '/finance', label: 'Finance', icon: DollarSign },
            ]
        },
        {
            title: 'System',
            items: [
                { path: '/workflows', label: 'Workflows', icon: GitBranch },
                { path: '/activity', label: 'Activity & Logs', icon: Activity },
                { path: '/data', label: 'Data & Integrations', icon: Database },
                { path: '/settings', label: 'Settings', icon: Settings },
            ]
        }
    ];

    return (
        <>
            {/* Mobile Overlay */}
            <div
                className={clsx(
                    "fixed inset-0 bg-black/50 z-20 md:hidden transition-opacity duration-300",
                    isOpen ? "opacity-100 visible" : "opacity-0 invisible pointer-events-none"
                )}
                onClick={onClose}
            />

            {/* Sidebar */}
            <aside className={clsx(
                "bg-gray-900 text-white h-screen flex flex-col border-r border-gray-800 flex-shrink-0 fixed md:sticky top-0 z-30 transition-transform duration-300 w-64",
                isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
            )}>
                <div className="p-6 border-b border-gray-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                            <span className="font-bold text-lg">A</span>
                        </div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            AgentX
                        </h1>
                    </div>
                    <button onClick={onClose} className="md:hidden text-gray-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6 custom-scrollbar">
                    {navSections.map((section) => {
                        const isExpanded = expandedSections.has(section.title);
                        const isActive = isSectionActive(section.items);
                        const showCollapsible = section.collapsible;

                        return (
                            <div key={section.title}>
                                {showCollapsible ? (
                                    <button
                                        onClick={() => toggleSection(section.title)}
                                        className={clsx(
                                            'w-full flex items-center justify-between px-4 py-2 mb-2 rounded-lg transition-all duration-200',
                                            isActive
                                                ? 'bg-blue-600/10 text-blue-400'
                                                : 'text-gray-500 hover:bg-gray-800 hover:text-white'
                                        )}
                                    >
                                        <h3 className="text-xs font-semibold uppercase tracking-wider">
                                            {section.title}
                                        </h3>
                                        {isExpanded ? (
                                            <ChevronDown size={14} />
                                        ) : (
                                            <ChevronRight size={14} />
                                        )}
                                    </button>
                                ) : (
                                    <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                        {section.title}
                                    </h3>
                                )}
                                {(!showCollapsible || isExpanded) && (
                                    <div className="space-y-1">
                                        {section.items.map((item) => (
                                            <NavLink
                                                key={item.path}
                                                to={item.path}
                                                onClick={() => {
                                                    if (window.innerWidth < 768) onClose();
                                                }}
                                                className={({ isActive }) =>
                                                    clsx(
                                                        'flex items-center justify-between px-4 py-2.5 rounded-lg transition-all duration-200 group ml-2',
                                                        isActive
                                                            ? 'bg-blue-600/10 text-blue-400'
                                                            : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                                    )
                                                }
                                            >
                                                {({ isActive }) => (
                                                    <>
                                                        <div className="flex items-center gap-3">
                                                            <item.icon size={18} className={isActive ? 'text-blue-400' : 'text-gray-500 group-hover:text-white transition-colors'} />
                                                            <span className="text-sm font-medium">{item.label}</span>
                                                        </div>
                                                        {isActive && <ChevronRight size={14} className="text-blue-400" />}
                                                    </>
                                                )}
                                            </NavLink>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-gray-800">
                    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-400">System Status</span>
                            <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                            <div className="bg-green-500 h-1.5 rounded-full" style={{ width: '98%' }}></div>
                        </div>
                        <p className="text-xs text-gray-500">All systems operational</p>
                    </div>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
