/**
 * Shared formatting utilities for consistent number, percentage, duration, and currency display.
 * 
 * These utilities ensure:
 * - No raw floating point leaks (e.g., 14.583333333333334)
 * - Consistent precision (max 1 decimal for time/percentages)
 * - Thousands separators for large numbers
 * - Proper units and labels
 */

/**
 * Format a number with optional precision and thousands separators
 * 
 * @param value - The number to format
 * @param options - Formatting options
 * @returns Formatted string (e.g., "1,234.5")
 */
export function formatNumber(
    value: number | string | null | undefined,
    options: {
        precision?: number;
        showThousands?: boolean;
        fallback?: string;
    } = {}
): string {
    const { precision = 0, showThousands = true, fallback = '0' } = options;

    if (value === null || value === undefined) {
        return fallback;
    }

    const num = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(num)) {
        return fallback;
    }

    // Round to specified precision
    const rounded = precision > 0 
        ? Math.round(num * Math.pow(10, precision)) / Math.pow(10, precision)
        : Math.round(num);

    if (showThousands) {
        return rounded.toLocaleString('en-US', {
            minimumFractionDigits: precision,
            maximumFractionDigits: precision,
        });
    }

    return rounded.toFixed(precision);
}

/**
 * Format a percentage value with max 1 decimal precision
 * 
 * @param value - The percentage value (0-100 or 0-1)
 * @param precision - Decimal places (default: 1, max: 1)
 * @param isDecimal - If true, treats value as 0-1; if false, treats as 0-100
 * @returns Formatted percentage string (e.g., "86.2%")
 */
export function formatPercentage(
    value: number | string | null | undefined,
    precision: number = 1,
    isDecimal: boolean = false
): string {
    if (value === null || value === undefined) {
        return '0%';
    }

    const num = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(num)) {
        return '0%';
    }

    // Clamp precision to max 1 decimal
    const clampedPrecision = Math.min(precision, 1);

    // Convert to 0-100 range if needed
    const percentage = isDecimal ? num * 100 : num;

    // Round to specified precision
    const rounded = clampedPrecision > 0
        ? Math.round(percentage * Math.pow(10, clampedPrecision)) / Math.pow(10, clampedPrecision)
        : Math.round(percentage);

    return `${rounded.toFixed(clampedPrecision)}%`;
}

/**
 * Format duration in hours with max 1 decimal precision
 * 
 * @param hours - Duration in hours (can be number or string like "14.5h")
 * @returns Formatted duration string (e.g., "14.5h" or "2.3h")
 */
export function formatDuration(
    hours: number | string | null | undefined
): string {
    if (hours === null || hours === undefined) {
        return '0h';
    }

    // If already a string with "h" suffix, extract the number
    if (typeof hours === 'string') {
        if (hours.endsWith('h')) {
            const numStr = hours.slice(0, -1);
            const num = parseFloat(numStr);
            if (!isNaN(num)) {
                // Round to 1 decimal
                const rounded = Math.round(num * 10) / 10;
                return `${rounded.toFixed(1)}h`;
            }
        }
        // Try parsing as number
        const num = parseFloat(hours);
        if (!isNaN(num)) {
            const rounded = Math.round(num * 10) / 10;
            return `${rounded.toFixed(1)}h`;
        }
        return '0h';
    }

    // Round to 1 decimal
    const rounded = Math.round(hours * 10) / 10;
    return `${rounded.toFixed(1)}h`;
}

/**
 * Format currency amount with thousands separators
 * 
 * @param amount - The amount to format
 * @param currency - Currency code (default: "USD")
 * @param showDecimals - Whether to show decimal places (default: true)
 * @returns Formatted currency string (e.g., "$1,234.56")
 */
export function formatCurrency(
    amount: number | string | null | undefined,
    currency: string = 'USD',
    showDecimals: boolean = true
): string {
    if (amount === null || amount === undefined) {
        return `$0${showDecimals ? '.00' : ''}`;
    }

    const num = typeof amount === 'string' ? parseFloat(amount) : amount;

    if (isNaN(num)) {
        return `$0${showDecimals ? '.00' : ''}`;
    }

    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: showDecimals ? 2 : 0,
        maximumFractionDigits: showDecimals ? 2 : 0,
    }).format(num);
}

/**
 * Format a large number with appropriate suffix (K, M, B)
 * 
 * @param value - The number to format
 * @param precision - Decimal places (default: 1)
 * @returns Formatted string (e.g., "1.2K", "3.5M")
 */
export function formatCompactNumber(
    value: number | string | null | undefined,
    precision: number = 1
): string {
    if (value === null || value === undefined) {
        return '0';
    }

    const num = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(num)) {
        return '0';
    }

    const abs = Math.abs(num);
    const sign = num < 0 ? '-' : '';

    if (abs >= 1_000_000_000) {
        return `${sign}${(abs / 1_000_000_000).toFixed(precision)}B`;
    }
    if (abs >= 1_000_000) {
        return `${sign}${(abs / 1_000_000).toFixed(precision)}M`;
    }
    if (abs >= 1_000) {
        return `${sign}${(abs / 1_000).toFixed(precision)}K`;
    }

    return `${sign}${abs.toFixed(precision)}`;
}
