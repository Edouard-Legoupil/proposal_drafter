# Local SSO Redirect Inference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow local development SSO to infer `/api/callback` from the request while preserving the explicit redirect URI requirement outside development.

**Architecture:** Add one redirect resolver in the authentication API. It prefers an explicitly configured URI, falls back to FastAPI's named callback route only in development, and returns no URI elsewhere. The status, login, and callback flows will share the same environment rule, while login and callback share the exact resolved URI.

**Tech Stack:** Python 3.10+, FastAPI/Starlette URL routing, MSAL, pytest, `unittest.mock`

---

### Task 1: Specify redirect resolution and SSO availability

**Files:**
- Modify: `backend/tests/test_auth_sso.py:1-51`
- Modify: `backend/api/auth.py:20-71`

**Step 1: Write failing resolver and status tests**

Import `sso_status` and the new resolver, make the request double return a realistic callback URL, and add focused tests:

```python
from backend.api.auth import _resolve_sso_redirect_uri, callback, sso_login, sso_status


def _mock_request(*, cookies=None):
    request = MagicMock(spec=Request)
    request.cookies = cookies or {}
    request.headers = {"host": "localhost"}
    request.url_for.return_value = "http://localhost:8502/api/callback"
    return request


def test_redirect_uri_prefers_explicit_configuration():
    with patch("backend.api.auth.ENTRA_REDIRECT_URI", "https://app.example/api/callback"), patch(
        "backend.api.auth.APP_ENV", "development"
    ):
        redirect_uri = _resolve_sso_redirect_uri(_mock_request())

    assert redirect_uri == "https://app.example/api/callback"


def test_redirect_uri_is_inferred_in_development():
    request = _mock_request()
    with patch("backend.api.auth.ENTRA_REDIRECT_URI", None), patch(
        "backend.api.auth.APP_ENV", "development"
    ):
        redirect_uri = _resolve_sso_redirect_uri(request)

    assert redirect_uri == "http://localhost:8502/api/callback"
    request.url_for.assert_called_once_with("callback")


def test_redirect_uri_is_not_inferred_outside_development():
    request = _mock_request()
    with patch("backend.api.auth.ENTRA_REDIRECT_URI", None), patch(
        "backend.api.auth.APP_ENV", "production"
    ):
        redirect_uri = _resolve_sso_redirect_uri(request)

    assert redirect_uri is None
    request.url_for.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("environment", "configured_redirect", "expected"),
    [
        ("development", None, True),
        ("production", None, False),
        ("production", "https://app.example/api/callback", True),
    ],
)
async def test_sso_status_redirect_availability(environment, configured_redirect, expected):
    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", configured_redirect
    ), patch("backend.api.auth.APP_ENV", environment):
        response = await sso_status()

    assert response == {"enabled": expected}
```

**Step 2: Run the new tests and verify RED**

Run:

```bash
pytest backend/tests/test_auth_sso.py -k "redirect_uri or sso_status" -v
```

Expected: collection fails because `_resolve_sso_redirect_uri` does not exist, or the new inference assertions fail against the existing behavior.

**Step 3: Implement the minimal resolver and status rule**

In `backend/api/auth.py`, import `APP_ENV` directly from configuration and add:

```python
from backend.core.config import APP_ENV


def _has_sso_credentials() -> bool:
    return bool(ENTRA_TENANT_ID and ENTRA_CLIENT_ID and ENTRA_CLIENT_SECRET)


def _redirect_uri_available() -> bool:
    return bool(ENTRA_REDIRECT_URI or APP_ENV == "development")


def _resolve_sso_redirect_uri(request: Request) -> str | None:
    if ENTRA_REDIRECT_URI:
        return ENTRA_REDIRECT_URI
    if APP_ENV == "development":
        return str(request.url_for("callback"))
    return None
```

Change `sso_status` to:

```python
@router.get("/sso-status")
async def sso_status():
    return {"enabled": _has_sso_credentials() and _redirect_uri_available()}
```

**Step 4: Run the focused tests and verify GREEN**

Run:

```bash
pytest backend/tests/test_auth_sso.py -k "redirect_uri or sso_status" -v
```

Expected: all selected tests pass.

**Step 5: Commit the resolver**

```bash
git add backend/api/auth.py backend/tests/test_auth_sso.py
git commit -m "feat(auth): infer local SSO redirect URI"
```

### Task 2: Use the inferred URI throughout OAuth

**Files:**
- Modify: `backend/tests/test_auth_sso.py:16-127`
- Modify: `backend/api/auth.py:65-115`

**Step 1: Write failing login and callback tests**

Replace the old test that requires a configured URI with a production-specific test, then add a development inference test:

```python
@pytest.mark.asyncio
async def test_sso_login_infers_redirect_uri_in_development():
    mock_msal_app = MagicMock()
    mock_msal_app.get_authorization_request_url.return_value = "https://login.example/authorize"

    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", None
    ), patch("backend.api.auth.APP_ENV", "development"), patch(
        "backend.api.auth._get_msal_app", return_value=mock_msal_app
    ), patch("backend.api.auth.secrets.token_urlsafe", return_value="expected-state"):
        response = await sso_login(_mock_request())

    assert response.status_code == 307
    mock_msal_app.get_authorization_request_url.assert_called_once_with(
        scopes=["User.Read"],
        redirect_uri="http://localhost:8502/api/callback",
        state="expected-state",
    )


@pytest.mark.asyncio
async def test_sso_login_requires_configured_redirect_uri_in_production():
    with patch("backend.api.auth.ENTRA_TENANT_ID", "tenant"), patch(
        "backend.api.auth.ENTRA_CLIENT_ID", "client"
    ), patch("backend.api.auth.ENTRA_CLIENT_SECRET", "secret"), patch(
        "backend.api.auth.ENTRA_REDIRECT_URI", None
    ), patch("backend.api.auth.APP_ENV", "production"):
        response = await sso_login(_mock_request())

    assert response.status_code == 503
```

