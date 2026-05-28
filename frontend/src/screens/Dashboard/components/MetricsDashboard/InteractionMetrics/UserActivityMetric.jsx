/**
 * User Activity Metric Component
 * 
 * Displays user activity statistics with role-based access control.
 * Requires 'ui_analysis' role to view.
 */

import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { Paper, Typography, CircularProgress, Alert, Box } from '@mui/material';
import { hasPermission } from '../../../../utils/roleUtils';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

const UNHCR_PALETTE = {
  blue: '#0072BC',
  darkBlue: '#003A8F',
  lightBlue: '#4F9DD7',
  textPrimary: '#222222',
  textSecondary: '#555555',
  gridLight: '#E6E6E6'
};

export function UserActivityMetric({ user, dateRange = '30d' }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Check if user has required permission
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
        console.error('Error fetching user activity metrics:', err);
        setError('Failed to load user activity data');
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
          User activity metrics require special permissions.
        </Typography>
      </Paper>
    );
  }
  
  if (loading) {
    return (
      <Paper elevation={3} style={{ padding: '40px', textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" style={{ marginTop: '10px' }}>
          Loading user activity metrics...
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
        <Typography variant="body2" color="textSecondary">
          Please try refreshing the page or contact support.
        </Typography>
      </Paper>
    );
  }
  
  if (!metrics) {
    return (
      <Paper elevation={3} style={{ padding: '20px' }}>
        <Typography variant="body2" color="textSecondary">
          No user activity data available.
        </Typography>
      </Paper>
    );
  }
  
  // Prepare chart data
  const interactionTypes = metrics.interaction_types || [];
  const chartData = {
    labels: interactionTypes.map(item => item.type.replace('_', ' ')),
    datasets: [{
      label: 'Interactions',
      data: interactionTypes.map(item => item.count),
      backgroundColor: interactionTypes.map((_, index) => 
        [UNHCR_PALETTE.blue, UNHCR_PALETTE.lightBlue, UNHCR_PALETTE.darkBlue, 
         UNHCR_PALETTE.yellow, UNHCR_PALETTE.orange][index % 5]
      ),
      borderRadius: 4,
      borderWidth: 0
    }]
  };
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = interactionTypes[context.dataIndex];
            return `${item.type}: ${item.count} (${item.percentage.toFixed(1)}%)`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: UNHCR_PALETTE.textSecondary }
      },
      y: {
        grid: { display: false },
        ticks: { color: UNHCR_PALETTE.textSecondary }
      }
    }
  };
  
  return (
    <Paper elevation={3} style={{ padding: '20px', height: '100%' }}>
      <Typography variant="h6" gutterBottom style={{ color: UNHCR_PALETTE.textPrimary }}>
        User Activity Metrics
      </Typography>
      
      <Typography variant="body2" color="textSecondary" paragraph>
        {metrics.date_range} • {metrics.total_interactions.toLocaleString()} total interactions
      </Typography>
      
      <Box style={{ height: '300px', marginBottom: '20px' }}>
        <Bar data={chartData} options={chartOptions} />
      </Box>
      
      <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
        <MetricStat
          label="Total Sessions"
          value={metrics.total_sessions.toLocaleString()}
          color={UNHCR_PALETTE.blue}
        />
        <MetricStat
          label="Active Users"
          value={metrics.total_users.toLocaleString()}
          color={UNHCR_PALETTE.lightBlue}
        />
        <MetricStat
          label="Avg Interactions/Session"
          value={metrics.average_interactions_per_session.toFixed(1)}
          color={UNHCR_PALETTE.darkBlue}
        />
        <MetricStat
          label="Error Rate"
          value={`${metrics.error_rate.toFixed(1)}%`}
          color={metrics.error_rate > 5 ? '#C6362B' : UNHCR_PALETTE.yellow}
        />
      </Box>
    </Paper>
  );
}

function MetricStat({ label, value, color }) {
  return (
    <Box style={{ textAlign: 'center' }}>
      <Typography variant="caption" display="block" style={{ color: UNHCR_PALETTE.textSecondary }}>
        {label}
      </Typography>
      <Typography variant="h5" style={{ color, fontWeight: 'bold', marginTop: '5px' }}>
        {value}
      </Typography>
    </Box>
  );
}