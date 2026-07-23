/**
 * FollowUpModal Component Tests
 * Comprehensive test suite for the FollowUpModal component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import FollowUpModal from './FollowUpModal';

describe('FollowUpModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnSkip = vi.fn();
  const mockOnSaveForLater = vi.fn();
  const mockOnRegenerate = vi.fn();
  const mockSetInstruction = vi.fn();

  const mockProps = {
    isOpen: true,
    onClose: mockOnClose,
    onSkip: mockOnSkip,
    onSaveForLater: mockOnSaveForLater,
    onRegenerate: mockOnRegenerate,
    instruction: '',
    setInstruction: mockSetInstruction,
    regenerateCloseIcon: 'close-icon.png',
    generateIcon: 'generate-icon.png'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly when isOpen is true', () => {
    render(<FollowUpModal {...mockProps} />);

    expect(screen.getByText('Provide Follow-up Instructions')).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., 'Make the budget section more detailed', 'Focus more on gender equality', 'Revise the timeline to be more realistic'...")).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Skip' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save for Later' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Regenerate Now' })).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(<FollowUpModal {...mockProps} isOpen={false} />);

    expect(container.querySelector('dialog[open]')).not.toBeInTheDocument();
  });

  it('should call onClose when close icon is clicked', () => {
    render(<FollowUpModal {...mockProps} />);

    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onSkip when Skip button is clicked', () => {
    render(<FollowUpModal {...mockProps} />);

    fireEvent.click(screen.getByRole('button', { name: 'Skip' }));
    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });

  it('should call onSaveForLater when Save for Later button is clicked', () => {
    render(<FollowUpModal {...mockProps} />);

    fireEvent.click(screen.getByRole('button', { name: 'Save for Later' }));
    expect(mockOnSaveForLater).toHaveBeenCalledTimes(1);
  });

  it('should call onRegenerate when Regenerate Now button is clicked with instruction', () => {
    render(<FollowUpModal {...mockProps} instruction="Test instruction" />);

    fireEvent.click(screen.getByRole('button', { name: 'Regenerate Now' }));
    expect(mockOnRegenerate).toHaveBeenCalledTimes(1);
  });

  it('should disable Regenerate Now button when instruction is empty', () => {
    render(<FollowUpModal {...mockProps} instruction="" />);

    const regenerateButton = screen.getByRole('button', { name: 'Regenerate Now' });
    expect(regenerateButton).toBeDisabled();
  });

  it('should enable Regenerate Now button when instruction is provided', () => {
    render(<FollowUpModal {...mockProps} instruction="Test instruction" />);

    const regenerateButton = screen.getByRole('button', { name: 'Regenerate Now' });
    expect(regenerateButton).not.toBeDisabled();
  });

  it('should call setInstruction when textarea value changes', () => {
    render(<FollowUpModal {...mockProps} />);

    const textarea = screen.getByPlaceholderText("e.g., 'Make the budget section more detailed', 'Focus more on gender equality', 'Revise the timeline to be more realistic'...");
    fireEvent.change(textarea, { target: { value: 'New instruction' } });

    expect(mockSetInstruction).toHaveBeenCalledWith('New instruction');
  });

  it('should have correct test IDs for testing', () => {
    render(<FollowUpModal {...mockProps} />);

    expect(screen.getByTestId('followup-modal')).toBeInTheDocument();
    expect(screen.getByTestId('followup-instruction-input')).toBeInTheDocument();
    expect(screen.getByTestId('followup-skip-button')).toBeInTheDocument();
    expect(screen.getByTestId('followup-save-button')).toBeInTheDocument();
    expect(screen.getByTestId('followup-regenerate-button')).toBeInTheDocument();
  });

  it('should apply correct CSS classes', () => {
    render(<FollowUpModal {...mockProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveClass('Chat_regenerate');
  });

  it('should have proper accessibility attributes', () => {
    render(<FollowUpModal {...mockProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('data-testid', 'followup-modal');
  });

  it('should match snapshot', () => {
    const { asFragment } = render(<FollowUpModal {...mockProps} />);
    expect(asFragment()).toMatchSnapshot();
  });
});
