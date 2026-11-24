from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import SERVICE_NAME, database_url
from app.database import engine
from app.errors import configure_http
from app.main import app


def test_database_identity_and_version():
    with engine.connect() as connection:
        actual_name = connection.scalar(text("SELECT current_database()"))
        version = int(connection.scalar(text("SHOW server_version_num")))
    assert actual_name == database_url().database == "f168_" + SERVICE_NAME
    assert 160000 <= version < 170000


def test_health_uses_real_postgres():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"service": SERVICE_NAME, "status": "ok", "database": "ok"}


def test_request_id_is_preserved_on_http_error():
    request_id = str(uuid4())
    with TestClient(app) as client:
        response = client.post("/health", headers={"X-Request-ID": request_id})
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"] == request_id


@pytest.mark.parametrize("mode,status,code", [
    ("bad-input", 422, "VALIDATION_ERROR"),
    ("crash", 500, "INTERNAL_ERROR"),
])
def test_error_does_not_echo_inputs_or_exception(caplog, mode, status, code):
    # Chỉ đăng ký hai route trên app test riêng, không thêm endpoint vào service.
    probe = FastAPI()
    configure_http(probe)

    @probe.get("/number/{value}")
    def number(value: int):
        return value

    @probe.get("/crash")
    def crash():
        raise RuntimeError("private-test-marker")

    path = "/crash" if mode == "crash" else "/number/private-test-marker"
    with TestClient(probe) as client:
        response = client.get(path, headers={"X-Request-ID": "invalid-id"})
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code and error["details"] == {}
    assert str(UUID(error["request_id"])) == response.headers["X-Request-ID"]
    assert "private-test-marker" not in response.text
    assert "private-test-marker" not in caplog.text
