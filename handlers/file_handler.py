import hashlib
import re
import shutil
from pathlib import Path

from handlers.decorators import input_error

# extensions from hw1
_EXTENSIONS: dict[str, set[str]] = {
    "images": {"JPEG", "PNG", "JPG", "SVG"},
    "videos": {"AVI", "MP4", "MOV", "MKV"},
    "documents": {"DOC", "DOCX", "TXT", "PDF", "XLSX", "PPTX"},
    "archives": {"ZIP", "GZ", "TAR"},
    "audio": {"MP3", "OGG", "WAV", "AMR"},
}

_CATEGORY_DIRS = set(_EXTENSIONS.keys()) | {"others"}

_EXT_TO_CATEGORY: dict[str, str] = {ext: cat for cat, exts in _EXTENSIONS.items() for ext in exts}

# couldn't transliterate UA and RU symbols simultaneously without using the map
_CYRILLIC_MAP: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ye",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "yi",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "yu",
    "я": "ya",
    "ы": "y",
    "э": "e",
    "ъ": "",
    "ё": "yo",
}


def _normalize_name(name: str) -> str:
    parts = []
    for ch in name:
        repl = _CYRILLIC_MAP.get(ch.lower(), ch)
        parts.append(repl.capitalize() if ch.isupper() else repl)
    return re.sub(r"[^a-zA-Z0-9]", "_", "".join(parts))


def _get_category(ext_without_dot: str) -> str:
    return _EXT_TO_CATEGORY.get(ext_without_dot.upper(), "others")


def _collect_files(directory: Path) -> list[Path]:
    result = []
    for item in directory.iterdir():
        if item.is_file():
            result.append(item)
        elif item.is_dir() and item.name not in _CATEGORY_DIRS:
            result.extend(_collect_files(item))
    return result


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):  # 64kb
            h.update(chunk)
    return h.hexdigest()


def _resolve_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        candidate = dest.parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


class FileHandler:
    @input_error
    def sort_files(self, flags: dict[str, str]) -> tuple[str, bool]:
        # check mandatory params
        if "-p" not in flags:
            raise ValueError("Usage: files --sort -p <directory>")

        # check & get directory
        directory = Path(flags["-p"])
        if not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        # collect files
        files = _collect_files(directory)
        if not files:
            return "No files found to sort.", False

        # move files
        moved = 0
        for file in files:
            category = _get_category(file.suffix.lstrip("."))
            dest_dir = directory / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            normalized_stem = _normalize_name(file.stem)

            if category == "archives":
                extract_dir = _resolve_dest(dest_dir / normalized_stem)
                try:
                    shutil.unpack_archive(file, extract_dir)
                    file.unlink()
                except (shutil.ReadError, ValueError):
                    shutil.move(file, _resolve_dest(dest_dir / (normalized_stem + file.suffix)))
            else:
                shutil.move(file, _resolve_dest(dest_dir / (normalized_stem + file.suffix)))
            moved += 1

        # delete empty folders
        for item in directory.iterdir():
            if item.is_dir() and item.name not in _CATEGORY_DIRS:
                try:
                    item.rmdir()
                except OSError:
                    pass

        return f"Sorted {moved} file(s) into categories.", False

    @input_error
    def find_duplicates(self, flags: dict[str, str]) -> tuple[str, bool]:
        # check mandatory params
        if "-p" not in flags:
            raise ValueError("Usage: files --duplicates -p <directory>")

        # check & get directory
        directory = Path(flags["-p"])
        if not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        # collect files
        files = _collect_files(directory)
        if not files:
            return "No files found.", False

        # collect hashes
        hashes: dict[str, list[Path]] = {}
        for file in files:
            digest = _file_md5(file)
            hashes.setdefault(digest, []).append(file)

        # find duplicates
        duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}
        if not duplicates:
            return "No duplicate files found.", False

        # create and return a user-friendly message
        lines = []
        for i, (digest, paths) in enumerate(duplicates.items(), start=1):
            lines.append(f"Group {i} [{digest[:8]}]:")  # 8 symbols of the hash
            for p in paths:
                lines.append(f"  {p}")
        total = sum(len(p) - 1 for p in duplicates.values())
        lines.append(f"\n{len(duplicates)} duplicate group(s), {total} redundant file(s).")
        return "\n".join(lines), False

    @input_error
    def normalize_files(self, flags: dict[str, str]) -> tuple[str, bool]:
        # check mandatory params
        if "-p" not in flags:
            raise ValueError("Usage: files --normalize -p <directory>")

        # check & get directory
        directory = Path(flags["-p"])
        if not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        # normalizing
        renamed = 0
        skipped = 0
        for item in sorted(directory.iterdir()):
            if not item.is_file():
                continue
            new_stem = _normalize_name(item.stem)
            new_name = new_stem + item.suffix
            if new_name == item.name:
                skipped += 1
                continue
            dest = _resolve_dest(item.parent / new_name)
            item.rename(dest)
            renamed += 1

        return f"Renamed {renamed} file(s). {skipped} already normalized.", False
