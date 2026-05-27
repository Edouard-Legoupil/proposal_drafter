/**
 * Unit tests for Wizard components
 * 
 * Tests for React components including:
 * - WizardButton
 * - ContextualHelpIcon
 * - WizardModal (basic functionality)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WizardProvider, useWizard } from '../../context/WizardContext';
import WizardButton from './WizardButton';
import ContextualHelpIcon from './ContextualHelpIcon';
import WizardModal from './WizardModal';

describe('WizardButton', () => {
    it('renders correctly', () => {
        render(
            <WizardProvider>
                <WizardButton />
            </WizardProvider>
        );
        expect(screen.getByText('Help')).toBeInTheDocument();
        expect(screen.getByLabelText('Help & Support')).toBeInTheDocument();
    });
    
    it('opens modal when clicked', () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        expect(screen.getByText('Proposal Drafter Help')).toBeInTheDocument();
    });
    
    it('has correct accessibility attributes', () => {
        render(
            <WizardProvider>
                <WizardButton />
            </WizardProvider>
        );
        
        const button = screen.getByText('Help');
        expect(button).toHaveAttribute('aria-label', 'Open help wizard');
    });
});

describe('ContextualHelpIcon', () => {
    it('renders correctly', () => {
        render(
            <WizardProvider>
                <ContextualHelpIcon />
            </WizardProvider>
        );
        expect(screen.getByLabelText('Get help on this topic')).toBeInTheDocument();
    });
    
    it('opens modal when clicked', () => {
        render(
            <WizardProvider>
                <ContextualHelpIcon />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByLabelText('Get help on this topic'));
        expect(screen.getByText('Proposal Drafter Help')).toBeInTheDocument();
    });
    
    it('passes topic to context when provided', () => {
        const mockSetSelectedCategory = jest.fn();
        const mockUseWizard = jest.fn(() => ({
            setIsOpen: jest.fn(),
            setSelectedCategory: mockSetSelectedCategory
        }));
        
        jest.mock('../../context/WizardContext', () => ({
            useWizard: mockUseWizard
        }));
        
        render(
            <WizardProvider>
                <ContextualHelpIcon topic="test-topic" />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByLabelText('Get help on test-topic'));
        expect(mockSetSelectedCategory).toHaveBeenCalledWith('test-topic');
    });
});

describe('WizardModal', () => {

    
    it('renders correctly when closed', () => {
        render(
            <WizardProvider>
                <WizardModal />
            </WizardProvider>
        );
        
        // Should not be visible initially
        expect(screen.queryByText('Proposal Drafter Help')).not.toBeInTheDocument();
    });
    
    it('shows loading state during API calls', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        // Open modal
        fireEvent.click(screen.getByText('Help'));
        
        // Should show loading initially
        expect(screen.getByLabelText('Loading questions')).toBeInTheDocument();
        
        // Wait for API calls to complete
        await waitFor(() => {
            expect(screen.getByText('General')).toBeInTheDocument();
        });
    });
    
    it('displays categories correctly', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        await waitFor(() => {
            expect(screen.getByText('General')).toBeInTheDocument();
            expect(screen.getByText('Proposal Creation')).toBeInTheDocument();
            expect(screen.getByText('5')).toBeInTheDocument(); // question count
            expect(screen.getByText('10')).toBeInTheDocument();
        });
    });
    
    it('displays popular questions correctly', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        // Switch to popular questions tab
        await waitFor(() => {
            const popularTab = screen.getByText('Popular Questions');
            fireEvent.click(popularTab);
        });
        
        await waitFor(() => {
            expect(screen.getByText('How do I create a proposal?')).toBeInTheDocument();
            expect(screen.getByText('Viewed 42 times')).toBeInTheDocument();
        });
    });
    
    it('handles search functionality', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        await waitFor(() => {
            const searchInput = screen.getByLabelText('Search help topics');
            fireEvent.change(searchInput, { target: { value: 'search test' } });
            fireEvent.keyPress(searchInput, { key: 'Enter', charCode: 13 });
        });
        
        await waitFor(() => {
            expect(screen.getByText('Search Result Question')).toBeInTheDocument();
        });
    });
    
    it('shows Q&A detail when item is selected', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        await waitFor(() => {
            fireEvent.click(screen.getByText('Test Question'));
        });
        
        await waitFor(() => {
            expect(screen.getByText('Test Question')).toBeInTheDocument();
            expect(screen.getByText('Test Answer')).toBeInTheDocument();
            expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
        });
    });
    
    it('handles feedback submission', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        await waitFor(() => {
            fireEvent.click(screen.getByText('Test Question'));
        });
        
        await waitFor(() => {
            // Select rating
            const rating = screen.getByLabelText('Rate this answer');
            fireEvent.click(rating.querySelector('svg[data-index="4"]')); // 5 stars
            
            // Submit feedback
            fireEvent.click(screen.getByText('Submit Feedback'));
        });
        
        // Feedback submission test would need proper mocking
        // This is a placeholder for actual API call verification
    });
    
    it('has proper accessibility attributes', async () => {
        render(
            <WizardProvider>
                <WizardButton />
                <WizardModal />
            </WizardProvider>
        );
        
        fireEvent.click(screen.getByText('Help'));
        
        await waitFor(() => {
            expect(screen.getByLabelText('Wizard tabs')).toBeInTheDocument();
            expect(screen.getByLabelText('Search help topics')).toBeInTheDocument();
            expect(screen.getByLabelText('Loading questions')).toBeInTheDocument();
        });
    });
});

describe('WizardContext', () => {
    it('throws error when used outside provider', () => {
        const TestComponent = () => {
            const context = useWizard();
            return <div>{context.isOpen ? 'open' : 'closed'}</div>;
        };
        
        expect(() => {
            render(<TestComponent />);
        }).toThrow('useWizard must be used within a WizardProvider');
    });
    
    it('provides correct initial state', () => {
        const TestComponent = () => {
            const context = useWizard();
            return (
                <div>
                    {context.isOpen ? 'open' : 'closed'}
                    {context.loading ? 'loading' : 'ready'}
                </div>
            );
        };
        
        render(
            <WizardProvider>
                <TestComponent />
            </WizardProvider>
        );
        
        expect(screen.getByText('closed')).toBeInTheDocument();
        expect(screen.getByText('ready')).toBeInTheDocument();
    });
});