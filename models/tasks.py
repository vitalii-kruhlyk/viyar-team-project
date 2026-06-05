from enum import Enum
from typing import Any


class TaskStatus(Enum):
    NEW = "new"
    IN_PROGRESS = "in progress"
    DONE = "done"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str) -> "TaskStatus":
        normalized = value.lower().replace("_", " ")
        for status in cls:
            if status.value == normalized:
                return status
        allowed = ", ".join(f"'{s.value}'" for s in cls)
        raise ValueError(f"Invalid status '{value}'. Allowed: {allowed}")


class Task:
    id: int
    title: str
    description: str | None
    status: TaskStatus

    def __init__(
        self,
        task_id: int,
        title: str,
        description: str | None = None,
        status: TaskStatus = TaskStatus.NEW,
    ) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title must be a non-empty string")
        self.id = task_id
        self.title = title.strip()
        self.description = description.strip() if description else None
        self.status = status

    def edit_title(self, title: str) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title must be a non-empty string")
        self.title = title.strip()

    def edit_description(self, description: str | None) -> None:
        self.description = (
            description.strip() if description and description.strip() else None
        )

    def __str__(self) -> str:
        parts = [f"[{self.id}] {self.title} ({self.status})"]
        if self.description:
            parts.append(f"  {self.description}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
        }
        if self.description is not None:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        task_id = data.get("id")
        if not isinstance(task_id, int):
            raise ValueError("Task id is missing or invalid")

        title = data.get("title")
        if not isinstance(title, str):
            raise ValueError("Task title is missing or invalid")

        description = data.get("description")
        status = TaskStatus.from_str(data.get("status", TaskStatus.NEW.value))

        return cls(task_id, title, description, status)


class TaskBook:
    _tasks: dict[int, Task]
    _next_id: int

    def __init__(self) -> None:
        self._tasks = {}
        self._next_id = 1

    def add_task(self, title: str, description: str | None = None) -> Task:
        task = Task(self._next_id, title, description)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def find(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def delete(self, task_id: int) -> None:
        if task_id not in self._tasks:
            raise KeyError(f"Task with id {task_id} not found")
        del self._tasks[task_id]

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def search(self, query: str) -> list[Task]:
        query_lower = query.lower()
        results = []
        for task in self._tasks.values():
            if query_lower in task.title.lower():
                results.append(task)
            elif task.description and query_lower in task.description.lower():
                results.append(task)
        return results

    def filter_by_status(self, status: TaskStatus) -> list[Task]:
        return [task for task in self._tasks.values() if task.status == status]

    def to_list(self) -> list[dict[str, Any]]:
        return [task.to_dict() for task in self._tasks.values()]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]]) -> "TaskBook":
        book = cls()
        for item in data:
            task = Task.from_dict(item)
            book._tasks[task.id] = task
            if task.id >= book._next_id:
                book._next_id = task.id + 1
        return book
