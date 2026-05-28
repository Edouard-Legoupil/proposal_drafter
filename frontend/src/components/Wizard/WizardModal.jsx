/**
 * Wizard Modal Component
 *
 * Main modal interface for the wizard utility that provides:
 * - Search functionality
 * - Category browsing
 * - Q&A display
 * - Feedback system
 * - Popular questions
 */

import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    Button, TextField, CircularProgress,
    List, ListItem, ListItemText, Divider,
    Tabs, Tab, Box, Typography, Rating,
    Pagination, Chip, IconButton
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

const WizardModal = () => {
    const {
        isOpen, setIsOpen,
        categories, qaItems, loading, error,
        searchQuery, setSearchQuery,
        selectedCategory, setSelectedCategory,
        popularQuestions, fetchQaItems, searchQa,
        submitFeedback, trackView,
        selectedQaItem, setSelectedQaItem,
        feedbackScore, setFeedbackScore,
        feedbackComment, setFeedbackComment,
        page, setPage
    } = useWizard();

    const [activeTab, setActiveTab] = useState(0);

    // Handle category selection
    const handleCategorySelect = (category) => {
        setSelectedCategory(category);
        setSelectedQaItem(null);
        setPage(1);
        fetchQaItems({ category_id: category.id, limit: 10, offset: 0 });
    };

    // Handle search
    const handleSearch = () => {
        if (searchQuery.trim()) {
            searchQa(searchQuery);
            setActiveTab(1);
            setSelectedQaItem(null);
        }
    };

    // Handle QA item selection
    const handleQaItemSelect = (item) => {
        setSelectedQaItem(item);
        trackView(item.id);
    };

    // Handle feedback submission
    const handleFeedbackSubmit = async () => {
        if (selectedQaItem && feedbackScore > 0) {
            const result = await submitFeedback({
                qa_item_id: selectedQaItem.id,
                feedback_score: feedbackScore,
                feedback_comment: feedbackComment
            });

            if (result.success) {
                setFeedbackScore(0);
                setFeedbackComment('');
            }
        }
    };

    // Handle page change
    const handlePageChange = (event, value) => {
        setPage(value);
        const offset = (value - 1) * 10;
        if (selectedCategory) {
            fetchQaItems({ category_id: selectedCategory.id, limit: 10, offset });
        } else {
            fetchQaItems({ limit: 10, offset });
        }
    };

    // Reset when going back to question list
    const handleBackToQuestions = () => {
        setSelectedQaItem(null);
        setFeedbackScore(0);
        setFeedbackComment('');
    };

    return (
        <Dialog
            open={isOpen}
            onClose={() => setIsOpen(false)}
            maxWidth="md"
            fullWidth
            scroll="paper"
            aria-labelledby="wizard-modal-title"
        >
            <DialogTitle id="wizard-modal-title">
                <Typography variant="h5" component="div">
                    Proposal Drafter Help
                </Typography>
            </DialogTitle>

            <DialogContent dividers>
                {!selectedQaItem ? (
                    <MainView
                        activeTab={activeTab}
                        setActiveTab={setActiveTab}
                        categories={categories}
                        qaItems={qaItems}
                        loading={loading}
                        error={error}
                        searchQuery={searchQuery}
                        setSearchQuery={setSearchQuery}
                        selectedCategory={selectedCategory}
                        popularQuestions={popularQuestions}
                        handleCategorySelect={handleCategorySelect}
                        handleSearch={handleSearch}
                        handleQaItemSelect={handleQaItemSelect}
                        handlePageChange={handlePageChange}
                        page={page}
                    />
                ) : (
                    <QADetailView
                        item={selectedQaItem}
                        feedbackScore={feedbackScore}
                        setFeedbackScore={setFeedbackScore}
                        feedbackComment={feedbackComment}
                        setFeedbackComment={setFeedbackComment}
                        handleFeedbackSubmit={handleFeedbackSubmit}
                        handleBackToQuestions={handleBackToQuestions}
                    />
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={() => setIsOpen(false)} color="primary" data-testid="wizard-close-button">
                    Close
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Main view with categories, search, and question list
const MainView = ({
    activeTab, setActiveTab,
    categories, qaItems, loading, error,
    searchQuery, setSearchQuery,
    selectedCategory, popularQuestions,
    handleCategorySelect, handleSearch,
    handleQaItemSelect, handlePageChange, page
}) => {
    return (
        <>
            {/* Search Bar */}
            <Box sx={{ display: 'flex', mb: 3, gap: 2 }}>
                <TextField
                    fullWidth
                    variant="outlined"
                    size="small"
                    placeholder="Search help topics..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    InputProps={{
                        endAdornment: (
                            <IconButton onClick={handleSearch} edge="end" aria-label="Search" data-testid="wizard-search-button">
                                <SearchIcon />
                            </IconButton>
                        )
                    }}
                    aria-label="Search help topics"
                />
            </Box>

            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} aria-label="Wizard tabs" data-testid="wizard-tabs">
                    <Tab label="Categories" data-testid="categories-tab" />
                    <Tab label="Popular Questions" data-testid="popular-questions-tab" />
                </Tabs>
            </Box>

            {/* Content based on active tab */}
            {activeTab === 0 ? (
                <CategoriesView
                    categories={categories}
                    selectedCategory={selectedCategory}
                    handleCategorySelect={handleCategorySelect}
                    qaItems={qaItems}
                    loading={loading}
                    error={error}
                    handleQaItemSelect={handleQaItemSelect}
                    handlePageChange={handlePageChange}
                    page={page}
                />
            ) : (
                <PopularQuestionsView
                    popularQuestions={popularQuestions}
                    handleQaItemSelect={handleQaItemSelect}
                />
            )}
        </>
    );
};

// Categories view with category list and questions
const CategoriesView = ({
    categories, selectedCategory, handleCategorySelect,
    qaItems, loading, error, handleQaItemSelect,
    handlePageChange, page
}) => {
    return (
        <>
            {/* Categories List */}
            <Typography variant="subtitle1" gutterBottom>
                Browse by Category
            </Typography>
            <List dense>
                {categories.map((category) => (
                    <ListItem
                        key={category.id}
                        button
                        onClick={() => handleCategorySelect(category)}
                        selected={selectedCategory?.id === category.id}
                        aria-label={`Select category ${category.name}`}
                        data-testid={`category-item-${category.id}`}
                    >
                        <ListItemText
                            primary={category.name}
                            secondary={category.description || `${category.question_count || 0} questions`}
                        />
                        <Chip label={category.question_count || 0} size="small" />
                    </ListItem>
                ))}
            </List>

            {/* Q&A Items for selected category */}
            {selectedCategory && (
                <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" gutterBottom>
                        Questions in {selectedCategory.name}
                    </Typography>

                    {loading ? (
                        <Box display="flex" justifyContent="center" my={4}>
                            <CircularProgress aria-label="Loading questions" />
                        </Box>
                    ) : error ? (
                        <Typography color="error" aria-live="polite">{error}</Typography>
                    ) : (
                        <>
                            <List>
                                {qaItems.map((item) => (
                                    <ListItem
                                        key={item.id}
                                        button
                                        onClick={() => handleQaItemSelect(item)}
                                        aria-label={`View answer to ${item.question}`}
                                        data-testid={`qa-item-${item.id}`}
                                    >
                                        <ListItemText
                                            primary={item.question}
                                            secondary={
                                                <Typography variant="body2" color="text.secondary">
                                                    {item.answer.substring(0, 100)}{item.answer.length > 100 ? '...' : ''}
                                                </Typography>
                                            }
                                        />
                                    </ListItem>
                                ))}
                            </List>

                            {qaItems.length > 0 && (
                                <Box display="flex" justifyContent="center" mt={2}>
                                    <Pagination
                                        count={Math.ceil(qaItems.length / 10)}
                                        page={page}
                                        onChange={handlePageChange}
                                        color="primary"
                                        aria-label="Question pagination"
                                    />
                                </Box>
                            )}
                        </>
                    )}
                </>
            )}
        </>
    );
};

// Popular questions view
const PopularQuestionsView = ({ popularQuestions, handleQaItemSelect }) => {
    return (
        <>
            <Typography variant="subtitle1" gutterBottom>
                Most Popular Questions
            </Typography>
            <List>
                {popularQuestions.map((item, index) => (
                    <ListItem
                        key={item.id}
                        button
                        onClick={() => handleQaItemSelect(item)}
                        aria-label={`View popular question ${index + 1}: ${item.question}`}
                        data-testid={`popular-qa-item-${item.id}`}
                    >
                        <ListItemText
                            primary={`${index + 1}. ${item.question}`}
                            secondary={
                                <>
                                    <Chip label={item.category} size="small" sx={{ mr: 1 }} />
                                    <Typography variant="body2" color="text.secondary">
                                        Viewed {item.view_count} times
                                    </Typography>
                                </>
                            }
                        />
                    </ListItem>
                ))}
            </List>
        </>
    );
};

// Q&A detail view with full answer and feedback
const QADetailView = ({
    item, feedbackScore, setFeedbackScore,
    feedbackComment, setFeedbackComment,
    handleFeedbackSubmit, handleBackToQuestions
}) => {
    return (
        <>
            {/* Back button */}
            <Box sx={{ mb: 2 }}>
                <Button
                    variant="outlined"
                    onClick={handleBackToQuestions}
                    startIcon={<ArrowBackIcon />}
                    aria-label="Back to questions"
                    data-testid="wizard-back-button"
                >
                    Back to Questions
                </Button>
            </Box>

            {/* Question */}
            <Typography variant="h6" gutterBottom>
                {item.question}
            </Typography>

            {/* Category tag */}
            <Box sx={{ mb: 2 }}>
                <Chip
                    label={item.category?.name || 'General'}
                    size="small"
                    sx={{ mr: 1 }}
                    aria-label={`Category: ${item.category?.name || 'General'}`}
                />
            </Box>

            {/* Answer */}
            <Typography variant="body1" paragraph>
                {item.answer}
            </Typography>

            <Divider sx={{ my: 3 }} />

            {/* Feedback section */}
            <Typography variant="subtitle2" gutterBottom>
                Was this helpful?
            </Typography>

            {/* Rating */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Rating
                    name="feedback-rating"
                    value={feedbackScore}
                    onChange={(e, newValue) => setFeedbackScore(newValue)}
                    precision={1}
                    aria-label="Rate this answer"
                />
                <Typography variant="body2" sx={{ ml: 1 }}>
                    {feedbackScore || 'Rate this answer'}
                </Typography>
            </Box>

            {/* Comments */}
            <TextField
                fullWidth
                multiline
                minRows={3}
                variant="outlined"
                size="small"
                placeholder="Additional comments (optional)"
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                sx={{ mb: 2 }}
                aria-label="Additional feedback comments"
            />

            {/* Submit button */}
            <Button
                variant="contained"
                color="primary"
                onClick={handleFeedbackSubmit}
                disabled={feedbackScore === 0}
                aria-label="Submit feedback"
                data-testid="wizard-feedback-submit-button"
            >
                Submit Feedback
            </Button>
        </>
    );
};

export default WizardModal;
