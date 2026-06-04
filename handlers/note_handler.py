from collections.abc import Callable

from handlers.decorators import input_error
from models import NoteBook
from storage import JsonStorage


class NoteHandler:
    book: NoteBook
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = NoteBook.from_list(storage.load())
        self.commands = {
            "note_add": self.note_add,
            "note_edit": self.note_edit,
            "note_delete": self.note_delete,
            "note_show": self.note_show,
            "note_find": self.note_find,
            "note_tag_add": self.note_tag_add,
            "note_tag_remove": self.note_tag_remove,
            "note_find_tag": self.note_find_tag,
        }

    def _save(self) -> None:
        self.storage.save(self.book.to_list())

    def _get_note_or_raise(self, id_str: str):
        note_id = int(id_str)
        note = self.book.get(note_id)
        if note is None:
            raise KeyError(note_id)
        return note

    @input_error
    def note_add(self, args: list[str]) -> tuple[str, bool]:
        if len(args) < 2:
            raise ValueError("Usage: note_add <title> <content...>")
        title = args[0]
        content = " ".join(args[1:])
        note = self.book.add(title, content)
        self._save()
        return f"Note [{note.id}] '{title}' added.", False

    @input_error
    def note_edit(self, args: list[str]) -> tuple[str, bool]:
        if len(args) < 2:
            raise ValueError("Usage: note_edit <id> <content...>")
        note = self._get_note_or_raise(args[0])
        note.edit(" ".join(args[1:]))
        self._save()
        return f"Note [{note.id}] updated.", False

    @input_error
    def note_delete(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: note_delete <id>")
        note = self._get_note_or_raise(args[0])
        self.book.delete(note.id)
        self._save()
        return f"Note [{note.id}] deleted.", False

    @input_error
    def note_show(self, _args: list[str]) -> tuple[str, bool]:
        notes = self.book.all()
        if not notes:
            return "No notes saved.", False
        return "\n".join(str(n) for n in notes), False

    @input_error
    def note_find(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: note_find <query>")
        results = self.book.search(args[0])
        if not results:
            return f"No notes found for query: {args[0]}", False
        return "\n".join(str(n) for n in results), False

    @input_error
    def note_tag_add(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: note_tag_add <id> <tag>")
        note = self._get_note_or_raise(args[0])
        note.add_tag(args[1])
        self._save()
        return f"Tag '{args[1]}' added to note [{note.id}].", False

    @input_error
    def note_tag_remove(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: note_tag_remove <id> <tag>")
        note = self._get_note_or_raise(args[0])
        note.remove_tag(args[1])
        self._save()
        return f"Tag '{args[1]}' removed from note [{note.id}].", False

    @input_error
    def note_find_tag(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: note_find_tag <tag>")
        results = self.book.find_by_tag(args[0])
        if not results:
            return f"No notes found with tag: {args[0]}", False
        return "\n".join(str(n) for n in results), False
