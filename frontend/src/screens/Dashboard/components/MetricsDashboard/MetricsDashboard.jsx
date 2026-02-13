// --- MetricsDashboard: UNHCR Visual Identity Alignment ---
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
import { Box, MenuItem, Select, FormControl, InputLabel, Typography, Dialog, DialogTitle, DialogContent, IconButton, CircularProgress, Grid, Paper } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import CloseIcon from '@mui/icons-material/Close';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DatePicker } from '@mui/x-date-pickers';

import './metrics-dashboard.css';

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

// --- UNHCR Brand Constants ---
const UNHCR_PALETTE = {
  blue: '#0072BC',
  darkBlue: '#003A8F',
  lightBlue: '#4F9DD7',
  vLightBlue: '#D9E8F5',
  yellow: '#F2A900',
  orange: '#E87722',
  red: '#C6362B',
  green: '#4C8C2B',
  purple: '#6F4E9C',
  textPrimary: '#222222',
  textSecondary: '#555555',
  gridLight: '#E6E6E6',
  axisSubtle: '#BDBDBD',
  bg: '#FFFFFF'
};

const CATEGORICAL_PALETTE = [
  UNHCR_PALETTE.blue,
  UNHCR_PALETTE.lightBlue,
  UNHCR_PALETTE.darkBlue,
  UNHCR_PALETTE.yellow,
  UNHCR_PALETTE.orange
];

const formatUSD = (value) => {
  if (value === null || value === undefined) return '0';
  const val = Number(value);
  if (Math.abs(val) >= 1000000) {
    return (val / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  }
  if (Math.abs(val) >= 1000) {
    return (val / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  }
  return val.toLocaleString();
};

const UNHCR_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y', // Default to horizontal bars for better legibility
  plugins: {
    legend: {
      position: 'top',
      display: true,
      labels: {
        color: UNHCR_PALETTE.textSecondary,
        font: { family: '"Lato", "Source Sans Pro", "Arial", sans-serif', size: 12 }
      }
    },
    title: { display: false } // Managed by UI <h3>
  },
  scales: {
    x: {
      grid: { display: false, color: UNHCR_PALETTE.gridLight, drawBorder: false },
      ticks: {
        color: UNHCR_PALETTE.textSecondary,
        font: { family: '"Lato", "Source Sans Pro", "Arial", sans-serif' }
      },
      border: { display: false }
    },
    y: {
      grid: { display: false, color: UNHCR_PALETTE.gridLight, drawBorder: false },
      ticks: {
        color: UNHCR_PALETTE.textSecondary,
        font: { family: '"Lato", "Source Sans Pro", "Arial", sans-serif' }
      },
      border: { display: false }
    }
  }
};

const heatmapValuePlugin = {
  id: 'heatmapValuePlugin',
  afterDatasetsDraw(chart) {
    const { ctx, data } = chart;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = 'bold 10px Lato';
    data.datasets.forEach((dataset, datasetIndex) => {
      chart.getDatasetMeta(datasetIndex).data.forEach((element, index) => {
        const val = dataset.data[index].v;
        if (val > 0) {
          // Change text color based on cell "darkness" (alpha)
          const alpha = Math.min(val / 10, 1);
          ctx.fillStyle = alpha > 0.6 ? '#ffffff' : UNHCR_PALETTE.textPrimary;
          ctx.fillText(val, element.x, element.y);
        }
      });
    });
    ctx.restore();
  }
};

// --- Sub-components moved outside to prevent remounting ---

function MetricBar({ title, labels, data, onExpand, horizontal = true, isMultiColor = false, isHistogram = false }) {
  const cleanLabels = Array.from(new Set(labels)).filter(Boolean);
  const cleanData = cleanLabels.map(label => {
    const idx = labels.indexOf(label);
    return idx !== -1 ? data[idx] : 0;
  });

  const barData = {
    labels: cleanLabels,
    datasets: [{
      label: '', // Hide redundant dataset label
      data: cleanData,
      backgroundColor: isMultiColor
        ? cleanLabels.map((_, i) => CATEGORICAL_PALETTE[i % CATEGORICAL_PALETTE.length])
        : UNHCR_PALETTE.blue,
      borderRadius: 4
    }]
  };

  const options = {
    ...UNHCR_CHART_OPTIONS,
    indexAxis: horizontal ? 'y' : 'x',
    plugins: {
      ...UNHCR_CHART_OPTIONS.plugins,
      legend: { display: false } // No legend title unless strictly necessary
    },
    scales: {
      ...UNHCR_CHART_OPTIONS.scales,
      x: {
        ...UNHCR_CHART_OPTIONS.scales.x,
        grid: { display: horizontal, color: UNHCR_PALETTE.gridLight },
        ticks: {
          ...UNHCR_CHART_OPTIONS.scales.x.ticks,
          stepSize: isHistogram && horizontal ? 1 : undefined,
          callback: function (value) {
            return horizontal ? (isHistogram ? value : formatUSD(value)) : this.getLabelForValue(value);
          }
        }
      },
      y: {
        ...UNHCR_CHART_OPTIONS.scales.y,
        grid: { display: !horizontal, color: UNHCR_PALETTE.gridLight },
        ticks: {
          ...UNHCR_CHART_OPTIONS.scales.y.ticks,
          stepSize: isHistogram && !horizontal ? 1 : undefined,
          callback: function (value) {
            return !horizontal ? (isHistogram ? value : formatUSD(value)) : this.getLabelForValue(value);
          }
        }
      }
    }
  };

  return (
    <div className="metric-card">
      <h3>{title}</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title, type: 'bar', data: barData, horizontal })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {cleanLabels.length === 0 || cleanData.every(v => v === 0) ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Bar data={barData} options={options} />
        )}
      </div>
    </div>
  );
}

