from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_local_setup_uses_registered_health_endpoint_and_current_ports():
    guide = _read("docs/doc_running_local.md")
    assert "/api/health_check" not in guide
    assert "http://localhost:8502/health" in guide
    assert "http://localhost:8503" in guide


def test_readme_points_to_existing_crewai_configuration():
    readme = _read("README.md")
    assert "backend/config/agents.yaml" not in readme
    assert "backend/config/tasks.yaml" not in readme
    assert "backend/utils/config/agents_proposal.yaml" in readme
    assert "docs/doc_running_local.md" in readme


def test_security_docs_match_session_implementation():
    security = _read("docs/SECURITY_OVERVIEW.md")
    assert "8 hours" in security
    assert "refresh tokens (24 hours)" not in security.lower()
    assert "does not issue a\nrefresh token" in security.lower()
    assert "HttpOnly" in security
    assert "SameSite=Lax" in security
    assert "Redis" in security


def test_sso_docs_explain_local_redirect_uri_inference():
    tutorial = _read("docs/sso_setup_tutorial.md")
    redirect_row = next(line for line in tutorial.splitlines() if "`ENTRA_REDIRECT_URI`" in line)
    assert "production" in redirect_row.lower()
    assert "development" in redirect_row.lower()
    assert "outside development" in redirect_row.lower()
    assert "inferred" in redirect_row.lower()
    assert "http://localhost:8502/api/callback" in tutorial


def test_architecture_plan_does_not_claim_unimplemented_refresh_tokens():
    plan = _read("specs/001-proposal_drafter/plan.md")
    assert "Implemented with refresh tokens" not in plan
    assert "React 19" in plan
    assert "Material UI (MUI) v6" in plan
    assert "Object-Level Authorization | HIGH | CRITICAL | 3-5 days | ✅ COMPLETE" in plan


def test_api_docs_report_the_current_token_lifetime():
    for relative_path in ("docs/README.md", "docs/OPENAPI_DOCUMENTATION.md"):
        document = _read(relative_path)
        assert "Tokens expire after 1 hour" not in document
        assert "Tokens expire after 8 hours" in document
