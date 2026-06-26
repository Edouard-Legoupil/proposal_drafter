/**
 * Wizard Context for state management
 *
 * This context provides state management for the wizard utility including:
 * - Modal visibility control
 * - Q&A categories and items
 * - Search functionality
 * - User interactions and feedback
 * - Loading states and error handling
 */

import React, { createContext, useState, useContext, useEffect } from 'react';
import {
    logWizardState,
    validateWizardData,
    WizardPerformanceMonitor,
    createWizardDebugReport
} from '../utils/wizardDebugUtils';

const WizardContext = createContext();

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export const WizardProvider = ({ children }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [categories, setCategories] = useState([]);
    const [qaItems, setQaItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [popularQuestions, setPopularQuestions] = useState([]);
    const [selectedQaItem, setSelectedQaItem] = useState(null);
    const [feedbackScore, setFeedbackScore] = useState(0);
    const [feedbackComment, setFeedbackComment] = useState('');
    const [page, setPage] = useState(1);

    // Debug utilities
    const performanceMonitor = new WizardPerformanceMonitor();
    const [debugMode, setDebugMode] = useState(import.meta.env.DEV);

    // Fetch categories from API
    const fetchCategories = async () => {
        try {
            performanceMonitor.startOperation('fetchCategories');
            setLoading(true);

            if (debugMode) {
                console.log(`🌐 Fetching categories from: ${API_BASE_URL}/wizard/categories`);
            }

            const response = await fetch(`${API_BASE_URL}/wizard/categories`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (debugMode) {
                console.log(`📡 Response status: ${response.status}`);
            }

            if (!response.ok) {
                throw new Error(`Failed to fetch categories: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            const categoriesData = Array.isArray(data) ? data : [];

            if (debugMode) {
                console.log(`📦 Received ${categoriesData.length} categories from API`);
            }

            // Always use mock data for development/when API returns empty data
            if (categoriesData.length === 0 || import.meta.env.DEV) {
                const mockData = getMockCategories();
                setCategories(mockData);
                if (debugMode) {
                    console.log('🎭 Using mock categories:', mockData);
                    validateWizardData(mockData, 'categories');
                }
            } else {
                setCategories(categoriesData);
                if (debugMode) {
                    console.log('📚 Categories loaded from API:', categoriesData);
                    validateWizardData(categoriesData, 'categories');
                }
            }
            setError(null);
        } catch (err) {
            setError('Failed to fetch categories');
            console.error('❌ Error fetching categories:', err);
            // Fallback to mock data if API fails
            const mockData = getMockCategories();
            setCategories(mockData);
            if (debugMode) {
                console.log('🛡️ Fallback to mock categories:', mockData);
            }
        } finally {
            performanceMonitor.endOperation('fetchCategories');
            setLoading(false);
        }
    };

    // Fetch Q&A items with optional filtering
    const fetchQaItems = async (params = {}) => {
        try {
            setLoading(true);
            // Convert params to query string
            const queryString = new URLSearchParams(params).toString();
            const url = `${API_BASE_URL}/wizard/qa${queryString ? '?' + queryString : ''}`;

            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to fetch Q&A items');
            }

            const data = await response.json();
            const qaItemsData = Array.isArray(data.items) ? data.items : [];

            // Always use mock data for development/when API returns empty data
            if (qaItemsData.length === 0 || import.meta.env.DEV) {
                const mockData = getMockQaItems(params.category_id);
                setQaItems(mockData);
                console.log('Using mock QA items:', mockData);
            } else {
                setQaItems(qaItemsData);
                console.log('QA items loaded:', qaItemsData);
            }
            setError(null);
        } catch (err) {
            setError('Failed to fetch Q&A items');
            console.error('Error fetching Q&A items:', err);
            // Fallback to mock data if API fails
            const mockData = getMockQaItems(params.category_id);
            setQaItems(mockData);
            console.log('Using mock QA items:', mockData);
        } finally {
            setLoading(false);
        }
    };

    // Fetch popular questions
    const fetchPopularQuestions = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/wizard/popular`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                const popularData = Array.isArray(data) ? data : [];

                // Always use mock data for development/when API returns empty data
                if (popularData.length === 0 || import.meta.env.DEV) {
                    const mockData = getMockPopularQuestions();
                    setPopularQuestions(mockData);
                    console.log('Using mock popular questions:', mockData);
                } else {
                    setPopularQuestions(popularData);
                    console.log('Popular questions loaded:', popularData);
                }
            } else {
                // Fallback to mock data if API fails
                const mockData = getMockPopularQuestions();
                setPopularQuestions(mockData);
                console.log('Using mock popular questions:', mockData);
            }
        } catch (err) {
            console.error('Error fetching popular questions:', err);
            // Fallback to mock data if API fails
            const mockData = getMockPopularQuestions();
            setPopularQuestions(mockData);
            console.log('Using mock popular questions:', mockData);
        }
    };

    // Search Q&A items
    const searchQa = async (query) => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/wizard/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error('Failed to search Q&A');
            }

            const data = await response.json();
            const searchResults = Array.isArray(data.results) ? data.results : [];

            // Always use mock data for development/when API returns empty results
            if (searchResults.length === 0 || import.meta.env.DEV) {
                const mockData = getMockSearchResults(query);
                setQaItems(mockData);
                console.log('Using mock search results:', mockData);
            } else {
                setQaItems(searchResults);
                console.log('Search results loaded:', searchResults);
            }
            setError(null);
        } catch (err) {
            setError('Failed to search Q&A');
            console.error('Error searching Q&A:', err);
            // Fallback to mock search results
            const mockData = getMockSearchResults(query);
            setQaItems(mockData);
            console.log('Using mock search results:', mockData);
        } finally {
            setLoading(false);
        }
    };

    // Submit feedback on a Q&A item
    const submitFeedback = async (feedbackData) => {
        try {
            const response = await fetch(`${API_BASE_URL}/wizard/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(feedbackData)
            });

            if (!response.ok) {
                throw new Error('Failed to submit feedback');
            }

            return { success: true };
        } catch (err) {
            console.error('Error submitting feedback:', err);
            return { success: false, error: 'Failed to submit feedback' };
        }
    };

    // Track view interaction
    const trackView = async (qaItemId) => {
        try {
            await fetch(`${API_BASE_URL}/wizard/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    qa_item_id: qaItemId,
                    interaction_type: 'view'
                })
            });
        } catch (err) {
            console.error('Error tracking view:', err);
        }
    };

    // Reset state when modal closes
    const resetState = () => {
        setSelectedQaItem(null);
        setFeedbackScore(0);
        setFeedbackComment('');
        setPage(1);
        setSearchQuery('');
        setSelectedCategory(null);
    };

    // Load initial data when modal opens
    useEffect(() => {
        if (isOpen) {
            console.log('🚀 Wizard modal opened, loading data...');
            logWizardState(
                { isOpen, categories, popularQuestions, qaItems, loading, error },
                'Modal Opened'
            );

            performanceMonitor.startOperation('initialDataLoad');

            // Load data sequentially to avoid race conditions
            fetchCategories()
                .then(() => fetchPopularQuestions())
                .then(() => fetchQaItems())
                .catch(err => console.error('❌ Error loading initial data:', err))
                .finally(() => performanceMonitor.endOperation('initialDataLoad'));
        } else {
            console.log('🔚 Wizard modal closed, resetting state...');
            resetState();
        }
    }, [isOpen]);

    const value = {
        isOpen,
        setIsOpen,
        categories,
        qaItems,
        loading,
        error,
        searchQuery,
        setSearchQuery,
        selectedCategory,
        setSelectedCategory,
        popularQuestions,
        selectedQaItem,
        setSelectedQaItem,
        feedbackScore,
        setFeedbackScore,
        feedbackComment,
        setFeedbackComment,
        page,
        setPage,
        fetchQaItems,
        searchQa,
        submitFeedback,
        trackView,
        // Debug functions
        debugMode,
        setDebugMode,
        logWizardState: (source) => logWizardState(
            { isOpen, categories, popularQuestions, qaItems, loading, error },
            source || 'Manual'
        ),
        getPerformanceMetrics: performanceMonitor.getMetrics.bind(performanceMonitor),
        logPerformanceMetrics: performanceMonitor.logMetrics.bind(performanceMonitor),
        createDebugReport: () => createWizardDebugReport(
            { isOpen, categories, popularQuestions, qaItems, loading, error }
        )
    };

    return (
        <WizardContext.Provider value={value}>
            {children}
        </WizardContext.Provider>
    );
};

