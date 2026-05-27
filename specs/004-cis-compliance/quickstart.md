# CIS Compliance Quickstart Guide

## Introduction

This guide provides step-by-step instructions for implementing and using CIS compliance in the Proposal Drafter application. Follow these steps to assess your security posture, apply hardening measures, and maintain continuous compliance.

## Prerequisites

Before starting, ensure you have:

- **Administrator access** to the Proposal Drafter application
- **CIS-CAT Pro license** (or equivalent assessment tool)
- **Python 3.11+** installed
- **Docker** installed (for container assessments)
- **Access to CIS benchmarks** for your technology stack

## Installation

### 1. Install CIS Assessment Tools

```bash
# Download and install CIS-CAT Pro
wget https://downloads.cisecurity.org/cis-cat-pro-latest.zip
unzip cis-cat-pro-latest.zip
cd cis-cat-pro

# Install Python dependencies
pip install cis-compliance prometheus-client pydantic sqlalchemy
```

### 2. Configure Environment

```bash
# Set environment variables
export CIS_CAT_PATH="/opt/cis-cat-pro"
export CIS_BENCHMARKS_PATH="/opt/cis-benchmarks"
export COMPLIANCE_DB_URL="postgresql://compliance_user:secure_password@localhost:5432/proposal_drafter"
```

## Running Your First Assessment

### 3. Initiate CIS Assessment

```bash
# Run assessment against all areas
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/assess \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "benchmark_version": "latest",
    "scope": ["os", "database", "application", "network"],
    "notify": ["security-team@unhcr.org"]
  }'

# Expected response:
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "timestamp": "2026-07-14T10:30:00Z",
  "estimated_completion": "2026-07-14T11:00:00Z",
  "message": "CIS assessment initiated successfully"
}
```

### 4. Monitor Assessment Progress

```bash
# Check assessment status (run periodically)
curl -X GET https://api.proposal-drafter.unhcr.org/api/cis/assessments/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN"

# Look for status: "COMPLETE"
```

### 5. Review Assessment Results

```bash
# Get full assessment results with findings
curl -X GET "https://api.proposal-drafter.unhcr.org/api/cis/assessments/550e8400-e29b-41d4-a716-446655440000?include_findings=true&severity_filter=HIGH" \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Accept: application/vnd.cis-compliance.v1+json" | jq '.'

# Key metrics to review:
# - compliance_score: Overall compliance percentage
# - failed_controls: Number of failed controls
# - findings: Detailed list of issues by severity
```

## Applying Security Hardening

### 6. Review Non-Compliant Configurations

```bash
# List all non-compliant configurations
curl -X GET "https://api.proposal-drafter.unhcr.org/api/cis/configurations?compliance_status=NON_COMPLIANT" \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" | jq '.configurations[] | {key: .config_key, current: .config_value, expected: .cis_recommendation, severity: "HIGH"}'
```

### 7. Apply Hardening Measures

```bash
# Apply hardening to critical configurations
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/harden \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": ["os"],
    "backup": true,
    "dry_run": false
  }'

# Expected response:
{
  "operation_id": "9d8e7f6g-5h4i-3j2k-1l0m-9n8o7p6q5r4s",
  "status": "PENDING",
  "affected_configs": ["config_id_1", "config_id_2"],
  "changes_summary": {
    "os.password_expiration": {"old": "never", "new": "365"}
  },
  "backup_created": true,
  "rollback_available": true
}
```

### 8. Verify Hardening Results

```bash
# Run assessment again to verify improvements
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/assess \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["os"], "benchmark_version": "latest"}'

# Compare compliance scores before and after hardening
```

## Setting Up Continuous Monitoring

### 9. Configure Automated Scans

```bash
# Schedule daily compliance scans
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/assess \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": "0 2 * * *",  # Daily at 2 AM
    "scope": ["os", "database", "application"],
    "notify": ["security-team@unhcr.org", "devops-team@unhcr.org"]
  }'
```

### 10. Set Up Compliance Alerts

```bash
# Configure alerting for critical compliance issues
curl -X POST https://api.proposal-drafter.unhcr.org/api/webhooks/cis-alerts \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://alerting.unhcr.org/webhooks/cis",
    "events": ["compliance.alert.created"],
    "severity_filter": ["CRITICAL", "HIGH"]
  }'
```

### 11. Monitor Compliance Dashboard

```bash
# Access the compliance dashboard in the frontend
# URL: https://proposal-drafter.unhcr.org/compliance/dashboard

# Features available:
# - Real-time compliance score
# - Historical trends
# - Active alerts
# - Remediation progress
# - Configuration drift detection
```

## Generating Compliance Reports

### 12. Generate Quarterly Report

```bash
# Generate compliance report for audit purposes
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/reports \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "Q3 2026 CIS Compliance Report",
    "report_period_start": "2026-07-01T00:00:00Z",
    "report_period_end": "2026-09-30T23:59:59Z",
    "format": "pdf",
    "include_trends": true,
    "include_remediation_plans": true
  }'

# Expected response:
{
  "report_id": "8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t",
  "report_name": "Q3 2026 CIS Compliance Report",
  "status": "PENDING",
  "file_format": "pdf"
}
```

### 13. Download Report

```bash
# Check report status first
curl -X GET https://api.proposal-drafter.unhcr.org/api/cis/reports/8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN"

# When status is "COMPLETE", download the report
curl -X GET https://api.proposal-drafter.unhcr.org/api/cis/reports/8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t/download \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  --output "Q3_2026_CIS_Compliance_Report.pdf"

# Verify report integrity
echo "$(sha256sum Q3_2026_CIS_Compliance_Report.pdf)" | grep "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
```

