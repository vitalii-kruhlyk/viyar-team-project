import json
from pathlib import Path

from models import Record

class JsonStorage:
    path: Path

    def __init__(self, filename: str) -> None:
        self.path = Path(__file__).resolve().parent.parent / filename

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []

    def save(self, data: list[dict]) -> None:
        temp_file = self.path.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        temp_file.replace(self.path)

class JsonFileHandler:
    storage: JsonStorage

    def __init__(self, data: dict) -> None:
        self.data = data
        self.storage = JsonStorage("contacts.json")

    def import_file(self, flags: dict[str, str]) -> tuple[str, bool]:

        if "-f" not in flags or "-path" not in flags:
            raise ValueError('Usage: file --import-contacts -f <format> -path <"file_path">')

        file_format = flags["-f"]
        file_path = flags["-path"]

        path = Path(file_path).with_suffix(f".{file_format}")

        self.storage.save([record.to_dict() for record in [Record.from_dict(item) for item in self.load(path)]])

        return "Contact list is loaded", False

    def export_file(self, flags: dict[str, str]) -> tuple[str, bool]:

        if "-f" not in flags or "-path" not in flags:
            raise ValueError('Usage: file --export-contacts -f <format> -path <"file_path">')

        file_format = flags["-f"]
        file_path = flags["-path"]

        path = Path(file_path).with_suffix(f".{file_format}")
        self.save([record.to_dict() for record in self.data.get("contacts").values()], path)

        return "Contact list is saved", False

    @staticmethod
    def save(data: list[dict], file_path: Path) -> None:

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    @staticmethod
    def load(path: Path) -> list[dict]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
