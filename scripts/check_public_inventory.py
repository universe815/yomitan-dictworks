"""Validate the unified inventory and optionally verify one archive."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[a-z0-9-]+$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def validate_entry(entry: dict) -> None:
    assert ID.fullmatch(entry["id"]), entry["id"]
    assert SHA256.fullmatch(entry["sha256"]), entry["id"]
    assert isinstance(entry["searchRecords"], int) and entry["searchRecords"] > 0
    assert isinstance(entry["bytes"], int) and entry["bytes"] > 0
    name = entry["assetName"]
    assert Path(name).name == name and "/" not in name and "\\" not in name
    publication = entry["publication"]
    assert publication["status"] in {"released", "local-only"}
    if publication["status"] == "released":
        assert publication["channel"] == "github-release"
        assert publication["releaseTag"]
        assert publication["releaseAssetName"].endswith(".zip")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictionary-id")
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if bool(args.dictionary_id) != bool(args.archive):
        parser.error("dictionary-id and archive must be supplied together")

    data = json.loads((ROOT / "catalog/build-inventory.json").read_text(encoding="utf-8"))
    entries = data["dictionaries"]
    assert data["editionCount"] == len(entries)
    assert data["workCount"] == len({e["work"] for e in entries})
    ids = set()
    for entry in entries:
        assert entry["id"] not in ids
        ids.add(entry["id"])
        validate_entry(entry)

    if args.dictionary_id:
        entry = next((e for e in entries if e["id"] == args.dictionary_id), None)
        if entry is None:
            raise ValueError("Unknown dictionary ID")
        assert args.archive.stat().st_size == entry["bytes"], "Archive size mismatch"
        assert (
            hashlib.sha256(args.archive.read_bytes()).hexdigest() == entry["sha256"]
        ), "Archive hash mismatch"

    print(
        f"Unified inventory valid: {data['workCount']} works / {len(entries)} editions."
    )


if __name__ == "__main__":
    main()
