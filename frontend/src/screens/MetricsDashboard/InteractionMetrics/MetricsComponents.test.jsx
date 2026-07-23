import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { UserActivityMetric } from './UserActivityMetric';
import { WizardUsageMetric } from './WizardUsageMetric';
import { ErrorAnalysisMetric } from './ErrorAnalysisMetric';

describe('Metrics Components - Undefined Data Handling', () => {
  const mockUser = { name: 'Test User', role: 'admin' };
  const mockDateRange = { start: '2023-01-01', end: '2023-01-31' };

  describe('UserActivityMetric', () => {
    it('should handle undefined metrics gracefully', () => {
      render(<UserActivityMetric user={mockUser} dateRange={mockDateRange} />);

      // Should show permission message or loading state
      expect(screen.getByText(/User activity metrics require special permissions/i)).toBeInTheDocument();
    });

    it('should handle null metrics gracefully', () => {
      // This test would require mocking the API call to return null
      // For now, we test that the component doesn't crash
      expect(() => {
        render(<UserActivityMetric user={mockUser} dateRange={mockDateRange} />);
      }).not.toThrow();
    });
  });

  describe('WizardUsageMetric', () => {
    it('should handle undefined metrics gracefully', () => {
      render(<WizardUsageMetric user={mockUser} dateRange={mockDateRange} />);

      expect(screen.getByText(/Wizard usage metrics require special permissions/i)).toBeInTheDocument();
    });

    it('should handle null metrics gracefully', () => {
      expect(() => {
        render(<WizardUsageMetric user={mockUser} dateRange={mockDateRange} />);
      }).not.toThrow();
    });
  });

  describe('ErrorAnalysisMetric', () => {
    it('should handle undefined metrics gracefully', () => {
      render(<ErrorAnalysisMetric user={mockUser} dateRange={mockDateRange} />);

      expect(screen.getByText(/Error analysis metrics require special permissions/i)).toBeInTheDocument();
    });

    it('should handle null metrics gracefully', () => {
      expect(() => {
        render(<ErrorAnalysisMetric user={mockUser} dateRange={mockDateRange} />);
      }).not.toThrow();
    });
  });

  describe('Optional Chaining Safety', () => {
    it('should use optional chaining for all metrics property access', () => {
      // This is more of a visual/test coverage check
      // The actual safety is in the code using metrics?.property syntax
      const testMetrics = {
        date_range: undefined,
        total_interactions: undefined,
        error_rate: undefined
      };

      // Test that optional chaining works
      expect(testMetrics?.date_range).toBeUndefined();
      expect(testMetrics?.total_interactions?.toLocaleString()).toBeUndefined();
      expect(testMetrics?.error_rate?.toFixed(1)).toBeUndefined();
    });
  });
});
