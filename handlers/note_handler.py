from handlers import ai_handler
from handlers.decorators import input_error
from models import NoteBook
from storage import JsonStorage


class NoteHandler:
    storage: JsonStorage
    book: NoteBook

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = NoteBook.from_list(storage.load())

    def _save(self) -> None:
        self.storage.save(self.book.to_list())

    def _get_note_or_raise(self, id_str: str):
        if not id_str.isdigit():
            raise ValueError("Note id must be a positive number")
        note_id = int(id_str)
        note = self.book.get(note_id)
        if note is None:
            raise KeyError("Note not found")
        return note

    @input_error
    def add_note(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-t" not in flags or "-c" not in flags:
            raise ValueError("Usage: add --note -t <title> -c <content>")
        note = self.book.add(flags["-t"], flags["-c"])
        self._save()
        return f"Note [{note.id}] '{note.title}' added.", False

    @input_error
    def add_tag(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-t" not in flags:
            raise ValueError("Usage: add --tag -i <id> -t <tag>")
        note = self._get_note_or_raise(flags["-i"])
        note.add_tag(flags["-t"])
        self._save()
        return f"Tag '{flags['-t']}' added to note [{note.id}].", False

    @input_error
    def edit_note(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-c" not in flags:
            raise ValueError("Usage: edit --note -i <id> -c <new_content>")
        note = self._get_note_or_raise(flags["-i"])
        note.edit(flags["-c"])
        self._save()
        return f"Note [{note.id}] updated.", False

    @input_error
    def remove_tag(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags or "-t" not in flags:
            raise ValueError("Usage: remove --tag -i <id> -t <tag>")
        note = self._get_note_or_raise(flags["-i"])
        note.remove_tag(flags["-t"])
        self._save()
        return f"Tag '{flags['-t']}' removed from note [{note.id}].", False

    @input_error
    def delete_note(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags:
            raise ValueError("Usage: delete --note -i <id>")
        note = self._get_note_or_raise(flags["-i"])
        self.book.delete(note.id)
        self._save()
        return f"Note [{note.id}] deleted.", False

    @input_error
    def show_notes(self, _flags: dict[str, str]) -> tuple[str, bool]:
        notes = self.book.all()
        if not notes:
            return "No notes saved.", False
        return "\n".join(str(n) for n in notes), False

    @input_error
    def search_note(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-q" not in flags:
            raise ValueError("Usage: search --note -q <query>")
        results = self.book.search(flags["-q"])
        if not results:
            return f"No notes found for query: {flags['-q']}", False
        return "\n".join(str(n) for n in results), False

    @input_error
    def filter_by_tag(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-t" not in flags:
            raise ValueError("Usage: filter --note -t <tag>")
        results = self.book.find_by_tag(flags["-t"])
        if not results:
            return f"No notes found with tag: {flags['-t']}", False
        return "\n".join(str(n) for n in results), False

    @input_error
    def ai_tags(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags:
            raise ValueError("Usage: add --tag -i <id> -ai")
        note = self._get_note_or_raise(flags["-i"])
        tags = ai_handler.generate_tags(note.content)
        for tag in tags:
            note.add_tag(tag)
        self._save()
        return f"AI generated tags for note [{note.id}]: {', '.join(tags)}", False

    @input_error
    def ai_summary(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-i" not in flags:
            raise ValueError("Usage: show --note -i <id> -ai")
        note = self._get_note_or_raise(flags["-i"])
        summary = ai_handler.generate_summary(note.content)
        return f"Summary of note [{note.id}]:\n{summary}", False

    @input_error
    def ai_search(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-q" not in flags:
            raise ValueError("Usage: search --note -q <query> -ai")
        notes_list = [
            {"id": n.id, "title": n.title, "content": n.content, "embedding": n.embedding} for n in self.book.all()
        ]
        results = ai_handler.semantic_search(flags["-q"], notes_list)
        for item in notes_list:
            note = self.book.get(item["id"])
            if note and note.embedding is None and item.get("embedding"):
                note.embedding = item["embedding"]
        self._save()
        if not results:
            return f"No notes found for query: {flags['-q']}", False
        found = [self.book.get(r["id"]) for r in results if self.book.get(r["id"])]
        return "\n".join(str(n) for n in found), False
