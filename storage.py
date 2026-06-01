import json
from pathlib import Path

from models import AddressBook, Record


class JsonStorage:
    path: Path

    def __init__(self, filename: str) -> None:
        self.path = Path(__file__).resolve().parent / filename

    def load(self) -> AddressBook:
        if not self.path.exists():
            return AddressBook()

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                book = AddressBook()
                for item in json.load(file):
                    record = Record.from_dict(item)
                    book.add_record(record)
                return book
        except json.JSONDecodeError:
            return AddressBook()

    def save(self, book: AddressBook) -> None:
        temp_file = self.path.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump([record.to_dict() for record in book.values()], file, indent=4)

        temp_file.replace(self.path)
