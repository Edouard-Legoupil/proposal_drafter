/**
 * RegenerateModal Component Tests
 * Comprehensive test suite for the RegenerateModal component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import RegenerateModal from './RegenerateModal';

describe('RegenerateModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnRegenerate = vi.fn();
  const mockSetInputValue = vi.fn();

  const mockProps = {
    isOpen: true,
    onClose: mockOnClose,
    onRegenerate: mockOnRegenerate,
    sectionName: 'Budget Section',
    inputValue: '',
    setInputValue: mockSetInputValue,
    loading: false,
    generateIcon: 'generate-icon.png',
    regenerateCloseIcon: 'close-icon.png'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly when isOpen is true', () => {
    render(<RegenerateModal {...mockProps} />);

    expect(screen.getByText('Regenerate — Budget Section')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Regenerate' })).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(<RegenerateModal {...mockProps} isOpen={false} />);

    expect(container.querySelector('dialog[open]')).not.toBeInTheDocument();
  });

  it('should display section name in header', () => {
    render(<RegenerateModal {...mockProps} sectionName="Timeline Section" />);

    expect(screen.getByText('Regenerate — Timeline Section')).toBeInTheDocument();
  });

  it('should show default section name when sectionName is not provided', () => {
    render(<RegenerateModal {...mockProps} sectionName="" />);

    expect(screen.getByText('Regenerate — Section')).toBeInTheDocument();
  });

  it('should call onClose when close icon is clicked', () => {
    render(<RegenerateModal {...mockProps} />);

    fireEvent.click(screen.getByTestId('regenerate-dialog-close-button'));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onRegenerate when Regenerate button is clicked', () => {
    render(<RegenerateModal {...mockProps} inputValue="Test input" />);

    fireEvent.click(screen.getByTestId('regenerate-dialog-regenerate-button'));
    expect(mockOnRegenerate).toHaveBeenCalledTimes(1);
  });

  it('should call setInputValue when textarea value changes', () => {
    render(<RegenerateModal {...mockProps} />);

    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'New regenerate instruction' } });

    expect(mockSetInputValue).toHaveBeenCalledWith('New regenerate instruction');
  });

  it('should disable Regenerate button when inputValue is empty', () => {
    render(<RegenerateModal {...mockProps} inputValue="" />);

    const regenerateButton = screen.getByTestId('regenerate-dialog-regenerate-button');
    expect(regenerateButton).toBeDisabled();
  });

  it('should enable Regenerate button when inputValue is provided', () => {
    render(<RegenerateModal {...mockProps} inputValue="Test input" />);

    const regenerateButton = screen.getByTestId('regenerate-dialog-regenerate-button');
    expect(regenerateButton).not.toBeDisabled();
  });

  it('should show loading state when loading is true', () => {
    render(<RegenerateModal {...mockProps} loading={true} />);

    const regenerateButton = screen.getByTestId('regenerate-dialog-regenerate-button');
    expect(regenerateButton).toHaveTextContent('Regenerating');
  });

  it('should have correct test IDs for testing', () => {
    render(<RegenerateModal {...mockProps} />);

    expect(screen.getByTestId('regenerate-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('regenerate-dialog-prompt-input')).toBeInTheDocument();
    expect(screen.getByTestId('regenerate-dialog-regenerate-button')).toBeInTheDocument();
    expect(screen.getByTestId('regenerate-dialog-close-button')).toBeInTheDocument();
  });

  it('should apply correct CSS classes', () => {
    render(<RegenerateModal {...mockProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveClass('Chat_regenerate');
  });

  it('should have proper accessibility attributes', () => {
    render(<RegenerateModal {...mockProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('data-testid', 'regenerate-dialog');
  });

  it('should match snapshot', () => {
    const { asFragment } = render(<RegenerateModal {...mockProps} />);
    expect(asFragment()).toMatchSnapshot();
  });
});