// Mock data functions for fallback when API fails
export const getMockCategories = () => {
    return [
        {
            id: 1,
            name: 'General',
            description: 'General questions about the Proposal Drafter application',
            question_count: 5
        },
        {
            id: 2,
            name: 'Getting Started',
            description: 'Questions about getting started with the application',
            question_count: 4
        },
        {
            id: 3,
            name: 'Proposal Creation',
            description: 'Questions about creating and managing proposals',
            question_count: 5
        },
        {
            id: 4,
            name: 'Knowledge Cards',
            description: 'Questions about knowledge cards and the knowledge base',
            question_count: 4
        },
        {
            id: 5,
            name: 'Review Process',
            description: 'Questions about the proposal review and approval process',
            question_count: 4
        }
    ];
};

export const getMockPopularQuestions = () => {
    return [
        {
            id: 1,
            question: 'What is the Proposal Drafter?',
            category: 'General',
            view_count: 150
        },
        {
            id: 2,
            question: 'How do I create a new proposal?',
            category: 'Proposal Creation',
            view_count: 120
        },
        {
            id: 3,
            question: 'What are knowledge cards?',
            category: 'Knowledge Cards',
            view_count: 90
        },
        {
            id: 4,
            question: 'How does the review process work?',
            category: 'Review Process',
            view_count: 80
        },
        {
            id: 5,
            question: 'Who can use the Proposal Drafter?',
            category: 'General',
            view_count: 70
        }
    ];
};

