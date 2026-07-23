/**
 * ValidationModal Component Tests
 * Comprehensive test suite for the ValidationModal component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ValidationModal from './ValidationModal';

describe('ValidationModal Component', () => {
  const mockMissingFields = ['Field 1', 'Field 2', 'Field 3'];
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly when isOpen is true', () => {
    render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );

    expect(screen.getByText('Missing Required Fields')).toBeInTheDocument();
    expect(screen.getByText('The following mandatory parameters are missing:')).toBeInTheDocument();

    mockMissingFields.forEach(field => {
      expect(screen.getByText(field)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <ValidationModal
        isOpen={false}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );

    expect(container.querySelector('dialog[open]')).not.toBeInTheDocument();
  });

  it('should call onClose when Close button is clicked', () => {
    render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should handle empty missingFields array gracefully', () => {
    render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={[]}
      />
    );

    expect(screen.getByText('Missing Required Fields')).toBeInTheDocument();
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
  });

  it('should apply correct CSS classes', () => {
    render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveClass('Chat_regenerate');
  });

  it('should have proper accessibility attributes', () => {
    render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
  });

  it('should match snapshot', () => {
    const { asFragment } = render(
      <ValidationModal
        isOpen={true}
        onClose={mockOnClose}
        missingFields={mockMissingFields}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });
});
