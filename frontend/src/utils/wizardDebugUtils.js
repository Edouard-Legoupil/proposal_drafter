/**
 * Wizard Debug Utilities
 *
 * Comprehensive debugging utilities for the Wizard Context and Help Modal
 */

/**
 * Log wizard state to console in a structured format
 * @param {Object} state - Current wizard state
 * @param {string} source - Source of the log call
 */
export const logWizardState = (state, source = 'Unknown') => {
    console.groupCollapsed(`🔍 Wizard State - ${source}`);
    console.log('📊 State Overview:', {
        isOpen: state.isOpen,
        loading: state.loading,
        error: state.error,
        categoriesCount: state.categories?.length || 0,
        popularQuestionsCount: state.popularQuestions?.length || 0,
        qaItemsCount: state.qaItems?.length || 0,
        selectedCategory: state.selectedCategory?.name || 'None',
        searchQuery: state.searchQuery || 'None'
    });

    if (state.categories?.length > 0) {
        console.log('📚 Categories:', state.categories);
    }

    if (state.popularQuestions?.length > 0) {
        console.log('🔥 Popular Questions:', state.popularQuestions);
    }

    if (state.qaItems?.length > 0) {
        console.log('💬 Q&A Items:', state.qaItems);
    }

    if (state.error) {
        console.error('❌ Error:', state.error);
    }

    console.groupEnd();
};

/**
 * Validate wizard data structure
 * @param {Object} data - Data to validate
 * @param {string} dataType - Type of data being validated
 * @returns {boolean} - True if data is valid
 */
export const validateWizardData = (data, dataType) => {
    if (!data || !Array.isArray(data)) {
        console.warn(`⚠️ Invalid ${dataType}: Not an array`, data);
        return false;
    }

    if (data.length === 0) {
        console.warn(`⚠️ Empty ${dataType} array`);
        return false;
    }

    // Validate structure based on data type
    switch (dataType) {
        case 'categories': {
            const requiredCategoryFields = ['id', 'name', 'description', 'question_count'];
            for (const item of data) {
                const missingFields = requiredCategoryFields.filter(field => !(field in item));
                if (missingFields.length > 0) {
                    console.warn(`⚠️ Category missing fields:`, missingFields, item);
                    return false;
                }
            }
            break;
        }

        case 'popularQuestions': {
            const requiredPopularFields = ['id', 'question', 'category', 'view_count'];
            for (const item of data) {
                const missingFields = requiredPopularFields.filter(field => !(field in item));
                if (missingFields.length > 0) {
                    console.warn(`⚠️ Popular question missing fields:`, missingFields, item);
                    return false;
                }
            }
            break;
        }

        case 'qaItems': {
            const requiredQaFields = ['id', 'question', 'answer', 'category_id', 'category'];
            for (const item of data) {
                const missingFields = requiredQaFields.filter(field => !(field in item));
                if (missingFields.length > 0) {
                    console.warn(`⚠️ QA item missing fields:`, missingFields, item);
                    return false;
                }
            }
            break;
        }
    }

    console.log(`✅ Valid ${dataType} data`, data);
    return true;
};

/**
 * Simulate API failure for testing fallback mechanisms
 * @param {boolean} shouldFail - Whether to simulate failure
 * @param {Function} originalFunction - Original API function
 * @returns {Function} - Wrapped function that may fail
 */
export const simulateApiFailure = (shouldFail, originalFunction) => {
    return async (...args) => {
        if (shouldFail) {
            console.warn('🚨 Simulating API failure for testing');
            throw new Error('Simulated API failure');
        }
        return originalFunction(...args);
    };
};

/**
 * Create performance metrics for wizard operations
 */
export class WizardPerformanceMonitor {
    constructor() {
        this.metrics = {};
    }

    startOperation(operationName) {
        console.time(`🕒 ${operationName}`);
        this.metrics[operationName] = {
            startTime: performance.now(),
            endTime: null,
            duration: null
        };
    }

    endOperation(operationName) {
        if (this.metrics[operationName]) {
            this.metrics[operationName].endTime = performance.now();
            this.metrics[operationName].duration = this.metrics[operationName].endTime - this.metrics[operationName].startTime;
            console.timeEnd(`🕒 ${operationName}`);
            console.log(`⏱️ ${operationName} took ${this.metrics[operationName].duration.toFixed(2)}ms`);
        }
    }

    getMetrics() {
        return this.metrics || {};
    }

    logMetrics() {
        if (!this.metrics) {
            console.warn('📊 No performance metrics available');
            return;
        }
        console.group('📊 Performance Metrics');
        Object.entries(this.metrics).forEach(([name, metric]) => {
            console.log(`${name}: ${metric.duration?.toFixed(2) || 0}ms`);
        });
        console.groupEnd();
    }
}

/**
 * Generate test data for specific scenarios
 */
export const generateTestData = {
    emptyCategories: [],
    emptyPopularQuestions: [],
    emptyQaItems: [],

    singleCategory: () => [{
        id: 999,
        name: 'Test Category',
        description: 'Test description',
        question_count: 1
    }],

    singlePopularQuestion: () => [{
        id: 999,
        question: 'Test Question',
        category: 'Test',
        view_count: 1
    }],

    singleQaItem: () => [{
        id: 999,
        question: 'Test Question',
        answer: 'Test Answer',
        category_id: 999,
        category: { id: 999, name: 'Test' }
    }]
};

/**
 * Create a debug report for the wizard system
 */
export const createWizardDebugReport = (state) => {
    const report = {
        timestamp: new Date().toISOString(),
        environment: import.meta.env.MODE,
        backendUrl: import.meta.env.VITE_BACKEND_URL || '/api',
        state: {
            isOpen: state.isOpen,
            loading: state.loading,
            error: state.error,
            categories: state.categories?.length || 0,
            popularQuestions: state.popularQuestions?.length || 0,
            qaItems: state.qaItems?.length || 0,
            selectedCategory: state.selectedCategory?.name || 'None',
            searchQuery: state.searchQuery || 'None'
        },
        dataQuality: {
            categoriesValid: validateWizardData(state.categories, 'categories'),
            popularQuestionsValid: validateWizardData(state.popularQuestions, 'popularQuestions'),
            qaItemsValid: validateWizardData(state.qaItems, 'qaItems')
        }
    };

    console.log('📋 Wizard Debug Report:', report);
    return report;
};
