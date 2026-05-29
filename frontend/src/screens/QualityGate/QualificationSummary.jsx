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
    TablePagination
} from '@mui/material'
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
    onQualRowsPerPageChange
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

    return (
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
                                        Status
                                    </TableSortLabel>
                                </TableCell>
                                {qualRules?.map(rule => (
                                    <TableCell key={rule.rule_code} title={rule.description}>
                                        <TableSortLabel
                                            active={qualSortConfig.key === rule.rule_code}
                                            direction={qualSortConfig.direction}
                                            onClick={() => onQualSort(rule.rule_code)}
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
                    onPageChange={onQualPageChange}
                    onRowsPerPageChange={onQualRowsPerPageChange}
                    sx={{ mt: 2 }}
                />
            </CardContent>
        </Card>
    )
}