from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileHandler(ABC):
    def import_file(self, source, flags: dict[str, str]) -> tuple[str, bool]:
        if "-path" not in flags:
            raise ValueError('Usage: import --contacts -path <"file_path">')
        source.import_records(self.load(Path(flags["-path"])))
        return "Records imported successfully", False

    def export_file(self, source, flags: dict[str, str]) -> tuple[str, bool]:
        if "-path" not in flags:
            raise ValueError('Usage: export --contacts -path <"file_path">')
        self.save(source.export_records(), Path(flags["-path"]))
        return "Records exported successfully", False

    @abstractmethod
    def load(self, file_path: Path) -> list[dict]:
        pass

    @abstractmethod
    def save(self, data: list[dict], file_path: Path) -> None:
        pass
