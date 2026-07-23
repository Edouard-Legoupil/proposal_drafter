/**
 * Simplified Metrics Dashboard Component
 * This is a cleaner version that avoids complex nested structures
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Bar, Line, Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler
} from 'chart.js';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';
import { TreemapController, TreemapElement } from 'chartjs-chart-treemap';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler,
  MatrixController,
  MatrixElement,
  TreemapController,
  TreemapElement
);

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

const UNHCR_PALETTE = {
  blue: '#0072BC',
  darkBlue: '#003A8F',
  lightBlue: '#4F9DD7',
  textPrimary: '#222222',
  textSecondary: '#666666',
  bg: '#f5f5f5',
  gridLight: '#e0e0e0',
  yellow: '#FFD700',
  green: '#2E8B57',
  red: '#C6362B',
  purple: '#8A2BE2',
  orange: '#FF8C00'
};

const UNHCR_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top' },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleFont: { family: 'Lato' },
      bodyFont: { family: 'Lato' }
    }
  },
  scales: {
    x: {
      grid: { display: true, color: UNHCR_PALETTE.gridLight },
      ticks: { font: { family: 'Lato' } }
    },
    y: {
      grid: { display: true, color: UNHCR_PALETTE.gridLight },
      ticks: { font: { family: 'Lato' } }
    }
  }
};

export default function MetricsDashboardSimplified() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [dateStart, setDateStart] = useState(null);
  const [dateEnd, setDateEnd] = useState(null);
  const [expandedChart, setExpandedChart] = useState(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);

    const filterParams = `?filter_by=${filter}&date_start=${dateStart || ''}&date_end=${dateEnd || ''}`;

    try {
      const response = await fetch(`${API_BASE_URL}/metrics/pipeline-kpis${filterParams}`, {
        credentials: 'include'
      });

      if (response.ok) {
        setMetrics(await response.json());
      } else {
        throw new Error(`Failed to fetch metrics: ${response.status}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filter, dateStart, dateEnd]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '400px' }}>
        <Alert severity="error">Failed to load metrics: {error}</Alert>
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '400px' }}>
        <Alert severity="warning">No metrics data available</Alert>
      </Box>
    );
  }

  return (
    <div className="metrics-dashboard">
      <Box sx={{ p: 2 }}>
        <Typography variant="h4" gutterBottom>Metrics Dashboard</Typography>

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker label="Start Date" value={dateStart} onChange={setDateStart} slotProps={{ size: 'small' }} />
            <DatePicker label="End Date" value={dateEnd} onChange={setDateEnd} slotProps={{ size: 'small' }} />
          </LocalizationProvider>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Scope</InputLabel>
            <Select value={filter} onChange={(e) => setFilter(e.target.value)} label="Scope">
              <MenuItem value="all">Global</MenuItem>
              <MenuItem value="team">Team</MenuItem>
              <MenuItem value="user">Me</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* KPIs */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2">Total Funding</Typography>
              <Typography variant="h5">${(metrics.total_funding || 0).toLocaleString()}</Typography>
              <Typography variant="body2" color="textSecondary">Requested funding</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2">Active Proposals</Typography>
              <Typography variant="h5">{metrics.total_proposals || 0}</Typography>
              <Typography variant="body2" color="textSecondary">In pipeline</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2">Active Donors</Typography>
              <Typography variant="h5">{metrics.total_donors || 0}</Typography>
              <Typography variant="body2" color="textSecondary">Engaged donors</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2">Teams</Typography>
              <Typography variant="h5">{metrics.total_teams || 0}</Typography>
              <Typography variant="body2" color="textSecondary">Organizational coverage</Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Simple chart example */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Proposal Status</Typography>
          <Bar
            data{{
              labels: ['Draft', 'Review', 'Submitted', 'Approved'],
              datasets: [{
                label: 'Proposals',
                data: [12, 19, 8, 15],
                backgroundColor: [
                  UNHCR_PALETTE.yellow,
                  UNHCR_PALETTE.blue,
                  UNHCR_PALETTE.green,
                  UNHCR_PALETTE.darkBlue
                ]
              }]
            }}
            options={UNHCR_CHART_OPTIONS}
          />
        </Paper>
      </Box>
    </div>
  );
}
