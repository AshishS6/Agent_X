import { useState } from 'react';
import { Search, Bell, ChevronDown, User, Menu } from 'lucide-react';

interface HeaderProps {
    onMenuClick: () => void;
}

const Header = ({ onMenuClick }: HeaderProps) => {
    const [dateRange, setDateRange] = useState('Last 7 days');

    return (
        <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4 md:px-6 sticky top-0 z-10">
            {/* Left: Page Title & Date Range */}
            <div className="flex items-center gap-4 md:gap-6">
                <button
                    onClick={onMenuClick}
                    className="md:hidden p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
                >
                    <Menu size={20} />
                </button>

                <h2 className="text-xl font-semibold text-white hidden sm:block">Dashboard</h2>
                <div className="relative group">
                    <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-700 hover:border-gray-600">
                        <span>{dateRange}</span>
                        <ChevronDown size={14} />
                    </button>
                    {/* Dropdown (Mock) */}
                    <div className="absolute top-full left-0 mt-1 w-40 bg-gray-800 border border-gray-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20">
                        {['Today', 'Last 7 days', 'Last 30 days', 'Custom'].map((range) => (
                            <button
                                key={range}
                                onClick={() => setDateRange(range)}
                                className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg"
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right: Search, Notifications, User */}
            <div className="flex items-center gap-2 md:gap-4">
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
        </header>
    );
};

export default Header;
