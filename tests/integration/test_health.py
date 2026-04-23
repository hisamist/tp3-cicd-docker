import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client_healthy(monkeypatch):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    monkeypatch.setattr("src.db.psycopg2.connect", lambda *a, **kw: mock_conn)

    mock_r = MagicMock()
    mock_r.ping.return_value = True
    monkeypatch.setattr("src.cache.r", mock_r)

    from src.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_db_down(monkeypatch):
    # init_db runs on startup — let it pass, then fail on health check calls
    call_count = {"n": 0}
    original_connect = __import__("psycopg2").connect

    def connect_fails_after_startup(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # First call is from init_db at startup — succeed
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = MagicMock()
            return mock_conn
        raise Exception("Connection refused")

    monkeypatch.setattr("src.db.psycopg2.connect", connect_fails_after_startup)
    mock_r = MagicMock()
    mock_r.ping.return_value = True
    monkeypatch.setattr("src.cache.r", mock_r)

    from src.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_redis_down(monkeypatch):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    monkeypatch.setattr("src.db.psycopg2.connect", lambda *a, **kw: mock_conn)

    mock_r = MagicMock()
    mock_r.ping.side_effect = Exception("Redis unavailable")
    monkeypatch.setattr("src.cache.r", mock_r)

    from src.main import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_healthy_returns_200(self, client_healthy):
        resp = client_healthy.get("/health")
        assert resp.status_code == 200

    def test_healthy_status_field(self, client_healthy):
        data = client_healthy.get("/health").json()
        assert data["status"] == "healthy"

    def test_healthy_services_connected(self, client_healthy):
        data = client_healthy.get("/health").json()
        assert data["services"]["database"] == "connected"
        assert data["services"]["cache"] == "connected"

    def test_healthy_has_timestamp(self, client_healthy):
        data = client_healthy.get("/health").json()
        assert "timestamp" in data

    def test_db_down_returns_503(self, client_db_down):
        resp = client_db_down.get("/health")
        assert resp.status_code == 503

    def test_db_down_status_unhealthy(self, client_db_down):
        data = client_db_down.get("/health").json()
        assert data["status"] == "unhealthy"
        assert "error" in data["services"]["database"]

    def test_redis_down_returns_503(self, client_redis_down):
        resp = client_redis_down.get("/health")
        assert resp.status_code == 503

    def test_redis_down_status_unhealthy(self, client_redis_down):
        data = client_redis_down.get("/health").json()
        assert data["status"] == "unhealthy"
        assert "error" in data["services"]["cache"]


class TestRootEndpoint:
    def test_root_returns_200(self, client_healthy):
        resp = client_healthy.get("/")
        assert resp.status_code == 200

    def test_root_welcome_message(self, client_healthy):
        data = client_healthy.get("/").json()
        assert "message" in data
