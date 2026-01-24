import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
    label: string;
    path: string;
}

/**
 * Breadcrumb component for navigation orientation
 * Automatically generates breadcrumbs based on current route
 * Example: "Home > Agents > Sales Agent"
 */
export const Breadcrumb: React.FC<{ currentTab?: string }> = ({ currentTab }) => {
    const location = useLocation();

    // Map route paths to human-readable labels
    const routeLabels: Record<string, string> = {
        '/': 'Dashboard',
        '/assistants/fintech': 'Fintech Assistant',
        '/assistants/code': 'Code Assistant',
        '/assistants/general': 'General Assistant',
        '/sales': 'Sales Agent',
        '/support': 'Support Agent',
        '/hr': 'HR Agent',
        '/market-research': 'Market Research Agent',
        '/marketing': 'Marketing Agent',
        '/blog': 'Blog Agent',
        '/leads': 'Lead Sourcing Agent',
        '/intelligence': 'Intelligence Agent',
        '/legal': 'Legal Agent',
        '/finance': 'Finance Agent',
        '/workflows': 'Workflows',
        '/activity': 'Activity & Logs',
        '/data': 'Data & Integrations',
        '/settings': 'Settings',
    };

    // Map tab IDs to labels
    const tabLabels: Record<string, string> = {
        'overview': 'Overview',
        'conversations': 'Conversations',
        'skills': 'Skills & Playbooks',
        'logs': 'Logs',
        'config': 'Configuration',
    };

    // Build breadcrumb items from current path
    const buildBreadcrumbs = (): BreadcrumbItem[] => {
        const items: BreadcrumbItem[] = [
            { label: 'Home', path: '/' },
        ];

        // Skip home page
        if (location.pathname === '/') {
            return items;
        }

        const pathSegments = location.pathname.split('/').filter(Boolean);

        // Handle assistants
        if (pathSegments[0] === 'assistants' && pathSegments[1]) {
            items.push({
                label: 'Assistants',
                path: '#', // Non-clickable intermediate
            });
            items.push({
                label: routeLabels[location.pathname] || pathSegments[1],
                path: location.pathname,
            });
            return items;
        }

        // Handle agents
        const agentRoutes = ['sales', 'support', 'hr', 'market-research', 'marketing', 'blog', 'leads', 'intelligence', 'legal', 'finance'];
        if (agentRoutes.includes(pathSegments[0])) {
            items.push({
                label: 'Agents',
                path: '#', // Non-clickable intermediate
            });
            const agentLabel = routeLabels[location.pathname] || pathSegments[0];
            items.push({
                label: agentLabel,
                path: `/${pathSegments[0]}`,
            });
            
            // Add tab if provided and not "overview" (default)
            if (currentTab && currentTab !== 'overview' && tabLabels[currentTab]) {
                items.push({
                    label: tabLabels[currentTab],
                    path: location.pathname, // Current page, non-clickable
                });
            }
            return items;
        }

        // Handle system routes
        const systemRoutes = ['workflows', 'activity', 'data', 'settings'];
        if (systemRoutes.includes(pathSegments[0])) {
            items.push({
                label: 'System',
                path: '#', // Non-clickable intermediate
            });
            items.push({
                label: routeLabels[location.pathname] || pathSegments[0],
                path: location.pathname,
            });
            return items;
        }

        // Fallback for unknown routes
        if (pathSegments.length > 0) {
            items.push({
                label: routeLabels[location.pathname] || pathSegments[0],
                path: location.pathname,
            });
        }

        return items;
    };

    const breadcrumbs = buildBreadcrumbs();

    // Don't show breadcrumb on home page
    if (location.pathname === '/') {
        return null;
    }

    return (
        <nav className="flex items-center gap-2 text-sm mb-4" aria-label="Breadcrumb">
            {breadcrumbs.map((item, index) => {
                const isLast = index === breadcrumbs.length - 1;
                const isNonClickable = item.path === '#';

                return (
                    <React.Fragment key={`${item.path}-${index}`}>
                        {index === 0 ? (
                            <Link
                                to={item.path}
                                className="flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors"
                            >
                                <Home size={14} />
                                <span>{item.label}</span>
                            </Link>
                        ) : (
                            <>
                                <ChevronRight size={14} className="text-gray-600" />
                                {isLast || isNonClickable ? (
                                    <span className={isLast ? "text-white font-medium" : "text-gray-500"}>
                                        {item.label}
                                    </span>
                                ) : (
                                    <Link
                                        to={item.path}
                                        className="text-gray-400 hover:text-white transition-colors"
                                    >
                                        {item.label}
                                    </Link>
                                )}
                            </>
                        )}
                    </React.Fragment>
                );
            })}
        </nav>
    );
};
