import React, { useState } from 'react';
import { TrendingUp, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface SEOHealthCardProps {
    seoAnalysis?: {
        seo_score?: number;
        title?: { present: boolean; length?: number };
        meta_description?: { present: boolean; length?: number };
        h1_count?: number;
        canonical?: boolean;
        indexable?: boolean;
        sitemap_found?: boolean;
        robots_txt_found?: boolean;
    };
}

const SEOHealthCard: React.FC<SEOHealthCardProps> = ({ seoAnalysis }) => {
    const [showDetails, setShowDetails] = useState(false);

    // Hide card if no SEO data
    if (!seoAnalysis) return null;

    const { seo_score } = seoAnalysis;

    // Determine score color
    const getScoreColor = (score?: number) => {
        if (score === undefined) return 'text-gray-400';
        if (score >= 80) return 'text-green-400';
        if (score >= 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getBgColor = (score?: number) => {
        if (score === undefined) return 'bg-gray-500/20';
        if (score >= 80) return 'bg-green-500/20';
        if (score >= 50) return 'bg-yellow-500/20';
        return 'bg-red-500/20';
    };

    const scoreColor = getScoreColor(seo_score);
    const bgColor = getBgColor(seo_score);

    // SEO Checklist Items
    const checklistItems = [
        {
            label: 'Title tag present',
            value: seoAnalysis.title?.present,
            detail: seoAnalysis.title?.length ? `Length: ${seoAnalysis.title.length}` : null,
        },
        {
            label: 'Meta description present',
            value: seoAnalysis.meta_description?.present,
            detail: seoAnalysis.meta_description?.length
                ? `Length: ${seoAnalysis.meta_description.length}`
                : null,
        },
        {
            label: 'H1 count',
            value: seoAnalysis.h1_count === 1,
            detail: `Count: ${seoAnalysis.h1_count ?? 'Unknown'}`,
        },
        {
            label: 'Canonical URL',
            value: seoAnalysis.canonical,
        },
        {
            label: 'Indexable',
            value: seoAnalysis.indexable,
        },
        {
            label: 'Sitemap found',
            value: seoAnalysis.sitemap_found,
        },
        {
            label: 'Robots.txt found',
            value: seoAnalysis.robots_txt_found,
        },
    ];

    return (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="text-green-400" size={20} />
                SEO Health Report
            </h3>

            {/* Score Display */}
            <div className={`${bgColor} rounded-lg p-4 mb-4`}>
                <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-300">SEO Score</span>
                    {seo_score !== undefined ? (
                        <span className={`text-3xl font-bold ${scoreColor}`}>
                            {seo_score} / 100
                        </span>
                    ) : (
                        <span className="text-sm text-gray-500 italic">Analysis unavailable</span>
                    )}
                </div>
            </div>

            {/* Checklist Summary */}
            <div className="space-y-2">
                {checklistItems.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                        {item.value ? (
                            <CheckCircle size={16} className="text-green-400" />
                        ) : (
                            <XCircle size={16} className="text-gray-500" />
                        )}
                        <span className={`text-sm ${item.value ? 'text-white' : 'text-gray-400'}`}>
                            {item.label}
                            {showDetails && item.detail && (
                                <span className="text-gray-500 ml-2">({item.detail})</span>
                            )}
                        </span>
                    </div>
                ))}
            </div>

            {/* Details Toggle */}
            <button
                onClick={() => setShowDetails(!showDetails)}
                className="mt-4 text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
                {showDetails ? (
                    <>
                        <ChevronUp size={14} /> Hide Details
                    </>
                ) : (
                    <>
                        <ChevronDown size={14} /> Show Details
                    </>
                )}
            </button>
        </div>
    );
};

export default SEOHealthCard;
