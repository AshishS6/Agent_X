import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { Breadcrumb } from '../Breadcrumb';

const DashboardLayout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    // Show breadcrumb for non-agent pages (agent pages have their own in AgentLayout)
    const isAgentPage = ['/sales', '/support', '/hr', '/market-research', '/blog', '/intelligence', '/legal', '/finance', '/operations/site-scan'].includes(location.pathname);

    return (
        <div className="flex h-screen bg-gray-950 overflow-hidden font-sans">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Header onMenuClick={() => setSidebarOpen(true)} />
                <main className="flex-1 flex flex-col min-h-0 overflow-hidden p-4 md:p-6">
                    {!isAgentPage && <Breadcrumb />}
                    <div className="flex-1 min-h-0 overflow-y-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
