import React from 'react';
import { Code, Database, BarChart3, CreditCard, Server } from 'lucide-react';

interface TechStackCardProps {
    techStack?: {
        cms?: string;
        analytics?: string[];
        frameworks?: string[];
        payments?: string[];
        hosting?: string;
    };
}

const TechStackCard: React.FC<TechStackCardProps> = ({ techStack }) => {
    // Hide card if no tech stack data
    if (!techStack) return null;

    const categories = [
        {
            icon: Code,
            label: 'CMS',
            value: techStack.cms || 'Not detected',
            isEmpty: !techStack.cms,
        },
        {
            icon: BarChart3,
            label: 'Analytics',
            value: techStack.analytics?.join(', ') || 'Not detected',
            isEmpty: !techStack.analytics?.length,
        },
        {
            icon: Database,
            label: 'Frameworks',
            value: techStack.frameworks?.join(', ') || 'Not detected',
            isEmpty: !techStack.frameworks?.length,
        },
        {
            icon: CreditCard,
            label: 'Payments',
            value: techStack.payments?.join(', ') || 'Not detected',
            isEmpty: !techStack.payments?.length,
        },
        {
            icon: Server,
            label: 'Hosting',
            value: techStack.hosting || 'Not detected',
            isEmpty: !techStack.hosting,
        },
    ];

    return (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Code className="text-purple-400" size={20} />
                Tech Stack Intelligence
            </h3>

            <div className="space-y-3">
                {categories.map((category) => {
                    const Icon = category.icon;
                    return (
                        <div key={category.label} className="flex items-start gap-3">
                            <Icon
                                size={16}
                                className={`mt-0.5 ${category.isEmpty ? 'text-gray-500' : 'text-blue-400'
                                    }`}
                            />
                            <div className="flex-1">
                                <span className="text-sm font-medium text-gray-400">
                                    {category.label}:
                                </span>{' '}
                                <span
                                    className={`text-sm ${category.isEmpty ? 'text-gray-500 italic' : 'text-white'
                                        }`}
                                >
                                    {category.value}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default TechStackCard;
