# Proposal Drafter security overview

This document describes controls implemented in the application. Infrastructure controls such as a web application
firewall, private networking, encryption at rest, backups, and SIEM integration remain deployment responsibilities.

## Authentication and sessions

The application supports local password authentication and optional Microsoft Entra ID single sign-on (SSO). Entra
multi-factor authentication and Conditional Access depend on the tenant policy; the application does not enable them.

Successful local or SSO authentication creates one HS256 JWT that expires after 8 hours. The token is stored only in an
`HttpOnly` cookie with `SameSite=Lax`; the cookie is `Secure` outside local development. The application does not issue a
refresh token. The OAuth flow also uses a random, `HttpOnly` state cookie with a ten-minute lifetime and compares the
returned state in constant time.

When Redis is available, the backend stores the active JWT for 8 hours and compares it on each authenticated request.
Logout deletes that Redis record and clears the cookie. If Redis is unavailable, the application deliberately falls back
to validating the signed JWT until it expires. Deploy Redis as a reliable service when immediate session revocation is a
requirement.

Set a unique `SECRET_KEY` of at least 32 characters outside development. The application rejects the documented default
or a short key when `APP_ENV` is not `development`.

## Authorization

Direct and team-inherited roles protect administrative, analytical, and workflow endpoints. A user is a system
administrator only when the normalized `system admin` role is present.

Object-level checks protect proposals, knowledge cards, templates, sessions, and related mutations. System administrators
can create explicit user or team grants for proposals, knowledge cards, and templates. Those grants are persisted in
`resource_access_grants` and consumed by runtime authorization checks. Ownership changes, grants, revocations, and
template-visibility changes are written to `resource_access_audit`.

## Browser and API controls

The backend configures trusted hosts, an explicit CORS origin allowlist, credentialed requests, and these response headers:

- Content Security Policy
- Strict-Transport-Security
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
- no-store cache directives for responses that do not define their own policy

Authentication cookies are not exposed to frontend JavaScript. The frontend uses `credentials: include` and does not
persist bearer tokens in local storage.

Login, signup, password-recovery, and selected generation endpoints use application rate limits. API inputs increasingly
use Pydantic models, while database access uses SQLAlchemy ORM or parameterized SQL. These controls reduce risk but do not
replace threat modelling, dependency review, penetration testing, or secure infrastructure configuration.

## Secrets and logging

Development reads secrets from ignored environment files. Production can resolve supported secrets through Azure Key
Vault, Google Secret Manager, or injected environment variables. Never commit `.env` files.

The application records security and administrative events in application logs, and resource-access changes in the
database audit table. It does not automatically forward logs to a SIEM or define retention; operators must configure log
shipping, access, alerting, and retention for their environment.

## Known operational considerations

- Redis fallback preserves availability but weakens immediate logout and revocation semantics.
- The JWT lifetime is fixed at 8 hours in the current authentication endpoints.
- Entra MFA, TLS termination, encryption at rest, network isolation, and monitoring are deployment controls.
- Apply database migrations before deploying code that depends on new access-control tables.
