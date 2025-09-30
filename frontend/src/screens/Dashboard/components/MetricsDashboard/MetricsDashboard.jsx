import './MetricsDashboard.css';
import { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function MetricsDashboard() {
    const [filter, setFilter] = useState('all'); // 'user', 'team', 'all'
    const [fundingStatusFilter, setFundingStatusFilter] = useState('all'); // 'all', 'approved'
    const [devTimeData, setDevTimeData] = useState(null);
    const [fundingData, setFundingData] = useState(null);
    const [interestData, setInterestData] = useState(null);
    const [averageFunding, setAverageFunding] = useState(null);
    const [proposalVolume, setProposalVolume] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAllMetrics = async () => {
            setLoading(true);
            try {
                const endpoints = [
                    `${API_BASE_URL}/metrics/development-time?filter_by=${filter}`,
                    `${API_BASE_URL}/metrics/funding-by-category?filter_by=${filter}`,
                    `${API_BASE_URL}/metrics/donor-interest?filter_by=${filter}`,
                    `${API_BASE_URL}/metrics/average-funding-amount?filter_by=${filter}&status=${fundingStatusFilter}`,
                    `${API_BASE_URL}/metrics/proposal-volume` // No filter for volume
                ];

                const [devTimeRes, fundingRes, interestRes, avgFundingRes, volumeRes] = await Promise.all(
                    endpoints.map(url => fetch(url, { credentials: 'include' }))
                );

                if (devTimeRes.ok) setDevTimeData((await devTimeRes.json()).data);
                if (fundingRes.ok) setFundingData((await fundingRes.json()).data);
                if (interestRes.ok) setInterestData((await interestRes.json()).data);
                if (avgFundingRes.ok) setAverageFunding((await avgFundingRes.json()));
                if (volumeRes.ok) setProposalVolume((await volumeRes.json()));

            } catch (error) {
                console.error("Error fetching metrics data:", error);
            }
            setLoading(false);
        };
        fetchAllMetrics();
    }, [filter, fundingStatusFilter]);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Chart Title',
            },
        },
    };

    const devTimeChartData = devTimeData ? {
        labels: devTimeData.map(d => d.status),
        datasets: [{
            label: 'Avg. Days in Status',
            data: devTimeData.map(d => (d.average_duration_seconds / 86400).toFixed(2)),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
        }]
    } : { labels: [], datasets: [] };

    const userVolumeChartData = proposalVolume ? {
        labels: proposalVolume.by_user.map(d => d.user_name),
        datasets: [{
            label: 'Proposals per User',
            data: proposalVolume.by_user.map(d => d.proposal_count),
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
        }]
    } : { labels: [], datasets: [] };

    const teamVolumeChartData = proposalVolume ? {
        labels: proposalVolume.by_team.map(d => d.team_name),
        datasets: [{
            label: 'Proposals per Team',
            data: proposalVolume.by_team.map(d => d.proposal_count),
            backgroundColor: 'rgba(153, 102, 255, 0.6)',
        }]
    } : { labels: [], datasets: [] };

    if (loading) {
        return <div className="metrics-loading">Loading metrics...</div>;
    }

    return (
        <div className="metrics-dashboard">
            <div className="metrics-header">
                <h2>Proposal Metrics</h2>
                <div className="metrics-filter">
                    <label htmlFor="metrics-filter-select">Filter by: </label>
                    <select id="metrics-filter-select" value={filter} onChange={e => setFilter(e.target.value)} data-testid="metrics-filter-select">
                        <option value="all">All Proposals</option>
                        <option value="team">My Team</option>
                        <option value="user">My Proposals</option>
                    </select>
                </div>
            </div>
            <div className="metrics-grid">
                <div className="metric-card metric-card-number">
                    <h3>Avg. Funding Amount</h3>
                    <div className="funding-filter">
                         <select value={fundingStatusFilter} onChange={e => setFundingStatusFilter(e.target.value)}>
                            <option value="all">All</option>
                            <option value="approved">Approved</option>
                        </select>
                    </div>
                    <p className="metric-value">
                        {averageFunding ? `$${Number(averageFunding.average_funding).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'}
                    </p>
                </div>
                <div className="metric-card">
                    <h3>Avg. Time in Status (Days)</h3>
                    {devTimeData && devTimeData.length > 0 ? <div className="chart-container"><Bar data={devTimeChartData} options={{...chartOptions, title: {display: true, text: 'Avg. Time in Status (Days)'}}} /></div> : <p>No data available.</p>}
                </div>
                <div className="metric-card">
                    <h3>Proposals per User</h3>
                    {proposalVolume && proposalVolume.by_user.length > 0 ? <div className="chart-container"><Bar data={userVolumeChartData} options={{...chartOptions, indexAxis: 'y', title: {display: true, text: 'Proposals per User'}}} /></div> : <p>No data available.</p>}
                </div>
                <div className="metric-card">
                    <h3>Proposals per Team</h3>
                    {proposalVolume && proposalVolume.by_team.length > 0 ? <div className="chart-container"><Bar data={teamVolumeChartData} options={{...chartOptions, indexAxis: 'y', title: {display: true, text: 'Proposals per Team'}}} /></div> : <p>No data available.</p>}
                </div>
            </div>
        </div>
    );
}
