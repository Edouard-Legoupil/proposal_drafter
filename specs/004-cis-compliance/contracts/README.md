# CIS Compliance API Contracts

## Overview

This document defines the API contracts for the CIS Compliance module in the Proposal Drafter application. The contracts specify the interfaces, data formats, and behaviors that clients can expect from the CIS compliance functionality.

## Base URL

```
https://api.proposal-drafter.unhcr.org/api/cis
```

## Authentication

All endpoints require authentication using the standard JWT authentication mechanism:

```http
Authorization: Bearer <jwt_token>
```

## API Endpoints

### 1. Run CIS Assessment

**Endpoint**: `POST /api/cis/assess`

**Description**: Initiate a CIS benchmark assessment against the current system configuration.

**Request Body**:
```json
{
  "benchmark_version": "1.0.0",
  "scope": ["os", "database", "application"],
  "schedule": "0 2 * * *",
  "notify": ["security-team@unhcr.org"]
}
```

**Request Parameters**:
- `benchmark_version` (string, optional): Specific CIS benchmark version to use. Default: "latest"
- `scope` (array, optional): Areas to assess. Options: ["os", "database", "application", "network", "container"]. Default: all areas
- `schedule` (string, optional): Cron expression for scheduled assessment. If omitted, runs immediately
- `notify` (array, optional): Email addresses to notify when assessment completes

