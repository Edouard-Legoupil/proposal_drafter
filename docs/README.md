# Proposal Drafter API Documentation

This directory contains comprehensive documentation for the Proposal Drafter API.

## Documentation Overview

The API documentation is organized into several formats to suit different needs:

### 1. Interactive Documentation (Swagger UI)

**Access**: `http://localhost:8502/docs` (when API is running)

- **Features**: Interactive testing, try endpoints directly from browser
- **Authentication**: Built-in JWT token management
- **Best For**: Development, testing, exploration

### 2. OpenAPI Specification

**Files**:
- `openapi-spec.json` - Complete OpenAPI 3.0.0 specification
- `OPENAPI_DOCUMENTATION.md` - Detailed markdown documentation

**Features**:
- Machine-readable JSON specification
- Importable into Postman, Insomnia, etc.
- Complete endpoint definitions with schemas
- Request/response examples

**Best For**: API client integration, automation, CI/CD

### 3. API Reference Guide

**File**: `api_reference.md`

**Features**:
- Practical usage examples
- Real-world request/response samples
- Status codes and error handling
- Best practices and recommendations

**Best For**: Developers implementing API clients

### 4. Security Documentation

**File**: `SECURITY_OVERVIEW.md`

**Features**:
- Complete security feature documentation
- Authentication and authorization details
- Compliance information (UN ICT Security Policy, OWASP Top 10)
- MFA implementation details
- Security controls and measures

**Best For**: Security reviews, CISO approval, compliance audits

## Documentation Structure

```
docs/
├── README.md                    # This file
├── api_reference.md             # Practical API usage guide
├── OPENAPI_DOCUMENTATION.md     # Complete OpenAPI documentation
├── openapi-spec.json            # OpenAPI 3.0.0 specification
└── SECURITY_OVERVIEW.md         # Comprehensive security documentation
```

## Getting Started

### 1. Run the API Server

```bash
cd backend
uvicorn main:app --reload
```

### 2. Access Interactive Documentation

Open your browser to: `http://localhost:8502/docs`

### 3. Authenticate

Click the "Authorize" button and enter your JWT token.

### 4. Explore Endpoints

Browse through the 14 API categories and try out endpoints.

## API Categories

The API is organized into logical categories:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Authentication** | `/api/login`, `/api/sso-status` | User authentication and SSO |
| **Session Management** | `/api/session` | Session information |
| **Proposals** | `/api/proposals`, `/api/proposals/{id}` | Proposal CRUD operations |
| **Documents** | `/api/documents/upload`, `/api/documents/{id}` | Document management |
| **Users** | `/api/users/me`, `/api/users` | User profiles and management |
| **Knowledge** | `/api/knowledge/cards` | Knowledge base access |
| **Metrics** | `/api/metrics/usage` | API usage metrics |
| **Admin** | `/api/admin/users`, `/api/admin/templates` | Administrative functions |
| **Donor Templates** | `/api/templates` | Donor template management |
| **Template Management** | `/api/admin/templates` | Template administration |
| **Incidents** | `/api/incidents` | Incident reporting |
| **Qualification** | `/api/qualification/check` | Proposal qualification |
| **Health** | `/health` | Health monitoring |
| **SharePoint** | `/api/sharepoint/sync-status` | SharePoint integration |

## Authentication

The API uses JWT (JSON Web Token) authentication:

### Authentication Flow

1. **Login**: `POST /api/login` with email and password
2. **Receive Token**: Get JWT token in response
3. **Use Token**: Include `Authorization: Bearer <token>` in requests
4. **Token Expiry**: Tokens expire after 1 hour (configurable)

### Role-Based Access Control

- **user**: Basic access to proposals and documents
- **editor**: Can create and edit proposals
- **admin**: Full access including user management
- **superadmin**: System-level access

## Using the Documentation

### For Developers

1. Start with `api_reference.md` for practical examples
2. Use Swagger UI (`/docs`) for interactive testing
3. Refer to `OPENAPI_DOCUMENTATION.md` for detailed endpoint specs
4. Check `SECURITY_OVERVIEW.md` for security implementation details

### For API Integration

1. Import `openapi-spec.json` into your API client
2. Use the predefined schemas and endpoints
3. Follow the authentication patterns
4. Implement error handling based on documented responses

### For Security Reviews

1. Review `SECURITY_OVERVIEW.md` for complete security documentation
2. Check authentication and authorization implementation
3. Verify compliance with UN ICT Security Policy
4. Review OWASP Top 10 protections

## Documentation Standards

### OpenAPI 3.0.0 Compliance

The API follows OpenAPI 3.0.0 standards:

- **Complete Spec**: All endpoints documented
- **Schemas**: Detailed request/response models
- **Examples**: Request and response examples
- **Tags**: Logical grouping of endpoints
- **Security**: Authentication requirements documented

### Documentation Quality

- **Comprehensive**: All 14 API categories covered
- **Up-to-Date**: Synchronized with codebase
- **Practical**: Includes real-world examples
- **Searchable**: Well-organized and indexed

## Versioning

- **API Version**: 0.0.1 (current)
- **Documentation Version**: 1.0
- **OpenAPI Version**: 3.0.0

## Support

For documentation issues or questions:

- **Email**: legoupil@unhcr.org
- **GitHub**: https://github.com/edouard-legoupil/proposal-drafter
- **Issues**: Report documentation issues in GitHub Issues

## Contributing to Documentation

Documentation is generated from:

1. **Code**: FastAPI route definitions and docstrings
2. **OpenAPI Spec**: Automatically generated from code
3. **Manual Files**: Supplementary documentation files

To update documentation:

1. Update docstrings in API route handlers
2. Regenerate OpenAPI spec (automatic with FastAPI)
3. Update supplementary files as needed
4. Test with Swagger UI

## Documentation Roadmap

### Current Status ✅

- [x] Complete OpenAPI specification
- [x] Interactive Swagger UI
- [x] Comprehensive API reference
- [x] Security documentation
- [x] Request/response examples
- [x] Error handling documentation
- [x] Authentication documentation

### Future Enhancements 🚀

- [ ] API changelog
- [ ] Version-specific documentation
- [ ] Client SDK documentation
- [ ] Integration guides
- [ ] Video tutorials

## Legal and Compliance

- **License**: MIT License
- **Terms of Service**: http://www.unhcr.org
- **Data Privacy**: Compliant with UN data protection policies
- **Security**: Follows UN ICT Security Policy and OWASP Top 10

## Quick Reference

### Common Endpoints

**Authentication**:
```bash
POST /api/login
{
  "email": "user@unhcr.org",
  "password": "securePassword123!"
}
```

**Proposals**:
```bash
GET /api/proposals
Authorization: Bearer <token>
```

**Documents**:
```bash
POST /api/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Troubleshooting

### Documentation Issues

**Problem**: Endpoint not showing in Swagger UI
**Solution**: Check if route has proper tags and docstrings

**Problem**: Schema validation errors
**Solution**: Verify request body matches documented schema

**Problem**: Authentication not working in Swagger
**Solution**: Click "Authorize" and enter valid JWT token

### API Issues

**Problem**: 401 Unauthorized
**Solution**: Verify token is valid and not expired

**Problem**: 403 Forbidden
**Solution**: Check user roles and permissions

**Problem**: 429 Too Many Requests
**Solution**: Wait for rate limit reset or request limit increase

## Conclusion

This comprehensive documentation provides everything needed to understand, integrate with, and use the Proposal Drafter API effectively. The documentation is available in multiple formats to suit different use cases and preferences.

For the most up-to-date information, always refer to the interactive Swagger UI when the API is running, as it reflects the current state of the codebase.
