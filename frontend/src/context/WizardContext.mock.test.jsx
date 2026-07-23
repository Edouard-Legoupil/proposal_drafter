import { describe, test, expect } from 'vitest';
import {
  getMockCategories,
  getMockPopularQuestions,
  getMockQaItems,
  getMockSearchResults
} from './WizardContext';

describe('WizardContext Mock Functions', () => {
  test('getMockCategories should return array of categories', () => {
    const categories = getMockCategories();

    expect(Array.isArray(categories)).toBe(true);
    expect(categories.length).toBeGreaterThan(0);

    // Check structure of first category
    const firstCategory = categories[0];
    expect(firstCategory).toHaveProperty('id');
    expect(firstCategory).toHaveProperty('name');
    expect(firstCategory).toHaveProperty('description');
    expect(firstCategory).toHaveProperty('question_count');

    expect(typeof firstCategory.id).toBe('number');
    expect(typeof firstCategory.name).toBe('string');
    expect(typeof firstCategory.description).toBe('string');
    expect(typeof firstCategory.question_count).toBe('number');
  });

  test('getMockPopularQuestions should return array of popular questions', () => {
    const popularQuestions = getMockPopularQuestions();

    expect(Array.isArray(popularQuestions)).toBe(true);
    expect(popularQuestions.length).toBeGreaterThan(0);

    // Check structure of first popular question
    const firstQuestion = popularQuestions[0];
    expect(firstQuestion).toHaveProperty('id');
    expect(firstQuestion).toHaveProperty('question');
    expect(firstQuestion).toHaveProperty('category');
    expect(firstQuestion).toHaveProperty('view_count');

    expect(typeof firstQuestion.id).toBe('number');
    expect(typeof firstQuestion.question).toBe('string');
    expect(typeof firstQuestion.category).toBe('string');
    expect(typeof firstQuestion.view_count).toBe('number');
  });

  test('getMockQaItems should return array of QA items', () => {
    // Test without category filter
    const allQaItems = getMockQaItems();
    expect(Array.isArray(allQaItems)).toBe(true);
    expect(allQaItems.length).toBeGreaterThan(0);

    // Check structure of first QA item
    const firstItem = allQaItems[0];
    expect(firstItem).toHaveProperty('id');
    expect(firstItem).toHaveProperty('question');
    expect(firstItem).toHaveProperty('answer');
    expect(firstItem).toHaveProperty('category_id');
    expect(firstItem).toHaveProperty('category');

    // Test with category filter
    const generalItems = getMockQaItems(1);
    expect(Array.isArray(generalItems)).toBe(true);
    expect(generalItems.length).toBeGreaterThan(0);

    // All items should be from category 1
    generalItems.forEach(item => {
      expect(item.category_id).toBe(1);
    });
  });

  test('getMockSearchResults should filter items by query', () => {
    // Test with empty query
    const allResults = getMockSearchResults('');
    expect(Array.isArray(allResults)).toBe(true);
    expect(allResults.length).toBeGreaterThan(0);

    // Test with specific query
    const proposalResults = getMockSearchResults('proposal');
    expect(Array.isArray(proposalResults)).toBe(true);

    // All results should contain the search term
    proposalResults.forEach(item => {
      const questionLower = item.question.toLowerCase();
      const answerLower = item.answer.toLowerCase();
      expect(questionLower.includes('proposal') || answerLower.includes('proposal')).toBe(true);
    });

    // Test with query that should return no results
    const noResults = getMockSearchResults('nonexistentterm12345');
    expect(Array.isArray(noResults)).toBe(true);
    expect(noResults.length).toBe(0);
  });

  test('mock data should have consistent IDs', () => {
    const categories = getMockCategories();
    const popularQuestions = getMockPopularQuestions();
    const qaItems = getMockQaItems();

    // Check that IDs are unique within each array
    const categoryIds = categories.map(cat => cat.id);
    const uniqueCategoryIds = new Set(categoryIds);
    expect(categoryIds.length).toBe(uniqueCategoryIds.size);

    const popularQuestionIds = popularQuestions.map(q => q.id);
    const uniquePopularQuestionIds = new Set(popularQuestionIds);
    expect(popularQuestionIds.length).toBe(uniquePopularQuestionIds.size);

    const qaItemIds = qaItems.map(item => item.id);
    const uniqueQaItemIds = new Set(qaItemIds);
    expect(qaItemIds.length).toBe(uniqueQaItemIds.size);
  });
});
