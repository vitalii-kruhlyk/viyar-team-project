import json
from pathlib import Path

from handlers.decorators import input_error


class JsonStorage:
    path: Path

    def __init__(self, filename: str, file_format: str = None) -> None:

        if file_format is None:
            self.path = Path(__file__).resolve().parent.parent / filename
        else:
            self.path = Path(filename + "." + file_format)

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

    def __init__(self) -> None:
        pass

    @input_error
    def import_file(self, flags: dict[str, str]) -> tuple[str, bool]:

        if "-f" not in flags or "-path" not in flags:
            raise ValueError("Usage: file --import-contacts -f <format> -path <file_path>")

        file_format = flags["-f"]
        file_path = flags["-path"]

        return "", False

    @input_error
    def export_file(self, flags: dict[str, str]) -> tuple[str, bool]:

        if "-f" not in flags or "-path" not in flags:
            raise ValueError("Usage: file --export-contacts -f <format> -path <file_path>")

        file_format = flags["-f"]
        file_path = flags["-path"]

        self.storage = JsonStorage(file_path, file_format)

        return "Contact list is saved", False
