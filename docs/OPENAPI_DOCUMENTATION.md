# OpenAPI/Swagger Documentation for Proposal Drafter API

This document provides comprehensive OpenAPI/Swagger documentation for the Proposal Drafter API, including all endpoints, request/response examples, and usage guidelines.

## API Overview

The Proposal Drafter API is a FastAPI-based RESTful API for generating, managing, and exporting project proposals for UN agencies and NGOs.

### Base Information

- **Title**: Proposal Drafting API
- **Version**: 0.0.1
- **Description**: An API for generating, managing, and exporting project proposals.
- **Terms of Service**: http://www.unhcr.org
- **Contact**: Edouard Legoupil (legoupil@unhcr.org)
- **License**: MIT

### API Base URL

The API is served at the `/api` prefix. All endpoints are relative to this base path.

## API Endpoints by Category

The API is organized into logical categories using FastAPI routers:

### 1. Authentication Endpoints

**Prefix**: `/api`
**Tag**: `Authentication`

#### POST `/api/login`

**Description**: Authenticate user and return JWT token

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200)**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response (401)**:
```json
{
  "detail": "Invalid credentials"
}
```

#### GET `/api/sso-status`

**Description**: Check SSO availability

**Response (200)**:
```json
{
  "enabled": true
}
```

### 2. Session Management Endpoints

**Prefix**: `/api`
**Tag**: `Session Management`

#### GET `/api/session`

**Description**: Get current session information

**Headers**:
- `Authorization: Bearer <token>`

**Response (200)**:
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "roles": ["string"],
  "expires_at": "datetime"
}
```

### 3. Proposals Endpoints

**Prefix**: `/api`
**Tag**: `Proposals`

#### GET `/api/proposals`

**Description**: List all proposals (filtered by user access)

**Headers**:
- `Authorization: Bearer <token>`

**Query Parameters**:
- `limit`: int (default: 100)
- `offset`: int (default: 0)
- `status`: string (optional filter)

**Response (200)**:
```json
{
  "proposals": [
    {
      "id": "string",
      "title": "string",
      "status": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "owner_id": "string"
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

#### POST `/api/proposals`

**Description**: Create a new proposal

**Headers**:
- `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "title": "string",
  "template_id": "string",
  "context": "string",
  "additional_data": {}
}
```

**Response (201)**:
```json
{
  "id": "string",
  "title": "string",
  "status": "draft",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### GET `/api/proposals/{proposal_id}`

**Description**: Get proposal details

**Headers**:
- `Authorization: Bearer <token>`

**Path Parameters**:
- `proposal_id`: string (required)

**Response (200)**:
```json
{
  "id": "string",
  "title": "string",
  "status": "string",
  "content": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "owner_id": "string",
  "template_id": "string"
}
```

### 4. Documents Endpoints

**Prefix**: `/api`
**Tag**: `Documents`

#### POST `/api/documents/upload`

**Description**: Upload a document for processing

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Request Body**:
- `file`: file (required)
- `document_type`: string (optional)

**Response (200)**:
```json
{
  "document_id": "string",
  "filename": "string",
  "size": 1024,
  "mime_type": "string",
  "status": "processing"
}
```

#### GET `/api/documents/{document_id}`

**Description**: Get document information

**Headers**:
- `Authorization: Bearer <token>`

**Path Parameters**:
- `document_id`: string (required)

**Response (200)**:
```json
{
  "id": "string",
  "filename": "string",
  "size": 1024,
  "mime_type": "string",
  "status": "string",
  "created_at": "datetime",
  "processed_at": "datetime"
}
```

### 5. Users Endpoints

**Prefix**: `/api`
**Tag**: `Users`

#### GET `/api/users/me`

**Description**: Get current user profile

**Headers**:
- `Authorization: Bearer <token>`

**Response (200)**:
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "roles": ["string"],
  "settings": {}
}
```

#### GET `/api/users`

**Description**: List users (admin only)

**Headers**:
- `Authorization: Bearer <token>`

**Query Parameters**:
- `limit`: int (default: 50)
- `offset`: int (default: 0)
- `role`: string (optional filter)

**Response (200)**:
```json
{
  "users": [
    {
      "id": "string",
      "username": "string",
      "email": "string",
      "full_name": "string",
      "roles": ["string"],
      "is_active": true
    }
  ],
  "total": 50,
  "limit": 50,
  "offset": 0
}
```

### 6. Knowledge Endpoints

**Prefix**: `/api`
**Tag**: `Knowledge`

#### GET `/api/knowledge/cards`

**Description**: Get knowledge cards

**Headers**:
- `Authorization: Bearer <token>`

**Query Parameters**:
- `category`: string (optional)
- `limit`: int (default: 20)

**Response (200)**:
```json
{
  "cards": [
    {
      "id": "string",
      "title": "string",
      "content": "string",
      "category": "string",
      "tags": ["string"],
      "source": "string"
    }
  ],
  "total": 20
}
```

### 7. Metrics Endpoints

**Prefix**: `/api`
**Tag**: `Metrics`

#### GET `/api/metrics/usage`

**Description**: Get API usage metrics (admin only)

**Headers**:
- `Authorization: Bearer <token>`

**Query Parameters**:
- `period`: string (day/week/month)

**Response (200)**:
```json
{
  "period": "month",
  "total_requests": 1000,
  "successful_requests": 950,
  "failed_requests": 50,
  "users": 25,
  "proposals_created": 150
}
```

### 8. Admin Endpoints

**Prefix**: `/api`
**Tag**: `Admin`

#### POST `/api/admin/users`

**Description**: Create a new user (admin only)

**Headers**:
- `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "roles": ["string"]
}
```

**Response (201)**:
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "roles": ["string"],
  "is_active": true
}
```

### 9. Donor Templates Endpoints

**Prefix**: `/api/templates`
**Tag**: `Donor Templates`

#### GET `/api/templates`

**Description**: List available donor templates

**Headers**:
- `Authorization: Bearer <token>`

**Response (200)**:
```json
{
  "templates": [
    {
      "id": "string",
      "name": "string",
      "donor": "string",
      "description": "string",
      "version": "string"
    }
  ],
  "total": 10
}
```

### 10. Template Management Endpoints

**Prefix**: `/api/admin`
**Tag**: `Template Management`

#### POST `/api/admin/templates`

**Description**: Upload a new template (admin only)

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Request Body**:
- `file`: file (required)
- `donor`: string (required)
- `description`: string (optional)

**Response (201)**:
```json
{
  "template_id": "string",
  "name": "string",
  "donor": "string",
  "status": "uploaded"
}
```

### 11. Incidents Endpoints

**Prefix**: `/api`
**Tag**: `Incidents`

#### POST `/api/incidents`

**Description**: Report an incident

**Headers**:
- `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "type": "string",
  "severity": "string",
  "description": "string",
  "context": {}
}
```

**Response (201)**:
```json
{
  "incident_id": "string",
  "status": "received",
  "created_at": "datetime"
}
```

### 12. Qualification Endpoints

**Prefix**: `/api`
**Tag**: `Qualification`

#### POST `/api/qualification/check`

**Description**: Check proposal qualification

**Headers**:
- `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "proposal_id": "string",
  "criteria": ["string"]
}
```

**Response (200)**:
```json
{
  "qualified": true,
  "score": 85,
  "feedback": "string",
  "criteria_results": {}
}
```

### 13. Health & Debugging Endpoints

**Tag**: `Health & Debugging`

#### GET `/health`

**Description**: Health check endpoint

**Response (200)**:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "timestamp": "datetime"
}
```

