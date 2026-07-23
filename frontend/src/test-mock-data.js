// Test script to verify mock data functions work correctly
import { getMockCategories, getMockPopularQuestions, getMockQaItems } from './context/WizardContext';

console.log('Testing mock data functions...');

// Test categories
const categories = getMockCategories();
console.log('Categories:', categories);
console.log('Categories length:', categories.length);

// Test popular questions
const popularQuestions = getMockPopularQuestions();
console.log('Popular Questions:', popularQuestions);
console.log('Popular Questions length:', popularQuestions.length);

// Test QA items
const qaItems = getMockQaItems();
console.log('QA Items:', qaItems);
console.log('QA Items length:', qaItems.length);

// Test QA items by category
const generalItems = getMockQaItems(1);
console.log('General QA Items:', generalItems);
console.log('General QA Items length:', generalItems.length);

console.log('Mock data test completed.');
