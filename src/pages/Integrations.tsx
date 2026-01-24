import { useState, useEffect } from 'react';
import {
    Plus,
    RefreshCw,
    Settings,
    Power,
    Database,
    MessageSquare,
    Mail,
    Briefcase,
    Layout,
    LifeBuoy,
    Clock,
    Loader2,
    ExternalLink
} from 'lucide-react';
import clsx from 'clsx';
import { IntegrationService, Integration } from '../services/api';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const iconMap: Record<string, any> = {
    salesforce: Briefcase,
    slack: MessageSquare,
    gmail: Mail,
    hubspot: Database,
    zendesk: LifeBuoy,
    notion: Layout
};

const Integrations = () => {
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const SUPPORTED_INTEGRATIONS = [
        { id: 'salesforce', name: 'Salesforce', icon: Briefcase, type: 'salesforce', category: 'CRM' },
        { id: 'slack', name: 'Slack', icon: MessageSquare, type: 'slack', category: 'Communication' },
        { id: 'gmail', name: 'Gmail', icon: Mail, type: 'gmail', category: 'Email' },
        { id: 'hubspot', name: 'HubSpot', icon: Database, type: 'hubspot', category: 'CRM' },
        { id: 'zendesk', name: 'Zendesk', icon: LifeBuoy, type: 'zendesk', category: 'Support' },
        { id: 'notion', name: 'Notion', icon: Layout, type: 'notion', category: 'Knowledge' }
    ];

    useEffect(() => {
        fetchIntegrations();
    }, []);

    const fetchIntegrations = async () => {
        try {
            setLoading(true);
            const data = await IntegrationService.getAll();
            setIntegrations(data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch integrations:', err);
            setError('Failed to load integrations');
        } finally {
            setLoading(false);
        }
    };

    const handleAddIntegration = async (template: typeof SUPPORTED_INTEGRATIONS[0]) => {
        try {
            // Check if already exists
            if (integrations.some(i => i.type === template.type)) {
                alert(`${template.name} is already added.`);
                return;
            }

            await IntegrationService.connect({
                name: template.name,
                type: template.type,
                status: 'disconnected', // Start as disconnected
                config: {},
                createdAt: new Date().toISOString()
            });

            await fetchIntegrations();
            setShowAddModal(false);
        } catch (err) {
            console.error('Failed to add integration:', err);
            alert('Failed to add integration');
        }
    };

    const handleToggleConnection = async (integration: Integration) => {
        try {
            if (integration.status === 'connected') {
                // If connected, we disconnect (update status, don't delete)
                await IntegrationService.update(integration.id, {
                    status: 'disconnected',
                    lastSync: undefined
                });
            } else {
                // If disconnected, we connect
                await IntegrationService.update(integration.id, {
                    status: 'connected',
                    lastSync: new Date().toISOString()
                });
            }
            await fetchIntegrations();
            // Update selected integration to reflect changes
            if (selectedIntegration?.id === integration.id) {
                const updated = await IntegrationService.getAll(); // We just fetched, but need the specific item
                const match = updated.find(i => i.id === integration.id);
                if (match) setSelectedIntegration(match);
            }
        } catch (err) {
            console.error('Failed to toggle connection:', err);
        }
    };

    const handleDeleteIntegration = async (id: string) => {
        if (!confirm('Are you sure you want to remove this integration?')) return;
        try {
            await IntegrationService.disconnect(id); // This calls DELETE
            await fetchIntegrations();
            setSelectedIntegration(null);
        } catch (err) {
            console.error('Failed to delete integration:', err);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'connected': return 'text-green-400 bg-green-500/10 border-green-500/20';
            case 'error': return 'text-red-400 bg-red-500/10 border-red-500/20';
            case 'disconnected': return 'text-gray-400 bg-gray-800 border-gray-700';
            default: return 'text-gray-400';
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center text-red-400">
                <p>{error}</p>
                <button onClick={fetchIntegrations} className="ml-4 text-blue-400 hover:underline">Retry</button>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col relative">
            {/* Add Integration Modal */}
            {showAddModal && (
                <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
                        <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-white">Add Integration</h2>
                            <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-white">
                                <Plus className="rotate-45" size={24} />
                            </button>
                        </div>
                        <div className="p-6 overflow-y-auto custom-scrollbar grid grid-cols-2 gap-4">
                            {SUPPORTED_INTEGRATIONS.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleAddIntegration(item)}
                                    disabled={integrations.some(i => i.type === item.type)}
                                    className={clsx(
                                        "flex items-center gap-4 p-4 rounded-xl border text-left transition-all",
                                        integrations.some(i => i.type === item.type)
                                            ? "bg-gray-800/50 border-gray-800 opacity-50 cursor-not-allowed"
                                            : "bg-gray-800/30 border-gray-700 hover:bg-gray-800 hover:border-gray-600"
                                    )}
                                >
                                    <div className="w-12 h-12 rounded-lg bg-gray-800 flex items-center justify-center text-white">
                                        <item.icon size={24} />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-white">{item.name}</h3>
                                        <p className="text-xs text-gray-500">{item.category}</p>
                                    </div>
                                    {integrations.some(i => i.type === item.type) && (
                                        <span className="ml-auto text-xs text-green-400 font-medium">Added</span>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Data & Integrations</h1>
                    <p className="text-gray-400 text-sm">Manage connections to external tools and services</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium shadow-lg shadow-blue-500/20"
                >
                    <Plus size={16} />
                    <span>Add Integration</span>
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 min-h-0">
                {/* Integrations Grid (Left 2/3) */}
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                    {integrations.length === 0 ? (
                        <EmptyState
                            icon={Database}
                            title="No integrations connected"
                            description="Connect external tools and services to enable automation and data synchronization."
                            primaryAction={{
                                label: 'Add Integration',
                                onClick: () => setShowAddModal(true),
                                icon: Plus,
                            }}
                            hint="Popular integrations include Salesforce, Slack, Gmail, HubSpot, Zendesk, and Notion."
                        />
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {integrations.map((integration) => {
                            const Icon = iconMap[integration.type] || Database;
                            return (
                                <div
                                    key={integration.id}
                                    onClick={() => setSelectedIntegration(integration)}
                                    className={clsx(
                                        "p-5 rounded-xl border transition-all cursor-pointer group relative overflow-hidden",
                                        selectedIntegration?.id === integration.id
                                            ? "bg-blue-600/5 border-blue-500/50 ring-1 ring-blue-500/20"
                                            : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/50 hover:border-gray-600"
                                    )}
                                >
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center text-white group-hover:scale-105 transition-transform">
                                                <Icon size={24} />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-white text-lg">{integration.name}</h3>
                                                <span className="text-xs text-gray-500 capitalize">{integration.type}</span>
                                            </div>
                                        </div>
                                        <span className={clsx(
                                            "px-2 py-1 rounded-lg text-xs font-medium uppercase tracking-wider border",
                                            getStatusColor(integration.status)
                                        )}>
                                            {integration.status}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between pt-4 border-t border-gray-700/50 text-xs text-gray-500">
                                        <div className="flex items-center gap-1.5">
                                            <RefreshCw size={12} />
                                            <span>Auto-Sync</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <Clock size={12} />
                                            <span>Last sync: {integration.lastSync ? new Date(integration.lastSync).toLocaleTimeString() : 'Never'}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                        </div>
                    )}
                </div>

                {/* Integration Detail (Right 1/3) */}
                {selectedIntegration ? (
                    <div className="w-96 bg-gray-900 border border-gray-800 rounded-xl flex flex-col overflow-hidden animate-fade-in">
                        <div className="p-6 border-b border-gray-800 bg-gray-800/30">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="w-16 h-16 rounded-2xl bg-gray-800 border border-gray-700 flex items-center justify-center text-white shadow-xl">
                                    {(() => {
                                        const Icon = iconMap[selectedIntegration.type] || Database;
                                        return <Icon size={32} />;
                                    })()}
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">{selectedIntegration.name}</h2>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className={clsx(
                                            "w-2 h-2 rounded-full",
                                            selectedIntegration.status === 'connected' ? "bg-green-500" :
                                                selectedIntegration.status === 'error' ? "bg-red-500" : "bg-gray-500"
                                        )}></span>
                                        <span className="text-sm text-gray-400 capitalize">{selectedIntegration.status}</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => handleToggleConnection(selectedIntegration)}
                                className={clsx(
                                    "w-full py-2 rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2 mb-3",
                                    selectedIntegration.status === 'connected'
                                        ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 hover:bg-yellow-500/20"
                                        : "bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-500/20"
                                )}
                            >
                                <Power size={16} />
                                {selectedIntegration.status === 'connected' ? 'Disconnect Integration' : 'Connect Integration'}
                            </button>

                            <button
                                onClick={() => handleDeleteIntegration(selectedIntegration.id)}
                                className="w-full py-2 rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2 bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20"
                            >
                                <Plus className="rotate-45" size={16} />
                                Remove Integration
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
                            {selectedIntegration.status === 'error' && (
                                <ErrorState
                                    title="Integration Failed"
                                    message={`${selectedIntegration.name} is not connected and may be experiencing issues.`}
                                    failureReason={
                                        selectedIntegration.config?.error || 
                                        (selectedIntegration.lastSync 
                                            ? `Last sync failed at ${new Date(selectedIntegration.lastSync || '').toLocaleString()}`
                                            : 'Connection failed. Check your credentials and network connection.')
                                    }
                                    impact={
                                        selectedIntegration.type === 'notion' 
                                            ? 'Blog content cannot be synced to Notion. New blog posts will not appear in your workspace.'
                                            : selectedIntegration.type === 'salesforce' || selectedIntegration.type === 'hubspot'
                                            ? 'CRM data synchronization is paused. Lead and contact updates may be delayed.'
                                            : selectedIntegration.type === 'slack'
                                            ? 'Notifications and alerts will not be sent to Slack channels.'
                                            : selectedIntegration.type === 'gmail'
                                            ? 'Email automation features are unavailable. Outbound emails will not be sent.'
                                            : 'This integration is not functioning. Some features may be limited.'
                                    }
                                    primaryAction={{
                                        label: 'Reconnect',
                                        onClick: () => handleToggleConnection(selectedIntegration),
                                        icon: RefreshCw,
                                    }}
                                    secondaryAction={{
                                        label: 'View Logs',
                                        onClick: () => {
                                            // TODO: Navigate to logs or open logs modal
                                            console.log('View logs for', selectedIntegration.id);
                                        },
                                        icon: ExternalLink,
                                    }}
                                    variant="error"
                                />
                            )}
                            
                            {selectedIntegration.status === 'disconnected' && (
                                <div className="text-center py-8 text-gray-500">
                                    <Settings size={48} className="mx-auto mb-4 opacity-20" />
                                    <p className="mb-2">Integration is disconnected</p>
                                    <p className="text-sm text-gray-600">
                                        Connect this integration to enable synchronization and automation features.
                                    </p>
                                </div>
                            )}

                            {selectedIntegration.status === 'connected' && (
                                <div className="text-center py-8 text-gray-500">
                                    <Settings size={48} className="mx-auto mb-4 opacity-20" />
                                    <p>Configuration options available when connected.</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="w-96 bg-gray-900/50 border border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500">
                        <Database size={48} className="mx-auto mb-4 opacity-20" />
                        <p className="text-sm">Select an integration to configure</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Integrations;
