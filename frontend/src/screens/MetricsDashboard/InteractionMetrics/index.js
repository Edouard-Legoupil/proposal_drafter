/**
 * Interaction Metrics Components
 *
 * Exports all interaction-related metric components for the dashboard.
 * All components require 'ui_analysis' role for access.
 */

export { UserActivityMetric } from './UserActivityMetric';
export { WizardUsageMetric } from './WizardUsageMetric';
export { ErrorAnalysisMetric } from './ErrorAnalysisMetric';

// Import components first
import { UserActivityMetric } from './UserActivityMetric';
import { WizardUsageMetric } from './WizardUsageMetric';
import { ErrorAnalysisMetric } from './ErrorAnalysisMetric';

// Export all components as a group for easy importing
export const InteractionMetrics = {
  UserActivityMetric,
  WizardUsageMetric,
  ErrorAnalysisMetric
};
