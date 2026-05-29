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
import QualificationDetailModal from './QualificationDetailModal'

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
    const [detailModalOpen, setDetailModalOpen] = useState(false)
    const [selectedTemplateId, setSelectedTemplateId] = useState(null)
    const [selectedTemplateName, setSelectedTemplateName] = useState('')
    const [currentRuleIndex, setCurrentRuleIndex] = useState(0)

    const handleQualPageChange = (event, newPage) => {
        setQualPage(newPage)
    }

    const handleQualRowsPerPageChange = (event) => {
        setQualRowsPerPage(parseInt(event.target.value, 10))
        setQualPage(0)
    }

    const statusOptions = ['submitted','pending','acknowledged','needs-more-info','resolved','removed']

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
                    onViewDetails={(templateId, templateName) => {
                        setSelectedTemplateId(templateId)
                        setSelectedTemplateName(templateName)
                        setCurrentRuleIndex(0)
                        setDetailModalOpen(true)
                    }}
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
            <QualificationDetailModal
                open={detailModalOpen}
                onClose={() => setDetailModalOpen(false)}
                templateName={selectedTemplateName}
                templateId={selectedTemplateId}
                qualRules={qualRules}
                qualResults={qualData.find(row => row.artifact_id === selectedTemplateId)?.results || []}
                currentRuleIndex={currentRuleIndex}
                onRuleChange={(newIndex) => setCurrentRuleIndex(newIndex)}
            />
        </Base>
    )
}
