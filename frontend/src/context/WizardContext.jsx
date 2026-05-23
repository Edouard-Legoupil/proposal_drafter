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
import axios from 'axios';

const WizardContext = createContext();

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
    
    // Fetch categories from API
    const fetchCategories = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/wizard/categories');
            setCategories(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch categories');
            console.error('Error fetching categories:', err);
        } finally {
            setLoading(false);
        }
    };
    
    // Fetch Q&A items with optional filtering
    const fetchQaItems = async (params = {}) => {
        try {
            setLoading(true);
            const response = await axios.get('/api/wizard/qa', { params });
            setQaItems(response.data.items);
            setError(null);
        } catch (err) {
            setError('Failed to fetch Q&A items');
            console.error('Error fetching Q&A items:', err);
        } finally {
            setLoading(false);
        }
    };
    
    // Fetch popular questions
    const fetchPopularQuestions = async () => {
        try {
            const response = await axios.get('/api/wizard/popular');
            setPopularQuestions(response.data);
        } catch (err) {
            console.error('Error fetching popular questions:', err);
        }
    };
    
    // Search Q&A items
    const searchQa = async (query) => {
        try {
            setLoading(true);
            const response = await axios.post('/api/wizard/search', { query });
            setQaItems(response.data.results);
            setError(null);
        } catch (err) {
            setError('Failed to search Q&A');
            console.error('Error searching Q&A:', err);
        } finally {
            setLoading(false);
        }
    };
    
    // Submit feedback on a Q&A item
    const submitFeedback = async (feedbackData) => {
        try {
            await axios.post('/api/wizard/feedback', feedbackData);
            return { success: true };
        } catch (err) {
            console.error('Error submitting feedback:', err);
            return { success: false, error: 'Failed to submit feedback' };
        }
    };
    
    // Track view interaction
    const trackView = async (qaItemId) => {
        try {
            await axios.post('/api/wizard/feedback', {
                qa_item_id: qaItemId,
                interaction_type: 'view'
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
            fetchCategories();
            fetchPopularQuestions();
            fetchQaItems();
        } else {
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
        trackView
    };
    
    return (
        <WizardContext.Provider value={value}>
            {children}
        </WizardContext.Provider>
    );
};

export const useWizard = () => {
    const context = useContext(WizardContext);
    if (!context) {
        throw new Error('useWizard must be used within a WizardProvider');
    }
    return context;
};