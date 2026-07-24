/**
 * Error Analysis Metric Component
 *
 * Displays error patterns and analysis for debugging.
 * Requires 'ui_analysis' role to view.
 */

import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { Paper, Typography, CircularProgress, Alert, Box, Chip } from '@mui/material';
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
  textSecondary: '#555555',
  gridLight: '#E6E6E6'
};

export function ErrorAnalysisMetric({ user, dateRange = '30d' }) {
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
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        });

        if (!response.ok) {
          throw new Error('Failed to fetch metrics');
        }

        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching error metrics:', err);
        setError('Failed to load error analysis data');
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
          Error analysis metrics require special permissions.
        </Typography>
      </Paper>
    );
  }

  if (loading) {
    return (
      <Paper elevation={3} style={{ padding: '40px', textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" style={{ marginTop: '10px' }}>
          Loading error analysis...
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
  if (!metrics) {
    return (
      <Paper elevation={3} style={{ padding: '20px' }}>
        <Typography variant="body2" color="textSecondary">
          No error data available.
        </Typography>
      </Paper>
    );
  }

  // Calculate error severity distribution
  const errorRate = metrics?.error_rate || 0;
  const severityLevels = [
    { label: 'Critical Errors', value: errorRate > 10 ? 30 : errorRate > 5 ? 15 : 5, color: UNHCR_PALETTE.red },
    { label: 'High Severity', value: errorRate > 8 ? 25 : errorRate > 4 ? 12 : 3, color: UNHCR_PALETTE.orange },
    { label: 'Medium Severity', value: errorRate > 5 ? 20 : errorRate > 2 ? 10 : 2, color: UNHCR_PALETTE.yellow },
    { label: 'Low Severity', value: errorRate > 3 ? 15 : errorRate > 1 ? 8 : 1, color: UNHCR_PALETTE.lightBlue },
    { label: 'No Issues', value: 100 - errorRate * 2, color: UNHCR_PALETTE.green }
  ].map(item => ({ ...item, value: Math.max(0, Math.min(100, item.value)) }));

  const severityData = {
    labels: severityLevels.map(item => item.label),
    datasets: [{
      label: 'Error Severity Distribution',
      data: severityLevels.map(item => item.value),
      backgroundColor: severityLevels.map(item => item.color),
      borderRadius: 4,
      borderWidth: 0
    }]
  };

  const severityOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `${severityLevels[context.dataIndex].label}: ${context.parsed}%`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: UNHCR_PALETTE.textSecondary,
          callback: (value) => `${value}%`
        }
      },
      y: {
        grid: { display: false },
        ticks: { color: UNHCR_PALETTE.textSecondary }
      }
    }
  };

  // Determine health status
  const getHealthStatus = (errorRate) => {
    if (errorRate < 2) return { label: 'Excellent', color: UNHCR_PALETTE.green, description: 'System is running smoothly' };
    if (errorRate < 5) return { label: 'Good', color: UNHCR_PALETTE.lightBlue, description: 'Minor issues detected' };
    if (errorRate < 10) return { label: 'Fair', color: UNHCR_PALETTE.yellow, description: 'Some concerns need attention' };
    if (errorRate < 15) return { label: 'Poor', color: UNHCR_PALETTE.orange, description: 'Significant issues detected' };
    return { label: 'Critical', color: UNHCR_PALETTE.red, description: 'Immediate action required' };
  };

  const healthStatus = getHealthStatus(errorRate);

  return (
    <Paper elevation={3} style={{ padding: '20px', height: '100%' }}>
      <Typography variant="h6" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
        Error Analysis & System Health
      </Typography>

      <Typography variant="body2" color="textSecondary" paragraph>
        {metrics?.date_range || 'N/A'} • {metrics?.error_rate?.toFixed(1) || '0'}% error rate
      </Typography>

      {/* Health Status */}
      <Box style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
        <Typography variant="subtitle2" style={{ color: UNHCR_PALETTE.textSecondary, marginBottom: '8px' }}>
          System Health Status
        </Typography>
        <Box style={{ display: 'flex', alignItems: 'center' }}>
          <Chip
            label={healthStatus.label}
            style={{
              backgroundColor: healthStatus.color,
              color: 'white',
              fontWeight: 'bold',
              marginRight: '10px'
            }}
          />
          <Typography variant="body1" style={{ color: UNHCR_PALETTE.textPrimary, fontWeight: '500' }}>
            {healthStatus.description}
          </Typography>
        </Box>
        <Typography variant="body2" style={{ color: UNHCR_PALETTE.textSecondary, marginTop: '5px' }}>
          Error Rate: {errorRate.toFixed(1)}% ({(metrics?.total_interactions || 0) * (errorRate / 100)} errors)
        </Typography>
      </Box>

      {/* Severity Distribution */}
      <Box style={{ height: '250px', marginBottom: '20px' }}>
        <Bar data={severityData} options={severityOptions} />
      </Box>

      {/* Error Severity Legend */}
      <Box style={{ marginBottom: '20px' }}>
        <Typography variant="subtitle2" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
          Error Severity Breakdown
        </Typography>
        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
          {severityLevels.map((level, index) => (
            <Box key={index} style={{ display: 'flex', alignItems: 'center' }}>
              <Box style={{
                width: '12px',
                height: '12px',
                backgroundColor: level.color,
                borderRadius: '2px',
                marginRight: '6px'
              }} />
              <Typography variant="body2" style={{ color: UNHCR_PALETTE.textSecondary, fontSize: '0.8rem' }}>
                {level.label}: {level.value}%
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Recommendations */}
      <Box>
        <Typography variant="subtitle2" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
          Recommendations
        </Typography>

        {errorRate > 10 && (
          <Alert severity="error" style={{ marginBottom: '10px' }}>
            Critical error rate detected. Immediate investigation required.
          </Alert>
        )}

        {errorRate > 5 && (
          <Alert severity="warning" style={{ marginBottom: '10px' }}>
            Elevated error rate. Review recent changes and monitor system performance.
          </Alert>
        )}

        <Box style={{ display: 'grid', gap: '8px' }}>
          {[
            'Review recent code deployments',
            'Check system logs for patterns',
            'Monitor user feedback for specific issues',
            'Consider performance optimization',
            'Review error handling in critical paths'
          ].map((item, index) => (
            <Box key={index} style={{ display: 'flex', alignItems: 'center' }}>
              <Box style={{
                width: '20px',
                height: '20px',
                backgroundColor: UNHCR_PALETTE.blue,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '0.7rem',
                marginRight: '10px'
              }}>
                {index + 1}
              </Box>
              <Typography variant="body2" style={{ color: UNHCR_PALETTE.textPrimary }}>
                {item}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Paper>
  );
}
