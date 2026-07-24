import { describe, test, expect, beforeEach } from 'vitest';
import {
  logWizardState,
  validateWizardData,
  WizardPerformanceMonitor,
  generateTestData,
  createWizardDebugReport
} from './wizardDebugUtils';

describe('Wizard Debug Utilities', () => {
  // Mock console methods for testing
  const originalConsole = {...console};
  let consoleOutput = [];

  beforeEach(() => {
    consoleOutput = [];
    console.log = (msg) => consoleOutput.push(msg);
    console.warn = (msg) => consoleOutput.push(msg);
    console.error = (msg) => consoleOutput.push(msg);
    console.group = (msg) => consoleOutput.push(msg);
    console.groupEnd = (msg) => consoleOutput.push(msg);
    console.time = (msg) => consoleOutput.push(msg);
    console.timeEnd = (msg) => consoleOutput.push(msg);
  });

  afterEach(() => {
    Object.assign(console, originalConsole);
  });

  describe('logWizardState', () => {
    test('should log state in structured format', () => {
      const mockState = {
        isOpen: true,
        loading: false,
        error: null,
        categories: [{ id: 1, name: 'Test' }],
        popularQuestions: [{ id: 1, question: 'Test' }],
        qaItems: [{ id: 1, question: 'Test', answer: 'Answer' }]
      };

      // Just test that the function doesn't throw errors
      expect(() => logWizardState(mockState, 'Test Source')).not.toThrow();
    });
  });

  describe('validateWizardData', () => {
    test('should return false for non-array data', () => {
      const result = validateWizardData(null, 'categories');
      expect(result).toBe(false);
      expect(consoleOutput.some(output => output.includes('Not an array'))).toBe(true);
    });

    test('should return false for empty array', () => {
      const result = validateWizardData([], 'categories');
      expect(result).toBe(false);
      expect(consoleOutput.some(output => output.includes('Empty'))).toBe(true);
    });

    test('should validate category structure', () => {
      const validCategories = [{
        id: 1,
        name: 'Test',
        description: 'Desc',
        question_count: 5
      }];

      const result = validateWizardData(validCategories, 'categories');
      expect(result).toBe(true);
      expect(consoleOutput.filter(output => output && output.includes('Valid categories data')).length).toBeGreaterThan(0);
    });

    test('should return false for category with missing fields', () => {
      const invalidCategories = [{
        id: 1,
        name: 'Test'
        // Missing description and question_count
      }];

      const result = validateWizardData(invalidCategories, 'categories');
      expect(result).toBe(false);
      expect(consoleOutput.filter(output => output && output.includes('missing fields')).length).toBeGreaterThan(0);
    });

    test('should validate popular questions structure', () => {
      const validPopular = [{
        id: 1,
        question: 'Test',
        category: 'General',
        view_count: 100
      }];

      const result = validateWizardData(validPopular, 'popularQuestions');
      expect(result).toBe(true);
    });

    test('should validate QA items structure', () => {
      const validQa = [{
        id: 1,
        question: 'Test',
        answer: 'Answer',
        category_id: 1,
        category: { id: 1, name: 'General' }
      }];

      const result = validateWizardData(validQa, 'qaItems');
      expect(result).toBe(true);
    });
  });

  describe('WizardPerformanceMonitor', () => {
    test('should track operation performance', async () => {
      const monitor = new WizardPerformanceMonitor();

      monitor.startOperation('testOp');
      expect(consoleOutput.some(output => output.includes('testOp'))).toBe(true);

      // Small delay to simulate work
      await new Promise(resolve => setTimeout(resolve, 10));
      monitor.endOperation('testOp');
      expect(consoleOutput.filter(output => output && output.includes('took')).length).toBeGreaterThan(0);
    });

    test('should return performance metrics', () => {
      const monitor = new WizardPerformanceMonitor();
      monitor.startOperation('testOp');

      const metrics = monitor.getMetrics();
      expect(metrics).toHaveProperty('testOp');
      expect(metrics.testOp).toHaveProperty('startTime');

      monitor.endOperation('testOp');
      const updatedMetrics = monitor.getMetrics();
      expect(updatedMetrics.testOp).toHaveProperty('duration');
    });
  });

  describe('generateTestData', () => {
    test('should provide empty arrays', () => {
      expect(generateTestData.emptyCategories).toEqual([]);
      expect(generateTestData.emptyPopularQuestions).toEqual([]);
      expect(generateTestData.emptyQaItems).toEqual([]);
    });

    test('should generate single test items', () => {
      const singleCategory = generateTestData.singleCategory();
      expect(Array.isArray(singleCategory)).toBe(true);
      expect(singleCategory.length).toBe(1);
      expect(singleCategory[0]).toHaveProperty('name', 'Test Category');

      const singlePopular = generateTestData.singlePopularQuestion();
      expect(singlePopular[0]).toHaveProperty('question', 'Test Question');

      const singleQa = generateTestData.singleQaItem();
      expect(singleQa[0]).toHaveProperty('answer', 'Test Answer');
    });
  });

  describe('createWizardDebugReport', () => {
    test('should create comprehensive debug report', () => {
      const mockState = {
        isOpen: true,
        loading: false,
        error: 'Test error',
        categories: [{ id: 1, name: 'Test' }],
        popularQuestions: [{ id: 1, question: 'Test' }],
        qaItems: [{ id: 1, question: 'Test', answer: 'Answer' }]
      };

      const report = createWizardDebugReport(mockState);

      expect(report).toHaveProperty('timestamp');
      expect(report).toHaveProperty('environment');
      expect(report).toHaveProperty('backendUrl');
      expect(report.state).toHaveProperty('isOpen', true);
      expect(report.state).toHaveProperty('error', 'Test error');
      expect(report.dataQuality).toHaveProperty('categoriesValid');

      expect(consoleOutput.filter(output => output && output.includes('Wizard Debug Report')).length).toBeGreaterThan(0);
    });
  });
});
