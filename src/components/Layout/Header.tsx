import { useMemo } from 'react';
import { Search, Bell, User, Menu } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { Breadcrumb } from '../Breadcrumb';

interface HeaderProps {
    onMenuClick: () => void;
}

const Header = ({ onMenuClick }: HeaderProps) => {
    const location = useLocation();

    const pageTitle = useMemo(() => {
        const p = location.pathname || '/';
        if (p === '/') return 'Dashboard';
        if (p.startsWith('/assistants')) return 'Assistants';
        if (p === '/sales/overview') return 'Sales Overview';
        if (p.startsWith('/sales')) return 'Lead Sourcing Agent';
        if (p === '/marketing/overview') return 'Marketing Overview';
        if (p === '/blog') return 'Blog Agent';
        if (p.startsWith('/blog/')) return 'Blog Editor';
        if (p.startsWith('/market-research')) return 'Market Research Agent';
        if (p === '/operations/overview') return 'Operations Overview';
        if (p.startsWith('/operations/site-scan')) return 'Site Scan';
        if (p.startsWith('/support')) return 'Support Agent';
        if (p.startsWith('/hr')) return 'HR Agent';
        if (p.startsWith('/intelligence')) return 'Intelligence';
        if (p.startsWith('/legal')) return 'Legal';
        if (p.startsWith('/finance')) return 'Finance';
        if (p.startsWith('/workflows')) return 'Workflows';
        if (p.startsWith('/activity')) return 'Activity Logs';
        if (p.startsWith('/data')) return 'Integrations';
        if (p.startsWith('/settings')) return 'Settings';

        // Fallback: convert "/foo-bar/baz" -> "Foo Bar / Baz"
        const parts = p.split('/').filter(Boolean).map(seg =>
            seg
                .replace(/-/g, ' ')
                .replace(/\b\w/g, c => c.toUpperCase())
        );
        return parts.join(' / ') || 'Dashboard';
    }, [location.pathname]);

    return (
        <header className="bg-gray-900 border-b border-gray-800 px-4 md:px-6 py-3 sticky top-0 z-10">
            <div className="flex items-center justify-between gap-4">
                {/* Left: Page Title & Breadcrumbs */}
                <div className="flex items-center gap-4 md:gap-6 min-w-0">
                <button
                    onClick={onMenuClick}
                    className="md:hidden p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
                >
                    <Menu size={20} />
                </button>

                <div className="hidden sm:flex flex-col min-w-0">
                    <h2 className="text-xl font-semibold text-white truncate">{pageTitle}</h2>
                    <Breadcrumb className="mt-1 text-xs text-gray-400" />
                </div>
                </div>

                {/* Right: Search, Notifications, User */}
                <div className="flex items-center gap-2 md:gap-4 shrink-0">
                {/* Global Search */}
                <div className="relative hidden md:block">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search agents, tasks..."
                        className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-4 py-1.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-64 transition-all"
                    />
                </div>

                {/* Notifications */}
                <button className="relative p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                    <Bell size={20} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-gray-900"></span>
                </button>

                {/* User Menu */}
                <div className="flex items-center gap-3 pl-2 md:pl-4 border-l border-gray-800">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-white">Admin User</p>
                        <p className="text-xs text-gray-500">Acme Corp</p>
                    </div>
                    <button className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium shadow-lg shadow-blue-500/20">
                        <User size={16} />
                    </button>
                </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
