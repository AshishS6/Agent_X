// Feature flags for progressive enhancement
export const FEATURES = {
    // Market Research Agent V2 UI Features
    // Enables Tech Stack, SEO Health, and Enhanced Business Metadata displays
    // Default: false for safe rollout
    ENABLE_MARKET_RESEARCH_V2_UI: import.meta.env.VITE_ENABLE_MR_V2_UI === 'true' || false,
};
