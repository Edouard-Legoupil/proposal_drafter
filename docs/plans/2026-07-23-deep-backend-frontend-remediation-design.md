# Deep Backend and Frontend Remediation Design

## Objective

Resolve the confirmed security, backend-contract, frontend-runtime, test, CI, and documentation defects while preserving supported client workflows and the existing FastAPI/React architecture.

## Architecture

The remediation will be delivered in small compatibility-preserving batches. Authorization decisions move to server-controlled policies: public signup cannot assign privileged roles, self-service settings cannot directly grant roles or memberships, and protected knowledge mutations require an approved administrative role. Authentication configuration will fail safely, cookies will use same-site protections, proxy-derived client addresses will only be trusted from configured proxies, and rate-limit state will use Redis when available.

Backend routes will expose only coherent, tested contracts. Broken router/service dependency mismatches will be repaired or deliberately excluded when no supported frontend consumes them. Contract tests will verify every frontend-consumed API path. Test databases will be isolated per test run and their schema will match production migrations.

The frontend will retain its current user journeys while repairing temporal-dead-zone and undefined-variable crashes. A single authentication-aware API path will use cookie credentials consistently. Client-side route guards will improve navigation behavior while backend authorization remains the security boundary. Large route bundles will be split only where this can be done without changing behavior.

## Data and Authorization Flow

Signup accepts identity and preference data but the server assigns the baseline proposal-writer role. Self-service updates may change personal/geographic preferences and submit pending access requests; they may not replace approved roles, donor access, team memberships, or other grants. Administrators continue to approve access through administrative endpoints.

JWTs remain the accepted session format, as requested. Production-like environments require an explicit non-default signing key. Session validation continues to check active Redis-backed state. Login and recovery failures use non-enumerating responses.

## Error Handling

Security-sensitive failures return stable generic messages. Configuration errors fail at startup with actionable diagnostics. Redis outages preserve current availability behavior where explicitly intended, but never silently broaden authorization. Frontend requests surface bounded user-facing errors and cancel or ignore stale asynchronous work during unmount.

## Testing and Delivery

Every behavior change follows red-green-refactor: first add a regression test that demonstrates the defect, verify the expected failure, implement the smallest correction, and rerun focused plus neighboring tests. Backend verification covers authorization, authentication, rate limiting, router contracts, and isolated database fixtures. Frontend verification covers components, route guards, request credentials, lint, and production compilation.

CI will gate deployment on backend tests, frontend tests, lint, and build. Documentation will state only behavior demonstrated by the code and verification suite. Work will be committed in independently reviewable conventional commits and integrated into `main_dev` only after final verification.

## Scope Boundaries

This remediation does not replace JWT with another session technology, redesign CrewAI workflows, or introduce unrelated product features. Existing public API shapes will be preserved where safe; unsafe privilege-bearing fields may be rejected or converted into pending requests.