function MetricHeatmap({ title, data, onExpand }) {
  const filteredData = data.filter(d => d.count > 0);
  const donors = Array.from(new Set(filteredData.map(d => d.donor)));
  const outcomes = Array.from(new Set(filteredData.map(d => d.outcome)));

  const heatmapData = {
    datasets: [{
      label: 'Outcome References',
      data: filteredData.map(d => ({
        x: d.donor,
        y: d.outcome,
        v: d.count
      })),
      backgroundColor(context) {
        const value = context.dataset.data[context.dataIndex]?.v || 0;
        const alpha = Math.min(value / 10, 1);
        return `rgba(0, 114, 188, ${0.1 + alpha * 0.9})`; // UNHCR Blue with alpha
      },
      width: ({ chart }) => {
        const area = chart.chartArea || { width: 0, height: 0 };
        const cellWidth = area.width / (donors.length || 1);
        const cellHeight = area.height / (outcomes.length || 1);
        const size = Math.min(cellWidth, cellHeight) * 0.8;
        return Math.max(8, Math.min(40, size));
      },
      height: ({ chart }) => {
        const area = chart.chartArea || { width: 0, height: 0 };
        const cellWidth = area.width / (donors.length || 1);
        const cellHeight = area.height / (outcomes.length || 1);
        const size = Math.min(cellWidth, cellHeight) * 0.8;
        return Math.max(8, Math.min(40, size));
      },
      borderRadius: 0,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.5)'
    }]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => `Donor: ${items[0].raw.x}`,
          label: (item) => `Outcome: ${item.raw.y} - Count: ${item.raw.v}`
        }
      }
    },
    scales: {
      x: {
        type: 'category',
        labels: donors,
        grid: { display: false },
        ticks: {
          autoSkip: false,
          maxRotation: 45,
          minRotation: 45
        }
      },
      y: { type: 'category', labels: outcomes, grid: { display: false } }
    }
  };

  return (
    <div className="metric-card">
      <h3>Donor to Outcome</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title: "Donor to Outcome", type: 'matrix', data: heatmapData, options })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {filteredData.length === 0 ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Chart type="matrix" data={heatmapData} options={options} plugins={[heatmapValuePlugin, MatrixController, MatrixElement]} />
        )}
      </div>
    </div>
  );
}

