import { describe, test, expect } from 'vitest';

describe('WizardContext Mock Data', () => {
  test('mock categories should have correct structure', () => {
    const mockCategories = [
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

    expect(mockCategories.length).toBe(5);
    expect(mockCategories[0].name).toBe('General');
    expect(mockCategories[1].question_count).toBe(4);
    expect(mockCategories[4].description).toContain('review');
  });

  test('mock popular questions should have correct structure', () => {
    const mockPopularQuestions = [
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

    expect(mockPopularQuestions.length).toBe(5);
    expect(mockPopularQuestions[0].category).toBe('General');
    expect(mockPopularQuestions[1].view_count).toBe(120);
    expect(mockPopularQuestions[3].question).toContain('review');
  });

  test('mock QA items should have correct structure', () => {
    const mockQaItems = [
      {
        id: 1,
        question: 'What is the Proposal Drafter?',
        answer: 'The Proposal Drafter is an AI-powered tool designed to help UN agencies and NGOs create high-quality project proposals efficiently.',
        category_id: 1,
        category: { id: 1, name: 'General' }
      },
      {
        id: 3,
        question: 'How do I create a new proposal?',
        answer: '1. Log in to the Proposal Drafter, 2. Navigate to the Dashboard, 3. Click the \'New Proposal\' button, 4. Select the donor organization, outcome, and field context, 5. Provide a brief project description, 6. Click \'Generate Proposal\' to let the AI create the initial draft.',
        category_id: 3,
        category: { id: 3, name: 'Proposal Creation' }
      }
    ];

    expect(mockQaItems.length).toBe(2);
    expect(mockQaItems[0].answer).toContain('AI-powered');
    expect(mockQaItems[1].category.name).toBe('Proposal Creation');
  });
});
