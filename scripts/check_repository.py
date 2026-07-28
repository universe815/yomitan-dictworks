import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "dictionary-output",
    "dist",
    "generated",
    "node_modules",
    "qa-output",
}
PROHIBITED_SUFFIXES = {
    ".7z",
    ".m4a",
    ".mdd",
    ".mdx",
    ".mp3",
    ".ogg",
    ".rar",
    ".wav",
    ".zip",
}
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?i)(?<![a-z0-9+.-])(?:[a-z]:\\|[a-z]:/(?!/))"
)
TEXT_SUFFIXES = {
    ".css",
    ".json",
    ".md",
    ".py",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}


def repository_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_DIRECTORIES for part in path.relative_to(ROOT).parts)
    ]


def main() -> None:
    problems: list[str] = []
    files = repository_files()

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.casefold() in PROHIBITED_SUFFIXES:
            problems.append(f"{relative}: proprietary/archive file type must not be committed")
        if path.stat().st_size > 10 * 1024 * 1024:
            problems.append(f"{relative}: file is larger than 10 MiB")

        if path.suffix.casefold() == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                problems.append(f"{relative}: invalid UTF-8 JSON ({error})")

        if path.suffix.casefold() in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as error:
                problems.append(f"{relative}: text is not UTF-8 ({error})")
                continue
            match = WINDOWS_ABSOLUTE_PATH.search(text)
            if match:
                problems.append(
                    f"{relative}: contains a Windows absolute path near {match.group(0)!r}"
                )

    if problems:
        raise SystemExit("\n".join(problems))

    print(f"Repository policy check passed ({len(files)} files checked).")


if __name__ == "__main__":
    main()
