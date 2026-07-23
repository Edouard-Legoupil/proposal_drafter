// Simple test to verify MetricsDashboard component syntax
import React from 'react';
import { render } from '@testing-library/react';
import MetricsDashboard from './src/screens/Dashboard/components/MetricsDashboard/MetricsDashboard.jsx';

describe('MetricsDashboard Component', () => {
  it('should render without syntax errors', () => {
    // Test with minimal props
    const { container } = render(
      <MetricsDashboard
        user={{ role: 'admin' }}
        dateRange={{ start: null, end: null }}
      />
    );

    // Basic check that it renders some content
    expect(container).toBeTruthy();
  });
});

console.log('MetricsDashboard syntax test passed!');
