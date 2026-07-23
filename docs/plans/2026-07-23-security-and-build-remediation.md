# Security and Build Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove container SSH credentials, enforce session/JWT/OAuth protections with an availability fallback, and restore a successful frontend production build.

**Architecture:** Keep the existing cookie JWT and per-user Redis session model, but make Redis availability explicit and validate active tokens whenever Redis is reachable. Protect temporary proposal sessions by owner and protect OAuth with a short-lived state cookie plus a fixed configured callback. Remove the container SSH surface entirely and make only compiler-directed frontend repairs.

**Tech Stack:** FastAPI, PyJWT, Redis, MSAL OAuth, pytest, React, Vite, Docker.

---

### Task 1: Remove production-container SSH

**Files:**
- Modify: `Dockerfile:117-138`
- Modify: `supervisor/start.sh:167-176`

**Step 1: Capture the failing static assertions**

Run:

```bash
rg -n 'openssh|root:Docker|sshd_config|EXPOSE 2222|/usr/sbin/sshd' Dockerfile supervisor/start.sh
```

Expected: matches prove the production image installs and starts SSH and embeds a password.

**Step 2: Remove the SSH image layer**

Delete the OpenSSH install, `chpasswd`, `sshd_config` copies, host-key generation, and port 2222 exposure from `Dockerfile`.

**Step 3: Remove SSH startup**

Delete the environment-to-`/etc/profile` export and `/usr/sbin/sshd` startup from `supervisor/start.sh`. Preserve the existing Gunicorn `exec` path.

**Step 4: Verify the static assertions are clean**

Run the command from Step 1.

Expected: no matches.

**Step 5: Commit**

```bash
git add Dockerfile supervisor/start.sh
git commit -m "fix: remove container ssh credentials"
```

### Task 2: Add explicit Redis availability and JWT active-session validation

**Files:**
- Modify: `backend/core/redis.py`
- Modify: `backend/core/security.py`
- Modify: `backend/tests/conftest.py:453-455`
- Create: `backend/tests/test_session_token_validation.py`

**Step 1: Write failing token-validation tests**

Test these behaviors through a small `is_session_token_active(user_id, token)` helper:

```python
def test_active_token_is_accepted(monkeypatch): ...
def test_missing_token_is_rejected_when_redis_available(monkeypatch): ...
def test_mismatched_token_is_rejected_when_redis_available(monkeypatch): ...
def test_valid_jwt_falls_back_when_redis_unavailable(monkeypatch): ...
def test_redis_error_falls_back_to_valid_jwt(monkeypatch): ...
```

The available cases must use constant-time token comparison. The unavailable/error cases must return `True`, matching the approved operational choice.

**Step 2: Run tests to verify RED**

```bash
cd backend && pytest tests/test_session_token_validation.py -v
```

Expected: import failure because the helper and availability function do not exist.

**Step 3: Implement Redis availability**

Track whether the real Redis `ping()` succeeded in `backend/core/redis.py` and expose `is_redis_available()`. The in-memory fallback must report unavailable.

**Step 4: Implement active-token validation**

In `backend/core/security.py`, add `is_session_token_active`. If Redis is unavailable or raises `RedisError`, log the fallback and accept the valid JWT. Otherwise require an active stored token and compare it with `hmac.compare_digest`.

Call the helper in `get_current_user` after resolving the user ID. Raise HTTP 401 for a revoked or superseded token.

**Step 5: Keep authenticated fixtures representative**

When the test session store reports available, place the fixture JWT under `user_session:{user_id}`. Do not bypass the production validation path with a `TESTING` branch.

**Step 6: Run tests to verify GREEN**

```bash
cd backend && pytest tests/test_session_token_validation.py tests/test_security_headers.py::test_session_invalidation_on_logout -v
```

Expected: all selected tests pass.

**Step 7: Commit**

```bash
git add backend/core/redis.py backend/core/security.py backend/tests/conftest.py backend/tests/test_session_token_validation.py
git commit -m "fix: validate active jwt sessions"
```

### Task 3: Enforce ownership of temporary proposal sessions

**Files:**
- Modify: `backend/api/session.py:64-90`
- Modify: `backend/tests/test_get_base_data.py`

**Step 1: Write a failing cross-user access test**

Store a temporary Redis session whose `user_id` differs from the authenticated fixture and assert:

```python
response = client.get(f"/api/get_base_data/{session_id}")
assert response.status_code == 403
```

**Step 2: Run the test to verify RED**

```bash
cd backend && pytest tests/test_get_base_data.py -v
```