export const getMockQaItems = (categoryId) => {
    const allMockItems = [
        // General category
        {
            id: 1,
            question: 'What is the Proposal Drafter?',
            answer: 'The Proposal Drafter is an AI-powered tool designed to help UN agencies and NGOs create high-quality project proposals efficiently. It uses artificial intelligence to generate proposal content based on your organization\'s knowledge base and best practices.',
            category_id: 1,
            category: { id: 1, name: 'General' }
        },
        {
            id: 2,
            question: 'Who can use the Proposal Drafter?',
            answer: 'The Proposal Drafter is available to authorized staff from UN agencies and partner NGOs. Access is controlled through our role-based access control system.',
            category_id: 1,
            category: { id: 1, name: 'General' }
        },
        // Proposal Creation category
        {
            id: 3,
            question: 'How do I create a new proposal?',
            answer: '1. Log in to the Proposal Drafter, 2. Navigate to the Dashboard, 3. Click the \'New Proposal\' button, 4. Select the donor organization, outcome, and field context, 5. Provide a brief project description, 6. Click \'Generate Proposal\' to let the AI create the initial draft.',
            category_id: 3,
            category: { id: 3, name: 'Proposal Creation' }
        },
        {
            id: 4,
            question: 'Can I edit the AI-generated proposal?',
            answer: 'Yes, you can edit any part of the AI-generated proposal. The system treats AI-generated content as a starting point that you can modify, expand, or replace as needed.',
            category_id: 3,
            category: { id: 3, name: 'Proposal Creation' }
        },
        // Knowledge Cards category
        {
            id: 5,
            question: 'What are knowledge cards?',
            answer: 'Knowledge cards are reusable snippets of validated information that form the foundation of the AI\'s understanding. They contain organization-specific knowledge about donors, outcomes, field contexts, and best practices.',
            category_id: 4,
            category: { id: 4, name: 'Knowledge Cards' }
        },
        // Review Process category
        {
            id: 6,
            question: 'How does the review process work?',
            answer: 'The review process involves: 1) Submitting your proposal for review, 2) Reviewers providing feedback and ratings, 3) Addressing reviewer comments, 4) Resubmitting for final approval, 5) Final submission to donors.',
            category_id: 5,
            category: { id: 5, name: 'Review Process' }
        }
    ];

    if (categoryId) {
        return allMockItems.filter(item => item.category_id === categoryId);
    }
    return allMockItems;
};

export const getMockSearchResults = (query) => {
    const allItems = getMockQaItems();

    if (!query || query.trim() === '') {
        return allItems;
    }

    const searchTerm = query.toLowerCase();
    return allItems.filter(item =>
        item.question.toLowerCase().includes(searchTerm) ||
        item.answer.toLowerCase().includes(searchTerm)
    );
};

export const useWizard = () => {
    const context = useContext(WizardContext);
    if (!context) {
        throw new Error('useWizard must be used within a WizardProvider');
    }
    return context;
};
