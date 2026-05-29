import React from 'react'
import {
    Box,
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    TextField,
    TableSortLabel,
    TablePagination,
    Button,
    Tooltip
} from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'
import './QualityGate.css'

export default function QualificationSummary({
    qualRules,
    qualData,
    qualSortConfig,
    qualSearch,
    qualPage,
    qualRowsPerPage,
    onQualSearchChange,
    onQualSort,
    onQualPageChange,
    onQualRowsPerPageChange,
    onViewDetails
}) {
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

    const getSummaryStats = (row) => {
        if (!qualRules || qualRules.length === 0) return { passed: 0, failed: 0 }
        
        const passed = qualRules.filter(rule => row.results[rule.rule_code]).length
        const failed = qualRules.filter(rule => !row.results[rule.rule_code]).length
        
        return { passed, failed }
    }

    return (
        <Card className="qual-card glass" sx={{ mb: 4 }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" gutterBottom>Qualification Summary</Typography>
                    <Tooltip title="Shows overall qualification status for templates with links to detailed criteria">
                        <InfoIcon color="action" fontSize="small" />
                    </Tooltip>
                </Box>
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
                        onQualSearchChange(e.target.value)
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
                                        onClick={() => onQualSort('template_name')}
                                    >
                                        Template Name
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>
                                    <TableSortLabel
                                        active={qualSortConfig.key === 'overall'}
                                        direction={qualSortConfig.direction}
                                        onClick={() => onQualSort('overall')}
                                    >
                                        Overall Status
                                    </TableSortLabel>
                                </TableCell>
                                <TableCell>Passed/Total Rules</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {getQualDataForDisplay()?.map(row => {
                                const stats = getSummaryStats(row)
                                return (
                                    <TableRow key={row.artifact_id} hover>
                                        <TableCell>
                                            {row.template_name || 'Unknown'}
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={row.overall ? 'QUALIFIED' : 'NOT QUALIFIED'}
                                                size="small"
                                                color={row.overall ? 'success' : 'error'}
                                                sx={{ fontWeight: 'bold' }}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {stats.passed}/{stats.passed + stats.failed} rules passed
                                            </Typography>
                                            {!row.overall && stats.failed > 0 && (
                                                <Chip
                                                    label={`${stats.failed} failed`}
                                                    size="small"
                                                    color="error"
                                                    sx={{ ml: 1, fontWeight: 'bold' }}
                                                />
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                onClick={() => onViewDetails(row.artifact_id, row.template_name)}
                                                disabled={!qualRules || qualRules.length === 0}
                                            >
                                                View Details
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                )
                            })}
                        </TableBody>
                    </Table>
                </TableContainer>
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25, 50, 100]}
                    component="div"
                    count={getFilteredAndSortedQualData().length}
                    rowsPerPage={qualRowsPerPage}
                    page={qualPage}
                    onPageChange={onQualPageChange}
                    onRowsPerPageChange={onQualRowsPerPageChange}
                    sx={{ mt: 2 }}
                />
            </CardContent>
        </Card>
    )
}