function MetricTreemap({ title, data, onExpand }) {
  const treemapData = {
    datasets: [{
      label: title,
      tree: data,
      key: 'total_value',
      groups: ['region', 'context'],
      spacing: 1,
      borderWidth: 0.5,
      borderColor: '#fff',
      backgroundColor(ctx) {
        if (ctx.type !== 'data') return 'transparent';
        const colorIndex = ctx.dataIndex % CATEGORICAL_PALETTE.length;
        return CATEGORICAL_PALETTE[colorIndex];
      },
      labels: {
        display: true,
        formatter: (ctx) => {
          if (ctx.type !== 'data') return '';
          const g = ctx.raw.g;
          const v = ctx.raw.v;
          return `${g}\n$${formatUSD(v)}`;
        },
        font: { size: 10, weight: 'bold' },
        color: '#fff'
      }
    }]
  };

  return (
    <div className="metric-card">
      <h3>{title}</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title, type: 'treemap', data: treemapData })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {data.length === 0 ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Chart
            type="treemap"
            data={treemapData}
            plugins={[TreemapController, TreemapElement]}
            options={{
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (item) => `${item.raw.g}: $${formatUSD(item.raw.v)} (UNHCR Region: ${item.raw.p || 'N/A'})`
                  }
                }
              },
              maintainAspectRatio: false
            }}
          />
        )}
      </div>
    </div>
  );
}

function MetricLine({ title, labels, data, onExpand }) {
  const cleanLabels = Array.from(new Set(labels)).filter(Boolean);
  const cleanData = cleanLabels.map(label => {
    const idx = labels.indexOf(label);
    return idx !== -1 ? data[idx] : 0;
  });

  const lineData = {
    labels: cleanLabels,
    datasets: [{
      label: title,
      data: cleanData,
      backgroundColor: 'transparent',
      borderColor: UNHCR_PALETTE.blue,
      pointBackgroundColor: UNHCR_PALETTE.darkBlue,
      fill: false,
      tension: 0.1
    }]
  };

  const options = {
    ...UNHCR_CHART_OPTIONS,
    indexAxis: 'x',
    plugins: {
      ...UNHCR_CHART_OPTIONS.plugins,
      legend: { display: false }
    }
  };

  return (
    <div className="metric-card">
      <h3>{title}</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title, type: 'line', data: lineData })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {cleanLabels.length === 0 || cleanData.every(v => v === 0) ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Line data={lineData} options={options} />
        )}
      </div>
    </div>
  );
}

const STATUS_COLORS = {
  'draft': UNHCR_PALETTE.vLightBlue,
  'in_review': UNHCR_PALETTE.yellow,
  'submitted': UNHCR_PALETTE.green,
  'approved': UNHCR_PALETTE.blue,
  'rejected': UNHCR_PALETTE.red,
  'deleted': '#555'
};

function MetricStackedBar({ title, data, onExpand }) {
  const teams = Array.from(new Set(data.map(d => d.team)));
  const orderedStatuses = ['draft', 'in_review', 'submitted', 'approved', 'rejected', 'deleted'];
  const activeStatuses = orderedStatuses.filter(s => data.some(d => d.status === s));

  const stackedData = {
    labels: teams,
    datasets: activeStatuses.map(status => ({
      label: status.replace('_', ' ').toUpperCase(),
      data: teams.map(team => {
        const item = data.find(d => d.team === team && d.status === status);
        return item ? item.value : 0;
      }),
      backgroundColor: STATUS_COLORS[status] || UNHCR_PALETTE.blue,
    }))
  };

  const options = {
    ...UNHCR_CHART_OPTIONS,
    indexAxis: 'y',
    scales: {
      x: {
        stacked: true,
        grid: { display: true, color: UNHCR_PALETTE.gridLight },
        ticks: { callback: (value) => formatUSD(value) }
      },
      y: { stacked: true, grid: { display: false } }
    }
  };

  return (
    <div className="metric-card">
      <h3>{title}</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title, type: 'bar', data: stackedData, options })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {data.length === 0 ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Bar data={stackedData} options={options} />
        )}
      </div>
    </div>
  );
}

