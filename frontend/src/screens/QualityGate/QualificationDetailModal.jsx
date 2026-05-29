import React from 'react'
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Chip,
    Box,
    IconButton,
    Stepper,
    Step,
    StepLabel,
    Divider,
    Paper
} from '@mui/material'
import { Close as CloseIcon, ArrowBack, ArrowForward } from '@mui/icons-material'
import './QualityGate.css'

export default function QualificationDetailModal({
    open,
    onClose,
    templateName,
    templateId,
    qualRules,
    qualResults,
    currentRuleIndex,
    onRuleChange
}) {
    if (!open || !qualRules || !qualResults || qualResults.length === 0) {
        return null
    }

    const currentRule = qualRules[currentRuleIndex]
    const currentResult = qualResults.find(r => r.rule_code === currentRule.rule_code) || {}
    
    const getStatusChip = (passed) => {
        return (
            <Chip
                label={passed ? 'PASS' : 'FAIL'}
                size="small"
                color={passed ? 'success' : 'error'}
                sx={{ fontWeight: 'bold' }}
            />
        )
    }

    const getSeverityChip = (severity) => {
        const severityColors = {
            'P0': { bgcolor: '#c0392b', label: 'CRITICAL' },
            'P1': { bgcolor: '#e67e22', label: 'MAJOR' },
            'P2': { bgcolor: '#2980b9', label: 'MINOR' },
            'P3': { bgcolor: '#27ae60', label: 'INFO' }
        }
        
        const config = severityColors[severity] || { bgcolor: '#7f8c8d', label: severity }
        return (
            <Chip
                label={config.label}
                size="small"
                sx={{ bgcolor: config.bgcolor, color: '#fff', fontWeight: 'bold' }}
            />
        )
    }

    const getUserFriendlyDescription = (rule) => {
        const descriptions = {
            'PROPOSAL_NO_UNRESOLVED_P0': {
                title: 'Critical Incident Check',
                description: 'This rule ensures there are no unresolved P0 (critical) incidents in the template. P0 incidents represent severe issues that could compromise the integrity or compliance of generated proposals.',
                whyItMatters: 'Critical incidents must be resolved before promotion to ensure proposal quality and regulatory compliance.',
                howToFix: 'Review all P0 incidents in the incident monitoring section and resolve them before re-running qualification.'
            },
            'PROPOSAL_MANDATORY_SECTIONS': {
                title: 'Mandatory Section Completeness',
                description: 'This rule verifies that all mandatory sections required by the template specification are present and properly structured.',
                whyItMatters: 'Missing mandatory sections could lead to incomplete proposals that fail to meet donor requirements.',
                howToFix: 'Review the template structure and ensure all required sections are defined in the template configuration.'
            },
            'PROPOSAL_MIN_SAMPLE_SIZE': {
                title: 'UAT Sample Size Validation',
                description: `This rule checks that the template has been tested with a sufficient number of UAT (User Acceptance Testing) samples.`,
                whyItMatters: 'Adequate testing ensures the template performs well across different scenarios and edge cases.',
                howToFix: 'Generate additional UAT proposals using the template and collect review feedback before re-running qualification.'
            },
            'PROPOSAL_AVG_SCORE': {
                title: 'Quality Score Threshold',
                description: 'This rule evaluates the average quality score across all UAT samples, using a weighted formula that considers incident severity.',
                whyItMatters: 'Consistent quality scores indicate reliable template performance and reduce the need for manual corrections.',
                howToFix: 'Improve template quality by addressing common P1 and P2 issues, enhancing section content, and refining prompt engineering.'
            },
            'PROPOSAL_MIN_SCENARIO_COUNT': {
                title: 'Scenario Coverage',
                description: 'This rule ensures the template has been tested across multiple distinct scenarios (donors, geographies, contexts).',
                whyItMatters: 'Diverse scenario testing helps identify template weaknesses and ensures adaptability to different use cases.',
                howToFix: 'Add missing scenario combinations to your UAT testing plan and generate proposals for each scenario.'
            }
        }

        return descriptions[rule.rule_code] || {
            title: rule.rule_name,
            description: rule.description || 'This rule evaluates a specific quality criterion for the template.',
            whyItMatters: 'Quality criteria ensure templates meet organizational standards and donor requirements.',
            howToFix: rule.remediation_guidance || 'Review the rule description and follow the recommended remediation steps.'
        }
    }

    const friendlyDesc = getUserFriendlyDescription(currentRule)

    return (
        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="md"
            className="qualification-detail-modal"
        >
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" component="div">
                    Qualification Details: {templateName}
                </Typography>
                <IconButton onClick={onClose} size="small">
                    <CloseIcon fontSize="small" />
                </IconButton>
            </DialogTitle>

            <DialogContent dividers>
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" color="textSecondary" gutterBottom>
                        Template ID: {templateId}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        {getStatusChip(currentResult.passed)}
                        {getSeverityChip(currentRule.severity)}
                        <Chip
                            label={currentRule.category}
                            size="small"
                            variant="outlined"
                        />
                    </Box>
                </Box>

                <Stepper activeStep={currentRuleIndex} alternativeLabel sx={{ mb: 3 }}>
                    {qualRules.map((rule, index) => (
                        <Step key={rule.rule_code} completed={qualResults.some(r => r.rule_code === rule.rule_code && r.passed)}>
                            <StepLabel
                                onClick={() => onRuleChange(index)}
                                style={{ cursor: 'pointer' }}
                            >
                                {rule.rule_code}
                            </StepLabel>
                        </Step>
                    ))}
                </Stepper>

                <Paper elevation={0} sx={{ p: 3, mb: 3, backgroundColor: 'background.paper' }}>
                    <Typography variant="h6" gutterBottom>
                        {friendlyDesc.title}
                    </Typography>

                    <Box sx={{ my: 2 }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                            Rule Code: {currentRule.rule_code}
                        </Typography>
                    </Box>

                    <Typography variant="body1" paragraph>
                        <strong>Description:</strong> {friendlyDesc.description}
                    </Typography>

                    <Typography variant="body1" paragraph>
                        <strong>Why it matters:</strong> {friendlyDesc.whyItMatters}
                    </Typography>

                    {currentResult.metric_name && (
                        <Box sx={{ my: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                            <Typography variant="body2" gutterBottom>
                                <strong>Metric Evaluation:</strong>
                            </Typography>
                            <Typography variant="body2">
                                {currentResult.metric_name}: {currentResult.metric_value}
                            </Typography>
                            <Typography variant="body2">
                                Threshold: {currentResult.comparator} {currentResult.threshold}
                            </Typography>
                        </Box>
                    )}

                    <Typography variant="body1" paragraph sx={{ mt: 2 }}>
                        <strong>How to fix:</strong> {friendlyDesc.howToFix}
                    </Typography>

                    {currentRule.remediation_guidance && (
                        <Typography variant="body2" color="textSecondary" paragraph>
                            <strong>Technical guidance:</strong> {currentRule.remediation_guidance}
                        </Typography>
                    )}
                </Paper>
            </DialogContent>

            <DialogActions sx={{ justifyContent: 'space-between', p: 2 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                        Rule {currentRuleIndex + 1} of {qualRules.length}
                    </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        onClick={() => onRuleChange(currentRuleIndex - 1)}
                        disabled={currentRuleIndex === 0}
                        startIcon={<ArrowBack />}
                        variant="outlined"
                    >
                        Previous
                    </Button>
                    <Button
                        onClick={() => onRuleChange(currentRuleIndex + 1)}
                        disabled={currentRuleIndex >= qualRules.length - 1}
                        endIcon={<ArrowForward />}
                        variant="contained"
                        color="primary"
                    >
                        Next
                    </Button>
                    <Button onClick={onClose} variant="outlined">
                        Close
                    </Button>
                </Box>
            </DialogActions>
        </Dialog>
    )
}