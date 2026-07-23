/**
 * ProgressModal Component Tests
 * Comprehensive test suite for the ProgressModal component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ProgressModal from './ProgressModal';

describe('ProgressModal Component', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly when isOpen is true', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={50}
        message="Generating proposal..."
      />
    );

    expect(screen.getByText('Generating proposal...')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Close' })).not.toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <ProgressModal
        isOpen={false}
        onClose={mockOnClose}
        progress={50}
        message="Generating proposal..."
      />
    );

    expect(container.querySelector('dialog[open]')).not.toBeInTheDocument();
  });

  it('should display progress bar with correct width', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={75}
        message="Almost done..."
      />
    );

    const progressBar = screen.getByRole('dialog').querySelector('div[style*="width: 75%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('should show green progress bar for successful operations', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={100}
        message="Generation completed!"
      />
    );

    const dialog = screen.getByRole('dialog');
    const progressContainer = dialog.querySelector('.Chat_regenerate_header > div');
    const progressBar = progressContainer?.querySelector('div');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle('backgroundColor: #4CAF50');
  });

  it('should show red progress bar for failed operations', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={100}
        message="Generation failed!"
      />
    );

    const dialog = screen.getByRole('dialog');
    const progressContainer = dialog.querySelector('.Chat_regenerate_header > div');
    const progressBar = progressContainer?.querySelector('div');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle('backgroundColor: #ff4444');
  });

  it('should show Close button only when operation failed', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={100}
        message="Generation failed!"
      />
    );

    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('should not show Close button when operation is in progress', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={50}
        message="Generating..."
      />
    );

    expect(screen.queryByRole('button', { name: 'Close' })).not.toBeInTheDocument();
  });

  it('should apply correct CSS classes', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={50}
        message="Generating..."
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveClass('Chat_regenerate');
  });

  it('should handle default props correctly', () => {
    render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('0%')).toBeInTheDocument();
    const messageElement = screen.getByText((content, element) => {
      return element.tagName.toLowerCase() === 'p' && element.textContent === '';
    });
    expect(messageElement).toBeInTheDocument(); // Empty message
  });

  it('should match snapshot for success state', () => {
    const { asFragment } = render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={100}
        message="Generation completed!"
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });

  it('should match snapshot for failure state', () => {
    const { asFragment } = render(
      <ProgressModal
        isOpen={true}
        onClose={mockOnClose}
        progress={100}
        message="Generation failed!"
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });
});
