# Local SSO Redirect Inference Design

## Context

The login page displays its SSO button only when the frontend feature flag is enabled and the backend reports that SSO is configured. The backend currently requires `ENTRA_REDIRECT_URI` in every environment, even though local development has a predictable callback route.

Microsoft Entra still requires every redirect URI to be registered exactly. Automatic inference removes the local environment variable; it does not remove the Entra registration requirement.

## Decision

Infer the SSO redirect URI from the incoming request only when `APP_ENV` is `development`. Keep `ENTRA_REDIRECT_URI` mandatory in every other environment.

A single helper will resolve the redirect URI:

1. Return the configured `ENTRA_REDIRECT_URI` when it is present.
2. Otherwise, in development, use FastAPI's route-aware `request.url_for("callback")` value.
3. Otherwise, return no URI so SSO remains unavailable.

Both the authorization request and token exchange must use this helper. This guarantees that the redirect URI passed to Entra is consistent across the login and callback phases.

For the documented local backend at `http://localhost:8502`, the inferred URI is:

```text
http://localhost:8502/api/callback
```

## Status Endpoint

`GET /api/sso-status` has no request-dependent redirect URI to resolve. It will report SSO as enabled when:

- the tenant ID, client ID, and client secret are present; and
- either `ENTRA_REDIRECT_URI` is configured or `APP_ENV` is `development`.

The login endpoint remains the authoritative check because it can construct the actual URI from its request.

## Security Boundaries

- Production, staging, and other non-development environments continue to require an explicit redirect URI.
- OAuth state creation and validation remain unchanged.
- Existing `TrustedHostMiddleware` continues to reject unapproved host headers before local request-derived URLs are used.
- No frontend-provided redirect or return URL is accepted.

## Error Handling

If the three Entra credentials are incomplete, SSO stays disabled. If no redirect URI can be resolved for the current environment, login and callback return the existing `503 SSO not configured` response.

## Verification

Backend tests will cover:

- local development status without `ENTRA_REDIRECT_URI`;
- inferred callback URL in the authorization request;
- the same inferred callback URL in the token exchange;
- production status and login remaining disabled without an explicit URI;
- configured redirect URIs continuing to take precedence.

The SSO setup documentation and environment examples will describe the local inference and the production requirement.
