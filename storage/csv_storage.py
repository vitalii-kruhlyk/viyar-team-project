import csv
from pathlib import Path

from models import Record

class CsvFileHandler:

    def __init__(self) -> None:
        pass

    def import_file(self, contacts, flags: dict[str, str]) -> tuple[str, bool]:
        if "-f" not in flags or "-path" not in flags:
            raise ValueError('Usage: file --import-contacts -f <format> -path <"file_path">')

        file_format = flags["-f"]
        file_path = flags["-path"]

        path = Path(file_path).with_suffix(f".{file_format}")

        for item in self.load(path):
            contacts.book.add_record(Record.from_dict(item))

        contacts._save()

        return "Contact list is saved", False

    def export_file(self, contacts, flags: dict[str, str]) -> tuple[str, bool]:
        if "-f" not in flags or "-path" not in flags:
            raise ValueError('Usage: file --import-contacts -f <format> -path <"file_path">')

        file_format = flags["-f"]
        file_path = flags["-path"]

        path = Path(file_path).with_suffix(f".{file_format}")

        self.save([record.to_dict() for record in contacts.book.values()], path)

        return "Contact list is saved", False

    @staticmethod
    def save(data: list[dict], file_path: Path) -> None:

        with open(file_path, "w", newline="", encoding="utf-8") as file:

            writer = csv.DictWriter(
                file,
                fieldnames=["name", "phones", "emails", "birthday", "address", "favorite"]
            )

            writer.writeheader()

            for record in data:
                writer.writerow(
                    {
                        "name": record["name"],
                        "phones": ";".join(record["phones"]),
                        "emails": ";".join(record["emails"]),
                        "birthday": record["birthday"],
                        "address": record["address"],
                        "favorite": record["favorite"],
                    }
                )

    @staticmethod
    def load(file_path: Path) -> list[dict]:

        if not file_path.exists():
            raise ValueError("File does not exist")

        result = []

        with open(file_path, "r", newline="", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                result.append(
                    {
                        "name": row["name"],
                        "phones": (
                            row["phones"].split(";")
                            if row["phones"]
                            else []
                        ),
                        "emails": (
                            row["emails"].split(";")
                            if row["emails"]
                            else []
                        ),
                        "birthday": row["birthday"] or None,
                        "address": row["address"] == "True",
                        "favorite": row["favorite"] == "True",
                    }
                )

        return result