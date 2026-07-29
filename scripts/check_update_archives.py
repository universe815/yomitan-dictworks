import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def update_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.scheme == "https" and bool(parsed.netloc):
        return True
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check built ZIP indexes against catalog and update configs."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(
        (ROOT / "catalog" / "dictionaries.json").read_text(encoding="utf-8")
    )
    results = []
    for entry in catalog["dictionaries"]:
        dictionary_id = entry["id"]
        distribution = entry["distribution"]
        asset_name = distribution["assetName"]
        archive_path = args.output_dir / asset_name
        if not archive_path.is_file():
            raise FileNotFoundError(f"{dictionary_id}: missing {archive_path}")

        config = json.loads((ROOT / entry["config"]).read_text(encoding="utf-8"))
        with zipfile.ZipFile(archive_path) as archive:
            index = json.loads(archive.read("index.json"))

        expected = {
            "title": entry["title"],
            "revision": entry["revision"],
            "isUpdatable": True,
            "indexUrl": config.get("indexUrl"),
            "downloadUrl": config.get("downloadUrl"),
        }
        mismatches = {
            field: {"expected": value, "actual": index.get(field)}
            for field, value in expected.items()
            if index.get(field) != value
        }
        if mismatches:
            raise ValueError(f"{dictionary_id}: index mismatch: {mismatches}")
        for field in ("indexUrl", "downloadUrl"):
            if not update_url(index[field]):
                raise ValueError(f"{dictionary_id}: invalid update URL in {field}")
        expected_download_path = f"/{dictionary_id}/{asset_name}"
        if not index["downloadUrl"].endswith(expected_download_path):
            raise ValueError(f"{dictionary_id}: local downloadUrl path mismatch")
        expected_index_path = f"/manifests/{dictionary_id}/index.json"
        if not index["indexUrl"].endswith(expected_index_path):
            raise ValueError(f"{dictionary_id}: indexUrl path mismatch")

        results.append(
            {
                "id": dictionary_id,
                "title": index["title"],
                "revision": index["revision"],
                "assetName": asset_name,
                "bytes": archive_path.stat().st_size,
                "sha256": sha256(archive_path),
                "indexUrl": index["indexUrl"],
                "downloadUrl": index["downloadUrl"],
            }
        )

    print(json.dumps({"updateArchivesValid": True, "archives": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