function MetricStackedArea({ title, data, onExpand }) {
  const periods = Array.from(new Set(data.map(d => d.period))).sort();
  const orderedStatuses = ['draft', 'in_review', 'submitted'];

  // Calculate cumulative values across periods
  const activeStatuses = orderedStatuses.filter(s => data.some(d => d.status === s));
  const cumulativeData = {};
  activeStatuses.forEach(status => {
    let runningTotal = 0;
    cumulativeData[status] = periods.map(period => {
      const item = data.find(d => d.period === period && d.status === status);
      runningTotal += item ? item.value : 0;
      return runningTotal;
    });
  });

  const areaData = {
    labels: periods,
    datasets: activeStatuses.map(status => ({
      label: status.replace('_', ' ').toUpperCase(),
      data: cumulativeData[status],
      backgroundColor: (STATUS_COLORS[status] || UNHCR_PALETTE.blue) + '80',
      borderColor: STATUS_COLORS[status] || UNHCR_PALETTE.blue,
      fill: true,
      pointRadius: 2,
      tension: 0.3
    }))
  };

  const options = {
    ...UNHCR_CHART_OPTIONS,
    indexAxis: 'x',
    scales: {
      x: { grid: { display: false } }, // Line chart (indexAxis: 'x'), no vertical lines
      y: { stacked: true, grid: { display: true, color: UNHCR_PALETTE.gridLight }, ticks: { callback: (value) => formatUSD(value) } } // Horizontal lines for line chart
    }
  };

  return (
    <div className="metric-card">
      <h3>{title}</h3>
      <IconButton size="small" className="expand-btn" onClick={() => onExpand({ title, type: 'line', data: areaData, options })}>
        <ZoomInIcon fontSize="small" />
      </IconButton>
      <div className="chart-container">
        {data.length === 0 ? (
          <div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa', fontStyle: 'italic' }}>No data available</div>
        ) : (
          <Line data={areaData} options={options} />
        )}
      </div>
    </div>
  );
}

