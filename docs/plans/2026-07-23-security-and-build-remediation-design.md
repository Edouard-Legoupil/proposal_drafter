# Security and Build Remediation Design

## Scope

This change is limited to three outcomes:

1. Remove SSH credentials and the SSH service from the production container.
2. Close the identified session, JWT revocation, and OAuth CSRF/redirect weaknesses.
3. Restore a successful frontend production build.

Database migrations, broad lint cleanup, unrelated authorization findings, dependency upgrades, and UI refactoring are explicitly out of scope.

## Container security

The production image will no longer install OpenSSH, set a root password, copy `sshd_config`, expose port 2222, or start `sshd`. The application will start Gunicorn directly through the existing startup script.

## Session and JWT security

Proposal session reads will verify that the stored `user_id` matches the authenticated user, matching the existing invalidation behavior.

JWT authentication will continue to validate signature and expiry. When Redis is available, the presented token must exactly match the active token stored for that user. A missing or different token is treated as revoked. When Redis is unavailable, a cryptographically valid JWT is accepted, as explicitly requested for current operational compatibility.

Logout will continue deleting the stored active token and clearing the browser cookie. Tests will cover active, revoked, mismatched, and Redis-unavailable behavior.

## OAuth security

The SSO login endpoint will generate a cryptographically random OAuth `state`, place it in a short-lived HttpOnly cookie, and include it in the Microsoft authorization request. The callback will compare the query state and cookie using constant-time comparison, reject missing or mismatched values, and clear the state cookie after use.

SSO will require the configured `ENTRA_REDIRECT_URI`. Redirect URIs will no longer be derived from request Host or forwarded headers.

## Frontend compilation

Compilation failures will be repaired iteratively from `npm run build`. Changes will be restricted to syntax errors, undefined identifiers, and other transform-time blockers. Existing behavior will be preserved wherever the intended expression is evident from neighboring components and hooks.

## Verification

- Focused backend tests for session ownership, JWT revocation/fallback, and OAuth state.
- Existing relevant authentication and session tests.
- `npm run build` for the frontend.
- A final repository status check to ensure no generated artifacts remain.
