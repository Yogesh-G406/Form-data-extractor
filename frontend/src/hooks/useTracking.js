/**
 * React Hook for Langfuse Tracking
 * Provides easy-to-use tracking functions for React components
 */

import { useCallback, useEffect } from 'react';
import {
    trackEvent,
    trackClick,
    trackInput,
    trackNavigation,
    trackFileSelection,
    trackApiCall,
    trackError,
    trackDownload,
    trackViewModeChange,
    flushEvents,
} from '../services/langfuseClient';

export const useTracking = () => {
    // Flush events on component unmount or page unload
    useEffect(() => {
        const handleBeforeUnload = () => {
            flushEvents();
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            flushEvents();
        };
    }, []);

    // Track click with automatic event target extraction
    const handleTrackClick = useCallback((event, metadata = {}) => {
        const target = event.currentTarget || event.target;
        trackClick(target, metadata);
    }, []);

    // Track input change
    const handleTrackInput = useCallback((fieldName, value, metadata = {}) => {
        trackInput(fieldName, value?.length || 0, metadata);
    }, []);

    // Track navigation between tabs/views
    const handleTrackNavigation = useCallback((from, to, metadata = {}) => {
        trackNavigation(from, to, metadata);
    }, []);

    // Track file selection
    const handleTrackFileSelection = useCallback((file, metadata = {}) => {
        if (file) {
            trackFileSelection(file, metadata);
        }
    }, []);

    // Track API call with timing
    const handleTrackApiCall = useCallback((endpoint, method, status, duration, metadata = {}) => {
        trackApiCall(endpoint, method, status, duration, metadata);
    }, []);

    // Track error
    const handleTrackError = useCallback((error, context = {}) => {
        trackError(error, context);
    }, []);

    // Track download
    const handleTrackDownload = useCallback((type, metadata = {}) => {
        trackDownload(type, metadata);
    }, []);

    // Track view mode change
    const handleTrackViewModeChange = useCallback((fromMode, toMode) => {
        trackViewModeChange(fromMode, toMode);
    }, []);

    // Generic event tracker
    const handleTrackEvent = useCallback((name, metadata = {}) => {
        trackEvent(name, metadata);
    }, []);

    return {
        trackClick: handleTrackClick,
        trackInput: handleTrackInput,
        trackNavigation: handleTrackNavigation,
        trackFileSelection: handleTrackFileSelection,
        trackApiCall: handleTrackApiCall,
        trackError: handleTrackError,
        trackDownload: handleTrackDownload,
        trackViewModeChange: handleTrackViewModeChange,
        trackEvent: handleTrackEvent,
    };
};

export default useTracking;
