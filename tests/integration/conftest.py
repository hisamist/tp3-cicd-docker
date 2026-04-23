import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def make_task_row(id=1, title="Test task", description="Desc", completed=False):
    """Return a dict mimicking RealDictCursor row."""
    return {"id": id, "title": title, "description": description, "completed": completed}


@pytest.fixture
def mock_db(monkeypatch):
    """Patch get_db_connection globally and return the mock cursor for per-test setup."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    monkeypatch.setattr("src.db.psycopg2.connect", lambda *a, **kw: mock_conn)
    return mock_cur


@pytest.fixture
def mock_redis(monkeypatch):
    mock_r = MagicMock()
    mock_r.ping.return_value = True
    monkeypatch.setattr("src.cache.r", mock_r)
    return mock_r


@pytest.fixture
def client(mock_db, mock_redis):
    from src.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
