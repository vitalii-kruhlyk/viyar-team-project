import json
from pathlib import Path

from storage.base import BaseFileHandler


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


class JsonFileHandler(BaseFileHandler):
    def save(self, data: list[dict], file_path: Path) -> None:
        if not data:
            raise ValueError("No data to export")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            raise ValueError("File does not exist")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON file")
