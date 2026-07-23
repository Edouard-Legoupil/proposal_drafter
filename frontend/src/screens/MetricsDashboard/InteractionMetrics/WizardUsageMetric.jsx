/**
 * Wizard Usage Metric Component
 *
 * Displays wizard usage statistics and effectiveness metrics.
 * Requires 'ui_analysis' role to view.
 */

import React, { useState, useEffect } from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Paper, Typography, CircularProgress, Alert, Box, LinearProgress } from '@mui/material';
import { hasPermission } from '../../../utils/roleUtils';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

const UNHCR_PALETTE = {
  blue: '#0072BC',
  darkBlue: '#003A8F',
  lightBlue: '#4F9DD7',
  yellow: '#F2A900',
  orange: '#E87722',
  green: '#4C8C2B',
  red: '#C6362B',
  textPrimary: '#222222',
  textSecondary: '#555555'
};

export function WizardUsageMetric({ user, dateRange = '30d' }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const hasAccess = hasPermission(user, 'ui_analysis');

  useEffect(() => {
    if (!hasAccess || !user?.id) {
      setLoading(false);
      return;
    }

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/interactions/analytics/?date_range=${dateRange}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch metrics');
        }

        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching wizard metrics:', err);
        setError('Failed to load wizard usage data');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [user?.id, dateRange, hasAccess]);

  if (!hasAccess) {
    return (
      <Paper elevation={3} style={{ padding: '20px', textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          Wizard usage metrics require special permissions.
        </Typography>
      </Paper>
    );
  }

  if (loading) {
    return (
      <Paper elevation={3} style={{ padding: '40px', textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" style={{ marginTop: '10px' }}>
          Loading wizard usage metrics...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} style={{ padding: '20px' }}>
        <Alert severity="error" style={{ marginBottom: '10px' }}>
          {error}
        </Alert>
      </Paper>
    );
  }

  // Check if metrics data is available
  if (!metrics?.wizard_usage_stats) {
    return (
      <Paper elevation={3} style={{ padding: '20px' }}>
        <Typography variant="body2" color="textSecondary">
          No wizard usage data available.
        </Typography>
      </Paper>
    );
  }

  const wizardStats = metrics?.wizard_usage_stats || {};

  // Prepare feedback distribution chart
  const feedbackData = {
    labels: ['Very Helpful (5)', 'Helpful (4)', 'Neutral (3)', 'Not Helpful (2)', 'Poor (1)'],
    datasets: [{
      data: [
        wizardStats.common_questions.filter(q => q.feedback === 5).length,
        wizardStats.common_questions.filter(q => q.feedback === 4).length,
        wizardStats.common_questions.filter(q => q.feedback === 3).length,
        wizardStats.common_questions.filter(q => q.feedback === 2).length,
        wizardStats.common_questions.filter(q => q.feedback === 1).length
      ],
      backgroundColor: [
        UNHCR_PALETTE.green,
        UNHCR_PALETTE.lightBlue,
        UNHCR_PALETTE.yellow,
        UNHCR_PALETTE.orange,
        UNHCR_PALETTE.red
      ],
      borderWidth: 0
    }]
  };

  const feedbackOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          boxWidth: 12,
          padding: 15,
          font: { size: 11 }
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
            return `${context.label}: ${context.parsed} (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <Paper elevation={3} style={{ padding: '20px', height: '100%' }}>
      <Typography variant="h6" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
        Wizard Usage & Effectiveness
      </Typography>

      <Typography variant="body2" color="textSecondary" paragraph>
        {metrics?.date_range} • {wizardStats.total_usage.toLocaleString()} total wizard interactions
      </Typography>

      {/* Feedback Distribution Chart */}
      <Box style={{ height: '250px', marginBottom: '20px' }}>
        <Doughnut data={feedbackData} options={feedbackOptions} />
      </Box>

      {/* Key Metrics */}
      <Box style={{ marginBottom: '20px' }}>
        <Typography variant="subtitle2" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
          User Satisfaction
        </Typography>

        <Box style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <Typography variant="body2" style={{ color: UNHCR_PALETTE.textSecondary, marginRight: '10px', width: '120px' }}>
            Average Rating:
          </Typography>
          <LinearProgress
            variant="determinate"
            value={wizardStats.average_feedback_score * 20}
            style={{ flex: 1, height: '8px', borderRadius: '4px' }}
            color={wizardStats.average_feedback_score >= 4 ? 'primary' : wizardStats.average_feedback_score >= 3 ? 'warning' : 'error'}
          />
          <Typography variant="body2" style={{ color: UNHCR_PALETTE.textPrimary, marginLeft: '10px', fontWeight: 'bold' }}>
            {wizardStats.average_feedback_score.toFixed(1)}/5.0
          </Typography>
        </Box>

        <Box style={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="body2" style={{ color: UNHCR_PALETTE.textSecondary, marginRight: '10px', width: '120px' }}>
            Helpfulness:
          </Typography>
          <LinearProgress
            variant="determinate"
            value={wizardStats.helpful_percentage}
            style={{ flex: 1, height: '8px', borderRadius: '4px' }}
            color={wizardStats.helpful_percentage >= 75 ? 'primary' : wizardStats.helpful_percentage >= 50 ? 'warning' : 'error'}
          />
          <Typography variant="body2" style={{ color: UNHCR_PALETTE.textPrimary, marginLeft: '10px', fontWeight: 'bold' }}>
            {wizardStats.helpful_percentage.toFixed(1)}%
          </Typography>
        </Box>
      </Box>

      {/* Common Questions */}
      <Box>
        <Typography variant="subtitle2" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
          Most Common Questions
        </Typography>

        {wizardStats.common_questions?.slice(0, 5).map((question, index) => (
          <Box key={index} style={{
            padding: '10px 0',
            borderBottom: index < 4 ? `1px solid ${UNHCR_PALETTE.gridLight}` : 'none'
          }}>
            <Typography variant="body2" style={{ color: UNHCR_PALETTE.textPrimary, fontWeight: '500' }}>
              {index + 1}. {question.question}
            </Typography>
            <Typography variant="caption" display="block" style={{ color: UNHCR_PALETTE.textSecondary, marginTop: '2px' }}>
              Category: {question.category} • Asked {question.frequency || 'N/A'} times
            </Typography>
          </Box>
        ))}

        {wizardStats.common_questions?.length === 0 && (
          <Typography variant="body2" color="textSecondary" style={{ padding: '10px 0' }}>
            No common questions data available.
          </Typography>
        )}
      </Box>
    </Paper>
  );
}