export default function MetricsDashboard() {
  // Unified filters
  const [filter, setFilter] = useState('all');
  const [dateStart, setDateStart] = useState(null);
  const [dateEnd, setDateEnd] = useState(null);

  // Unified status state
  const [loading, setLoading] = useState(true);
  const [expandedChart, setExpandedChart] = useState(null);

  // Single state object for all metrics to batch updates
  // Single state object for all metrics
  const [metrics, setMetrics] = useState({
    pipelineKpis: null,
    proposalsByDonor: [],
    proposalsByOutcome: [],
    proposalsByContext: [],
    proposalsByTeam: [],
    proposalsByTime: [],
    // Legacy mapping or placeholder for other sections if needed
    editActivity: { labels: [], data: [] },
    reviewerActivity: { labels: [], data: [] },
    knowledgeCardCounts: { labels: [], data: [] },
    knowledgeCardHistory: { labels: [], data: [] },
    referenceCounts: { labels: [], data: [] },
    referenceUsage: { labels: [], data: [] },
    referenceIssues: { labels: [], data: [] },
    cardEditFrequency: { labels: [], data: [] },
    cardImpactScore: { labels: [], data: [] },
    knowledgeSilos: { labels: [], data: [] }
  });

  const fetchMetric = useCallback(async (path, filterParams) => {
    try {
      const res = await fetch(`${API_BASE_URL}${path}${filterParams}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Error fetching ${path}:`, e);
    }
    return null;
  }, []);

  const fetchAllMetrics = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    const filterParams = `?filter_by=${filter}&date_start=${dateStart || ''}&date_end=${dateEnd || ''}`;

    try {
      const results = await Promise.all([
        fetchMetric('/metrics/pipeline-kpis', filterParams),
        fetchMetric('/metrics/proposals-by-donor', filterParams),
        fetchMetric('/metrics/proposals-by-outcome', filterParams),
        fetchMetric('/metrics/proposals-by-context', filterParams),
        fetchMetric('/metrics/proposals-by-team', filterParams),
        fetchMetric('/metrics/proposals-by-time', filterParams),
        fetchMetric('/metrics/edit-activity', filterParams),
        fetchMetric('/metrics/reviewer-activity', filterParams),
        fetchMetric('/metrics/knowledge-cards', filterParams),
        fetchMetric('/metrics/knowledge-cards-history', filterParams),
        fetchMetric('/metrics/reference', filterParams),
        fetchMetric('/metrics/reference-usage', filterParams),
        fetchMetric('/metrics/reference-issue', filterParams),
        fetchMetric('/metrics/card-edit-frequency', filterParams),
        fetchMetric('/metrics/card-impact-score', filterParams),
        fetchMetric('/metrics/knowledge-silos', filterParams)
      ]);

      setMetrics({
        pipelineKpis: results[0],
        proposalsByDonor: results[1] || [],
        proposalsByOutcome: results[2] || [],
        proposalsByContext: results[3] || [],
        proposalsByTeam: results[4] || [],
        proposalsByTime: results[5] || [],
        editActivity: { labels: results[6]?.labels || [], data: results[6]?.data || [] },
        reviewerActivity: { labels: results[7]?.labels || [], data: results[7]?.data || [] },
        knowledgeCardCounts: { labels: results[8]?.types || [], data: results[8]?.counts || [] },
        knowledgeCardHistory: { labels: results[9]?.card_ids || [], data: results[9]?.revisions || [] },
        referenceCounts: { labels: results[10]?.types || [], data: results[10]?.references || [] },
        referenceUsage: { labels: results[11]?.urls || [], data: results[11]?.usage_counts || [] },
        referenceIssues: { labels: results[12]?.error_types || [], data: results[12]?.counts || [] },
        cardEditFrequency: { labels: results[13]?.card_ids || [], data: results[13]?.edit_frequency || [] },
        cardImpactScore: { labels: results[14]?.card_ids || [], data: results[14]?.impact_scores || [] },
        knowledgeSilos: { labels: results[15]?.silo_teams || [], data: results[15]?.isolated_card_ids || [] }
      });
    } catch (error) {
      console.error("Metrics parallel fetch error:", error);
    } finally {
      setLoading(false);
    }
  }, [filter, dateStart, dateEnd, fetchMetric]);

  useEffect(() => {
    fetchAllMetrics(true);
    const poll = setInterval(() => fetchAllMetrics(false), 120000); // 2 minute refresh
    return () => clearInterval(poll);
  }, [fetchAllMetrics]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '400px', bgcolor: UNHCR_PALETTE.bg }}>
        <CircularProgress sx={{ color: UNHCR_PALETTE.blue }} />
      </Box>
    );
  }

  return (
    <div className="metrics-dashboard" style={{ backgroundColor: UNHCR_PALETTE.bg }}>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', p: 2 }}>
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DatePicker label="Start Date" value={dateStart} onChange={setDateStart} slotProps={{ textField: { size: 'small' } }} />
          <DatePicker label="End Date" value={dateEnd} onChange={setDateEnd} slotProps={{ textField: { size: 'small' } }} />
        </LocalizationProvider>
        <FormControl size="small" sx={{ minWidth: 150 }}><InputLabel>Scope</InputLabel>
          <Select value={filter} onChange={e => setFilter(e.target.value)} label="Scope">
            <MenuItem value="all">Global</MenuItem>
            <MenuItem value="team">Team</MenuItem>
            <MenuItem value="user">Me</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Section 1: Pipeline Management */}
      <Typography variant="h5" className="section-title">Pipeline Management</Typography>

      {/* KPI Row */}
      <Grid container spacing={2} sx={{ mb: 4, px: 2 }}>
        {[
          { label: 'Total Funding', value: `$${(metrics.pipelineKpis?.total_funding || 0).toLocaleString()}`, desc: 'Requested funding amount', color: UNHCR_PALETTE.darkBlue },
          { label: 'Active Proposals', value: metrics.pipelineKpis?.total_proposals || 0, desc: `Avg: $${(metrics.pipelineKpis?.avg_value || 0).toLocaleString()}`, color: UNHCR_PALETTE.blue },
          { label: 'Active Donors', value: metrics.pipelineKpis?.total_donors || 0, desc: 'Donors in pipeline', color: UNHCR_PALETTE.purple },
          { label: 'Org Coverage', value: `${metrics.pipelineKpis?.total_teams || 0} Teams`, desc: `${metrics.pipelineKpis?.total_users || 0} active users`, color: UNHCR_PALETTE.lightBlue },
          { label: 'Under Review', value: `${(metrics.pipelineKpis?.pct_under_review || 0).toFixed(1)}%`, desc: 'Of total proposals', color: UNHCR_PALETTE.yellow },
          { label: 'Submitted', value: `${(metrics.pipelineKpis?.pct_submitted || 0).toFixed(1)}%`, desc: 'Successfully submitted', color: UNHCR_PALETTE.green },
          { label: 'Deleted/Withdrawn', value: `${(metrics.pipelineKpis?.pct_deleted || 0).toFixed(1)}%`, desc: 'Pipeline churn', color: UNHCR_PALETTE.red },
          { label: 'Avg. Cycle Time', value: `${((metrics.pipelineKpis?.avg_cycle_time || 0) / 86400).toFixed(1)}d`, desc: 'Creation to submission', color: UNHCR_PALETTE.orange }
        ].map((kpi, i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <div className="metric-card kpi-card" style={{ minHeight: '140px', padding: '16px' }}>
              <h3 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>{kpi.label}</h3>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: kpi.color }}>{kpi.value}</div>
              <div className="metric-desc" style={{ marginTop: '4px' }}>{kpi.desc}</div>
            </div>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: 3, mb: 4, width: '100%', px: 2 }}>
        {/* Proposal by Donors */}
        <MetricBar
          title="Proposal Value by Donor"
          labels={metrics.proposalsByDonor.slice(0, 10).map(d => `${d.donor} (${d.proposal_count} prop, ${d.submitted_count} sub)`)}
          data={metrics.proposalsByDonor.slice(0, 10).map(d => d.total_value)}
          onExpand={() => setExpandedChart({
            title: "Proposals by Donor (All)",
            type: 'bar',
            data: {
              labels: metrics.proposalsByDonor.map(d => `${d.donor} (${d.proposal_count} prop, ${d.submitted_count} sub)`),
              datasets: [{
                label: 'Total Value ($)',
                data: metrics.proposalsByDonor.map(d => d.total_value),
                backgroundColor: UNHCR_PALETTE.blue,
                borderRadius: 4
              }]
            },
            horizontal: true
          })}
        />

        <MetricHeatmap title="Donor x Outcome Match" data={metrics.proposalsByOutcome} onExpand={setExpandedChart} />
        <MetricTreemap title="Value by Field Context & Region" data={metrics.proposalsByContext} onExpand={setExpandedChart} />
        <MetricStackedBar title="Team Pipeline Status" data={metrics.proposalsByTeam} onExpand={setExpandedChart} />
        <MetricStackedArea title="Pipeline Value Trend" data={metrics.proposalsByTime} onExpand={setExpandedChart} />
      </Box>

      {/* Section 2: Collaboration */}
      <Typography variant="h5" className="section-title">Collaboration</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 3, mb: 4, width: '100%', px: 2 }}>
        <MetricBar title="Edit Distribution (Proposals by # of Edits)" labels={metrics.editActivity.labels} data={metrics.editActivity.data} onExpand={setExpandedChart} isHistogram={true} />
        <MetricBar title="Review Distribution (Proposals by # of Reviews)" labels={metrics.reviewerActivity.labels} data={metrics.reviewerActivity.data} onExpand={setExpandedChart} isHistogram={true} />
      </Box>

      {/* Section 3: Knowledge Management */}
      <Typography variant="h5" className="section-title">Knowledge Management</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 3, mb: 4, width: '100%', px: 2 }}>
        <MetricBar title="Knowledge Cards by Type" labels={metrics.knowledgeCardCounts.labels} data={metrics.knowledgeCardCounts.data} onExpand={setExpandedChart} isMultiColor />
        <MetricBar title="Knowledge Card Revision Frequency" labels={metrics.knowledgeCardHistory.labels} data={metrics.knowledgeCardHistory.data} onExpand={setExpandedChart} />
        <MetricBar title="Reference Counts by Type" labels={metrics.referenceCounts.labels} data={metrics.referenceCounts.data} onExpand={setExpandedChart} />
        <MetricBar title="Reference Usage (reused URLs)" labels={metrics.referenceUsage.labels} data={metrics.referenceUsage.data} onExpand={setExpandedChart} />
        <MetricBar title="Reference Issues" labels={metrics.referenceIssues.labels} data={metrics.referenceIssues.data} onExpand={setExpandedChart} />
        <MetricBar title="Card Edit Frequency" labels={metrics.cardEditFrequency.labels} data={metrics.cardEditFrequency.data} onExpand={setExpandedChart} />
        <MetricBar title="Card Impact Score" labels={metrics.cardImpactScore.labels} data={metrics.cardImpactScore.data} onExpand={setExpandedChart} />
        <MetricBar title="Knowledge Silos by Team" labels={metrics.knowledgeSilos.labels} data={metrics.knowledgeSilos.data} onExpand={setExpandedChart} />
      </Box>

      {/* Modal for Expanded Chart */}
      <Dialog open={!!expandedChart} onClose={() => setExpandedChart(null)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontStyle: 'Lato' }}>
          {expandedChart?.title}
          <IconButton onClick={() => setExpandedChart(null)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ minHeight: '70vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: UNHCR_PALETTE.bg }}>
          {expandedChart && (
            <div style={{ width: '100%', height: '550px' }}>
              {(expandedChart.type === 'bar') && (
                <Bar
                  data={expandedChart.data}
                  options={expandedChart.options || {
                    ...UNHCR_CHART_OPTIONS,
                    indexAxis: expandedChart.horizontal ? 'y' : 'x',
                    maintainAspectRatio: false,
                    scales: {
                      ...UNHCR_CHART_OPTIONS.scales,
                      x: {
                        ...UNHCR_CHART_OPTIONS.scales.x,
                        grid: { display: !!expandedChart.horizontal },
                        ticks: {
                          ...UNHCR_CHART_OPTIONS.scales.x.ticks,
                          callback: function (value) {
                            return expandedChart.horizontal ? formatUSD(value) : this.getLabelForValue(value);
                          }
                        }
                      },
                      y: {
                        ...UNHCR_CHART_OPTIONS.scales.y,
                        grid: { display: !expandedChart.horizontal },
                        ticks: {
                          ...UNHCR_CHART_OPTIONS.scales.y.ticks,
                          callback: function (value) {
                            return !expandedChart.horizontal ? formatUSD(value) : this.getLabelForValue(value);
                          }
                        }
                      }
                    }
                  }}
                />
              )}
              {expandedChart.type === 'matrix' && (
                <Chart
                  type="matrix"
                  data={expandedChart.data}
                  options={expandedChart.options}
                  plugins={[heatmapValuePlugin, MatrixController, MatrixElement]}
                />
              )}
              {expandedChart.type === 'treemap' && (
                <Chart
                  type="treemap"
                  data={expandedChart.data}
                  plugins={[TreemapController, TreemapElement]}
                  options={{
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (item) => `${item.raw.g}: $${formatUSD(item.raw.v)} (UNHCR Region: ${item.raw.p || 'N/A'})`
                        }
                      }
                    },
                    maintainAspectRatio: false
                  }}
                />
              )}
              {expandedChart.type === 'line' && (
                <Line
                  data={expandedChart.data}
                  options={expandedChart.options || {
                    ...UNHCR_CHART_OPTIONS,
                    indexAxis: 'x',
                    maintainAspectRatio: false,
                    scales: {
                      ...UNHCR_CHART_OPTIONS.scales,
                      x: { ...UNHCR_CHART_OPTIONS.scales.x, grid: { display: false } },
                      y: {
                        ...UNHCR_CHART_OPTIONS.scales.y,
                        grid: { display: true },
                        ticks: { callback: (value) => formatUSD(value) }
                      }
                    }
                  }}
                />
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
