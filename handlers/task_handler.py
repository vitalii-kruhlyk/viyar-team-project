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
            "task_add": self.add_task,
            "task_edit": self.edit_task,
            "task_edit_desc": self.edit_task_desc,
            "task_delete": self.delete_task,
            "task_show": self.show_tasks,
            "task_search": self.search_task,
            "task_status": self.task_status,
            "task_by_status": self.tasks_by_status,
        }
        self.descriptions = {
            "task_add": "Create a new task: task_add <title>",
            "task_edit": "Edit task title: task_edit <id> <new_title>",
            "task_edit_desc": (
                "Edit task description: task_edit_desc <id> <new_description>"
            ),
            "task_delete": "Delete a task: task_delete <id>",
            "task_show": "Show all tasks",
            "task_search": "Search tasks by title or description: task_search <query>",
            "task_status": (
                "Change task status: task_status <id> <status>"
                "  (new, in_progress, done, cancelled)"
            ),
            "task_by_status": "Filter tasks by status: task_by_status <status>",
        }

    def _save(self) -> None:
        self.storage.save(self.book.to_list())

    @input_error
    def add_task(self, args: list[str]) -> tuple[str, bool]:
        if not args:
            raise ValueError("Usage: task_add <title>")

        title = " ".join(args)
        task = self.book.add_task(title)
        self._save()
        return f"Task [{task.id}] '{task.title}' created.", False

    @input_error
    def edit_task(self, args: list[str]) -> tuple[str, bool]:
        if len(args) < 2:
            raise ValueError("Usage: task_edit <id> <new_title>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_title = " ".join(args[1:])

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        task.edit_title(new_title)
        self._save()
        return f"Task [{task_id}] title updated to '{task.title}'.", False

    @input_error
    def edit_task_desc(self, args: list[str]) -> tuple[str, bool]:
        if len(args) < 2:
            raise ValueError("Usage: task_edit_desc <id> <new_description>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_desc = " ".join(args[1:])

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        task.edit_description(new_desc)
        self._save()
        return f"Task [{task_id}] description updated.", False

    @input_error
    def delete_task(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: task_delete <id>")

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
        if not args:
            raise ValueError("Usage: task_search <query>")

        query = " ".join(args)
        results = self.book.search(query)
        if not results:
            return f"No tasks found for query: {query}", False

        return "\n".join(str(task) for task in results), False

    @input_error
    def task_status(self, args: list[str]) -> tuple[str, bool]:
        if len(args) < 2:
            raise ValueError("Usage: task_status <id> <status>")

        if not args[0].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(args[0])
        new_status = TaskStatus.from_str(" ".join(args[1:]))

        task = self.book.find(task_id)
        if task is None:
            raise KeyError

        task.status = new_status
        self._save()
        return f"Task [{task_id}] status changed to '{new_status}'.", False

    @input_error
    def tasks_by_status(self, args: list[str]) -> tuple[str, bool]:
        if not args:
            raise ValueError("Usage: task_by_status <status>")

        status = TaskStatus.from_str(" ".join(args))
        results = self.book.filter_by_status(status)

        if not results:
            return f"No tasks with status '{status}'.", False

        return "\n".join(str(task) for task in results), False
