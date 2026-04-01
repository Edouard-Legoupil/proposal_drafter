import Base from '../../components/Base/Base'
import { useState, useEffect } from 'react'
import { 
    Box, 
    Card, 
    CardContent, 
    Typography, 
    Grid, 
    Table, 
    TableBody, 
    TableCell, 
    TableContainer, 
    TableHead, 
    TableRow, 
    Paper,
    Chip,
    CircularProgress,
    Alert
} from '@mui/material'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTriangleExclamation, faCircleExclamation, faInfoCircle, faCheckCircle, faFilter } from '@fortawesome/free-solid-svg-icons'
import './QualityGate.css'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function QualityGate() {
    const [incidents, setIncidents] = useState([])
    const [kpis, setKpis] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [incidentsRes, kpisRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/metrics/quality-incidents`, { credentials: 'include' }),
                    fetch(`${API_BASE_URL}/metrics/quality-kpis`, { credentials: 'include' })
                ])

                if (incidentsRes.ok && kpisRes.ok) {
                    const incidentsData = await incidentsRes.json()
                    const kpisData = await kpisRes.json()
                    setIncidents(incidentsData)
                    setKpis(kpisData)
                } else {
                    setError("Failed to fetch quality data")
                }
            } catch (err) {
                console.error("Error fetching quality data:", err)
                setError("Connection error")
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const getSeverityColor = (sev) => {
        switch (sev) {
            case 'P0': return '#c0392b'
            case 'P1': return '#e67e22'
            case 'P2': return '#2980b9'
            case 'P3': return '#27ae60'
            default: return '#7f8c8d'
        }
    }

    const getSeverityIcon = (sev) => {
        switch (sev) {
            case 'P0': return faTriangleExclamation
            case 'P1': return faCircleExclamation
            case 'P2': return faInfoCircle
            case 'P3': return faCheckCircle
            default: return faInfoCircle
        }
    }

    // Process KPI for total by type
    const incidentsByType = kpis.reduce((acc, k) => {
        if (!acc[k.type]) acc[k.type] = 0
        acc[k.type] += parseInt(k.count)
        return acc
    }, {})

    // Process KPI for total by severity
    const incidentsBySeverity = kpis.reduce((acc, k) => {
        if (!acc[k.severity]) acc[k.severity] = 0
        acc[k.severity] += parseInt(k.count)
        return acc
    }, {})

    if (loading) return (
        <Base>
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
                <CircularProgress />
            </Box>
        </Base>
    )

    return (
        <Base>
            <div className="QualityGate">
                <header className="page-header">
                    <h1>Quality Management Gate</h1>
                    <Typography variant="body2" color="textSecondary">
                        Unified monitoring of quality incidents across all proposal drafting workflows.
                    </Typography>
                </header>

                {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

                {/* KPI Section */}
                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid item xs={12} md={6}>
                        <Card className="kpi-card glass">
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Incidents by Type</Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                                    {Object.entries(incidentsByType).length > 0 ? Object.entries(incidentsByType).map(([type, count]) => (
                                        <Box key={type} className="kpi-item">
                                            <Typography className="kpi-label">{type}</Typography>
                                            <Typography className="kpi-value">{count}</Typography>
                                        </Box>
                                    )) : <Typography color="textSecondary">No incidents found.</Typography>}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Card className="kpi-card glass">
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Incidents by Severity</Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                                    {['P0', 'P1', 'P2', 'P3'].map(sev => (
                                        <Box key={sev} className="kpi-item" style={{ borderLeft: `4px solid ${getSeverityColor(sev)}` }}>
                                            <Typography className="kpi-label">{sev}</Typography>
                                            <Typography className="kpi-value">{incidentsBySeverity[sev] || 0}</Typography>
                                        </Box>
                                    ))}
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Details Table */}
                <TableContainer component={Paper} className="incidents-table-container glass">
                    <div className="table-header">
                        <Typography variant="h6">Incident Details</Typography>
                        <div className="filter-group">
                             <FontAwesomeIcon icon={faFilter} />
                             <span>Latest {incidents.length} tickets</span>
                        </div>
                    </div>
                    <Table stickyHeader>
                        <TableHead>
                            <TableRow>
                                <TableCell>Severity</TableCell>
                                <TableCell>Source</TableCell>
                                <TableCell>Section</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Reviewer</TableCell>
                                <TableCell>Date</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {incidents.map((incident) => (
                                <TableRow key={incident.id} hover>
                                    <TableCell>
                                        <Chip 
                                            icon={<FontAwesomeIcon icon={getSeverityIcon(incident.severity)} style={{ color: '#fff' }} />}
                                            label={incident.severity}
                                            size="small"
                                            sx={{ 
                                                bgcolor: getSeverityColor(incident.severity), 
                                                color: '#fff',
                                                fontWeight: 'bold'
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Box>
                                            <Typography variant="body2" fontWeight="bold">{incident.source_type}</Typography>
                                            <Typography variant="caption" color="textSecondary">{incident.source_name}</Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>{incident.section_name || '-'}</TableCell>
                                    <TableCell>
                                        <Chip label={incident.type_of_comment} variant="outlined" size="small" />
                                    </TableCell>
                                    <TableCell className="review-text-cell" title={incident.review_text}>
                                        {incident.review_text}
                                    </TableCell>
                                    <TableCell>{incident.reviewer_name}</TableCell>
                                    <TableCell>{new Date(incident.created_at).toLocaleDateString()}</TableCell>
                                </TableRow>
                            ))}
                            {incidents.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={7} align="center">No quality incidents logged.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </div>
        </Base>
    )
}
