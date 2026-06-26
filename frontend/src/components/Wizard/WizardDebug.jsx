import React, { useEffect } from 'react';
import { useWizard } from '../../context/WizardContext';
import { Button, Typography, Box, Chip, List, ListItem, ListItemText, Switch, FormControlLabel, Divider, Paper } from '@mui/material';
import { generateTestData } from '../../utils/wizardDebugUtils';

const WizardDebug = () => {
    const {
        isOpen, setIsOpen,
        categories,
        popularQuestions,
        qaItems,
        loading,
        error,
        debugMode, setDebugMode,
        logWizardState,
        getPerformanceMetrics,
        logPerformanceMetrics,
        createDebugReport,
        fetchCategories,
        fetchPopularQuestions,
        fetchQaItems
    } = useWizard();

    useEffect(() => {
        if (isOpen) {
            console.log('Debug: Modal opened, current state:', {
                categories: categories.length,
                popularQuestions: popularQuestions.length,
                qaItems: qaItems.length,
                loading,
                error
            });
        }
    }, [isOpen, categories, popularQuestions, qaItems, loading, error]);

    const testDataLoading = () => {
        console.log('🧪 Testing data loading...');
        // Note: Performance monitoring is handled by the context automatically
        // during the fetch operations
        fetchCategories()
            .then(() => fetchPopularQuestions())
            .then(() => fetchQaItems())
            .catch(err => console.error('❌ Test failed:', err));
    };

    const handleDebugToggle = () => {
        const newDebugMode = !debugMode;
        setDebugMode(newDebugMode);
        console.log(`🔧 Debug mode ${newDebugMode ? 'enabled' : 'disabled'}`);
    };

    const logCurrentState = () => {
        logWizardState('Manual Debug');
    };

    const showPerformanceMetrics = () => {
        logPerformanceMetrics();
    };

    const generateDebugReport = () => {
        createDebugReport();
    };

    const testEmptyData = () => {
        console.log('🧪 Testing empty data scenario...');
        // This would require modifying the context temporarily
        console.log('Empty categories:', generateTestData.emptyCategories);
        console.log('Empty popular questions:', generateTestData.emptyPopularQuestions);
        console.log('Empty QA items:', generateTestData.emptyQaItems);
    };

    return (
        <Box sx={{ p: 2, border: '1px dashed #ccc', m: 2 }}>
            <Typography variant="h6" gutterBottom>
                Wizard Debug Panel
            </Typography>

            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                    variant="contained"
                    color="secondary"
                    onClick={() => setIsOpen(true)}
                >
                    Open Wizard
                </Button>
                <Button
                    variant="outlined"
                    onClick={testDataLoading}
                >
                    Test Data Loading
                </Button>
                <Button
                    variant="outlined"
                    color="info"
                    onClick={logCurrentState}
                >
                    Log State
                </Button>
                <Button
                    variant="outlined"
                    color="success"
                    onClick={showPerformanceMetrics}
                >
                    Show Metrics
                </Button>
                <Button
                    variant="outlined"
                    color="warning"
                    onClick={generateDebugReport}
                >
                    Debug Report
                </Button>
                <Button
                    variant="outlined"
                    color="error"
                    onClick={testEmptyData}
                >
                    Test Empty Data
                </Button>
            </Box>

            <Box sx={{ mb: 2 }}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={debugMode}
                            onChange={handleDebugToggle}
                            color="primary"
                        />
                    }
                    label="Debug Mode"
                />
            </Box>

            <Typography variant="subtitle2" gutterBottom>
                Current State:
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <Chip label={`Categories: ${categories.length}`} color={categories.length > 0 ? 'success' : 'error'} />
                <Chip label={`Popular: ${popularQuestions.length}`} color={popularQuestions.length > 0 ? 'success' : 'error'} />
                <Chip label={`QA Items: ${qaItems.length}`} color={qaItems.length > 0 ? 'success' : 'error'} />
                <Chip label={`Loading: ${loading}`} color={loading ? 'info' : 'default'} />
                <Chip label={`Debug: ${debugMode ? 'ON' : 'OFF'}`} color={debugMode ? 'success' : 'default'} />
                {error && <Chip label={`Error: ${error}`} color="error" />}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" gutterBottom>
                Performance Metrics:
            </Typography>
            <Paper sx={{ p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
                <pre style={{ margin: 0, fontSize: '0.8em', overflowX: 'auto' }}>
                    {JSON.stringify(getPerformanceMetrics(), null, 2)}
                </pre>
            </Paper>

            {categories.length > 0 && (
                <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Categories Preview:
                    </Typography>
                    <List dense>
                        {categories.slice(0, 3).map((category) => (
                            <ListItem key={category.id}>
                                <ListItemText
                                    primary={category.name}
                                    secondary={category.description || `${category.question_count || 0} questions`}
                                />
                                <Chip label={category.question_count || 0} size="small" />
                            </ListItem>
                        ))}
                    </List>
                </Box>
            )}

            {popularQuestions.length > 0 && (
                <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Popular Questions Preview:
                    </Typography>
                    <List dense>
                        {popularQuestions.slice(0, 3).map((item, index) => (
                            <ListItem key={item.id}>
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
                </Box>
            )}
        </Box>
    );
};

export default WizardDebug;
