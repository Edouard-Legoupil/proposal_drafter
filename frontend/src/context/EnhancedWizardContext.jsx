/**
 * Enhanced Wizard Context with Interaction Tracking Integration
 * 
 * This context extends the basic wizard functionality with:
 * - User interaction history awareness
 * - Context-aware suggestions based on past behavior
 * - Personalized help recommendations
 * - Learning from user feedback and interactions
 */

import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useInteractionTracking } from '../hooks/useInteractionTracking';
import { useWizard } from './WizardContext';

const EnhancedWizardContext = createContext();

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export const EnhancedWizardProvider = ({ children, user }) => {
    // Get basic wizard functionality
    const wizard = useWizard();
    
    // Get interaction tracking
    const tracking = useInteractionTracking(user);
    
    // Enhanced state for learning capabilities
    const [contextAwareSuggestions, setContextAwareSuggestions] = useState([]);
    const [userJourneyPatterns, setUserJourneyPatterns] = useState([]);
    const [recentInteractions, setRecentInteractions] = useState([]);
    const [learningMode, setLearningMode] = useState('basic'); // 'basic', 'intermediate', 'advanced'
    const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
    const [suggestionError, setSuggestionError] = useState(null);
    
    // Track when wizard is opened
    const trackWizardOpen = useCallback(() => {
        if (tracking?.isTracking) {
            tracking.logWizardInteraction({
                action_type: 'wizard_open',
                context: {
                    page: window.location.pathname,
                    component: 'wizard'
                }
            });
        }
    }, [tracking]);
    
    // Track category selection
    const trackCategorySelect = useCallback((category) => {
        if (tracking?.isTracking) {
            tracking.logWizardInteraction({
                action_type: 'category_select',
                selected_category_id: category?.id,
                context: {
                    category_name: category?.name,
                    category_description: category?.description
                }
            });
        }
    }, [tracking]);
    
    // Track Q&A item view
    const trackQaItemView = useCallback((item) => {
        if (tracking?.isTracking) {
            const startTime = Date.now();
            
            tracking.logWizardInteraction({
                action_type: 'qa_item_view',
                viewed_qa_item_id: item?.id,
                context: {
                    question: item?.question,
                    category_id: item?.category_id
                }
            });
            
            // Return a function to track time spent when item is closed
            return () => {
                const timeSpent = Date.now() - startTime;
                tracking.logWizardInteraction({
                    action_type: 'qa_item_view_completed',
                    viewed_qa_item_id: item?.id,
                    time_spent_ms: timeSpent,
                    context: {
                        question: item?.question,
                        time_spent_seconds: Math.round(timeSpent / 1000)
                    }
                });
            };
        }
        return () => {};
    }, [tracking]);
    
    // Track search
    const trackSearch = useCallback((query, results) => {
        if (tracking?.isTracking) {
            tracking.logSearch(query, results?.length || 0);
            
            tracking.logWizardInteraction({
                action_type: 'search',
                search_query: query,
                context: {
                    results_count: results?.length || 0
                }
            });
        }
    }, [tracking]);
    
    // Track feedback submission
    const trackFeedback = useCallback((itemId, score, comment) => {
        if (tracking?.isTracking) {
            tracking.logWizardInteraction({
                action_type: 'feedback',
                viewed_qa_item_id: itemId,
                feedback_score: score,
                feedback_comment: comment,
                was_helpful: score >= 3 // Consider 3+ as helpful
            });
        }
    }, [tracking]);
    
    // Fetch context-aware suggestions based on current context
    const fetchContextAwareSuggestions = useCallback(async (currentPage, currentComponent) => {
        if (!tracking?.isTracking || !user?.id) return;
        
        try {
            setIsLoadingSuggestions(true);
            setSuggestionError(null);
            
            const response = await fetch(`${API_BASE_URL}/interactions/suggestions/?current_page=${encodeURIComponent(currentPage || '')}&current_component=${encodeURIComponent(currentComponent || '')}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setContextAwareSuggestions(data);
                
                // Update learning mode based on suggestion quality
                const hasHighConfidence = data.some(s => s.confidence > 0.8);
                if (hasHighConfidence) {
                    setLearningMode(prev => prev === 'advanced' ? 'advanced' : 'intermediate');
                }
            } else {
                throw new Error('Failed to fetch suggestions');
            }
        } catch (error) {
            console.error('Error fetching context-aware suggestions:', error);
            setSuggestionError('Failed to load personalized suggestions');
        } finally {
            setIsLoadingSuggestions(false);
        }
    }, [tracking, user?.id]);
    
    // Fetch user journey patterns
    const fetchUserJourneyPatterns = useCallback(async () => {
        if (!user?.id) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/interactions/users/${user.id}/journey-patterns/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setUserJourneyPatterns(data);
            }
        } catch (error) {
            console.error('Error fetching journey patterns:', error);
        }
    }, [user?.id]);
    
    // Fetch recent interactions
    const fetchRecentInteractions = useCallback(async (limit = 10) => {
        if (!user?.id) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/interactions/users/${user.id}/interactions/?limit=${limit}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setRecentInteractions(data);
            }
        } catch (error) {
            console.error('Error fetching recent interactions:', error);
        }
    }, [user?.id]);
    
    // Enhanced search that uses historical data
    const enhancedSearchQa = useCallback(async (query) => {
        if (!query.trim()) return;
        
        try {
            setIsLoadingSuggestions(true);
            
            // First get basic search results
            await wizard.searchQa(query);
            
            // Then get context-aware suggestions
            await fetchContextAwareSuggestions(
                window.location.pathname,
                'wizard'
            );
            
            // Track the search
            trackSearch(query, wizard.qaItems);
        } finally {
            setIsLoadingSuggestions(false);
        }
    }, [wizard, fetchContextAwareSuggestions, trackSearch]);
    
    // Enhanced feedback submission
    const enhancedSubmitFeedback = useCallback(async (feedbackData) => {
        const result = await wizard.submitFeedback(feedbackData);
        
        if (result.success && feedbackData.qa_item_id) {
            trackFeedback(
                feedbackData.qa_item_id,
                feedbackData.feedback_score,
                feedbackData.feedback_comment
            );
        }
        
        return result;
    }, [wizard, trackFeedback]);
    
    // Get personalized greeting based on time of day and user patterns
    const getPersonalizedGreeting = useCallback(() => {
        const hour = new Date().getHours();
        let greeting;
        
        if (hour < 12) greeting = 'Good morning';
        else if (hour < 18) greeting = 'Good afternoon';
        else greeting = 'Good evening';
        
        // Add personal touch based on learning mode
        const personalizations = {
            basic: `${greeting}, how can I help you today?`,
            intermediate: `${greeting}! Based on your recent activity, I have some suggestions that might be helpful.`,
            advanced: `${greeting}! I've been learning from your interactions and have personalized recommendations ready.`
        };
        
        return personalizations[learningMode] || personalizations.basic;
    }, [learningMode]);
    
    // Get suggestions for the current context
    const getCurrentContextSuggestions = useCallback((currentPage, currentComponent) => {
        // Filter suggestions by context
        return contextAwareSuggestions.filter(suggestion => 
            suggestion.source !== 'error_analysis' || // Always show error-related suggestions
            (currentPage && suggestion.metadata?.page === currentPage) ||
            (currentComponent && suggestion.metadata?.component === currentComponent)
        );
    }, [contextAwareSuggestions]);
    
    // Enhanced category selection that tracks usage
    const enhancedSelectCategory = useCallback((category) => {
        wizard.setSelectedCategory(category);
        trackCategorySelect(category);
        
        // Fetch QA items for this category
        wizard.fetchQaItems({ category_id: category.id });
        
        // Get suggestions for this category
        fetchContextAwareSuggestions(
            window.location.pathname,
            `wizard-category-${category.id}`
        );
    }, [wizard, trackCategorySelect, fetchContextAwareSuggestions]);
    
    // Enhanced QA item selection with time tracking
    const enhancedSelectQaItem = useCallback((item) => {
        wizard.setSelectedQaItem(item);
        
        // Track the view and get cleanup function for time tracking
        const cleanupTimeTracking = trackQaItemView(item);
        
        // Return cleanup function
        return () => {
            cleanupTimeTracking();
            wizard.setSelectedQaItem(null);
        };
    }, [wizard, trackQaItemView]);
    
    // Initialize when component mounts
    useEffect(() => {
        if (user?.id && wizard.isOpen) {
            // Fetch initial data when wizard opens
            fetchUserJourneyPatterns();
            fetchRecentInteractions(5);
            fetchContextAwareSuggestions(
                window.location.pathname,
                'wizard'
            );
        }
    }, [user?.id, wizard.isOpen, fetchUserJourneyPatterns, fetchRecentInteractions, fetchContextAwareSuggestions]);
    
    // Track when wizard opens
    useEffect(() => {
        if (wizard.isOpen) {
            trackWizardOpen();
        }
    }, [wizard.isOpen, trackWizardOpen]);
    
    // Enhanced context value
    const contextValue = {
        ...wizard,
        
        // Enhanced methods
        enhancedSearchQa,
        enhancedSubmitFeedback,
        enhancedSelectCategory,
        enhancedSelectQaItem,
        
        // New properties
        contextAwareSuggestions,
        userJourneyPatterns,
        recentInteractions,
        learningMode,
        isLoadingSuggestions,
        suggestionError,
        
        // New methods
        fetchContextAwareSuggestions,
        fetchUserJourneyPatterns,
        fetchRecentInteractions,
        getPersonalizedGreeting,
        getCurrentContextSuggestions,
        
        // Tracking methods
        trackWizardOpen,
        trackCategorySelect,
        trackQaItemView,
        trackSearch,
        trackFeedback,
        
        // Utility
        isEnhanced: true,
        trackingActive: tracking?.isTracking || false
    };
    
    return (
        <EnhancedWizardContext.Provider value={contextValue}>
            {children}
        </EnhancedWizardContext.Provider>
    );
};

/**
 * Custom hook to use the enhanced wizard context
 */
export function useEnhancedWizard() {
    const context = useContext(EnhancedWizardContext);
    if (context === undefined) {
        throw new Error('useEnhancedWizard must be used within an EnhancedWizardProvider');
    }
    return context;
}

/**
 * Higher-order component to wrap components with enhanced wizard functionality
 */
export function withEnhancedWizard(Component) {
    return function WrappedComponent(props) {
        const enhancedWizard = useEnhancedWizard();
        return <Component {...props} enhancedWizard={enhancedWizard} />;
    };
}