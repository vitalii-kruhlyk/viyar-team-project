from handlers.decorators import input_error
from models import TaskBook, TaskStatus
from storage import JsonStorage


class TaskHandler:
    storage: JsonStorage
    book: TaskBook

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = TaskBook.from_list(storage.load())

    def _save(self) -> None:
        self.storage.save(self.book.to_list())

    @input_error
    def add_task(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-t" not in flags:
            raise ValueError("Usage: add --task -t <title> [-d <description>]")

        task = self.book.add_task(flags["-t"], flags.get("-d"))
        self._save()
        return f"Task [{task.id}] '{task.title}' created.", False

    @input_error
    def edit_task(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-t" not in flags:
            raise ValueError("Usage: edit --task -i <id> -t <new_title>")
        if not flags["-i"].isdigit():
            raise ValueError("Task id must be a positive number")

        task = self.book.find(int(flags["-i"]))
        if task is None:
            raise KeyError

        task.title = flags["-t"].strip()
        self._save()
        return f"Task [{task.id}] title updated to '{task.title}'.", False

    @input_error
    def edit_task_desc(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-d" not in flags:
            raise ValueError("Usage: edit --task-desc -i <id> -d <new_description>")

        task = self.book.find(int(flags["-i"]))
        if task is None:
            raise KeyError

        task.description = flags["-d"].strip() or None
        self._save()
        return f"Task [{task.id}] description updated.", False

    @input_error
    def delete_task(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags:
            raise ValueError("Usage: delete --task -i <id>")
        if not flags["-i"].isdigit():
            raise ValueError("Task id must be a positive number")

        task_id = int(flags["-i"])
        if self.book.find(task_id) is None:
            raise KeyError

        self.book.delete(task_id)
        self._save()
        return f"Task [{task_id}] deleted.", False

    @input_error
    def show_tasks(self, _flags: dict[str, str]) -> tuple[str, bool]:
        tasks = self.book.all_tasks()
        if not tasks:
            return "No tasks found.", False

        return "\n".join(str(task) for task in tasks), False

    @input_error
    def search_task(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-q" not in flags:
            raise ValueError("Usage: search --task -q <query>")

        query = flags["-q"]
        results = self.book.search(query)
        if not results:
            return f"No tasks found for query: {query}", False

        return "\n".join(str(task) for task in results), False

    @input_error
    def task_status(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-s" not in flags:
            raise ValueError("Usage: status --task -i <id> -s <status>")
        if not flags["-i"].isdigit():
            raise ValueError("Task id must be a positive number")

        task = self.book.find(int(flags["-i"]))
        if task is None:
            raise KeyError

        task.status = TaskStatus.from_str(flags["-s"])
        self._save()
        return f"Task [{task.id}] status changed to '{task.status}'.", False

    @input_error
    def tasks_by_status(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-s" not in flags:
            raise ValueError("Usage: filter --task -s <status>")

        status = TaskStatus.from_str(flags["-s"])
        results = self.book.filter_by_status(status)
        if not results:
            return f"No tasks with status '{status}'.", False

        return "\n".join(str(task) for task in results), False
