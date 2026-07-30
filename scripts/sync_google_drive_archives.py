import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy built public dictionaries into the Google Drive download folder."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Flat dictionary-output directory containing the built ZIP files.",
    )
    parser.add_argument(
        "--drive-root",
        type=Path,
        required=True,
        help="Root of the Yomitan Dictionaries folder in Google Drive.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned copies without changing the Drive folder.",
    )
    parser.add_argument(
        "--dictionary-id",
        action="append",
        dest="dictionary_ids",
        help="Sync only the selected catalog edition; repeat as needed.",
    )
    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    drive_root = args.drive_root.expanduser().resolve()
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    selected_ids = set(args.dictionary_ids or [])
    catalog_ids = {entry["id"] for entry in catalog["dictionaries"]}
    unknown_ids = sorted(selected_ids - catalog_ids)
    if unknown_ids:
        raise ValueError(
            f"unknown dictionary IDs: {', '.join(unknown_ids)}"
        )
    results = []

    for entry in catalog["dictionaries"]:
        if selected_ids and entry["id"] not in selected_ids:
            continue
        distribution = entry["distribution"]
        if distribution["status"] != "public":
            continue

        source = (source_dir / distribution["assetName"]).resolve()
        destination = (drive_root / distribution["archivePath"]).resolve()
        try:
            destination.relative_to(drive_root)
        except ValueError as error:
            raise ValueError(
                f"{entry['id']}: archivePath escapes the Drive root"
            ) from error
        if not source.is_file():
            raise FileNotFoundError(f"{entry['id']}: missing source archive {source}")

        if args.dry_run:
            print(f"[dry-run] {source} -> {destination}")
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source_hash = sha256(source)
        destination_hash = sha256(destination)
        if source_hash != destination_hash:
            raise ValueError(f"{entry['id']}: SHA-256 mismatch after copy")
        results.append(
            {
                "id": entry["id"],
                "path": str(destination),
                "bytes": destination.stat().st_size,
                "sha256": destination_hash,
            }
        )

    if args.dry_run:
        return
    print(
        json.dumps(
            {"googleDriveArchivesValid": True, "archives": results},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