Update `test_sso_callback_group_mapping` so `ENTRA_REDIRECT_URI` is `None`, `APP_ENV` is `development`, and its final MSAL assertion expects `http://localhost:8502/api/callback`. This proves the token exchange uses the same inferred value as authorization.

**Step 2: Run the OAuth tests and verify RED**

Run:

```bash
pytest backend/tests/test_auth_sso.py -k "login or callback_group_mapping" -v
```

Expected: the development login or callback assertion fails because the endpoints still pass `ENTRA_REDIRECT_URI` directly.

**Step 3: Resolve once per endpoint and pass the result to MSAL**

At the beginning of `sso_login`:

```python
redirect_uri = _resolve_sso_redirect_uri(request)
if not _has_sso_credentials() or not redirect_uri:
    return JSONResponse(status_code=503, content={"error": "SSO not configured"})
```

Pass `redirect_uri` to `get_authorization_request_url`.

At the beginning of `callback`, apply the same resolution and availability check. Keep OAuth state validation unchanged, then pass `redirect_uri` to `acquire_token_by_authorization_code`.

**Step 4: Run the SSO test module and verify GREEN**

Run:

```bash
pytest backend/tests/test_auth_sso.py -v
```

Expected: all tests pass, including state validation and group mapping.

**Step 5: Run authentication regression tests**

Run:

```bash
pytest backend/tests/test_auth_authorization.py backend/tests/test_session_token_validation.py -v
```

Expected: all tests pass.

**Step 6: Commit OAuth integration**

```bash
git add backend/api/auth.py backend/tests/test_auth_sso.py
git commit -m "fix(auth): reuse inferred URI across SSO flow"
```

### Task 3: Update configuration documentation

**Files:**
- Modify: `backend/tests/test_documentation_contract.py:35-42`
- Modify: `docs/sso_setup_tutorial.md:13-56`
- Modify: `.env.example:95-100`
- Modify: `backend/.env.example:38-42`

**Step 1: Update the documentation contract first**

Replace the existing unconditional requirement test with:

```python
def test_sso_docs_describe_local_inference_and_production_redirect_requirement():
    tutorial = _read("docs/sso_setup_tutorial.md")
    redirect_row = next(line for line in tutorial.splitlines() if "`ENTRA_REDIRECT_URI`" in line)
    assert "production" in redirect_row.lower()
    assert "development" in redirect_row.lower()
    assert "inferred" in redirect_row.lower()
    assert "http://localhost:8502/api/callback" in tutorial
```

**Step 2: Run the documentation contract and verify RED**

Run:

```bash
pytest backend/tests/test_documentation_contract.py::test_sso_docs_describe_local_inference_and_production_redirect_requirement -v
```

Expected: FAIL because the tutorial still says the redirect URI is always required and never inferred.

**Step 3: Update the tutorial and examples**

In `docs/sso_setup_tutorial.md`:

- State that local development infers `http://localhost:8502/api/callback` when the variable is absent.
- State that this exact URI must still be registered in Entra.
- State that production requires an explicit `ENTRA_REDIRECT_URI` matching the registered public callback.
- Update verification so local `/api/sso-status` requires the three Entra credentials, while production also requires the redirect variable.

In `.env.example`, replace the incorrect `/auth/callback` example with a commented production example:

```dotenv
# Required outside development; local development infers http://localhost:8502/api/callback
# ENTRA_REDIRECT_URI="https://proposal.example/api/callback"
```

Add the same commented guidance to `backend/.env.example`.

**Step 4: Run documentation and SSO tests**

Run:

```bash
pytest backend/tests/test_documentation_contract.py backend/tests/test_auth_sso.py -v
```

Expected: all tests pass.

**Step 5: Commit documentation**

```bash
git add .env.example backend/.env.example docs/sso_setup_tutorial.md backend/tests/test_documentation_contract.py
git commit -m "docs(auth): explain local SSO callback inference"
```

### Task 4: Final verification

**Files:**
- Verify only; no expected changes

**Step 1: Run backend lint checks on changed Python files**

Run:

```bash
ruff check --line-length 120 backend/api/auth.py backend/tests/test_auth_sso.py backend/tests/test_documentation_contract.py
```

Expected: exit code 0 with no findings.

**Step 2: Run the complete backend test suite**

Run:

```bash
pytest backend/tests/
```

Expected: all tests pass.

**Step 3: Verify patch cleanliness**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors. Only intentional changes or the user's pre-existing `frontend/.env` edit may remain.

**Step 4: Perform a local configuration smoke check**

Launch with `APP_ENV=development`, the three Entra credentials, and no `ENTRA_REDIRECT_URI`. Request:

```bash
curl --fail --silent --show-error http://localhost:8502/api/sso-status
```

Expected:

```json
{"enabled":true}
```

Open `http://localhost:8502/api/sso-login` and confirm the Entra authorization URL contains the URL-encoded value of `http://localhost:8502/api/callback`. Do not complete the flow unless that callback is registered in the Entra application.