**Response**:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "timestamp": "2026-07-14T10:30:00Z",
  "estimated_completion": "2026-07-14T11:00:00Z",
  "message": "CIS assessment initiated successfully"
}
```

**Response Codes**:
- `201 Created`: Assessment initiated successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `500 Internal Server Error`: Assessment initiation failed

**Error Responses**:
```json
{
  "error": {
    "code": "VAL_001",
    "message": "Invalid benchmark version specified",
    "details": "Version 1.0.0 not found. Available versions: 1.1.0, 1.2.0, 2.0.0"
  }
}
```

### 2. Get Assessment Results

**Endpoint**: `GET /api/cis/assessments/{assessment_id}`

**Description**: Retrieve the results of a specific CIS assessment.

**Path Parameters**:
- `assessment_id` (UUID, required): ID of the assessment to retrieve

**Query Parameters**:
- `include_findings` (boolean, optional): Include detailed findings. Default: false
- `severity_filter` (string, optional): Filter findings by severity (LOW, MEDIUM, HIGH, CRITICAL)

**Response**:
```json
{
  "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-07-14T10:30:00Z",
  "completed_timestamp": "2026-07-14T11:00:00Z",
  "benchmark_version": "2.0.0",
  "compliance_score": 85.5,
  "total_controls": 120,
  "passed_controls": 102,
  "failed_controls": 18,
  "status": "COMPLETE",
  "duration_seconds": 1800,
  "assessed_by": "system",
  "findings": [
    {
      "finding_id": "7c6f1b9f-3c3a-4b9e-9d1a-5b5d7c7e8f9g",
      "control_id": "5.1.1",
      "control_description": "Ensure password expiration is set to 365 days or less",
      "control_category": "Account Policy",
      "current_value": "never",
      "expected_value": "365",
      "severity": "HIGH",
      "remediation": "Set password expiration policy to 365 days in /etc/login.defs",
      "status": "FAIL",
      "first_detected": "2026-07-14T10:35:00Z",
      "last_updated": "2026-07-14T10:35:00Z"
    }
  ]
}
```

**Response Codes**:
- `200 OK`: Assessment retrieved successfully
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `404 Not Found`: Assessment not found
- `500 Internal Server Error`: Failed to retrieve assessment

### 3. List Security Configurations

**Endpoint**: `GET /api/cis/configurations`

**Description**: Retrieve all security configurations with their compliance status.

**Query Parameters**:
- `compliance_status` (string, optional): Filter by compliance status (COMPLIANT, NON_COMPLIANT, PENDING, EXEMPT)
- `config_type` (string, optional): Filter by configuration type (OS, DATABASE, APPLICATION, NETWORK, CONTAINER)
- `search` (string, optional): Search term for configuration keys or descriptions
- `limit` (integer, optional): Maximum number of results. Default: 100
- `offset` (integer, optional): Pagination offset. Default: 0

**Response**:
```json
{
  "total_count": 42,
  "limit": 100,
  "offset": 0,
  "configurations": [
    {
      "config_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
      "config_key": "os.password_expiration",
      "config_value": "never",
      "cis_recommendation": "365",
      "compliance_status": "NON_COMPLIANT",
      "config_type": "OS",
      "config_source": "/etc/login.defs",
      "last_assessed": "2026-07-14T10:30:00Z",
      "last_modified": "2026-01-15T09:25:00Z",
      "modified_by": "system"
    },
    {
      "config_id": "2b3c4d5e-6f7g-8h9i-0j1k-2l3m4n5o6p7q",
      "config_key": "db.ssl_enabled",
      "config_value": "on",
      "cis_recommendation": "on",
      "compliance_status": "COMPLIANT",
      "config_type": "DATABASE",
      "config_source": "postgresql.conf",
      "last_assessed": "2026-07-14T10:30:00Z",
      "last_modified": "2026-03-20T14:15:00Z",
      "modified_by": "admin@unhcr.org"
    }
  ]
}
```

**Response Codes**:
- `200 OK`: Configurations retrieved successfully
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `500 Internal Server Error`: Failed to retrieve configurations

### 4. Apply Security Hardening

**Endpoint**: `POST /api/cis/harden`

**Description**: Apply CIS-recommended security hardening to specified configurations.

**Request Body**:
```json
{
  "config_ids": ["1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p"],
  "scope": ["os"],
  "dry_run": false,
  "backup": true,
  "schedule": "2026-07-15T02:00:00Z"
}
```

**Request Parameters**:
- `config_ids` (array, optional): Specific configuration IDs to harden. If omitted, hardens all non-compliant configs in scope
- `scope` (array, optional): Areas to harden. Options: ["os", "database", "application", "network", "container"]. Default: all areas
- `dry_run` (boolean, optional): Test without applying changes. Default: false
- `backup` (boolean, optional): Create backup before hardening. Default: true
- `schedule` (string, optional): ISO 8601 timestamp for scheduled execution. If omitted, runs immediately

**Response**:
```json
{
  "operation_id": "9d8e7f6g-5h4i-3j2k-1l0m-9n8o7p6q5r4s",
  "status": "PENDING",
  "affected_configs": ["1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p"],
  "changes_summary": {
    "os.password_expiration": {
      "old": "never",
      "new": "365"
    }
  },
  "backup_created": true,
  "backup_location": "/backups/cis-hardening-20260714-103000.tar.gz",
  "rollback_available": true,
  "rollback_instructions": "Run: python -m backend.scripts.cis_hardening rollback --operation 9d8e7f6g-5h4i-3j2k-1l0m-9n8o7p6q5r4s",
  "message": "Hardening operation scheduled for 2026-07-15T02:00:00Z"
}
```

**Response Codes**:
- `201 Created`: Hardening operation initiated successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `409 Conflict`: Conflicting hardening operation in progress
- `500 Internal Server Error`: Hardening operation initiation failed

### 5. Get Compliance Alerts

**Endpoint**: `GET /api/cis/alerts`

**Description**: Retrieve active compliance alerts that require attention.

**Query Parameters**:
- `status` (string, optional): Filter by alert status (OPEN, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE)
- `severity` (string, optional): Filter by severity (INFO, WARNING, CRITICAL)
- `limit` (integer, optional): Maximum number of results. Default: 50
- `offset` (integer, optional): Pagination offset. Default: 0
- `resolved` (boolean, optional): Filter resolved (true) or unresolved (false) alerts

**Response**:
```json
{
  "total_count": 5,
  "limit": 50,
  "offset": 0,
  "alerts": [
    {
      "alert_id": "3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r",
      "alert_timestamp": "2026-07-14T10:45:00Z",
      "severity": "CRITICAL",
      "affected_configuration": "os.password_expiration",
      "current_value": "never",
      "expected_value": "365",
      "remediation_steps": "Set PASS_MAX_DAYS=365 in /etc/login.defs and run 'passwd -x 365 username' for existing users",
      "status": "OPEN",
      "source": "AUTOMATED_SCAN"
    },
    {
      "alert_id": "4d5e6f7g-8h9i-0j1k-2l3m-4n5o6p7q8r9s",
      "alert_timestamp": "2026-07-13T15:20:00Z",
      "severity": "HIGH",
      "affected_configuration": "db.log_connections",
      "current_value": "off",
      "expected_value": "on",
      "remediation_steps": "Set log_connections = on in postgresql.conf and restart PostgreSQL service",
      "status": "ACKNOWLEDGED",
      "resolved_timestamp": null,
      "resolved_by": null,
      "source": "MANUAL_CHECK"
    }
  ]
}
```

**Response Codes**:
- `200 OK`: Alerts retrieved successfully
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `500 Internal Server Error`: Failed to retrieve alerts

### 6. Resolve Compliance Alert

**Endpoint**: `POST /api/cis/alerts/{alert_id}/resolve`

**Description**: Mark a compliance alert as resolved or provide resolution details.

**Path Parameters**:
- `alert_id` (UUID, required): ID of the alert to resolve

**Request Body**:
```json
{
  "status": "RESOLVED",
  "resolution_notes": "Applied recommended hardening. Password expiration set to 365 days.",
  "verify_fix": true
}
```

**Request Parameters**:
- `status` (string, required): New status for the alert (RESOLVED, FALSE_POSITIVE)
- `resolution_notes` (string, optional): Details about how the alert was resolved
- `verify_fix` (boolean, optional): Verify that the issue is actually fixed. Default: false

**Response**:
```json
{
  "alert_id": "3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r",
  "status": "RESOLVED",
  "resolved_timestamp": "2026-07-14T11:30:00Z",
  "resolved_by": "admin@unhcr.org",
  "resolution_notes": "Applied recommended hardening. Password expiration set to 365 days.",
  "verification_result": {
    "verified": true,
    "current_value": "365",
    "compliant": true
  }
}
```

**Response Codes**:
- `200 OK`: Alert resolved successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `404 Not Found`: Alert not found
- `409 Conflict`: Alert already resolved
- `500 Internal Server Error`: Failed to resolve alert

### 7. Generate Compliance Report

**Endpoint**: `POST /api/cis/reports`

**Description**: Generate a formal compliance report for audit purposes.

**Request Body**:
```json
{
  "report_name": "Q3 2026 CIS Compliance Report",
  "report_period_start": "2026-07-01T00:00:00Z",
  "report_period_end": "2026-09-30T23:59:59Z",
  "format": "pdf",
  "include_assessments": ["550e8400-e29b-41d4-a716-446655440000"],
  "include_trends": true,
  "include_remediation_plans": true
}
```

**Request Parameters**:
- `report_name` (string, required): Name for the compliance report
- `report_period_start` (string, required): Start date for report period (ISO 8601)
- `report_period_end` (string, required): End date for report period (ISO 8601)
- `format` (string, required): Report format (pdf, json, csv, html)
- `include_assessments` (array, optional): Specific assessment IDs to include. If omitted, includes all assessments in period
- `include_trends` (boolean, optional): Include historical trends. Default: false
- `include_remediation_plans` (boolean, optional): Include detailed remediation plans. Default: false

**Response**:
```json
{
  "report_id": "8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t",
  "report_name": "Q3 2026 CIS Compliance Report",
  "generated_timestamp": "2026-07-14T11:45:00Z",
  "report_period_start": "2026-07-01T00:00:00Z",
  "report_period_end": "2026-09-30T23:59:59Z",
  "compliance_score": 87.2,
  "critical_findings": 3,
  "high_findings": 8,
  "medium_findings": 12,
  "low_findings": 22,
  "report_format": "pdf",
  "report_status": "DRAFT",
  "generated_by": "admin@unhcr.org",
  "file_path": "/reports/compliance/Q3-2026-CIS-Compliance-Report.pdf",
  "file_size": 1245678,
  "file_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

**Response Codes**:
- `201 Created`: Report generation initiated successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `500 Internal Server Error`: Report generation failed

### 8. Get Report Status

**Endpoint**: `GET /api/cis/reports/{report_id}`

**Description**: Check the status of a compliance report generation job.

**Path Parameters**:
- `report_id` (UUID, required): ID of the report to check

**Response**:
```json
{
  "report_id": "8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t",
  "report_name": "Q3 2026 CIS Compliance Report",
  "status": "COMPLETE",
  "generated_timestamp": "2026-07-14T11:45:00Z",
  "completed_timestamp": "2026-07-14T11:47:30Z",
  "file_path": "/reports/compliance/Q3-2026-CIS-Compliance-Report.pdf",
  "download_url": "https://api.proposal-drafter.unhcr.org/api/cis/reports/8e7f6g5h-4i3j-2k1l-0m9n-8o7p6q5r4s3t/download"
}
```

**Response Codes**:
- `200 OK`: Report status retrieved successfully
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `404 Not Found`: Report not found
- `500 Internal Server Error`: Failed to retrieve report status

### 9. Download Compliance Report

**Endpoint**: `GET /api/cis/reports/{report_id}/download`

**Description**: Download a generated compliance report file.

**Path Parameters**:
- `report_id` (UUID, required): ID of the report to download

**Response**:
- Binary file download with appropriate Content-Type and Content-Disposition headers

**Response Codes**:
- `200 OK`: Report downloaded successfully
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: User lacks permission
- `404 Not Found`: Report not found or not ready
- `500 Internal Server Error`: Failed to retrieve report file

## Webhook Integration

### Compliance Alert Webhook

**Endpoint**: `POST /api/webhooks/cis-alerts`

**Description**: Receive compliance alerts from external monitoring systems.

**Request Headers**:
- `X-Webhook-Signature`: HMAC signature for request verification
- `Content-Type`: `application/json`

**Request Body**:
```json
{
  "webhook_id": "wh_abc123",
  "event": "compliance.alert.created",
  "timestamp": "2026-07-14T12:00:00Z",
  "alert": {
    "severity": "CRITICAL",
    "configuration": "os.ssh_permit_root_login",
    "current_value": "yes",
    "expected_value": "no",
    "description": "SSH PermitRootLogin should be set to 'no' for security",
    "remediation": "Edit /etc/ssh/sshd_config and set PermitRootLogin no, then restart sshd service"
  }
}
```

**Response**:
```json
{
  "success": true,
  "alert_id": "3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r",
  "message": "Compliance alert received and processed"
}
```

## Error Handling

### Standard Error Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional technical details (optional)",
    "timestamp": "2026-07-14T12:00:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_001` | 401 | Invalid or missing authentication credentials |
| `AUTHZ_001` | 403 | Insufficient permissions for requested operation |
| `VAL_001` | 400 | Invalid input parameters |
| `NOT_FOUND_001` | 404 | Requested resource not found |
| `CONFLICT_001` | 409 | Resource conflict or duplicate operation |
| `SERVER_001` | 500 | Internal server error |
| `RATE_001` | 429 | Rate limit exceeded |

## Rate Limiting

- **Authenticated Users**: 100 requests per minute
- **Unauthenticated Users**: 10 requests per minute
- **Response Headers**:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (UTC timestamp)

## Versioning

The API uses semantic versioning in the `Accept` header:

```http
Accept: application/vnd.cis-compliance.v1+json
```

Current version: `v1`

## Deprecation Policy

- Deprecated endpoints will be marked with `Deprecation` header
- Deprecated endpoints will be removed after 6 months
- Deprecation notices will be included in changelog

## Security Considerations

- All endpoints require authentication
- Sensitive operations require additional authorization
- Input validation on all parameters
- Rate limiting to prevent abuse
- Audit logging for all operations
- HTTPS required for all endpoints

## Examples

### Full Assessment Workflow

```bash
# 1. Run assessment
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/assess \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["os", "database"]}'

# 2. Check assessment results
curl -X GET https://api.proposal-drafter.unhcr.org/api/cis/assessments/$ASSESSMENT_ID \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Accept: application/vnd.cis-compliance.v1+json"

# 3. Apply hardening
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/harden \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["os"]}'

# 4. Generate compliance report
curl -X POST https://api.proposal-drafter.unhcr.org/api/cis/reports \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_name": "July 2026 Compliance Report", "format": "pdf"}'

# 5. Download report
curl -X GET https://api.proposal-drafter.unhcr.org/api/cis/reports/$REPORT_ID/download \
  -H "Authorization: Bearer $JWT_TOKEN" \
  --output compliance_report.pdf
```

## Changelog

### v1.0.0 (2026-07-14)
- Initial release of CIS Compliance API
- All core endpoints implemented
- Full CIS benchmark assessment support
- Security hardening automation
- Compliance reporting functionality
