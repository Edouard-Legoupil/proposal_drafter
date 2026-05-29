import Base from '../../components/Base/Base'
import { useState, useEffect } from 'react'
import {
    Box,
    Typography,
    CircularProgress,
    Alert
} from '@mui/material'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import './QualityGate.css'
import AnalysisModal from '../../components/AnalysisModal/AnalysisModal'
import IncidentTable from './IncidentTable'
import QualificationSummary from './QualificationSummary'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function QualityGate() {
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

                {/* Qualification Summary Component */}
                <QualificationSummary
                    qualRules={qualRules}
                    qualData={qualData}
                    qualSortConfig={qualSortConfig}
                    qualSearch={qualSearch}
                    qualPage={qualPage}
                    qualRowsPerPage={qualRowsPerPage}
                    onQualSearchChange={(value) => {
                        setQualSearch(value)
                        setQualPage(0)
                    }}
                    onQualSort={requestQualSort}
                    onQualPageChange={handleQualPageChange}
                    onQualRowsPerPageChange={handleQualRowsPerPageChange}
                />

                {/* Incident Table Component */}
                <IncidentTable
                    incidents={incidents}
                    loading={loading}
                    error={error}
                    sortConfig={sortConfig}
                    selectedStatuses={selectedStatuses}
                    statusOptions={statusOptions}
                    isSystemAdmin={isSystemAdmin}
                    removingIncidentId={removingIncidentId}
                    analysisLoading={analysisLoading}
                    loadingReviewId={loadingReviewId}
                    onStatusFilterChange={handleStatusFilterChange}
                    onRequestSort={requestSort}
                    onRemoveIncident={handleRemoveIncident}
                    onLoadAnalysis={loadAnalysis}
                />
            </div>
            <AnalysisModal
                open={analysisModalOpen}
                onClose={() => setAnalysisModalOpen(false)}
                analysis={analysis}
            />
        </Base>
    )
}
