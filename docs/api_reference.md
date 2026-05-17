# Proposal Drafter API Reference

## Version 1.0 - Production Ready

**Base URL:** `https://api.proposal-drafter.unhcr.org/api`
**Authentication:** JWT Bearer Token
**Content-Type:** `application/json`

## OpenAPI/Swagger Documentation

The API provides comprehensive OpenAPI/Swagger documentation for easy integration and testing.

### Interactive Documentation

- **Swagger UI**: Available at `/docs` when running locally
- **OpenAPI JSON**: Available at `/openapi.json`
- **Redoc**: Available at `/redoc` for alternative documentation format

### Documentation Files

- **Complete OpenAPI Spec**: `docs/openapi-spec.json` (JSON format)
- **Markdown Documentation**: `docs/OPENAPI_DOCUMENTATION.md` (detailed endpoint guide)
- **API Reference**: This file with practical examples

### Features

- **14 API Categories**: Authentication, Proposals, Documents, Users, Knowledge, Metrics, Admin, Templates, Incidents, Qualification, Health, SharePoint
- **Complete Endpoint Coverage**: All endpoints documented with request/response examples
- **Authentication Integration**: JWT bearer token support
- **Error Handling**: Standardized error responses documented
- **Pagination Support**: Consistent pagination across list endpoints

---

## Authentication

### Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive JWT token

**Request Body:**
```json
{
  "email": "user@unhcr.org",
  "password": "securePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Status Codes:**
- `200 OK`: Successful authentication
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

---

## User Management

### Get Current User

**Endpoint:** `GET /users/me`

**Description:** Get authenticated user's profile information

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "user-uuid-here",
  "email": "user@unhcr.org",
  "name": "John Doe",
  "roles": ["proposal_drafter", "knowledge_manager"],
  "team_id": "team-uuid-here",
  "geographic_coverage": "Africa"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated

### Get All Users (Admin)

**Endpoint:** `GET /admin/users`

**Description:** Get list of all users (Admin only)

**Headers:**
- `Authorization: Bearer <token>`
- `X-Admin-Key: <admin_key>`

**Response:**
```json
[{
  "id": "user-uuid-here",
  "email": "user@unhcr.org",
  "name": "John Doe",
  "roles": ["proposal_drafter"],
  "donor_groups": ["Education", "Health"],
  "outcomes": ["outcome-uuid-1", "outcome-uuid-2"],
  "field_contexts": ["field-uuid-1"]
}]
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized

---

## Proposal Management

### Create Proposal

**Endpoint:** `POST /proposals`

**Description:** Create a new proposal

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "project_short_name": "Refugee Education Initiative",
  "project_description": "Comprehensive education program for 2,500 refugee children",
  "main_outcomes": ["OA11. Education", "OA7. Community Engagement"],
  "beneficiaries_profile": "2,500 refugee children aged 6-14",
  "potential_implementing_partners": ["UNHCR", "UNICEF"],
  "geographical_scope": "One Country Operation",
  "country": "Afghanistan",
  "budget_range": "1M$",
  "duration": "12 months",
  "targeted_donor": "Sweden - Ministry for Foreign Affairs",
  "template_name": "proposal_template_unhcr.json"
}
```

**Response:**
```json
{
  "proposal_id": "proposal-uuid-here",
  "status": "draft",
  "created_at": "2025-05-15T14:30:45Z",
  "message": "Proposal created successfully"
}
```

**Status Codes:**
- `201 Created`: Proposal created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated

### Get Proposal

**Endpoint:** `GET /proposals/{proposal_id}`

**Description:** Get proposal details

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "proposal-uuid-here",
  "user_id": "user-uuid-here",
  "status": "draft",
  "template_name": "proposal_template_unhcr.json",
  "form_data": {
    "project_short_name": "Refugee Education Initiative",
    "project_description": "Comprehensive education program...",
    "main_outcomes": ["OA11. Education", "OA7. Community Engagement"],
    "beneficiaries_profile": "2,500 refugee children aged 6-14",
    "potential_implementing_partners": ["UNHCR", "UNICEF"],
    "geographical_scope": "One Country Operation",
    "country": "Afghanistan",
    "budget_range": "1M$",
    "duration": "12 months",
    "targeted_donor": "Sweden - Ministry for Foreign Affairs"
  },
  "generated_sections": {
    "executive_summary": "This project aims to provide...",
    "problem_analysis": "The refugee crisis has resulted in...",
    "objectives": ["Objective 1", "Objective 2"],
    "methodology": "The project will implement...",
    "budget": "Detailed budget breakdown...",
    "monitoring_evaluation": "Monitoring framework..."
  },
  "created_at": "2025-05-15T14:30:45Z",
  "updated_at": "2025-05-15T14:30:45Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal not found

### Update Proposal Section

**Endpoint:** `PUT /proposals/{proposal_id}/sections/{section_name}`

**Description:** Update a specific section of a proposal

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "content": "Updated executive summary content with more details..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Section updated successfully",
  "section": "executive_summary",
  "updated_at": "2025-05-15T14:35:22Z"
}
```

**Status Codes:**
- `200 OK`: Section updated
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal or section not found

### Regenerate Proposal Section

**Endpoint:** `POST /proposals/{proposal_id}/sections/{section_name}/regenerate`

