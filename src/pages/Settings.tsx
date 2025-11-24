import { useState } from 'react';
import {
    Building,
    Users,
    Shield,
    Bell,
    CreditCard,
    Key,
    Save,
    Upload,
    Plus,
    MoreVertical,

} from 'lucide-react';
import clsx from 'clsx';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('organization');

    const tabs = [
        { id: 'organization', label: 'Organization', icon: Building },
        { id: 'users', label: 'Users & Roles', icon: Users },
        { id: 'models', label: 'Models & Safety', icon: Shield },
        { id: 'preferences', label: 'Preferences', icon: Bell },
        { id: 'billing', label: 'Billing', icon: CreditCard },
        { id: 'api', label: 'API & Webhooks', icon: Key },
    ];

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
                    <p className="text-gray-400 text-sm">Manage your organization, users, and preferences</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium shadow-lg shadow-blue-500/20">
                    <Save size={16} />
                    <span>Save Changes</span>
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-8 min-h-0">
                {/* Sidebar Tabs (Left) */}
                <div className="w-64 flex-shrink-0">
                    <nav className="space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={clsx(
                                    "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                                    activeTab === tab.id
                                        ? "bg-blue-600/10 text-blue-400"
                                        : "text-gray-400 hover:bg-gray-800 hover:text-white"
                                )}
                            >
                                <tab.icon size={18} />
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Content Area (Right) */}
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                    <div className="max-w-3xl">
                        {/* Organization Tab */}
                        {activeTab === 'organization' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                                    <h2 className="text-lg font-semibold text-white mb-4">Organization Profile</h2>
                                    <div className="space-y-6">
                                        <div className="flex items-center gap-6">
                                            <div className="w-20 h-20 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-500">
                                                <Building size={32} />
                                            </div>
                                            <div>
                                                <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 hover:bg-gray-700 text-sm font-medium">
                                                    <Upload size={16} />
                                                    Upload Logo
                                                </button>
                                                <p className="text-xs text-gray-500 mt-2">Recommended size: 400x400px</p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-6">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-400 mb-2">Organization Name</label>
                                                <input
                                                    type="text"
                                                    defaultValue="Acme Corp"
                                                    className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-400 mb-2">Industry</label>
                                                <select className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 appearance-none">
                                                    <option>Technology</option>
                                                    <option>Finance</option>
                                                    <option>Healthcare</option>
                                                    <option>Retail</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-400 mb-2">Timezone</label>
                                                <select className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 appearance-none">
                                                    <option>UTC (GMT+00:00)</option>
                                                    <option>EST (GMT-05:00)</option>
                                                    <option>PST (GMT-08:00)</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-400 mb-2">Date Format</label>
                                                <select className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 appearance-none">
                                                    <option>MM/DD/YYYY</option>
                                                    <option>DD/MM/YYYY</option>
                                                    <option>YYYY-MM-DD</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                                    <h2 className="text-lg font-semibold text-white mb-4">Primary Contact</h2>
                                    <div className="grid grid-cols-2 gap-6">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-2">Contact Name</label>
                                            <input
                                                type="text"
                                                defaultValue="Admin User"
                                                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                                            <input
                                                type="email"
                                                defaultValue="admin@acmecorp.com"
                                                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Users Tab */}
                        {activeTab === 'users' && (
                            <div className="space-y-6 animate-fade-in">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-semibold text-white">Team Members</h2>
                                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium">
                                        <Plus size={16} />
                                        Invite User
                                    </button>
                                </div>

                                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                                    <table className="w-full text-left text-sm">
                                        <thead className="bg-gray-800/50 text-gray-400 font-medium">
                                            <tr>
                                                <th className="px-6 py-3">User</th>
                                                <th className="px-6 py-3">Role</th>
                                                <th className="px-6 py-3">Status</th>
                                                <th className="px-6 py-3">Last Active</th>
                                                <th className="px-6 py-3 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-800">
                                            {[
                                                { name: 'Admin User', email: 'admin@acmecorp.com', role: 'Admin', status: 'Active', lastActive: 'Now' },
                                                { name: 'Sarah Smith', email: 'sarah@acmecorp.com', role: 'Manager', status: 'Active', lastActive: '2h ago' },
                                                { name: 'John Doe', email: 'john@acmecorp.com', role: 'Viewer', status: 'Pending', lastActive: '-' },
                                            ].map((user, i) => (
                                                <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div>
                                                            <div className="font-medium text-white">{user.name}</div>
                                                            <div className="text-xs text-gray-500">{user.email}</div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300">
                                                            {user.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={clsx(
                                                            "px-2 py-1 rounded text-xs font-medium",
                                                            user.status === 'Active' ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                                                        )}>
                                                            {user.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-500">{user.lastActive}</td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button className="text-gray-500 hover:text-white p-1 rounded hover:bg-gray-700">
                                                            <MoreVertical size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Models Tab */}
                        {activeTab === 'models' && (
                            <div className="space-y-8 animate-fade-in">
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                                    <h2 className="text-lg font-semibold text-white mb-4">Default Model Configuration</h2>
                                    <div className="space-y-6">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-2">Default Model</label>
                                            <select className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 appearance-none">
                                                <option>GPT-4o (Recommended)</option>
                                                <option>GPT-4 Turbo</option>
                                                <option>Claude 3.5 Sonnet</option>
                                                <option>Llama 3.1 70B</option>
                                            </select>
                                            <p className="text-xs text-gray-500 mt-2">This model will be used for all agents unless overridden.</p>
                                        </div>

                                        <div>
                                            <div className="flex justify-between mb-2">
                                                <label className="text-sm font-medium text-gray-400">Temperature</label>
                                                <span className="text-sm text-gray-400">0.7</span>
                                            </div>
                                            <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-600" />
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                                    <h2 className="text-lg font-semibold text-white mb-4">Safety & Compliance</h2>
                                    <div className="space-y-4">
                                        {[
                                            { label: 'Mask PII in logs', desc: 'Automatically redact emails, phone numbers, and credit cards.' },
                                            { label: 'Block exporting raw logs', desc: 'Prevent users from downloading full JSON logs.' },
                                            { label: 'Enable profanity filter', desc: 'Block inappropriate content in agent outputs.' },
                                        ].map((item, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-800/30 transition-colors">
                                                <div className="mt-0.5">
                                                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-gray-900" />
                                                </div>
                                                <div>
                                                    <div className="text-sm font-medium text-white">{item.label}</div>
                                                    <div className="text-xs text-gray-500">{item.desc}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Placeholder for other tabs */}
                        {['preferences', 'billing', 'api'].includes(activeTab) && (
                            <div className="flex flex-col items-center justify-center h-64 text-gray-500 animate-fade-in">
                                <Building size={48} className="mb-4 opacity-20" /> {/* Changed from Settings to Building as Settings is the component name */}
                                <p>This section is coming soon.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
