import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, ArrowRight, Loader2, Shield, Clock } from 'lucide-react';
import { AgentService, TaskService, Agent, Task } from '../services/api';
import { EmptyState } from '../components/EmptyState';

const OperationsOverview = () => {
    const navigate = useNavigate();
    const [recentScans, setRecentScans] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const agents = await AgentService.getAll();
            const agent = agents.find(a => a.type === 'market_research');
            
            if (agent) {
                const tasksData = await TaskService.getAll({ agentId: agent.id, limit: 10, offset: 0 });
                
                // Filter for site scan tasks only
                const scanTasks = tasksData.tasks.filter(task => 
                    task.action === 'site_scan' || task.action === 'comprehensive_site_scan'
                );
                setRecentScans(scanTasks.slice(0, 5));
            }
        } catch (err) {
            console.error('Failed to fetch operations data:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    const siteScanTask = {
        id: 'site-scan',
        title: 'Site Scan',
        description: 'Comprehensive website analysis for compliance, risk assessment, and structural insights. Crawls websites to extract business metadata, payment systems, compliance signals, and technical infrastructure.',
        icon: Globe,
        color: 'bg-blue-500',
        onClick: () => navigate('/operations/site-scan')
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white mb-2">Operations</h1>
                <p className="text-gray-400 text-sm max-w-2xl">
                    Operational intelligence and compliance. Analyze websites for compliance, risk, and structural insights to inform operational decisions.
                </p>
            </div>

            {/* Site Scan Task */}
            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 hover:border-gray-700 transition-all cursor-pointer hover:shadow-lg"
                onClick={siteScanTask.onClick}
            >
                <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-lg ${siteScanTask.color} bg-opacity-10`}>
                        <siteScanTask.icon className={`w-6 h-6 ${siteScanTask.color.replace('bg-', 'text-')}`} />
                    </div>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{siteScanTask.title}</h3>
                <p className="text-sm text-gray-400 mb-4">{siteScanTask.description}</p>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        siteScanTask.onClick();
                    }}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors text-sm"
                >
                    Run site scan
                    <ArrowRight size={14} />
                </button>
            </div>

            {/* Recent Site Scans */}
            {recentScans.length > 0 && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <Clock className="text-blue-400" size={20} />
                            Recent Site Scans
                        </h3>
                        <button
                            onClick={() => navigate('/operations/site-scan')}
                            className="text-sm text-blue-400 hover:text-blue-300"
                        >
                            View all
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-3">
                            {recentScans.map((task) => (
                                <div
                                    key={task.id}
                                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors cursor-pointer"
                                    onClick={() => navigate('/operations/site-scan')}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${
                                            task.status === 'completed' ? 'bg-green-500' :
                                            task.status === 'failed' ? 'bg-red-500' :
                                            'bg-blue-500 animate-pulse'
                                        }`} />
                                        <div>
                                            <p className="text-sm font-medium text-white">
                                                {task.action === 'comprehensive_site_scan' ? 'Comprehensive Site Scan' : 'Site Scan'}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {new Date(task.createdAt).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <span className={`text-xs px-2 py-1 rounded-full ${
                                        task.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                                        task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                        'bg-blue-500/10 text-blue-400'
                                    }`}>
                                        {task.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OperationsOverview;
