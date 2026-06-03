import json
from pathlib import Path


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
            json.dump(data, file, indent=4)

        temp_file.replace(self.path)
