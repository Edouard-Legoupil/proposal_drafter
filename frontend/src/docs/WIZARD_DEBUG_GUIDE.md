# Wizard Help Modal Debugging Guide

## Overview

This guide provides comprehensive information about debugging the Wizard Help Modal system in the Proposal Drafter application. The system includes robust debugging capabilities to help identify and resolve issues with the help modal functionality.

## Debugging Components

### 1. Wizard Debug Utilities (`wizardDebugUtils.js`)

A comprehensive set of debugging utilities located in `frontend/src/utils/wizardDebugUtils.js`:

#### Key Functions:

- **`logWizardState(state, source)`**: Logs the current wizard state in a structured format
- **`validateWizardData(data, dataType)`**: Validates the structure of wizard data
- **`WizardPerformanceMonitor`**: Tracks and measures performance of wizard operations
- **`generateTestData`**: Provides test data for various scenarios
- **`createWizardDebugReport(state)`**: Generates a comprehensive debug report

### 2. Enhanced Wizard Context

The `WizardContext.jsx` has been enhanced with debugging capabilities:

#### Debug Features:

- **Debug Mode**: Automatically enabled in development environment
- **Performance Monitoring**: Tracks loading times for all operations
- **Detailed Logging**: Comprehensive console logging for all API calls
- **Automatic Fallback**: Uses mock data when API calls fail or return empty data
- **Data Validation**: Validates all incoming data structures

### 3. Wizard Debug Component

A visual debug panel located in `frontend/src/components/Wizard/WizardDebug.jsx`:

#### Features:

- **State Overview**: Shows current counts for categories, popular questions, and QA items
- **Performance Metrics**: Displays operation timings
- **Debug Controls**:
  - Toggle debug mode on/off
  - Manual data loading test
  - State logging
  - Performance metrics display
  - Comprehensive debug report generation
  - Empty data testing

## Debugging Workflow

### Step 1: Enable Debug Mode

```javascript
// Debug mode is automatically enabled in development
// You can manually toggle it using the debug panel
```

### Step 2: Open the Wizard Modal

Click the "Help" button in the navigation to open the wizard modal. This triggers:
- Automatic data loading from API endpoints
- Fallback to mock data if APIs fail
- Comprehensive logging to console

### Step 3: Monitor Console Output

The system logs detailed information to the console:

```
🚀 Wizard modal opened, loading data...
🌐 Fetching categories from: /api/wizard/categories
📡 Response status: 200
📦 Received 0 categories from API
🎭 Using mock categories: [Array of mock categories]
✅ Valid categories data [Array of validated categories]
```

### Step 4: Use the Debug Panel

The debug panel provides visual debugging tools:

- **Current State**: Shows real-time counts and status
- **Performance Metrics**: Displays operation timings
- **Controls**: Buttons to trigger various debug actions

### Step 5: Generate Debug Reports

Use the "Debug Report" button to generate a comprehensive report containing:
- Timestamp
- Environment information
- Backend URL
- Current state snapshot
- Data quality validation results

## Common Issues and Solutions

### Issue: Empty Categories/Popular Questions

**Symptoms**: "Browse by Category" and "Most Popular Questions" sections are empty

**Debug Steps**:
1. Check console for API response status
2. Verify if mock data is being used (look for "Using mock" messages)
3. Use debug panel to test data loading
4. Check network tab for failed API requests

**Solutions**:
- Ensure backend API endpoints are working
- Verify database connection
- Check CORS settings
- Use mock data for development

### Issue: Data Not Loading

**Symptoms**: Loading spinner continues indefinitely

**Debug Steps**:
1. Check console for error messages
2. Verify network connectivity
3. Test API endpoints manually
4. Check debug panel for loading state

**Solutions**:
- Verify backend server is running
- Check API endpoint URLs
- Ensure proper authentication/credentials
- Test with mock data

### Issue: Invalid Data Structure

**Symptoms**: Console warnings about missing fields