### 14. SharePoint Endpoints

**Prefix**: `/api`
**Tag**: `SharePoint`

#### GET `/api/sharepoint/sync-status`

**Description**: Get SharePoint sync status

**Headers**:
- `Authorization: Bearer <token>`

**Response (200)**:
```json
{
  "status": "string",
  "last_sync": "datetime",
  "next_sync": "datetime",
  "synced_items": 100
}
```

## Authentication

The API uses JWT (JSON Web Token) authentication with the following requirements:

### Authentication Flow

1. **Obtain Token**: POST to `/api/login` with username/password
2. **Use Token**: Include `Authorization: Bearer <token>` header in subsequent requests
3. **Token Expiry**: Tokens expire after 1 hour (configurable)

### Role-Based Access Control

The API implements role-based access control with the following roles:

- **user**: Basic access to proposals and documents
- **editor**: Can create and edit proposals
- **admin**: Full access including user management
- **superadmin**: System-level access

## Error Handling

The API uses standardized error responses:

### Common Error Responses

**400 Bad Request**:
```json
{
  "detail": "Invalid request parameters",
  "errors": [
    {
      "field": "string",
      "message": "string"
    }
  ]
}
```

**401 Unauthorized**:
```json
{
  "detail": "Authentication required"
}
```

**403 Forbidden**:
```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found**:
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error",
  "error_id": "string"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit**: 100 requests per minute per user
- **Admin Limit**: 500 requests per minute
- **Headers**:
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets

## Pagination

Endpoints that return lists support pagination:

- **Query Parameters**:
  - `limit`: Number of items per page (default: 100, max: 1000)
  - `offset`: Starting position (default: 0)

- **Response Structure**:
```json
{
  "data": [],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

## API Versioning

The API uses semantic versioning:

- **Current Version**: 0.0.1
- **Version Header**: `Accept: application/vnd.proposaldrafter.v1+json`
- **Backward Compatibility**: Maintained within major versions

## Swagger UI Access

The API provides interactive Swagger UI documentation:

- **URL**: `/docs` (when running locally)
- **OpenAPI Schema**: `/openapi.json`
- **Redoc**: `/redoc`

## Usage Examples

### Python Example

```python
import requests

# Login
login_response = requests.post("http://localhost:8502/api/login", json={
    "username": "user@example.com",
    "password": "password123"
})

token = login_response.json()["access_token"]

# Use authenticated endpoint
headers = {
    "Authorization": f"Bearer {token}"
}

proposals = requests.get("http://localhost:8502/api/proposals", headers=headers)
print(proposals.json())
```

### cURL Example

```bash
# Login
curl -X POST "http://localhost:8502/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'

# Get proposals
curl -X GET "http://localhost:8502/api/proposals" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Best Practices

### Request Guidelines

1. **Use HTTPS**: Always use HTTPS in production
2. **Authentication**: Store tokens securely and rotate them regularly
3. **Pagination**: Use pagination for large datasets
4. **Rate Limiting**: Respect rate limits and implement retries with backoff
5. **Error Handling**: Implement proper error handling for all API calls

### Response Handling

1. **Validation**: Validate all responses before processing
2. **Error Codes**: Handle specific HTTP status codes appropriately
3. **Retry Logic**: Implement exponential backoff for 5xx errors
4. **Logging**: Log API calls and responses for debugging

## Security Considerations

### Data Protection

- All sensitive data is encrypted in transit (TLS 1.2+)
- Passwords are hashed using bcrypt
- JWT tokens are signed with strong algorithms

### Input Validation

- All inputs are validated using Pydantic models
- SQL injection is prevented using SQLAlchemy ORM
- File uploads are scanned and size-limited

### Compliance

- Follows UN ICT Security Policy
- Implements OWASP Top 10 protections
- Regular security audits and penetration testing

## API Changelog

### Version 0.0.1 (Current)

- Initial API release
- Core proposal management endpoints
- Authentication and authorization
- Basic document handling
- Admin functionality

## Support

For API support, contact:

- **Email**: legoupil@unhcr.org
- **GitHub**: https://github.com/edouard-legoupil/proposal-drafter
- **Documentation**: Complete API reference available at `/docs`

## Deprecation Policy

- Deprecated endpoints are marked in responses
- 3-month deprecation period before removal
- Version increments for breaking changes
- Migration guides provided for major changes

## Performance Considerations

- **Response Times**: Most endpoints respond in < 500ms
- **Timeouts**: 30-second timeout for all requests
- **Caching**: Redis caching for frequently accessed data
- **Optimization**: Database queries are optimized with indexes

## Monitoring and Analytics

The API includes comprehensive monitoring:

- Request/response logging
- Performance metrics
- Error tracking
- Usage analytics (aggregated and anonymized)

## Legal and Compliance

- **Data Privacy**: Compliant with UN data protection policies
- **Terms of Service**: http://www.unhcr.org
- **Acceptable Use**: Prohibits automated scraping without permission
- **Intellectual Property**: All content remains property of respective owners

## Getting Started Guide

### 1. Authentication

```bash
# Get your API token
POST /api/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

### 2. Make Your First Request

```bash
# List proposals
GET /api/proposals
Authorization: Bearer YOUR_TOKEN
```

### 3. Create a Proposal

```bash
# Create proposal
POST /api/proposals
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "title": "My First Proposal",
  "template_id": "unhcr-standard",
  "context": "Humanitarian aid for refugees"
}
```

### 4. Download a Proposal

```bash
# Get proposal content
GET /api/proposals/{proposal_id}
Authorization: Bearer YOUR_TOKEN
```

## Troubleshooting

### Common Issues

**401 Unauthorized**:
- Verify your token is valid and not expired
- Check token format: `Bearer <token>`
- Ensure you're using the correct credentials

**403 Forbidden**:
- Check your user roles and permissions
- Contact administrator if you need elevated access

**429 Too Many Requests**:
- Wait for rate limit to reset
- Implement request throttling in your client
- Contact support if you need higher limits

**500 Internal Server Error**:
- Check the error ID in the response
- Include error ID when contacting support
- Try again later if it's a temporary issue

### Debugging Tips

1. **Check Headers**: Ensure all required headers are present
2. **Validate Payload**: Use JSON linting tools to validate request bodies
3. **Inspect Responses**: Look at full response including headers
4. **Test with Swagger**: Use the interactive `/docs` interface for testing
5. **Enable Logging**: Use verbose logging in your client

## API Reference Quick Guide

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Authentication | `/api/login`, `/api/sso-status` | User authentication |
| Session | `/api/session` | Session management |
| Proposals | `/api/proposals`, `/api/proposals/{id}` | Proposal CRUD operations |
| Documents | `/api/documents/upload`, `/api/documents/{id}` | Document management |
| Users | `/api/users/me`, `/api/users` | User profile and management |
| Knowledge | `/api/knowledge/cards` | Knowledge base access |
| Metrics | `/api/metrics/usage` | API usage metrics |
| Admin | `/api/admin/users` | Administrative functions |
| Templates | `/api/templates` | Donor template management |
| Template Admin | `/api/admin/templates` | Template administration |
| Incidents | `/api/incidents` | Incident reporting |
| Qualification | `/api/qualification/check` | Proposal qualification |
| Health | `/health` | Health monitoring |
| SharePoint | `/api/sharepoint/sync-status` | SharePoint integration |

## Conclusion

This comprehensive OpenAPI/Swagger documentation provides everything needed to integrate with the Proposal Drafter API. The API follows RESTful principles, uses JWT authentication, and provides detailed error handling and rate limiting.

For the most up-to-date documentation, always refer to the interactive Swagger UI available at `/docs` when the API is running.