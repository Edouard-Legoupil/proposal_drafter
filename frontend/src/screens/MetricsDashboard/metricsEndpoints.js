/**
 * Metrics API Endpoints Configuration
 * Centralized configuration for all metrics-related API endpoints
 */

const METRICS_ENDPOINTS = {
  pipelineKpis: '/metrics/pipeline-kpis',
  proposalsByDonor: '/metrics/proposals-by-donor',
  proposalsByOutcome: '/metrics/proposals-by-outcome',
  proposalsByContext: '/metrics/proposals-by-context',
  proposalsByTeam: '/metrics/proposals-by-team',
  proposalsByTime: '/metrics/proposals-by-time',
  editActivity: '/metrics/edit-activity',
  reviewerActivity: '/metrics/reviewer-activity',
  knowledgeCards: '/metrics/knowledge-cards',
  knowledgeCardsHistory: '/metrics/knowledge-cards-history',
  reference: '/metrics/reference',
  referenceUsage: '/metrics/reference-usage',
  referenceIssue: '/metrics/reference-issue',
  cardEditFrequency: '/metrics/card-edit-frequency',
  cardImpactScore: '/metrics/card-impact-score',
  knowledgeSilos: '/metrics/knowledge-silos'
};

// Ordered list of all endpoint keys for sequential fetching
const ENDPOINT_KEYS = [
  'pipelineKpis',
  'proposalsByDonor',
  'proposalsByOutcome',
  'proposalsByContext',
  'proposalsByTeam',
  'proposalsByTime',
  'editActivity',
  'reviewerActivity',
  'knowledgeCards',
  'knowledgeCardsHistory',
  'reference',
  'referenceUsage',
  'referenceIssue',
  'cardEditFrequency',
  'cardImpactScore',
  'knowledgeSilos'
];

export { METRICS_ENDPOINTS, ENDPOINT_KEYS };