**Debug Steps**:
1. Check console for validation warnings
2. Use `validateWizardData()` to test data structures
3. Examine API response payloads

**Solutions**:
- Ensure API returns correct data structure
- Update mock data to match expected structure
- Fix data transformation logic

## Advanced Debugging Techniques

### Performance Monitoring

```javascript
const monitor = new WizardPerformanceMonitor();
monitor.startOperation('customOperation');
// ... perform operation ...
monitor.endOperation('customOperation');
monitor.logMetrics();
```

### Manual Data Validation

```javascript
import { validateWizardData } from '../utils/wizardDebugUtils';

const isValid = validateWizardData(yourData, 'categories');
if (!isValid) {
    // Handle invalid data
}
```

### Testing Empty Data Scenarios

```javascript
import { generateTestData } from '../utils/wizardDebugUtils';

// Test with empty data
const emptyCategories = generateTestData.emptyCategories;
const emptyPopular = generateTestData.emptyPopularQuestions;
```

## Debugging API Endpoints

The wizard system uses the following API endpoints:

- **GET `/api/wizard/categories`**: Fetch Q&A categories
- **GET `/api/wizard/popular`**: Fetch popular questions
- **GET `/api/wizard/qa`**: Fetch Q&A items with filtering
- **POST `/api/wizard/search`**: Search Q&A content

### Testing Endpoints Manually

```bash
# Test categories endpoint
curl -X GET http://localhost:8502/api/wizard/categories

# Test popular questions endpoint
curl -X GET http://localhost:8502/api/wizard/popular

# Test Q&A items endpoint
curl -X GET http://localhost:8502/api/wizard/qa

# Test search endpoint
curl -X POST http://localhost:8502/api/wizard/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## Mock Data Structure

### Categories
```javascript
[{
    id: 1,
    name: 'General',
    description: 'General questions about the Proposal Drafter application',
    question_count: 5
}]
```

### Popular Questions
```javascript
[{
    id: 1,
    question: 'What is the Proposal Drafter?',
    category: 'General',
    view_count: 150
}]
```

### Q&A Items
```javascript
[{
    id: 1,
    question: 'What is the Proposal Drafter?',
    answer: 'The Proposal Drafter is an AI-powered tool...',
    category_id: 1,
    category: { id: 1, name: 'General' }
}]
```

## Development vs Production

### Development Mode
- Debug mode automatically enabled
- Mock data used by default
- Comprehensive console logging
- Performance monitoring active

### Production Mode
- Debug mode disabled
- Real API data used
- Minimal logging
- Performance monitoring disabled

## Troubleshooting Checklist

1. [ ] Verify backend API endpoints are accessible
2. [ ] Check database connection and data
3. [ ] Test API endpoints manually
4. [ ] Enable debug mode and check console output
5. [ ] Use debug panel to test data loading
6. [ ] Validate data structures with `validateWizardData()`
7. [ ] Generate debug report for comprehensive analysis
8. [ ] Check network tab for failed requests
9. [ ] Verify CORS and authentication settings
10. [ ] Test with mock data to isolate issues

## Best Practices

1. **Use Debug Mode**: Always enable debug mode during development
2. **Monitor Console**: Pay attention to console output for warnings and errors
3. **Test Regularly**: Use the debug panel to test functionality regularly
4. **Validate Data**: Use data validation functions to catch structure issues early
5. **Performance Monitoring**: Track performance metrics to identify bottlenecks
6. **Generate Reports**: Create debug reports when issues occur for easier analysis

## Support

For additional help with debugging the wizard system:

1. Check the comprehensive test suite in `WizardContext.test.jsx` and `wizardDebugUtils.test.js`
2. Review the source code comments and documentation
3. Examine the debug console output for detailed information
4. Use the visual debug panel for interactive debugging

The wizard system is designed with resilience and debuggability in mind, providing multiple layers of fallback and comprehensive debugging tools to ensure smooth operation.
