from datetime import datetime
from typing import Any


class Note:
    id: int
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    def __init__(self, id: int, title: str, content: str) -> None:
        self.id = id
        self.title = title
        self.content = content
        self.tags = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        tags_str = f", tags: {', '.join(self.tags)}" if self.tags else ""
        return f"[{self.id}] {self.title}: {self.content}{tags_str}"

    def edit(self, content: str) -> None:
        self.content = content
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        tag = tag.lower().strip()
        if not tag:
            raise ValueError("Tag cannot be empty")
        if tag in self.tags:
            return
        self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        tag = tag.lower().strip()
        if tag not in self.tags:
            raise ValueError(f"Tag '{tag}' not found on this note")
        self.tags.remove(tag)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Note":
        note = cls(data["id"], data["title"], data["content"])
        note.tags = data.get("tags", [])
        note.created_at = datetime.fromisoformat(data["created_at"])
        note.updated_at = datetime.fromisoformat(data["updated_at"])
        return note


class NoteBook:
    _notes: dict[int, Note]
    _next_id: int

    def __init__(self) -> None:
        self._notes = {}
        self._next_id = 1

    def add(self, title: str, content: str) -> Note:
        note = Note(self._next_id, title, content)
        self._notes[note.id] = note
        self._next_id += 1
        return note

    def get(self, note_id: int) -> Note | None:
        return self._notes.get(note_id)

    def delete(self, note_id: int) -> None:
        if note_id not in self._notes:
            raise KeyError(note_id)
        del self._notes[note_id]

    def all(self) -> list[Note]:
        return list(self._notes.values())

    def search(self, query: str) -> list[Note]:
        q = query.lower()
        return [n for n in self._notes.values() if q in n.title.lower() or q in n.content.lower()]

    def find_by_tag(self, tag: str) -> list[Note]:
        tag = tag.lower().strip()
        return [n for n in self._notes.values() if tag in n.tags]

    def to_list(self) -> list[dict]:
        return [n.to_dict() for n in self._notes.values()]

    @classmethod
    def from_list(cls, data: list[dict]) -> "NoteBook":
        book = cls()
        for item in data:
            note = Note.from_dict(item)
            book._notes[note.id] = note
        if book._notes:
            book._next_id = max(book._notes) + 1
        return book
