import pytest
from pydantic import ValidationError
from src.schemas.task import Task, TaskCreate, TaskUpdate


class TestTaskCreate:
    def test_minimal_valid(self):
        task = TaskCreate(title="Buy milk")
        assert task.title == "Buy milk"
        assert task.description is None
        assert task.completed is False

    def test_full_valid(self):
        task = TaskCreate(title="Buy milk", description="2% fat", completed=True)
        assert task.description == "2% fat"
        assert task.completed is True

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate()

    def test_empty_title_allowed(self):
        # Pydantic allows empty string unless constrained
        task = TaskCreate(title="")
        assert task.title == ""

    def test_extra_fields_ignored(self):
        task = TaskCreate(title="Test", unknown_field="ignored")
        assert not hasattr(task, "unknown_field")


class TestTaskUpdate:
    def test_defaults(self):
        update = TaskUpdate(title="Updated")
        assert update.completed is False
        assert update.description is None

    def test_partial_fields(self):
        update = TaskUpdate(title="New title", completed=True)
        assert update.title == "New title"
        assert update.completed is True

    def test_model_dump_exclude_unset(self):
        update = TaskUpdate(title="Only title")
        dumped = update.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "description" not in dumped
        assert "completed" not in dumped

    def test_model_dump_all_fields_set(self):
        update = TaskUpdate(title="T", description="D", completed=True)
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"title": "T", "description": "D", "completed": True}


class TestTask:
    def test_valid_task(self):
        task = Task(id=1, title="Buy milk", description="2% fat", completed=False)
        assert task.id == 1

    def test_id_required(self):
        with pytest.raises(ValidationError):
            Task(title="No ID")

    def test_serialization(self):
        task = Task(id=42, title="Test", completed=True)
        data = task.model_dump()
        assert data["id"] == 42
        assert data["title"] == "Test"
        assert data["completed"] is True
        assert data["description"] is None
