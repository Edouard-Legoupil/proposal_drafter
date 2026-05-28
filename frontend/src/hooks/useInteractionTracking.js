/**
 * useInteractionTracking Hook
 * 
 * Comprehensive hook for tracking all user interactions and sending them to the backend.
 * This hook provides the foundation for the learning wizard system.
 */

import { useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

/**
 * Custom hook for tracking user interactions
 * @param {Object} user - Current user object
 * @param {boolean} enabled - Whether tracking is enabled
 * @returns {Object} Tracking functions and session information
 */
export function useInteractionTracking(user, enabled = true) {
    const navigate = useNavigate();
    const location = useLocation();
    
    // State management
    const sessionRef = useRef(null);
    const interactionQueue = useRef([]);
    const isProcessing = useRef(false);
    const lastActivity = useRef(Date.now());
    
    // Start a new session when user logs in or page loads
    const startSession = useCallback(async () => {
        if (!user?.id || !enabled) return;
        
        try {
            // Get device and browser information
            const deviceInfo = getDeviceInfo();
            
            const response = await fetch(`${API_BASE_URL}/interactions/sessions/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(deviceInfo)
            });
            
            if (response.ok) {
                const data = await response.json();
                sessionRef.current = data.session_id;
                console.log('Interaction tracking session started:', data.session_id);
                
                // Log the initial page view
                logPageView();
            }
        } catch (error) {
            console.error('Failed to start interaction session:', error);
        }
    }, [user?.id, enabled]);
    
    // End the session when user logs out or tab closes
    const endSession = useCallback(async () => {
        if (!sessionRef.current || !enabled) return;
        
        try {
            await fetch(`${API_BASE_URL}/interactions/sessions/${sessionRef.current}/end`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            // Flush any remaining interactions
            await flushInteractionQueue();
            
            console.log('Interaction tracking session ended:', sessionRef.current);
            sessionRef.current = null;
        } catch (error) {
            console.error('Failed to end interaction session:', error);
        }
    }, [enabled]);
    
    // Log a page view interaction
    const logPageView = useCallback(() => {
        if (!sessionRef.current || !enabled) return;
        
        const pageViewData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'page_view',
            page_url: window.location.href,
            page_title: document.title,
            component_name: 'page',
            element_type: 'document',
            element_test_id: 'document',
            element_text: document.title,
            event_data: {
                referrer: document.referrer,
                path: location.pathname,
                search: location.search,
                hash: location.hash
            },
            metadata: {
                timestamp: new Date().toISOString(),
                screen_width: window.screen.width,
                screen_height: window.screen.height
            }
        };
        
        queueInteraction(pageViewData);
    }, [user?.id, enabled, location]);
    
    // Log a click interaction
    const logClick = useCallback((event) => {
        if (!sessionRef.current || !enabled) return;
        
        const target = event.target;
        const testId = target.getAttribute('data-testid') || 
                      findParentTestId(target) || 
                      'unknown';
        
        const clickData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'click',
            page_url: window.location.href,
            page_title: document.title,
            component_name: getComponentName(target),
            element_type: target.tagName.toLowerCase(),
            element_selector: getElementSelector(target),
            element_test_id: testId,
            element_text: target.textContent?.trim() || target.value || '',
            event_data: {
                button: event.button,
                ctrlKey: event.ctrlKey,
                shiftKey: event.shiftKey,
                altKey: event.altKey,
                metaKey: event.metaKey
            },
            metadata: {
                timestamp: new Date().toISOString(),
                clientX: event.clientX,
                clientY: event.clientY
            }
        };
        
        queueInteraction(clickData);
    }, [user?.id, enabled]);
    
    // Log a form submission
    const logFormSubmission = useCallback((formElement, success = true) => {
        if (!sessionRef.current || !enabled) return;
        
        const formData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'form_submission',
            page_url: window.location.href,
            page_title: document.title,
            component_name: getComponentName(formElement),
            element_type: 'form',
            element_selector: getElementSelector(formElement),
            element_test_id: formElement.getAttribute('data-testid') || 'form',
            element_text: formElement.getAttribute('name') || 'form',
            event_data: {
                form_id: formElement.id,
                form_name: formElement.name,
                field_count: formElement.elements.length,
                success: success
            },
            metadata: {
                timestamp: new Date().toISOString()
            }
        };
        
        queueInteraction(formData);
    }, [user?.id, enabled]);
    
    // Log a navigation event
    const logNavigation = useCallback((from, to) => {
        if (!sessionRef.current || !enabled) return;
        
        const navData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'navigation',
            page_url: window.location.href,
            page_title: document.title,
            component_name: 'router',
            element_type: 'navigation',
            element_test_id: 'navigation',
            element_text: `Navigated from ${from} to ${to}`,
            event_data: {
                from_url: from,
                to_url: to,
                navigation_type: 'route_change'
            },
            metadata: {
                timestamp: new Date().toISOString()
            }
        };
        
        queueInteraction(navData);
    }, [user?.id, enabled]);
    
    // Log a search interaction
    const logSearch = useCallback((query, resultsCount) => {
        if (!sessionRef.current || !enabled) return;
        
        const searchData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'search',
            page_url: window.location.href,
            page_title: document.title,
            component_name: 'search',
            element_type: 'input',
            element_test_id: 'search-input',
            element_text: query,
            event_data: {
                search_query: query,
                results_count: resultsCount,
                search_type: 'global'
            },
            metadata: {
                timestamp: new Date().toISOString()
            }
        };
        
        queueInteraction(searchData);
    }, [user?.id, enabled]);
    
    // Log a wizard interaction
    const logWizardInteraction = useCallback((wizardData) => {
        if (!sessionRef.current || !enabled) return;
        
        // First log the base interaction
        const baseInteraction = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'wizard_interaction',
            page_url: window.location.href,
            page_title: document.title,
            component_name: 'wizard',
            element_type: 'wizard',
            element_test_id: 'wizard',
            element_text: `Wizard interaction: ${wizardData.action_type}`,
            event_data: {
                action_type: wizardData.action_type,
                context: wizardData.context
            },
            metadata: {
                timestamp: new Date().toISOString()
            }
        };
        
        queueInteraction(baseInteraction, true).then(interactionId => {
            if (interactionId) {
                // Then log the wizard-specific details
                logWizardDetails(interactionId, wizardData);
            }
        });
    }, [user?.id, enabled]);
    
    // Log wizard-specific details
    const logWizardDetails = useCallback(async (interactionId, wizardData) => {
        try {
            const wizardDetails = {
                interaction_id: interactionId,
                session_id: sessionRef.current,
                user_id: user?.id,
                action_type: wizardData.action_type,
                search_query: wizardData.search_query,
                selected_category_id: wizardData.selected_category_id,
                viewed_qa_item_id: wizardData.viewed_qa_item_id,
                feedback_score: wizardData.feedback_score,
                feedback_comment: wizardData.feedback_comment,
                time_spent_ms: wizardData.time_spent_ms,
                was_helpful: wizardData.was_helpful,
                context_data: wizardData.context_data
            };
            
            await fetch(`${API_BASE_URL}/interactions/wizard/log/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(wizardDetails)
            });
        } catch (error) {
            console.error('Failed to log wizard details:', error);
        }
    }, [user?.id, enabled]);
    
    // Log an error
    const logError = useCallback((error, context = {}) => {
        if (!sessionRef.current || !enabled) return;
        
        const errorData = {
            session_id: sessionRef.current,
            user_id: user?.id,
            interaction_type: 'error',
            page_url: window.location.href,
            page_title: document.title,
            component_name: context.component || 'unknown',
            element_type: context.element_type || 'unknown',
            element_selector: context.selector || 'unknown',
            element_test_id: context.test_id || 'unknown',
            element_text: context.message || error.message || 'Unknown error',
            event_data: {
                error_type: error.name,
                error_message: error.message,
                error_code: context.code
            },
            metadata: {
                timestamp: new Date().toISOString(),
                stack_trace: error.stack?.substring(0, 1000) // Limit length
            },
            was_successful: false,
            error_message: error.message,
            error_stack: error.stack
        };
        
        queueInteraction(errorData);
    }, [user?.id, enabled]);
    
    // Queue interaction for batch processing
    const queueInteraction = useCallback((interactionData, isWizard = false) => {
        if (!sessionRef.current || !enabled) {
            return Promise.resolve(null);
        }
        
        // Add timestamp if not present
        if (!interactionData.metadata) {
            interactionData.metadata = {};
        }
        if (!interactionData.metadata.timestamp) {
            interactionData.metadata.timestamp = new Date().toISOString();
        }
        
        // For wizard interactions, we want immediate processing
        if (isWizard) {
            return sendInteraction(interactionData);
        }
        
        // Add to queue
        interactionQueue.current.push(interactionData);
        lastActivity.current = Date.now();
        
        // Process queue if not already processing
        if (!isProcessing.current) {
            processQueue();
        }
        
        return Promise.resolve(null);
    }, [user?.id, enabled]);
    
    // Send interaction to backend
    const sendInteraction = useCallback(async (interactionData) => {
        if (!sessionRef.current || !enabled) return null;
        
        try {
            const response = await fetch(`${API_BASE_URL}/interactions/log/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(interactionData)
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.interaction_id;
            } else {
                console.error('Failed to log interaction:', await response.text());
                return null;
            }
        } catch (error) {
            console.error('Network error logging interaction:', error);
            return null;
        }
    }, [user?.id, enabled]);
    
    // Process the interaction queue
    const processQueue = useCallback(async () => {
        if (isProcessing.current || interactionQueue.current.length === 0) {
            return;
        }
        
        isProcessing.current = true;
        
        try {
            // Process in batches of 10 for better performance
            const batchSize = Math.min(10, interactionQueue.current.length);
            const batch = interactionQueue.current.splice(0, batchSize);
            
            // Send batch (in a real app, you might have a bulk endpoint)
            for (const interaction of batch) {
                await sendInteraction(interaction);
            }
        } catch (error) {
            console.error('Error processing interaction batch:', error);
        } finally {
            isProcessing.current = false;
            
            // Process remaining items if any
            if (interactionQueue.current.length > 0) {
                processQueue();
            }
        }
    }, [sendInteraction]);
    
    // Flush the queue (e.g., before unload)
    const flushInteractionQueue = useCallback(async () => {
        if (interactionQueue.current.length > 0) {
            await processQueue();
        }
    }, [processQueue]);
    
    // Helper function to get device information
    const getDeviceInfo = useCallback(() => {
        return {
            ip_address: 'client_ip', // Would be set server-side
            user_agent: navigator.userAgent,
            device_type: getDeviceType(),
            browser_name: getBrowserName(),
            browser_version: getBrowserVersion(),
            os_name: getOSName(),
            os_version: getOSVersion(),
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            is_mobile: isMobileDevice()
        };
    }, []);
    
    // Helper function to find parent test ID
    const findParentTestId = useCallback((element, maxDepth = 5) => {
        let current = element;
        for (let i = 0; i < maxDepth; i++) {
            if (current.getAttribute('data-testid')) {
                return current.getAttribute('data-testid');
            }
            if (current.parentElement) {
                current = current.parentElement;
            } else {
                break;
            }
        }
        return null;
    }, []);
    
    // Helper function to get component name
    const getComponentName = useCallback((element) => {
        // Try to find a component name from class or data attributes
        const className = element.className;
        if (className) {
            const match = className.match(/\b([A-Z][a-z]+)/);
            if (match) return match[1];
        }
        
        // Check for data-component attribute
        const component = element.getAttribute('data-component');
        if (component) return component;
        
        // Fallback to tag name
        return element.tagName.toLowerCase();
    }, []);
    
    // Helper function to get element selector
    const getElementSelector = useCallback((element) => {
        try {
            if (element.id) return `#${element.id}`;
            if (element.className) return `.${element.className.split(' ')[0]}`;
            return element.tagName.toLowerCase();
        } catch (e) {
            return 'unknown';
        }
    }, []);
    
    // Helper functions for device detection
    const getDeviceType = useCallback(() => {
        if (isMobileDevice()) return 'mobile';
        if (isTabletDevice()) return 'tablet';
        return 'desktop';
    }, []);
    
    const isMobileDevice = useCallback(() => {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }, []);
    
    const isTabletDevice = useCallback(() => {
        return /(tablet|ipad|playbook|silk)|(android(?!.*mobile))/i.test(navigator.userAgent);
    }, []);
    
    const getBrowserName = useCallback(() => {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Firefox')) return 'Firefox';
        if (userAgent.includes('SamsungBrowser')) return 'Samsung Internet';
        if (userAgent.includes('Opera') || userAgent.includes('OPR')) return 'Opera';
        if (userAgent.includes('Trident') || userAgent.includes('MSIE')) return 'Internet Explorer';
        if (userAgent.includes('Edge')) return 'Edge';
        if (userAgent.includes('Edg')) return 'Edge Chromium';
        if (userAgent.includes('Chrome')) return 'Chrome';
        if (userAgent.includes('Safari')) return 'Safari';
        return 'Unknown';
    }, []);
    
    const getBrowserVersion = useCallback(() => {
        const userAgent = navigator.userAgent;
        const match = userAgent.match(/(Firefox|Chrome|Safari|Edge|OPR)\/(\d+)/);
        return match ? match[2] : 'Unknown';
    }, []);
    
    const getOSName = useCallback(() => {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Windows')) return 'Windows';
        if (userAgent.includes('Macintosh') || userAgent.includes('Mac OS X')) return 'macOS';
        if (userAgent.includes('Linux')) return 'Linux';
        if (userAgent.includes('Android')) return 'Android';
        if (userAgent.includes('iPhone') || userAgent.includes('iPad')) return 'iOS';
        return 'Unknown';
    }, []);
    
    const getOSVersion = useCallback(() => {
        const userAgent = navigator.userAgent;
        const match = userAgent.match(/(Windows NT|Mac OS X|Android|iOS) (\d+[._]\d+)/);
        return match ? match[2].replace('_', '.') : 'Unknown';
    }, []);
    
    // Set up event listeners when component mounts
    useEffect(() => {
        if (!enabled || !user?.id) return;
        
        // Start session
        startSession();
        
        // Set up click tracking
        const handleClick = (event) => {
            logClick(event);
        };
        
        document.addEventListener('click', handleClick, true);
        
        // Set up navigation tracking
        const unlisten = navigate((to, from) => {
            logNavigation(from.pathname, to.pathname);
        });
        
        // Set up beforeunload to flush queue
        const handleBeforeUnload = () => {
            flushInteractionQueue();
        };
        
        window.addEventListener('beforeunload', handleBeforeUnload);
        
        // Set up periodic flushing
        const flushInterval = setInterval(() => {
            if (Date.now() - lastActivity.current > 30000) { // 30 seconds of inactivity
                flushInteractionQueue();
            }
        }, 60000); // Check every minute
        
        // Cleanup
        return () => {
            document.removeEventListener('click', handleClick, true);
            unlisten();
            window.removeEventListener('beforeunload', handleBeforeUnload);
            clearInterval(flushInterval);
            endSession();
        };
    }, [user?.id, enabled, startSession, endSession, logClick, navigate, flushInteractionQueue]);
    
    // Track page views on route changes
    useEffect(() => {
        if (sessionRef.current && enabled) {
            logPageView();
        }
    }, [location.pathname, logPageView, enabled]);
    
    // Public API
    return {
        sessionId: sessionRef.current,
        logPageView,
        logClick,
        logFormSubmission,
        logNavigation,
        logSearch,
        logWizardInteraction,
        logError,
        flush: flushInteractionQueue,
        isTracking: enabled && !!sessionRef.current
    };
}

/**
 * Helper hook to wrap components with interaction tracking
 */
export function withInteractionTracking(Component) {
    return function WrappedComponent(props) {
        const { user } = props; // Assume user is passed as prop
        const tracking = useInteractionTracking(user);
        
        return <Component {...props} tracking={tracking} />;
    };
}

/**
 * Global interaction tracker instance
 */
let globalTracker = null;

export function initGlobalInteractionTracker(user) {
    if (!globalTracker) {
        globalTracker = useInteractionTracking(user);
    }
    return globalTracker;
}

export function getGlobalInteractionTracker() {
    return globalTracker;
}