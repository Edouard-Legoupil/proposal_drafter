# OWASP Application Hardening Design

## Objective

Remediate the application-level findings from the backend and frontend OWASP review for the actual production topology: FastAPI serves the compiled React application and production authentication uses SSO exclusively.

## Scope

The work covers FastAPI, React, the scraper and document-ingestion paths, session validation, application rate limiting, error responses, static-file delivery, and application dependencies.

The following are deliberately excluded:

- Nginx configuration, because Nginx is not used in deployment.
- Azure Bicep modules, because they are not used for production deployment.
- Changes that label or delimit retrieved knowledge as untrusted prompt content.

## Security Architecture

### Authentication and sessions

Production permits SSO authentication only. Local signup, password login, security-question lookup, and security-question password reset remain available for local development and automated testing, but production rejects them.

Redis is configured through `REDIS_URL`. Production session validation fails closed when Redis is unavailable and returns a service-unavailable response rather than accepting a token whose server-side session cannot be verified. Local and test environments may retain an explicit in-memory fallback.

### Remote content ingestion

Production requires `SCRAPER_ALLOWED_SCHEMES`, configured as `http,https`. Local development defaults to these schemes when the variable is omitted.

Every requested URL and redirect target is validated. The scraper rejects loopback, private, link-local, multicast, reserved, unspecified, and otherwise non-public resolved addresses. It limits redirect hops, response bytes, request duration, and recursive document discovery. Validation is repeated after every redirect to prevent DNS and redirect bypasses.

### Files and resource consumption

PDF uploads are streamed with a byte limit, checked for a PDF file signature, and processed with a page limit. Temporary files are removed in `finally` blocks. Remote downloads use bounded streaming rather than loading arbitrary response bodies into memory.

Application rate limiting is installed in FastAPI and applied more strictly to generation, ingestion, uploads, authentication, and unauthenticated wizard endpoints. Public list parameters receive explicit upper bounds.

### Errors and observability

Unexpected failures are logged server-side with a correlation identifier. Client responses contain stable generic messages and the identifier, not raw database, connector, stack, or provider exceptions. Expected validation and authorization messages remain actionable without exposing internals.

### FastAPI static frontend

Security headers apply to API, static asset, and SPA fallback responses. The policy includes CSP, HSTS in production, frame protection, MIME sniffing protection, referrer policy, and permissions policy. Static fallback paths are resolved and verified to remain within the frontend build directory before files are served.

### Frontend and dependencies

Audited React Router and YAML dependencies are upgraded to non-vulnerable versions. New-window navigation validates supported HTTP(S) URLs and uses `noopener,noreferrer`.

## Testing

Each behavior change starts with a failing regression test. Coverage includes environment-gated local authentication, fail-closed sessions, Redis URL parsing, SSRF and redirect defenses, bounded uploads and downloads, rate-limiter registration, public endpoint limits, sanitized errors, static-file containment and headers, safe new-window navigation, and dependency audit policy.

Final verification runs the backend test suite, frontend unit tests, frontend production build, relevant Playwright journeys, linting, and available Python and npm dependency audits.
