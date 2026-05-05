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
    Alert,
    TableSortLabel,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Checkbox,
    ListItemText,
    OutlinedInput,
    TextField,
    TablePagination
} from '@mui/material'
import { useNavigate, Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTriangleExclamation, faCircleExclamation, faInfoCircle, faCheckCircle, faFilter, faSkullCrossbones, faExclamationTriangle, faExclamationCircle } from '@fortawesome/free-solid-svg-icons'
import './QualityGate.css'
import AnalysisModal from '../../components/AnalysisModal/AnalysisModal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function QualityGate() {
    const navigate = useNavigate()
    const [incidents, setIncidents] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
    const [isSystemAdmin, setIsSystemAdmin] = useState(false)
    const [removingIncidentId, setRemovingIncidentId] = useState(null)
    const defaultStatusFilters = ['submitted', 'pending', 'acknowledged', 'needs-more-info']
    const [selectedStatuses, setSelectedStatuses] = useState(defaultStatusFilters)
    const [qualRules, setQualRules] = useState([])
    const [qualData, setQualData] = useState([])
    const [qualSortConfig, setQualSortConfig] = useState({ key: null, direction: 'asc' })
    const [qualSearch, setQualSearch] = useState('')
    const [qualPage, setQualPage] = useState(0)
    const [qualRowsPerPage, setQualRowsPerPage] = useState(10)

    const [analysis, setAnalysis] = useState(null)
    const [analysisLoading, setAnalysisLoading] = useState(false)
    const [loadingReviewId, setLoadingReviewId] = useState(null)
    const [analysisModalOpen, setAnalysisModalOpen] = useState(false)

    const loadAnalysis = async (reviewId) => {
        setAnalysisLoading(true)
        setLoadingReviewId(reviewId)
        try {
            const resp = await fetch(`${API_BASE_URL}/reviews/${reviewId}/analysis`, { credentials: 'include' })
            if (!resp.ok) {
                if (resp.status === 404) {
                    window.alert('Analysis not completed yet.')
                } else {
                    window.alert('Failed to fetch analysis.')
                }
            } else {
                const data = await resp.json()
                setAnalysis(data)
                setAnalysisModalOpen(true)
            }
        } catch (err) {
            console.error('Error fetching analysis:', err)
            window.alert('Error fetching analysis.')
        } finally {
            setAnalysisLoading(false)
            setLoadingReviewId(null)
        }
    }

    const fetchQualityData = async (showLoader = true) => {
        if (showLoader) {
            setLoading(true)
        }
        try {
            const incidentsRes = await fetch(`${API_BASE_URL}/metrics/quality-incidents`, { credentials: 'include' })

            if (incidentsRes.ok) {
                const incidentsData = await incidentsRes.json()
                setIncidents(incidentsData)
                setError(null)
            } else {
                setError("Failed to fetch quality data")
            }
        } catch (err) {
            console.error("Error fetching quality data:", err)
            setError("Connection error")
        } finally {
            if (showLoader) {
                setLoading(false)
            }
        }
    }

    const fetchUserProfile = async () => {
        try {
            const profileRes = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' })
            if (profileRes.ok) {
                const profileData = await profileRes.json()
                const roles = profileData.user?.roles || []
                setIsSystemAdmin(roles.includes('system admin'))
            }
        } catch (err) {
            console.error('Error fetching profile:', err)
        }
    }

    const fetchQualificationStatus = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/qualification/status?template_type=proposal`, { credentials: 'include' })
            if (res.ok) {
                const { rules, data } = await res.json()
                setQualRules(rules)
                setQualData(data)
            }
        } catch (err) {
            console.error('Error fetching qualification status:', err)
        }
    }

    useEffect(() => {
        fetchQualityData()
        fetchUserProfile()
        fetchQualificationStatus()
    }, [])

    const handleStatusFilterChange = (event) => {
        const value = event.target.value
        setSelectedStatuses(typeof value === 'string' ? value.split(',') : value)
    }

    // Sorting function
    const requestSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const requestQualSort = (key) => {
        let direction = 'asc'
        if (qualSortConfig.key === key && qualSortConfig.direction === 'asc') {
            direction = 'desc'
        }
        setQualSortConfig({ key, direction })
    }

    const getFilteredAndSortedQualData = () => {
        const arr = Array.isArray(qualData) ? [...qualData] : []
        
        // Filter by search term (template name)
        let filtered = arr
        if (qualSearch) {
            const searchLower = qualSearch.toLowerCase()
            filtered = arr.filter(row => 
                (row.template_name || '').toLowerCase().includes(searchLower)
            )
        }
        
        // Sort
        if (qualSortConfig.key) {
            filtered.sort((a, b) => {
                let av, bv;
                if (qualSortConfig.key === 'overall') {
                    av = a.overall ? 1 : 0;
                    bv = b.overall ? 1 : 0;
                } else if (qualSortConfig.key === 'template_name') {
                    av = (a.template_name || '').toLowerCase();
                    bv = (b.template_name || '').toLowerCase();
                } else {
                    av = a.results[qualSortConfig.key] ? 1 : 0;
                    bv = b.results[qualSortConfig.key] ? 1 : 0;
                }
                
                if (av < bv) return qualSortConfig.direction === 'asc' ? -1 : 1
                if (av > bv) return qualSortConfig.direction === 'asc' ? 1 : -1
                return 0
            })
        }
        return filtered
    }
    
    const getQualDataForDisplay = () => {
        const filteredAndSorted = getFilteredAndSortedQualData()
        return filteredAndSorted.slice(
            qualPage * qualRowsPerPage,
            qualPage * qualRowsPerPage + qualRowsPerPage
        )
    }
    
    const handleQualPageChange = (event, newPage) => {
        setQualPage(newPage)
    }
    
    const handleQualRowsPerPageChange = (event) => {
        setQualRowsPerPage(parseInt(event.target.value, 10))
        setQualPage(0)
    }

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
            case 'P0': return faSkullCrossbones;
            case 'P1': return faExclamationTriangle;
            case 'P2': return faExclamationCircle;
            case 'P3': return faInfoCircle;
            default: return faInfoCircle;
        }
    }

    const getSourceLabel = (incident) => {
        if (!incident.source_type) return 'Unknown source'
        
        const typeLabels = {
            'proposal': 'Proposal',
            'knowledge_card': 'Knowledge Card',
            'template': 'Template'
        }
        
        const typeLabel = typeLabels[incident.source_type] || incident.source_type
        
        if (incident.source_name) {
            return `${typeLabel}: ${incident.source_name}`
        }
        
        // Fallback when no name is available
        return `${typeLabel} (ID: ${incident.source_id})`
    }

    const getSourceUrl = (incident) => {
        try {
            // Handle Donor Templates - use the incident ID to view the specific template
            if (incident.source_type === 'Donor Template') {
                if (incident.source_name) {
                    // Keep the .json extension for donor templates
                    return `/donor-templates/${incident.source_name}?type=file`;
                }
                return '/dashboard?tab=templates';
            }
            
            // Handle Knowledge Cards - use the source ID to view the specific card
            if (incident.source_type.includes('knowledge_card_') && incident.source_type.endsWith('_template.json')) {
                // Extract the type from the filename (e.g., "knowledge_card_donor_template.json" -> "donor")
                const typeMatch = incident.source_type.match(/knowledge_card_(\w+)_template\.json/);
                const cardType = typeMatch ? typeMatch[1] : 'donor';
                
                // Use the source ID to construct a direct URL to the knowledge card
                return `/knowledge-card/${incident.source_id}`;
            }
            
            // Handle Proposals - use the source ID to view the specific proposal through chat
            if (incident.source_type === 'Proposal') {
                // Use the source ID to construct a URL to the chat interface for this proposal
                return `/chat/${incident.source_id}`;
            }
            
            // Fallback for unknown types
            console.warn('Unknown source type pattern:', incident.source_type);
            return '/dashboard';
            
        } catch (error) {
            console.error('Error constructing URL for incident:', incident.incident_id || incident.id, error);
            return '/dashboard';
        }
    }

    const handleRemoveIncident = async (incident) => {
        if (!window.confirm('Remove this incident and hide it from all dashboards?')) return
        setRemovingIncidentId(incident.incident_id)
        try {
            const response = await fetch(`${API_BASE_URL}/metrics/quality-incidents/remove`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    incident_id: incident.incident_id,
                    artifact_type: incident.artifact_type || 'proposal'
                })
            })

            if (!response.ok) {
                const payload = await response.json().catch(() => ({}))
                throw new Error(payload.detail || 'Failed to remove incident')
            }

            await fetchQualityData(false)
        } catch (err) {
            console.error('Error removing incident:', err)
            window.alert(err.message || 'Unable to remove this comment')
        } finally {
            setRemovingIncidentId(null)
        }
    }

    // Process KPI for total by type
    const statusOptions = ['submitted','pending','acknowledged','needs-more-info','resolved','removed']

    const formatStatusLabel = (status) => {
        if (!status) return ''
        return status
            .split('-')
            .map(part => part.charAt(0).toUpperCase() + part.slice(1))
            .join(' ')
    }

    const filteredIncidents = incidents.filter(incident => {
        const status = incident.status ? incident.status.toLowerCase() : ''
        if (selectedStatuses.length === 0) return true
        return selectedStatuses.some(s => s.toLowerCase() === status)
    })

    const incidentsByType = filteredIncidents.reduce((acc, incident) => {
        const type = incident.type_of_comment || 'Unknown'
        acc[type] = (acc[type] || 0) + 1
        return acc
    }, {})

    const incidentsBySeverity = filteredIncidents.reduce((acc, incident) => {
        const severity = incident.severity || 'Unknown'
        acc[severity] = (acc[severity] || 0) + 1
        return acc
    }, {})

    const getSortedIncidents = () => {
        const sortableIncidents = [...filteredIncidents]
        if (sortConfig.key) {
            sortableIncidents.sort((a, b) => {
                const aValue = a[sortConfig.key]
                const bValue = b[sortConfig.key]
                if (aValue < bValue) {
                    return sortConfig.direction === 'asc' ? -1 : 1
                }
                if (aValue > bValue) {
                    return sortConfig.direction === 'asc' ? 1 : -1
                }
                return 0
            })
        }
        return sortableIncidents
    }

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
                </header>

                {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

                {/* Qualification Summary */}
                <Card className="qual-card glass" sx={{ mb: 4 }}>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>Qualification Summary</Typography>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                            Qualifications are automated structural and semantic rules evaluated against templates to guarantee compliance and quality standards.
                        </Typography>
                        <TextField
                            fullWidth
                            label="Search by Template Name"
                            variant="outlined"
                            size="small"
                            value={qualSearch}
                            onChange={(e) => {
                                setQualSearch(e.target.value)
                                setQualPage(0)
                            }}
                            sx={{ mb: 2 }}
                            placeholder="Type to filter templates..."
                        />
                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>
                                            <TableSortLabel
                                                active={qualSortConfig.key === 'template_name'}
                                                direction={qualSortConfig.direction}
                                                onClick={() => requestQualSort('template_name')}
                                            >
                                                Template Name
                                            </TableSortLabel>
                                        </TableCell>
                                        <TableCell>
                                            <TableSortLabel
                                                active={qualSortConfig.key === 'overall'}
                                                direction={qualSortConfig.direction}
                                                onClick={() => requestQualSort('overall')}
                                            >
                                                Status
                                            </TableSortLabel>
                                        </TableCell>
                                        {qualRules?.map(rule => (
                                            <TableCell key={rule.rule_code} title={rule.description}>
                                                <TableSortLabel
                                                    active={qualSortConfig.key === rule.rule_code}
                                                    direction={qualSortConfig.direction}
                                                    onClick={() => requestQualSort(rule.rule_code)}
                                                >
                                                    {`${rule.rule_code} - ${rule.rule_name}`}
                                                </TableSortLabel>
                                            </TableCell>
                                        ))}
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {getQualDataForDisplay()?.map(row => (
                                        <TableRow key={row.artifact_id} hover>
                                            <TableCell>
                                                {row.template_name || 'Unknown'}
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={row.overall ? 'PASS' : 'FAIL'}
                                                    size="small"
                                                    color={row.overall ? 'success' : 'error'}
                                                />
                                            </TableCell>
                                            {qualRules?.map(rule => (
                                                <TableCell key={rule.rule_code}>
                                                    <Chip
                                                        label={row.results[rule.rule_code] ? 'PASS' : 'FAIL'}
                                                        size="small"
                                                        color={row.results[rule.rule_code] ? 'success' : 'error'}
                                                    />
                                                </TableCell>
                                            ))}
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                        <TablePagination
                            rowsPerPageOptions={[5, 10, 25, 50, 100]}
                            component="div"
                            count={getFilteredAndSortedQualData().length}
                            rowsPerPage={qualRowsPerPage}
                            page={qualPage}
                            onPageChange={handleQualPageChange}
                            onRowsPerPageChange={handleQualRowsPerPageChange}
                            sx={{ mt: 2 }}
                        />
                    </CardContent>
                </Card>

                <Box sx={{ mb: 4, mt: 4 }}>
                    <Typography variant="h5" gutterBottom>Incident Monitoring</Typography>
                    <Typography variant="body2" color="textSecondary">
                        Unified monitoring of quality incidents across all proposal drafting workflows.
                    </Typography>
                </Box>

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
                            <div className="table-header-controls">
                            <FormControl size="small" sx={{ minWidth: 240 }} className="StatusFilter">
                                <InputLabel>Status</InputLabel>
                                <Select
                                    multiple
                                    value={selectedStatuses}
                                    onChange={handleStatusFilterChange}
                                    input={<OutlinedInput label="Status" />}
                                    renderValue={(selected) => (selected || []).map(formatStatusLabel).join(', ')}
                                >
                                    {statusOptions.map(option => (
                                        <MenuItem key={option} value={option}>
                                            <Checkbox checked={selectedStatuses.includes(option)} />
                                            <ListItemText primary={formatStatusLabel(option)} />
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </div>
                    </div>
                    <Table stickyHeader>
                        <TableHead>
                            <TableRow>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'severity'}
                                        direction={sortConfig.key === 'severity' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('severity')}
                                    >
                                        Severity
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'source_type'}
                                        direction={sortConfig.key === 'source_type' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('source_type')}
                                    >
                                        Source
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'section_name'}
                                        direction={sortConfig.key === 'section_name' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('section_name')}
                                    >
                                        Section
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'type_of_comment'}
                                        direction={sortConfig.key === 'type_of_comment' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('type_of_comment')}
                                    >
                                        Type
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'status'}
                                        direction={sortConfig.key === 'status' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('status')}
                                    >
                                        Status
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'reviewer_name'}
                                        direction={sortConfig.key === 'reviewer_name' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('reviewer_name')}
                                    >
                                        Reviewer
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={sortConfig.key === 'created_at'}
                                        direction={sortConfig.key === 'created_at' ? sortConfig.direction : 'asc'}
                                        onClick={() => requestSort('created_at')}
                                    >
                                        Date
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {getSortedIncidents().map((incident) => (
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
                                        {(() => {
                                            const url = getSourceUrl(incident);
                                            console.log('Source URL:', url, 'for incident:', incident);
                                            
                                            return (
                                                <Link
                                                    to={url}
                                                    className="source-link"
                                                    title={`View ${getSourceLabel(incident)}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{ 
                                                        display: 'block', 
                                                        color: 'inherit', 
                                                        textDecoration: 'none',
                                                        width: '100%'
                                                    }}
                                                >
                                                    <Typography variant="body2" sx={{ 
                                                        '&:hover': {
                                                            textDecoration: 'underline'
                                                        }
                                                    }}>
                                                        {getSourceLabel(incident)}
                                                    </Typography>
                                                </Link>
                                            );
                                        })()}
                                    </TableCell>
                                    <TableCell>{incident.section_name || '-'}</TableCell>
                                    <TableCell>
                                        <Chip label={incident.type_of_comment} variant="outlined" size="small" />
                                    </TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={incident.status || 'active'}
                                            size="small"
                                            sx={{
                                                bgcolor: incident.status === 'resolved' ? '#4caf50' : 
                                                       incident.status === 'acknowledged' ? '#2196f3' :
                                                       incident.status === 'needs-more-info' ? '#ff9800' :
                                                       '#9e9e9e',
                                                color: '#fff',
                                                fontWeight: 'bold'
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell className="review-text-cell" title={incident.review_text}>
                                        {incident.review_text}
                                    </TableCell>
                                    <TableCell>{incident.reviewer_name}</TableCell>
                                    <TableCell>{new Date(incident.created_at).toLocaleString()}</TableCell>
                                    <TableCell align="center">
                                        {isSystemAdmin && (
                                            <button
                                                className="QualityGate_removeButton"
                                                onClick={() => handleRemoveIncident(incident)}
                                                disabled={removingIncidentId === incident.incident_id}
                                            >
                                                {removingIncidentId === incident.incident_id ? 'Removing…' : 'Remove'}
                                            </button>
                                        )}
                                        <button
                                            type="button"
                                            className="QualityGate_viewAnalysisButton"
                                            onClick={() => loadAnalysis(incident.incident_id)}
                                            disabled={analysisLoading && loadingReviewId === incident.incident_id}
                                            style={{ marginLeft: isSystemAdmin ? '8px' : '0' }}
                                        >
                                            {analysisLoading && loadingReviewId === incident.incident_id ? 'Loading…' : 'View Analysis'}
                                        </button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {incidents.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={9} align="center">No quality incidents logged.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </div>
            <AnalysisModal
                open={analysisModalOpen}
                onClose={() => setAnalysisModalOpen(false)}
                analysis={analysis}
            />
        </Base>
    )
}
