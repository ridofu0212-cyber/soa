"""Black-box Phase 1. Chạy sau khi gateway và ba DB đã sẵn sàng."""
import os
from uuid import uuid4

import httpx
import pytest


@pytest.fixture(scope="module")
def client():
    base = os.getenv("F168_GATEWAY_URL", "http://127.0.0.1:8080")
    with httpx.Client(base_url=base, trust_env=False, timeout=10) as http:
        yield http


@pytest.mark.parametrize("name", ["user", "loan", "payment"])
def test_health_swagger_and_openapi(client, name):
    health = client.get("/health/" + name)
    assert health.status_code == 200
    assert health.json() == {"service": name, "status": "ok", "database": "ok"}
    docs = client.get("/docs/" + name)
    assert docs.status_code == 200 and "/openapi/" + name + ".json" in docs.text
    schema = client.get("/openapi/" + name + ".json").json()
    assert schema["info"]["title"] == f"F168 {name.capitalize()} Service"
    assert list(schema["paths"]) == ["/health/" + name]


@pytest.mark.parametrize("name,path", [
    ("user", "auth/login"), ("user", "users/me"),
    ("loan", "loan-products"), ("loan", "loan-applications"), ("loan", "loans"),
    ("loan", "installments/sample"), ("loan", "admin/loan-products"),
    ("loan", "admin/loan-applications"), ("loan", "admin/loans"),
    ("payment", "payment-otp-requests"), ("payment", "payment-otp-verifications"),
    ("payment", "payment-transactions"), ("payment", "admin/payment-transactions"),
])
def test_reserved_resource_reaches_owner(client, name, path):
    request_id = str(uuid4())
    response = client.get("/api/v1/" + path, headers={"X-Request-ID": request_id})
    # Phase 1 đã nối mạng; 404 từ đúng backend vì nghiệp vụ thuộc phase sau.
    assert response.status_code == 404
    assert response.headers["X-Service-Name"] == name
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"] == request_id


@pytest.mark.parametrize("path", [
    "/api/v1/internal", "/api/v1/internal/", "/api/v1/internal/users/demo/verification",
    "/api/v1/internal/installments/demo/settlements",
])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_gateway_blocks_internal(client, path, method):
    response = client.request(method, path, headers={"X-Internal-Token": "test-marker"})
    assert response.status_code == 403
    assert "X-Service-Name" not in response.headers
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_ROUTE_FORBIDDEN"
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_unknown_api_is_json(client):
    response = client.get("/api/v1/missing", headers={"X-Request-ID": "invalid-value"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROUTE_NOT_FOUND"
    assert response.headers["X-Request-ID"] != "invalid-value"


def test_gateway_serves_build_and_swagger_assets(client):
    assert client.get("/health/gateway").json() == {"service": "gateway", "status": "ok"}
    response = client.get("/")
    assert response.status_code == 200 and 'id="root"' in response.text
    for path in ["/swagger-assets/swagger-ui.css", "/swagger-assets/swagger-ui-bundle.js"]:
        asset = client.get(path)
        assert asset.status_code == 200 and len(asset.content) > 1000
