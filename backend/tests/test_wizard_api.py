"""Contract tests for the read-only wizard knowledge API and feedback."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_db_session


@pytest.fixture
def wizard_client(authenticated_client):
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()

    async def override_session():
        yield db

    authenticated_client.app.dependency_overrides[get_db_session] = override_session
    yield authenticated_client, db
    authenticated_client.app.dependency_overrides.pop(get_db_session, None)


def _result(*, scalar=None, scalars=None, rows=None):
    result = MagicMock()
    result.scalar.return_value = scalar
    result.scalars.return_value.all.return_value = scalars or []
    result.all.return_value = rows or []
    return result


def test_get_categories_uses_registered_api_route(wizard_client):
    client, db = wizard_client
    db.execute.return_value = _result(scalars=[])

    response = client.get("/api/wizard/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_get_qa_items_returns_pagination_contract(wizard_client):
    client, db = wizard_client
    db.execute.side_effect = [_result(scalar=0), _result(scalars=[])]

    response = client.get("/api/wizard/qa?limit=5&offset=2")

    assert response.status_code == 200
    assert response.json() == {"total": 0, "limit": 5, "offset": 2, "items": []}


def test_search_qa_returns_search_contract(wizard_client):
    client, db = wizard_client
    db.execute.side_effect = [_result(scalar=0), _result(scalars=[])]

    response = client.post("/api/wizard/search", json={"query": "test"})

    assert response.status_code == 200
    assert response.json() == {"total": 0, "results": []}


def test_get_popular_questions(wizard_client):
    client, db = wizard_client
    db.execute.return_value = _result(rows=[])

    response = client.get("/api/wizard/popular")

    assert response.status_code == 200
    assert response.json() == []


def test_submit_feedback_uses_authenticated_user(wizard_client):
    client, db = wizard_client

    response = client.post(
        "/api/wizard/feedback",
        json={"qa_item_id": 7, "feedback_score": 5, "feedback_comment": "Helpful"},
    )

    assert response.status_code == 200
    interaction = db.add.call_args.args[0]
    assert str(interaction.user_id)
    assert interaction.qa_item_id == 7
    db.commit.assert_awaited_once()


@pytest.mark.parametrize("score", [0, 6])
def test_feedback_score_validation(wizard_client, score):
    client, db = wizard_client

    response = client.post(
        "/api/wizard/feedback",
        json={"qa_item_id": 7, "feedback_score": score, "feedback_comment": "Invalid"},
    )

    assert response.status_code in {400, 422}
    db.commit.assert_not_awaited()


def test_wizard_write_endpoints_are_not_exposed(wizard_client):
    client, _ = wizard_client

    response = client.post("/api/wizard/categories", json={"name": "Untrusted content"})

    assert response.status_code == 405
