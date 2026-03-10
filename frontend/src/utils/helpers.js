// Utility helpers for the Leukemia AI Platform

/**
 * Format a confidence score as a percentage string.
 */
export function formatConfidence(confidence) {
    return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Format an ISO date string to a human-readable format.
 */
export function formatDate(isoStr) {
    return new Date(isoStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Classify a result as benign or malignant for badge coloring.
 */
export function isBenignResult(classification) {
    return classification === 'Benign';
}

/**
 * Truncate a string with ellipsis.
 */
export function truncate(str, maxLen = 30) {
    if (!str) return '';
    return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}