## Advanced Operations

### 14. Rollback Hardening Changes

```bash
# Rollback a hardening operation if issues occur
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/operations/9d8e7f6g-5h4i-3j2k-1l0m-9n8o7p6q5r4s/rollback \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "verify_backup": true,
    "notify": ["security-team@unhcr.org"]
  }'
```

### 15. Manage Configuration Exemptions

```bash
# Apply exemption for a configuration that cannot be hardened
curl -X PATCH https://api.proposal-drafter.unhcr.org/api/cis/configurations/1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exemption_reason": "Legacy system dependency prevents hardening",
    "exemption_approved_by": "security-admin@unhcr.org",
    "exemption_expires": "2027-01-14T00:00:00Z"
  }'
```

### 16. Custom Benchmark Assessment

```bash
# Run custom assessment with specific benchmarks
python -m backend.scripts.cis_hardening assess \
  --benchmark "CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0" \
  --scope os \
  --output custom_assessment_results.json \
  --verbose
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Assessment fails to start**
```bash
# Check logs
journalctl -u proposal-drafter --since "1 hour ago" | grep cis_hardening

# Verify CIS-CAT Pro is accessible
ls -la /opt/cis-cat-pro/cis-cat.sh

# Check permissions
sudo chmod +x /opt/cis-cat-pro/cis-cat.sh
```

**Issue: Compliance score not improving**
```bash
# Check if hardening was actually applied
curl -X GET "https://api.proposal-drafter.unhcr.org/api/cis/configurations?compliance_status=NON_COMPLIANT" \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN"

# Verify manual changes were made
sudo grep "PASS_MAX_DAYS" /etc/login.defs

# Check for configuration conflicts
sudo systemctl status sshd
```

**Issue: Alerts not being generated**
```bash
# Check monitoring service status
sudo systemctl status cis-compliance-monitor

# Test alert generation
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/alerts/test \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN"

# Check webhook configuration
curl -X GET https://api.proposal-drafter.unhcr.org/api/webhooks \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN"
```

## Maintenance

### 17. Update CIS Benchmarks

```bash
# Download latest benchmarks
wget https://downloads.cisecurity.org/benchmarks/CIS_Ubuntu_Linux_22.04_LTS_Benchmark_v2.0.0.pdf
wget https://downloads.cisecurity.org/benchmarks/CIS_PostgreSQL_14_Benchmark_v1.1.0.pdf

# Update benchmark repository
python -m backend.scripts.cis_hardening update-benchmarks \
  --benchmarks-dir /opt/cis-benchmarks \
  --cleanup
```

### 18. Database Maintenance

```bash
# Clean up old compliance data (keep last 2 years)
python -m backend.scripts.cis_hardening cleanup \
  --older-than 730 \
  --dry-run

# Optimize database
psql -U compliance_user -d proposal_drafter -c "VACUUM ANALYZE cis_assessments;"
```

### 19. Backup and Restore

```bash
# Backup compliance data
pg_dump -U compliance_user -d proposal_drafter -t cis_* -f compliance_backup_$(date +%Y%m%d).sql

# Restore compliance data
psql -U compliance_user -d proposal_drafter -f compliance_backup_20260714.sql
```

## Best Practices

### Security Best Practices

1. **Regular Assessments**: Run CIS assessments monthly
2. **Prioritize Critical Findings**: Address HIGH/CRITICAL severity issues first
3. **Test Before Production**: Always test hardening in staging first
4. **Maintain Backups**: Create backups before major hardening operations
5. **Document Exemptions**: Clearly document why configurations are exempted
6. **Monitor Continuously**: Set up alerts for configuration drift
7. **Review Regularly**: Conduct quarterly compliance reviews

### Performance Best Practices

1. **Schedule During Low Traffic**: Run assessments during off-peak hours
2. **Limit Scope**: Focus on critical areas for frequent assessments
3. **Use Dry Runs**: Test hardening impact before applying changes
4. **Monitor Resource Usage**: Watch for increased CPU/memory during assessments
5. **Optimize Database**: Regularly clean up old assessment data

### Compliance Best Practices

1. **Maintain Audit Trail**: Keep records of all compliance operations
2. **Document Changes**: Record all hardening operations and their impact
3. **Regular Reporting**: Generate quarterly compliance reports
4. **Stay Updated**: Keep benchmarks and tools current
5. **Train Team**: Ensure security team is trained on CIS requirements
6. **Prepare for Audits**: Maintain organized compliance documentation

## Next Steps

After completing this quickstart guide:

1. **Review compliance dashboard** regularly
2. **Address critical findings** within SLA (2 days for CRITICAL, 7 days for HIGH)
3. **Schedule quarterly compliance reviews**
4. **Plan for formal CIS certification** within 12 months
5. **Integrate compliance checks** into CI/CD pipeline
6. **Train additional team members** on CIS compliance procedures

## Support

For issues not covered in this guide:

- **Documentation**: https://proposal-drafter.unhcr.org/docs/security/cis-compliance
- **API Reference**: https://proposal-drafter.unhcr.org/api/docs#tag/CIS-Compliance
- **Support Email**: security-support@unhcr.org
- **Slack Channel**: #security-compliance

## Glossary

- **CIS**: Center for Internet Security
- **Benchmark**: Set of security configuration recommendations
- **Control**: Individual security requirement
- **Finding**: Instance where a control is not met
- **Hardening**: Process of securing a system by reducing attack surface
- **Compliance Score**: Percentage of controls that are met
- **Drift**: Configuration changes that reduce compliance
- **Exemption**: Approved exception to a control requirement
