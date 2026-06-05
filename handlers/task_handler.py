from collections.abc import Callable

from handlers.decorators import input_error
from models import TaskBook, TaskStatus
from storage import JsonStorage


class TaskHandler:
    storage: JsonStorage
    book: TaskBook
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]
    descriptions: dict[str, str]

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = TaskBook.from_list(storage.load())
        self.commands = {
            "add_task": self.add_task,
            "edit_task": self.edit_task,
            "edit_task_desc": self.edit_task_desc,
            "delete_task": self.delete_task,
            "show_tasks": self.show_tasks,
            "search_task": self.search_task,
            "task_status": self.task_status,
            "tasks_by_status": self.tasks_by_status,
        }
        self.descriptions = {
            "add_task": "Create a new task: add_task <title>",
            "edit_task": "Edit task title: edit_task <id> <new_title>",
            "edit_task_desc": (
                "Edit task description: edit_task_desc <id> <new_description>"
            ),
            "delete_task": "Delete a task: delete_task <id>",
            "show_tasks": "Show all tasks",
            "search_task": "Search tasks by title or description: search_task <query>",
            "task_status": (
                "Change task status: task_status <id> <status>"
                "  (new, in_progress, done, cancelled)"
            ),
            "tasks_by_status": "Filter tasks by status: tasks_by_status <status>",
        }

    def _save(self) -> None:
        self.storage.save(self.book.to_list())

    @input_error
    def add_task(self, args: list[str]) -> tuple[str, bool]:
        if not args:
            raise ValueError("Usage: add_task <title>")

        title = args[0]
        task = self.book.add_task(title)
        self._save()
        return f"Task [{task.id}] '{task.title}' created.", False

    @input_error
    def edit_task(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: edit_task <id> <new_title>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_title = args[1]

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        if not new_title.strip():
            raise ValueError("Task title must be a non-empty string")

        task.title = new_title.strip()
        self._save()
        return f"Task [{task_id}] title updated to '{task.title}'.", False

    @input_error
    def edit_task_desc(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: edit_task_desc <id> <new_description>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_desc = args[1]

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        task.description = new_desc.strip() if new_desc.strip() else None
        self._save()
        return f"Task [{task_id}] description updated.", False

    @input_error
    def delete_task(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: delete_task <id>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])

        if self.book.find(task_id) is None:
            raise KeyError

        self.book.delete(task_id)
        self._save()
        return f"Task [{task_id}] deleted.", False

    @input_error
    def show_tasks(self, _args: list[str]) -> tuple[str, bool]:
        tasks = self.book.all_tasks()
        if not tasks:
            return "No tasks found.", False

        return "\n".join(str(task) for task in tasks), False

    @input_error
    def search_task(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: search_task <query>")

        results = self.book.search(args[0])
        if not results:
            return f"No tasks found for query: {args[0]}", False

        return "\n".join(str(task) for task in results), False

    @input_error
    def task_status(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: task_status <id> <status>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_status = TaskStatus.from_str(args[1])

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        task.status = new_status
        self._save()
        return f"Task [{task_id}] status changed to '{new_status}'.", False

    @input_error
    def tasks_by_status(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: tasks_by_status <status>")

        status = TaskStatus.from_str(args[0])
        results = self.book.filter_by_status(status)

        if not results:
            return f"No tasks with status '{status}'.", False

        return "\n".join(str(task) for task in results), False
