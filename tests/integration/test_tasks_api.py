import pytest
from tests.integration.conftest import make_task_row


class TestGetTasks:
    def test_returns_empty_list(self, client, mock_db):
        mock_db.fetchall.return_value = []
        resp = client.get("/api/tasks/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_list_of_tasks(self, client, mock_db):
        mock_db.fetchall.return_value = [
            make_task_row(1, "Task 1"),
            make_task_row(2, "Task 2"),
        ]
        resp = client.get("/api/tasks/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"

    def test_task_shape(self, client, mock_db):
        mock_db.fetchall.return_value = [make_task_row(1, "Buy milk", "2% fat", False)]
        data = client.get("/api/tasks/").json()
        task = data[0]
        assert set(task.keys()) == {"id", "title", "description", "completed"}


class TestGetTask:
    def test_returns_existing_task(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "Buy milk")
        resp = client.get("/api/tasks/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1
        assert resp.json()["title"] == "Buy milk"

    def test_returns_404_when_not_found(self, client, mock_db):
        mock_db.fetchone.return_value = None
        resp = client.get("/api/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Tâche non trouvée"

    def test_uses_correct_id(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(42, "Task 42")
        resp = client.get("/api/tasks/42")
        assert resp.status_code == 200
        executed_sql = mock_db.execute.call_args[0][0]
        assert "WHERE id" in executed_sql


class TestCreateTask:
    def test_creates_and_returns_task(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "New task", "Details", False)
        payload = {"title": "New task", "description": "Details"}
        resp = client.post("/api/tasks/", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["title"] == "New task"

    def test_missing_title_returns_422(self, client, mock_db):
        resp = client.post("/api/tasks/", json={"description": "No title"})
        assert resp.status_code == 422

    def test_minimal_payload(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(2, "Minimal")
        resp = client.post("/api/tasks/", json={"title": "Minimal"})
        assert resp.status_code == 200

    def test_db_commit_called(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "Task")
        client.post("/api/tasks/", json={"title": "Task"})
        # Connection commit is on the mock_conn; verify execute was called with INSERT
        executed_sql = mock_db.execute.call_args[0][0]
        assert "INSERT" in executed_sql


class TestUpdateTask:
    def test_full_update_returns_updated_task(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "Updated", "New desc", True)
        payload = {"title": "Updated", "description": "New desc", "completed": True}
        resp = client.put("/api/tasks/1", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True

    def test_returns_404_when_not_found(self, client, mock_db):
        mock_db.fetchone.return_value = None
        resp = client.put("/api/tasks/999", json={"title": "X", "completed": False})
        assert resp.status_code == 404

    def test_missing_title_returns_422(self, client, mock_db):
        resp = client.put("/api/tasks/1", json={"completed": True})
        assert resp.status_code == 422

    def test_uses_update_sql(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "T")
        client.put("/api/tasks/1", json={"title": "T", "completed": False})
        executed_sql = mock_db.execute.call_args[0][0]
        assert "UPDATE" in executed_sql


class TestPatchTask:
    def test_partial_update_title_only(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "New title")
        resp = client.patch("/api/tasks/1", json={"title": "New title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

    def test_partial_update_completed_only(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "Task", completed=True)
        resp = client.patch("/api/tasks/1", json={"title": "Task", "completed": True})
        assert resp.status_code == 200

    def test_empty_body_returns_422(self, client, mock_db):
        # TaskUpdate requires `title`; sending {} fails Pydantic validation before the route runs
        resp = client.patch("/api/tasks/1", json={})
        assert resp.status_code == 422

    def test_returns_404_when_not_found(self, client, mock_db):
        mock_db.fetchone.return_value = None
        resp = client.patch("/api/tasks/999", json={"title": "X"})
        assert resp.status_code == 404

    def test_only_sent_fields_in_update_query(self, client, mock_db):
        mock_db.fetchone.return_value = make_task_row(1, "Updated")
        client.patch("/api/tasks/1", json={"title": "Updated"})
        executed_sql = mock_db.execute.call_args[0][0]
        assert "title" in executed_sql
        assert "description" not in executed_sql


class TestDeleteTask:
    def test_delete_existing_task(self, client, mock_db):
        mock_db.fetchone.return_value = {"id": 1}
        resp = client.delete("/api/tasks/1")
        assert resp.status_code == 200
        assert "supprimée" in resp.json()["message"]

    def test_delete_returns_404_when_not_found(self, client, mock_db):
        mock_db.fetchone.return_value = None
        resp = client.delete("/api/tasks/999")
        assert resp.status_code == 404

    def test_delete_message_contains_id(self, client, mock_db):
        mock_db.fetchone.return_value = {"id": 5}
        data = client.delete("/api/tasks/5").json()
        assert "5" in data["message"]

    def test_db_commit_called_on_delete(self, client, mock_db):
        mock_db.fetchone.return_value = {"id": 1}
        client.delete("/api/tasks/1")
        executed_sql = mock_db.execute.call_args[0][0]
        assert "DELETE" in executed_sql
