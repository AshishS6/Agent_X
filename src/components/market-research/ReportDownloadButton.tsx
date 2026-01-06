import React, { useState } from 'react';
import { Download, FileText, FileJson, FileCode, Loader } from 'lucide-react';
import { TaskService } from '../../services/api';

interface ReportDownloadButtonProps {
    taskId: string;
    taskStatus: 'pending' | 'processing' | 'completed' | 'failed';
    disabled?: boolean;
}

const ReportDownloadButton: React.FC<ReportDownloadButtonProps> = ({ 
    taskId, 
    taskStatus,
    disabled = false 
}) => {
    const [loading, setLoading] = useState<string | null>(null);
    const [showDropdown, setShowDropdown] = useState(false);

    const isDisabled = disabled || taskStatus !== 'completed';

    const handleDownload = async (format: 'pdf' | 'json' | 'markdown') => {
        if (isDisabled) return;

        setLoading(format);
        setShowDropdown(false);

        try {
            await TaskService.downloadReport(taskId, format);
            // Show success toast (you may want to use a toast library)
            console.log(`${format.toUpperCase()} report downloaded successfully`);
        } catch (error) {
            console.error(`Failed to download ${format} report:`, error);
            // Show error toast
            alert(`Failed to download ${format} report. Please try again.`);
        } finally {
            setLoading(null);
        }
    };

    const formatOptions = [
        { 
            value: 'pdf' as const, 
            label: 'PDF (Compliance Report)', 
            icon: FileText,
            hint: '~500KB estimated'
        },
        { 
            value: 'json' as const, 
            label: 'JSON (Full Scan Data)', 
            icon: FileJson,
            hint: 'Machine-readable'
        },
        { 
            value: 'markdown' as const, 
            label: 'Markdown (Readable Report)', 
            icon: FileCode,
            hint: 'Human-readable'
        }
    ];

    return (
        <div className="relative">
            <button
                onClick={() => !isDisabled && setShowDropdown(!showDropdown)}
                disabled={isDisabled}
                className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium
                    transition-colors
                    ${isDisabled 
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }
                `}
                title={isDisabled ? 'Scan must be completed to download report' : 'Download Report'}
            >
                <Download className="w-4 h-4" />
                <span>Download Report</span>
            </button>

            {showDropdown && !isDisabled && (
                <>
                    <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setShowDropdown(false)}
                    />
                    <div className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-20">
                        <div className="py-1">
                            {formatOptions.map((option) => {
                                const Icon = option.icon;
                                const isLoading = loading === option.value;
                                
                                return (
                                    <button
                                        key={option.value}
                                        onClick={() => handleDownload(option.value)}
                                        disabled={isLoading}
                                        className={`
                                            w-full flex items-center gap-3 px-4 py-3 text-left
                                            hover:bg-gray-700 transition-colors
                                            ${isLoading ? 'opacity-50 cursor-wait' : ''}
                                        `}
                                    >
                                        {isLoading ? (
                                            <Loader className="w-4 h-4 animate-spin text-blue-400" />
                                        ) : (
                                            <Icon className="w-4 h-4 text-gray-400" />
                                        )}
                                        <div className="flex-1">
                                            <div className="text-white text-sm font-medium">
                                                {option.label}
                                            </div>
                                            <div className="text-gray-400 text-xs">
                                                {option.hint}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default ReportDownloadButton;