**Description:** Regenerate a section with new instructions

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "prompt": "Revise this section to be more concise and focus on impact",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "message": "Section regeneration started",
  "section": "executive_summary",
  "status": "processing",
  "estimated_completion": "2025-05-15T14:37:22Z"
}
```

**Status Codes:**
- `202 Accepted`: Regeneration started
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal or section not found

### Submit Proposal for Review

**Endpoint:** `POST /proposals/{proposal_id}/submit`

**Description:** Submit proposal for peer review

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "reviewer_id": "reviewer-uuid-here",
  "comments": "Please review the budget section carefully",
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Proposal submitted for review",
  "review_id": "review-uuid-here",
  "status": "pending",
  "due_date": "2025-05-22T14:30:45Z"
}
```

**Status Codes:**
- `200 OK`: Proposal submitted
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal not found

---

## Knowledge Management

### Create Knowledge Card

**Endpoint:** `POST /knowledge-cards`

**Description:** Create a new knowledge card

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "title": "Education Program Lessons Learned",
  "summary": "Key insights from implementing education programs",
  "content": "After implementing education programs in 5 refugee camps...",
  "donor_id": "donor-uuid-here",
  "outcome_id": "outcome-uuid-here",
  "field_context_id": "field-uuid-here",
  "tags": ["education", "refugee", "lessons-learned"],
  "template_name": "knowledge_card_template.json"
}
```

**Response:**
```json
{
  "knowledge_card_id": "card-uuid-here",
  "status": "draft",
  "created_at": "2025-05-15T14:30:45Z",
  "message": "Knowledge card created successfully"
}
```

**Status Codes:**
- `201 Created`: Knowledge card created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Not authenticated

### Get Knowledge Card

**Endpoint:** `GET /knowledge-cards/{card_id}`

**Description:** Get knowledge card details

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "card-uuid-here",
  "title": "Education Program Lessons Learned",
  "summary": "Key insights from implementing education programs",
  "content": "After implementing education programs in 5 refugee camps...",
  "donor_id": "donor-uuid-here",
  "outcome_id": "outcome-uuid-here",
  "field_context_id": "field-uuid-here",
  "tags": ["education", "refugee", "lessons-learned"],
  "status": "published",
  "created_at": "2025-05-15T14:30:45Z",
  "updated_at": "2025-05-15T14:30:45Z",
  "created_by": "user-uuid-here",
  "template_name": "knowledge_card_template.json"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Knowledge card not found

---

## Template Management

### Get Available Templates

**Endpoint:** `GET /templates`

**Description:** Get list of available proposal templates

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "templates": {
    "Sweden - Ministry for Foreign Affairs": "proposal_template_sweden.json",
    "UNHCR Standard": "proposal_template_unhcr.json",
    "Education Focus": "proposal_template_education.json",
    "Health Focus": "proposal_template_health.json"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated

### Get Template Content

**Endpoint:** `GET /templates/{template_name}`

**Description:** Get full template content

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "template_name": "proposal_template_unhcr.json",
  "sections": [
    {
      "name": "executive_summary",
      "word_limit": 250,
      "instructions": "Provide a concise overview of the project...",
      "required": true
    },
    {
      "name": "problem_analysis",
      "word_limit": 500,
      "instructions": "Describe the problem this project addresses...",
      "required": true
    },
    {
      "name": "objectives",
      "word_limit": 300,
      "instructions": "List the specific objectives of the project...",
      "required": true
    }
  ],
  "metadata": {
    "version": "1.2",
    "last_updated": "2025-01-15",
    "donor": "UNHCR"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Template not found

---

## Document Export

### Export Proposal to Word

**Endpoint:** `GET /documents/export/{proposal_id}?format=docx`

**Description:** Export proposal to Word format

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
- **Content-Disposition:** `attachment; filename="proposal.docx"`
- **Content-Type:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

**Status Codes:**
- `200 OK`: Document generated
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal not found
- `500 Internal Server Error`: Export failed

### Export Proposal to PDF

**Endpoint:** `GET /documents/export/{proposal_id}?format=pdf`

**Description:** Export proposal to PDF format

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
- **Content-Disposition:** `attachment; filename="proposal.pdf"`
- **Content-Type:** `application/pdf`

**Status Codes:**
- `200 OK`: Document generated
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized
- `404 Not Found`: Proposal not found
- `500 Internal Server Error`: Export failed

---

## Error Responses

### Standard Error Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400
  }
}
```

### Common Error Codes

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| `auth_001` | Invalid credentials | 401 |
| `auth_002` | Token expired | 401 |
| `auth_003` | Insufficient permissions | 403 |
| `val_001` | Validation failed | 400 |
| `res_001` | Resource not found | 404 |
| `db_001` | Database error | 500 |
| `rate_001` | Rate limit exceeded | 429 |

---

## Rate Limiting

**Standard Limits:**
- **Authentication endpoints:** 10 requests per minute
- **API endpoints:** 100 requests per minute
- **Export endpoints:** 10 requests per minute

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets (UTC timestamp)

---

## Best Practices

### Authentication
- Always include `Authorization: Bearer <token>` header
- Store tokens securely (HttpOnly, Secure cookies)
- Refresh tokens before expiration

### Error Handling
- Check error codes for specific handling
- Implement retry logic for rate limits
- Log errors for debugging

### Performance
- Use pagination for list endpoints
- Cache responses where appropriate
- Minimize payload size

### Security
- Use HTTPS for all requests
- Validate all inputs
- Sanitize outputs
- Follow principle of least privilege

---

## Changelog

### Version 1.0 (2025-05-15)
- Initial production release
- Comprehensive API coverage
- JWT authentication
- Role-based access control
- SQL injection protections
- Rate limiting
- Standardized error responses

---

**End of API Reference Documentation**

*This document provides comprehensive API documentation for the Proposal Drafter application. All endpoints are production-ready and follow RESTful best practices.*