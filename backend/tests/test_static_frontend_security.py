from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.testclient import TestClient

from backend.core.middleware import setup_security_middleware
from backend.main import resolve_frontend_file


def test_frontend_file_resolution_stays_inside_distribution_root(tmp_path):
    frontend_root = tmp_path / "dist"
    frontend_root.mkdir()
    asset = frontend_root / "assets" / "app.js"
    asset.parent.mkdir()
    asset.write_text("safe", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    assert resolve_frontend_file(frontend_root, "assets/app.js") == asset.resolve()
    assert resolve_frontend_file(frontend_root, "../secret.txt") is None
    assert resolve_frontend_file(frontend_root, "%2e%2e/secret.txt") is None


def test_hashed_static_assets_are_cacheable_and_receive_security_headers():
    app = FastAPI()
    setup_security_middleware(app)

    @app.get("/assets/app-a1b2c3.js")
    async def asset():
        return Response("javascript", media_type="application/javascript")

    response = TestClient(app).get("/assets/app-a1b2c3.js")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
