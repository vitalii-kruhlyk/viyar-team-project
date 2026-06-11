import csv
import json
from pathlib import Path

from storage.base import BaseFileHandler


class CsvFileHandler(BaseFileHandler):
    def save(self, data: list[dict], file_path: Path) -> None:
        if not data:
            raise ValueError("No data to export")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = sorted({key for record in data for key in record.keys()})

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for record in data:
                row = {}
                for key, value in record.items():
                    if isinstance(value, list):
                        row[key] = ";".join(value)
                    elif isinstance(value, dict):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    elif value is None:
                        row[key] = ""
                    else:
                        row[key] = value
                writer.writerow(row)

    def load(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            raise ValueError("File does not exist")

        with open(file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ValueError("CSV file is empty")

            result = []
            for row in reader:
                record = {}
                for key, value in row.items():
                    if value == "":
                        record[key] = None
                    else:
                        try:
                            record[key] = json.loads(value)
                        except (json.JSONDecodeError, ValueError):
                            record[key] = value
                result.append(record)

        return result
