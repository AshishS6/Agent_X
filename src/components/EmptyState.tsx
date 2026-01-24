import React from 'react';
import { LucideIcon } from 'lucide-react';
import clsx from 'clsx';

interface EmptyStateProps {
    icon?: LucideIcon;
    title: string;
    description?: string;
    primaryAction?: {
        label: string;
        onClick: () => void;
        icon?: React.ElementType;
    };
    secondaryAction?: {
        label: string;
        onClick: () => void;
        icon?: React.ElementType;
    };
    hint?: string;
    variant?: 'default' | 'minimal';
}

/**
 * EmptyState component for displaying helpful empty states with CTAs
 * Used for conversations, tasks, activity logs, etc.
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
    icon: Icon,
    title,
    description,
    primaryAction,
    secondaryAction,
    hint,
    variant = 'default',
}) => {
    if (variant === 'minimal') {
        return (
            <div className="text-center text-gray-500 py-8">
                {Icon && <Icon size={32} className="mx-auto mb-2 opacity-30" />}
                <p className="text-sm">{title}</p>
                {hint && <p className="text-xs text-gray-600 mt-1">{hint}</p>}
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            {Icon && (
                <div className="w-16 h-16 rounded-full bg-gray-800/50 flex items-center justify-center mb-4">
                    <Icon size={32} className="text-gray-500 opacity-50" />
                </div>
            )}
            
            <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
            
            {description && (
                <p className="text-sm text-gray-400 mb-6 max-w-md">{description}</p>
            )}

            {(primaryAction || secondaryAction) && (
                <div className="flex flex-wrap gap-3 justify-center mb-4">
                    {primaryAction && (
                        <button
                            onClick={primaryAction.onClick}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            {primaryAction.icon && <primaryAction.icon size={16} />}
                            {primaryAction.label}
                        </button>
                    )}
                    {secondaryAction && (
                        <button
                            onClick={secondaryAction.onClick}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors border border-gray-700"
                        >
                            {secondaryAction.icon && <secondaryAction.icon size={16} />}
                            {secondaryAction.label}
                        </button>
                    )}
                </div>
            )}

            {hint && (
                <p className="text-xs text-gray-500 mt-2 max-w-md">{hint}</p>
            )}
        </div>
    );
};
