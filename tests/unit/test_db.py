import pytest
from unittest.mock import MagicMock, patch, call


class TestGetDbConnection:
    @patch("src.db.psycopg2.connect")
    def test_uses_database_url_env(self, mock_connect):
        mock_connect.return_value = MagicMock()
        from src.db import get_db_connection
        get_db_connection()
        mock_connect.assert_called_once()

    @patch("src.db.psycopg2.connect")
    def test_returns_connection(self, mock_connect):
        fake_conn = MagicMock()
        mock_connect.return_value = fake_conn
        from src.db import get_db_connection
        conn = get_db_connection()
        assert conn is fake_conn

    @patch("src.db.psycopg2.connect", side_effect=Exception("DB down"))
    def test_propagates_connection_error(self, mock_connect):
        from src.db import get_db_connection
        with pytest.raises(Exception, match="DB down"):
            get_db_connection()


class TestInitDb:
    @patch("src.db.get_db_connection")
    def test_creates_tasks_table(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_conn.return_value = mock_conn

        from src.db import init_db
        init_db()

        executed_sql = mock_cur.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS tasks" in executed_sql
        mock_conn.commit.assert_called_once()
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()
