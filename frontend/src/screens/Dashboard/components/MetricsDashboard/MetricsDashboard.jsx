// --- MetricsDashboard: Full API Coverage with Unified Filters ---
import React, { useState, useEffect } from 'react';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, LineElement, PointElement } from 'chart.js';
import { Box, MenuItem, Select, FormControl, InputLabel, Typography, Dialog, DialogTitle, DialogContent, IconButton } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import CloseIcon from '@mui/icons-material/Close';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DatePicker } from '@mui/x-date-pickers';

import './metrics-dashboard.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, LineElement, PointElement);

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;


export default function MetricsDashboard() {
  // Unified filters
  const [filter, setFilter] = useState('all');
  const [dateStart, setDateStart] = useState(null);
  const [dateEnd, setDateEnd] = useState(null);

  // State for every metric endpoint
  const [avgFundingAmount, setAvgFundingAmount] = useState(null); // /metrics/average-funding-amount
  const [proposalsByCategory, setProposalsByCategory] = useState({ labels: [], data: [] }); // /metrics/proposal-volume
  const [donorInterest, setDonorInterest] = useState({ labels: [], data: [] }); // /metrics/donor-interest
  const [fundingByCategory, setFundingByCategory] = useState({ labels: [], data: [] }); // /metrics/funding-by-category
  const [devTimeData, setDevTimeData] = useState([]); // /metrics/development-time
  const [proposalTrend, setProposalTrend] = useState({ labels: [], datasets: [] }); // /metrics/proposal-trends
  const [conversionRate, setConversionRate] = useState(0); // /metrics/conversion-rate
  const [abandonmentRate, setAbandonmentRate] = useState({ rate: 0, total_abandoned: 0 }); // /metrics/abandonment-rate
  const [editActivity, setEditActivity] = useState({ labels: [], data: [] }); // /metrics/edit-activity
  const [reviewerActivity, setReviewerActivity] = useState({ labels: [], data: [] }); // /metrics/reviewer-activity
  const [knowledgeCardCounts, setKnowledgeCardCounts] = useState({ labels: [], data: [] }); // /metrics/knowledge-cards
  const [knowledgeCardHistory, setKnowledgeCardHistory] = useState({ labels: [], data: [] }); // /metrics/knowledge-cards-history
  const [referenceCounts, setReferenceCounts] = useState({ labels: [], data: [] }); // /metrics/reference
  const [referenceUsage, setReferenceUsage] = useState({ labels: [], data: [] }); // /metrics/reference-usage
  const [referenceIssues, setReferenceIssues] = useState({ labels: [], data: [] }); // /metrics/reference-issue
  const [cardEditFrequency, setCardEditFrequency] = useState({ labels: [], data: [] }); // /metrics/card-edit-frequency
  const [cardImpactScore, setCardImpactScore] = useState({ labels: [], data: [] }); // /metrics/card-impact-score
  const [knowledgeSilos, setKnowledgeSilos] = useState({ labels: [], data: [] }); // /metrics/knowledge-silos
  const [expandedChart, setExpandedChart] = useState(null); // { title, labels, data, type }

  const chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' }, title: { display: false } } };

  useEffect(() => {
    const fetchAllMetrics = async () => {
      // Helper for filter params
      const filterParams = `?filter_by=${filter}&date_start=${dateStart || ''}&date_end=${dateEnd || ''}`;
      try {
        // Avg Funding
        let res = await fetch(`${API_BASE_URL}/metrics/average-funding-amount${filterParams}`);
        setAvgFundingAmount(res.ok ? (await res.json()).amount : null);
        // Proposal Volume
        res = await fetch(`${API_BASE_URL}/metrics/proposal-volume${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setProposalsByCategory({ labels: data.categories, data: data.counts });
        }
        // Donor Interest
        res = await fetch(`${API_BASE_URL}/metrics/donor-interest${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setDonorInterest({ labels: data.donors, data: data.interest });
        }
        // Funding By Category
        res = await fetch(`${API_BASE_URL}/metrics/funding-by-category${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setFundingByCategory({ labels: data.categories, data: data.amounts });
        }
        // Development Time
        res = await fetch(`${API_BASE_URL}/metrics/development-time${filterParams}`);
        setDevTimeData(res.ok ? (await res.json()) : []);
        // Proposal Trends
        res = await fetch(`${API_BASE_URL}/metrics/proposal-trends${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setProposalTrend({ labels: data.timeline, datasets: [{ label: 'Proposals', data: data.counts }] });
        }
        // Conversion Rate
        res = await fetch(`${API_BASE_URL}/metrics/conversion-rate${filterParams}`);
        setConversionRate(res.ok ? (await res.json()).rate : 0);
        // Abandonment Rate
        res = await fetch(`${API_BASE_URL}/metrics/abandonment-rate${filterParams}`);
        setAbandonmentRate(res.ok ? (await res.json()) : { rate: 0, total_abandoned: 0 });
        // Edit Activity
        res = await fetch(`${API_BASE_URL}/metrics/edit-activity${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setEditActivity({ labels: data.authors, data: data.edit_counts });
        }
        // Reviewer Activity
        res = await fetch(`${API_BASE_URL}/metrics/reviewer-activity${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setReviewerActivity({ labels: data.reviewers, data: data.reviews });
        }
        // Knowledge Card Counts
        res = await fetch(`${API_BASE_URL}/metrics/knowledge-cards${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setKnowledgeCardCounts({ labels: data.types, data: data.counts });
        }
        // Knowledge Card History
        res = await fetch(`${API_BASE_URL}/metrics/knowledge-cards-history${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setKnowledgeCardHistory({ labels: data.card_ids, data: data.revisions });
        }
        // Reference Counts
        res = await fetch(`${API_BASE_URL}/metrics/reference${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setReferenceCounts({ labels: data.types, data: data.references });
        }
        // Reference Usage
        res = await fetch(`${API_BASE_URL}/metrics/reference-usage${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setReferenceUsage({ labels: data.urls, data: data.usage_counts });
        }
        // Reference Issues
        res = await fetch(`${API_BASE_URL}/metrics/reference-issue${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setReferenceIssues({ labels: data.error_types, data: data.counts });
        }
        // Card Edit Frequency
        res = await fetch(`${API_BASE_URL}/metrics/card-edit-frequency${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setCardEditFrequency({ labels: data.card_ids, data: data.edit_frequency });
        }
        // Card Impact Score
        res = await fetch(`${API_BASE_URL}/metrics/card-impact-score${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setCardImpactScore({ labels: data.card_ids, data: data.impact_scores });
        }
        // Knowledge Silos
        res = await fetch(`${API_BASE_URL}/metrics/knowledge-silos${filterParams}`);
        if (res.ok) {
          const data = await res.json();
          setKnowledgeSilos({ labels: data.silo_teams, data: data.isolated_card_ids });
        }
      } catch (error) {
        console.error("Metrics fetch error:", error);
        // Mark all metrics as unavailable or empty
        setAvgFundingAmount(null);
        setProposalsByCategory({ labels: [], data: [] });
        setDonorInterest({ labels: [], data: [] });
        setFundingByCategory({ labels: [], data: [] });
        setDevTimeData([]);
        setProposalTrend({ labels: [], datasets: [] });
        setConversionRate(0);
        setAbandonmentRate({ rate: 0, total_abandoned: 0 });
        setEditActivity({ labels: [], data: [] });
        setReviewerActivity({ labels: [], data: [] });
        setKnowledgeCardCounts({ labels: [], data: [] });
        setKnowledgeCardHistory({ labels: [], data: [] });
        setReferenceCounts({ labels: [], data: [] });
        setReferenceUsage({ labels: [], data: [] });
        setReferenceIssues({ labels: [], data: [] });
        setCardEditFrequency({ labels: [], data: [] });
        setCardImpactScore({ labels: [], data: [] });
        setKnowledgeSilos({ labels: [], data: [] });
      }
    };
    fetchAllMetrics();
    const poll = setInterval(fetchAllMetrics, 60000);
    return () => clearInterval(poll);
  }, [filter, dateStart, dateEnd]);


  // Chart rendering component for each metric with deduplication
  function MetricPie({ title, labels, data }) {
    const cleanLabels = Array.from(new Set(labels)).filter(Boolean);
    const cleanData = cleanLabels.map(label => {
      const idx = labels.indexOf(label);
      return idx !== -1 ? data[idx] : 0;
    });
    const pieData = { labels: cleanLabels, datasets: [{ label: title, data: cleanData, backgroundColor: cleanLabels.map((_, i) => `hsl(${(i * 33) % 360},70%,70%)`) }] };
    return (
      <div className="metric-card">
        <h3>{title}</h3>
        <IconButton size="small" className="expand-btn" onClick={() => setExpandedChart({ title, type: 'pie', data: pieData })}>
          <ZoomInIcon fontSize="small" />
        </IconButton>
        <div className="chart-container">
          {cleanLabels.length === 0 || cleanData.every(v => v === 0) ? (<div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa' }}>No data available</div>) : (<Pie data={pieData} options={chartOptions} />)}
        </div>
      </div>
    );
  }

  function MetricBar({ title, labels, data }) {
    const cleanLabels = Array.from(new Set(labels)).filter(Boolean);
    const cleanData = cleanLabels.map(label => {
      const idx = labels.indexOf(label);
      return idx !== -1 ? data[idx] : 0;
    });
    const barData = { labels: cleanLabels, datasets: [{ label: title, data: cleanData, backgroundColor: 'rgba(30,128,220,0.55)' }] };
    return (
      <div className="metric-card">
        <h3>{title}</h3>
        <IconButton size="small" className="expand-btn" onClick={() => setExpandedChart({ title, type: 'bar', data: barData })}>
          <ZoomInIcon fontSize="small" />
        </IconButton>
        <div className="chart-container">
          {cleanLabels.length === 0 || cleanData.every(v => v === 0) ? (<div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa' }}>No data available</div>) : (<Bar data={barData} options={chartOptions} />)}
        </div>
      </div>
    );
  }

  function MetricLine({ title, labels, data }) {
    const cleanLabels = Array.from(new Set(labels)).filter(Boolean);
    const cleanData = cleanLabels.map(label => {
      const idx = labels.indexOf(label);
      return idx !== -1 ? data[idx] : 0;
    });
    const lineData = { labels: cleanLabels, datasets: [{ label: title, data: cleanData, backgroundColor: 'rgba(40,180,100,0.4)', borderColor: 'rgba(40,180,100,1)', fill: false, tension: 0.1 }] };
    return (
      <div className="metric-card">
        <h3>{title}</h3>
        <IconButton size="small" className="expand-btn" onClick={() => setExpandedChart({ title, type: 'line', data: lineData })}>
          <ZoomInIcon fontSize="small" />
        </IconButton>
        <div className="chart-container">
          {cleanLabels.length === 0 || cleanData.every(v => v === 0) ? (<div style={{ margin: '32px 0', textAlign: 'center', color: '#aaa' }}>No data available</div>) : (<Line data={lineData} options={chartOptions} />)}
        </div>
      </div>
    );
  }



  return (
    <div className="metrics-dashboard">
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
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
      <Typography variant="h5" sx={{ mt: 4, mb: 2, fontWeight: 'bold', color: '#1a237e' }}>Pipeline Management</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 2, mb: 4, width: '100%' }}>
        <div className="metric-card"><h3>Average Funding Amount</h3><div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: '#1565c0', margin: '10px 0' }}>{avgFundingAmount === null ? 'Loading…' : `$${avgFundingAmount.toLocaleString()}`}</div></div>
        <MetricPie title="Proposals by Category" labels={proposalsByCategory.labels} data={proposalsByCategory.data} />
        <MetricBar title="Donor Interest" labels={donorInterest.labels} data={donorInterest.data} />
        <MetricPie title="Funding by Category" labels={fundingByCategory.labels} data={fundingByCategory.data} />
        <MetricBar title="Avg. Time in Status (Days)" labels={devTimeData.map(d => d.status)} data={devTimeData.map(d => +(d.average_duration_seconds / 86400).toFixed(2))} />
        <MetricLine title="Proposal Submissions Trend" labels={proposalTrend.labels} data={proposalTrend.datasets.length > 0 ? proposalTrend.datasets[0].data : []} />
        <div className="metric-card"><h3>Conversion Rate</h3><div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#388e3c' }}>{(conversionRate * 100).toFixed(1)}%</div></div>
        <div className="metric-card"><h3>Abandonment Rate</h3><div style={{ fontSize: '2rem', color: '#d32f2f' }}>{(abandonmentRate.rate * 100).toFixed(2)}%<br />Total abandoned: {abandonmentRate.total_abandoned}</div></div>
      </Box>

      {/* Section 2: Collaboration */}
      <Typography variant="h5" sx={{ mt: 4, mb: 2, fontWeight: 'bold', color: '#1a237e' }}>Collaboration</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 2, mb: 4, width: '100%' }}>
        <MetricBar title="Edit Activity by Team/Author" labels={editActivity.labels} data={editActivity.data} />
        <MetricBar title="Reviewer Activity" labels={reviewerActivity.labels} data={reviewerActivity.data} />
      </Box>

      {/* Section 3: Knowledge Management */}
      <Typography variant="h5" sx={{ mt: 4, mb: 2, fontWeight: 'bold', color: '#1a237e' }}>Knowledge Management</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 2, mb: 4, width: '100%' }}>
        <MetricBar title="Knowledge Cards by Type" labels={knowledgeCardCounts.labels} data={knowledgeCardCounts.data} />
        <MetricBar title="Knowledge Card Revision Frequency" labels={knowledgeCardHistory.labels} data={knowledgeCardHistory.data} />
        <MetricBar title="Reference Counts by Type" labels={referenceCounts.labels} data={referenceCounts.data} />
        <MetricBar title="Reference Usage (reused URLs)" labels={referenceUsage.labels} data={referenceUsage.data} />
        <MetricBar title="Reference Issues" labels={referenceIssues.labels} data={referenceIssues.data} />
        <MetricBar title="Card Edit Frequency" labels={cardEditFrequency.labels} data={cardEditFrequency.data} />
        <MetricBar title="Card Impact Score" labels={cardImpactScore.labels} data={cardImpactScore.data} />
        <MetricBar title="Knowledge Silos by Team" labels={knowledgeSilos.labels} data={knowledgeSilos.data} />
      </Box>

      {/* Modal for Expanded Chart */}
      <Dialog open={!!expandedChart} onClose={() => setExpandedChart(null)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {expandedChart?.title}
          <IconButton onClick={() => setExpandedChart(null)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {expandedChart && (
            <div style={{ width: '100%', height: '500px' }}>
              {expandedChart.type === 'pie' && <Pie data={expandedChart.data} options={{ ...chartOptions, maintainAspectRatio: false }} />}
              {expandedChart.type === 'bar' && <Bar data={expandedChart.data} options={{ ...chartOptions, maintainAspectRatio: false }} />}
              {expandedChart.type === 'line' && <Line data={expandedChart.data} options={{ ...chartOptions, maintainAspectRatio: false }} />}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
