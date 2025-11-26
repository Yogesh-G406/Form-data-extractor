/**
 * Langfuse Client for Frontend
 * Tracks user interactions and events
 */

import { Langfuse } from 'langfuse';

// Initialize Langfuse client
let langfuseClient = null;

try {
    const publicKey = import.meta.env.VITE_LANGFUSE_PUBLIC_KEY;
    const host = import.meta.env.VITE_LANGFUSE_HOST || 'https://cloud.langfuse.com';

    if (publicKey) {
        langfuseClient = new Langfuse({
            publicKey,
            baseUrl: host,
        });
        console.log('[OK] Langfuse client initialized');
    } else {
        console.warn('[WARNING] Langfuse public key not configured');
    }
} catch (error) {
    console.error('[ERROR] Failed to initialize Langfuse:', error);
}

/**
 * Track a custom event
 */
export const trackEvent = (name, metadata = {}) => {
    if (!langfuseClient) return;

    try {
        langfuseClient.event({
            name,
            metadata: {
                ...metadata,
                timestamp: new Date().toISOString(),
                url: window.location.href,
            },
        });
    } catch (error) {
        console.error(`[ERROR] Failed to track event ${name}:`, error);
    }
};

/**
 * Track a click event
 */
export const trackClick = (element, additionalMetadata = {}) => {
    trackEvent('click', {
        element: element.tagName || 'unknown',
        id: element.id || null,
        className: element.className || null,
        text: element.innerText?.substring(0, 50) || null,
        ...additionalMetadata,
    });
};

/**
 * Track an input event
 */
export const trackInput = (fieldName, valueLength, additionalMetadata = {}) => {
    trackEvent('input', {
        field: fieldName,
        value_length: valueLength,
        ...additionalMetadata,
    });
};

/**
 * Track navigation
 */
export const trackNavigation = (from, to, additionalMetadata = {}) => {
    trackEvent('navigation', {
        from,
        to,
        ...additionalMetadata,
    });
};

/**
 * Track file selection
 */
export const trackFileSelection = (file, additionalMetadata = {}) => {
    trackEvent('file_selected', {
        filename: file.name,
        size: file.size,
        type: file.type,
        ...additionalMetadata,
    });
};

/**
 * Track API call
 */
export const trackApiCall = (endpoint, method, status, duration, additionalMetadata = {}) => {
    trackEvent('api_call', {
        endpoint,
        method,
        status,
        duration_ms: duration,
        ...additionalMetadata,
    });
};

/**
 * Track error
 */
export const trackError = (error, context = {}) => {
    trackEvent('error', {
        error_message: error.message || String(error),
        error_type: error.name || 'Error',
        stack: error.stack || null,
        ...context,
    });
};

/**
 * Track download
 */
export const trackDownload = (type, additionalMetadata = {}) => {
    trackEvent('download', {
        type,
        ...additionalMetadata,
    });
};

/**
 * Track view mode change
 */
export const trackViewModeChange = (fromMode, toMode) => {
    trackEvent('view_mode_change', {
        from_mode: fromMode,
        to_mode: toMode,
    });
};

/**
 * Flush events (call before page unload)
 */
export const flushEvents = () => {
    if (langfuseClient) {
        langfuseClient.flush();
    }
};

export default langfuseClient;
