import argparse
import json
import zipfile
from pathlib import Path
from urllib.parse import urlparse


def is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract and validate a Yomitan remote update index from a ZIP."
    )
    parser.add_argument("dictionary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.dictionary) as archive:
        index = json.loads(archive.read("index.json"))

    for field in ("title", "revision", "author", "description", "attribution"):
        if not isinstance(index.get(field), str) or not index[field]:
            raise ValueError(f"dictionary index lacks {field}")
    if index.get("format") != 3:
        raise ValueError("only Yomitan dictionary format 3 is supported")
    if index.get("isUpdatable") is not True:
        raise ValueError("dictionary was not built with isUpdatable=true")
    for field in ("indexUrl", "downloadUrl"):
        if not is_https_url(index.get(field)):
            raise ValueError(f"dictionary index lacks a valid HTTPS {field}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "title": index["title"],
                "revision": index["revision"],
                "indexUrl": index["indexUrl"],
                "downloadUrl": index["downloadUrl"],
                "output": args.output.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
