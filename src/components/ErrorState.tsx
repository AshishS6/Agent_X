import React from 'react';
import { AlertTriangle, RefreshCw, ExternalLink, Power, X } from 'lucide-react';
import clsx from 'clsx';

interface ErrorStateProps {
    title: string;
    message?: string;
    failureReason?: string;
    impact?: string;
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
    variant?: 'error' | 'degraded' | 'warning';
}

/**
 * ErrorState component for displaying actionable error information
 * Used for integrations, agents, and other error scenarios
 */
export const ErrorState: React.FC<ErrorStateProps> = ({
    title,
    message,
    failureReason,
    impact,
    primaryAction,
    secondaryAction,
    variant = 'error',
}) => {
    const variantStyles = {
        error: {
            bg: 'bg-red-500/10',
            border: 'border-red-500/20',
            text: 'text-red-400',
            textSecondary: 'text-red-300/70',
            icon: 'text-red-400',
        },
        degraded: {
            bg: 'bg-yellow-500/10',
            border: 'border-yellow-500/20',
            text: 'text-yellow-400',
            textSecondary: 'text-yellow-300/70',
            icon: 'text-yellow-400',
        },
        warning: {
            bg: 'bg-orange-500/10',
            border: 'border-orange-500/20',
            text: 'text-orange-400',
            textSecondary: 'text-orange-300/70',
            icon: 'text-orange-400',
        },
    };

    const styles = variantStyles[variant];

    return (
        <div className={clsx('rounded-lg p-4 border', styles.bg, styles.border)}>
            <div className="flex items-start gap-3">
                <AlertTriangle size={20} className={clsx('shrink-0 mt-0.5', styles.icon)} />
                <div className="flex-1 min-w-0">
                    <h4 className={clsx('font-semibold mb-1', styles.text)}>{title}</h4>
                    
                    {message && (
                        <p className={clsx('text-sm mb-2', styles.textSecondary)}>{message}</p>
                    )}

                    {failureReason && (
                        <div className="mb-2">
                            <p className={clsx('text-xs font-medium mb-1', styles.text)}>Failure Reason:</p>
                            <p className={clsx('text-sm', styles.textSecondary)}>{failureReason}</p>
                        </div>
                    )}

                    {impact && (
                        <div className="mb-3">
                            <p className={clsx('text-xs font-medium mb-1', styles.text)}>Impact:</p>
                            <p className={clsx('text-sm', styles.textSecondary)}>{impact}</p>
                        </div>
                    )}

                    {(primaryAction || secondaryAction) && (
                        <div className="flex flex-wrap gap-2 mt-3">
                            {primaryAction && (
                                <button
                                    onClick={primaryAction.onClick}
                                    className={clsx(
                                        'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                                        variant === 'error'
                                            ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/30'
                                            : variant === 'degraded'
                                            ? 'bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500/30 border border-yellow-500/30'
                                            : 'bg-orange-500/20 text-orange-300 hover:bg-orange-500/30 border border-orange-500/30'
                                    )}
                                >
                                    {primaryAction.icon && <primaryAction.icon size={14} />}
                                    {primaryAction.label}
                                </button>
                            )}
                            {secondaryAction && (
                                <button
                                    onClick={secondaryAction.onClick}
                                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
                                >
                                    {secondaryAction.icon && <secondaryAction.icon size={14} />}
                                    {secondaryAction.label}
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
