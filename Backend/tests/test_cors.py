from fastapi.testclient import TestClient
from app.main import app


def test_cors_allows_local_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/users/",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:4200"