Expected: cross-user test returns 200 instead of 403.

**Step 3: Add the ownership check**

After decoding session JSON and before returning it, compare its `user_id` with `current_user["user_id"]`. Return a generic 403 without disclosing the owner.

**Step 4: Run the test to verify GREEN**

```bash
cd backend && pytest tests/test_get_base_data.py tests/test_store_base_data.py -v
```

Expected: selected tests pass.

**Step 5: Commit**

```bash
git add backend/api/session.py backend/tests/test_get_base_data.py
git commit -m "fix: enforce temporary session ownership"
```

### Task 4: Protect OAuth state and callback configuration

**Files:**
- Modify: `backend/api/auth.py:42-206`
- Modify: `backend/tests/test_auth_sso.py`

**Step 1: Write failing OAuth tests**

Add tests proving:

```python
async def test_sso_login_sets_state_cookie_and_authorization_state(): ...
async def test_sso_login_requires_configured_redirect_uri(): ...
async def test_callback_rejects_missing_state(): ...
async def test_callback_rejects_mismatched_state(): ...
async def test_callback_accepts_matching_state_and_clears_cookie(): ...
```

Patch MSAL, the configured Entra values, and the fixed redirect URI. Assert the authorization-code exchange always uses that configured URI.

**Step 2: Run tests to verify RED**

```bash
cd backend && pytest tests/test_auth_sso.py -v
```

Expected: failures because login does not set state and callback does not validate it.

**Step 3: Implement state generation and validation**

Use `secrets.token_urlsafe(32)` for state and `hmac.compare_digest` for validation. Store state in a ten-minute HttpOnly, `SameSite=Lax` cookie scoped to `/api`. Include it in MSAL's authorization URL.

Accept callback state as optional so missing state produces a controlled HTTP 400 response. Delete the state cookie on success and on validation failure.

**Step 4: Require a fixed redirect URI**

Treat SSO as configured only when tenant ID, client ID, client secret, and `ENTRA_REDIRECT_URI` are all present. Remove request Host and `X-Forwarded-Proto` redirect construction.

**Step 5: Run tests to verify GREEN**

```bash
cd backend && pytest tests/test_auth_sso.py -v
```

Expected: all SSO tests pass.

**Step 6: Commit**

```bash
git add backend/api/auth.py backend/tests/test_auth_sso.py
git commit -m "fix: validate oauth state and redirect uri"
```

### Task 5: Restore frontend production compilation

**Files:**
- Modify as reported: `frontend/src/screens/Admin/resources/TeamsAccessPanel.jsx`
- Modify as reported: `frontend/src/components/TeamMembershipManagement.jsx`
- Modify only additional files named by subsequent Vite transform errors

**Step 1: Reproduce the compiler failure**

```bash
cd frontend && npm run build
```

Expected: failure at `TeamsAccessPanel.jsx:132`, where `InputProps{{` is invalid JSX.

**Step 2: Apply the minimal syntax correction**

Change `InputProps{{` to `InputProps={{`.

**Step 3: Re-run the build**

```bash
cd frontend && npm run build
```

Expected: either success or the next precise transform error.

**Step 4: Repair each subsequent transform error separately**

For every new compiler error, inspect the neighboring component pattern, make the smallest syntax/identifier correction, and rerun the build before proceeding. The known stray `>` in `TeamMembershipManagement.jsx:206` should be removed if it becomes the next failure.

Do not perform broad lint cleanup or unrelated UI refactoring.

**Step 5: Verify GREEN**

```bash
cd frontend && npm run build
```

Expected: exit 0 and a generated `dist` bundle.

**Step 6: Commit**

```bash
git add frontend/src
git commit -m "fix: restore frontend production build"
```

### Task 6: Final focused verification

**Files:** No production changes expected.

**Step 1: Run focused backend security tests**

```bash
cd backend && pytest tests/test_session_token_validation.py tests/test_get_base_data.py tests/test_store_base_data.py tests/test_auth_sso.py -v
```

Expected: all selected tests pass.

**Step 2: Run the frontend production build**

```bash
cd frontend && npm run build
```

Expected: exit 0.

**Step 3: Confirm SSH removal**

```bash
rg -n 'openssh|root:Docker|sshd_config|EXPOSE 2222|/usr/sbin/sshd' Dockerfile supervisor/start.sh
```

Expected: no matches.

**Step 4: Inspect repository state**

```bash
git status --short
git diff --check
```

Expected: only intentional changes, with no whitespace errors or generated audit logs.
