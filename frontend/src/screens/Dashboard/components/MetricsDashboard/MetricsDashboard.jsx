import './MetricsDashboard.css';
import { useState, useEffect } from 'react';
import { Bar, Pie } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function MetricsDashboard() {
    const [filter, setFilter] = useState('all'); // 'user', 'team', 'all'
    const [devTimeData, setDevTimeData] = useState(null);
    const [fundingData, setFundingData] = useState(null);
    const [interestData, setInterestData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAllMetrics = async () => {
            setLoading(true);
            try {
                const [devTimeRes, fundingRes, interestRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/metrics/development-time?filter_by=${filter}`, { credentials: 'include' }),
                    fetch(`${API_BASE_URL}/metrics/funding-by-category?filter_by=${filter}`, { credentials: 'include' }),
                    fetch(`${API_BASE_URL}/metrics/donor-interest?filter_by=${filter}`, { credentials: 'include' })
                ]);

                if (devTimeRes.ok) setDevTimeData((await devTimeRes.json()).data);
                if (fundingRes.ok) setFundingData((await fundingRes.json()).data);
                if (interestRes.ok) setInterestData((await interestRes.json()).data);

            } catch (error) {
                console.error("Error fetching metrics data:", error);
            }
            setLoading(false);
        };
        fetchAllMetrics();
    }, [filter]);

    // Placeholder for chart data processing
    const devTimeChartData = devTimeData ? {
        labels: devTimeData.map(d => d.status),
        datasets: [{
            label: 'Avg. Days in Status',
            data: devTimeData.map(d => (d.average_duration_seconds / 86400).toFixed(2)),
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
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
                    <select id="metrics-filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
                        <option value="all">All Proposals</option>
                        <option value="team">My Team</option>
                        <option value="user">My Proposals</option>
                    </select>
                </div>
            </div>
            <div className="metrics-grid">
                <div className="metric-card">
                    <h3>Avg. Time in Status (Days)</h3>
                    {devTimeData && devTimeData.length > 0 ? <Bar data={devTimeChartData} /> : <p>No data available.</p>}
                </div>
                <div className="metric-card">
                    <h3>Proposals by Category</h3>
                    {/* Placeholder for Funding Chart */}
                    <p>Funding chart coming soon.</p>
                </div>
                <div className="metric-card">
                    <h3>Donor Interest</h3>
                    {/* Placeholder for Interest Chart */}
                    <p>Donor interest chart coming soon.</p>
                </div>
            </div>
        </div>
    );
}
