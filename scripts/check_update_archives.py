import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
RELEASE_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")


def https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


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
    parser.add_argument(
        "--dictionary-id",
        dest="dictionary_ids",
        action="append",
        help="Check only the selected catalog ID; repeat for multiple editions.",
    )
    args = parser.parse_args()

    catalog = json.loads(
        (ROOT / "catalog" / "dictionaries.json").read_text(encoding="utf-8")
    )
    repository = catalog["repository"]
    selected_ids = set(args.dictionary_ids or [])
    known_ids = {entry["id"] for entry in catalog["dictionaries"]}
    unknown_ids = selected_ids - known_ids
    if unknown_ids:
        raise ValueError(f"unknown dictionary IDs: {sorted(unknown_ids)}")
    results = []
    for entry in catalog["dictionaries"]:
        dictionary_id = entry["id"]
        if selected_ids and dictionary_id not in selected_ids:
            continue
        distribution = entry["distribution"]
        if distribution["status"] != "public":
            continue
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
            "indexUrl": distribution["indexUrl"],
            "downloadUrl": distribution["downloadUrl"],
        }
        mismatches = {
            field: {"expected": value, "actual": index.get(field)}
            for field, value in expected.items()
            if index.get(field) != value
        }
        if mismatches:
            raise ValueError(f"{dictionary_id}: index mismatch: {mismatches}")
        for field in ("indexUrl", "downloadUrl"):
            if config.get(field) != distribution[field]:
                raise ValueError(
                    f"{dictionary_id}: config {field} differs from catalog"
                )
        for field in ("indexUrl", "downloadUrl"):
            if not https_url(index[field]):
                raise ValueError(f"{dictionary_id}: {field} must use HTTPS")
        update_hosting = distribution.get("updateHosting", "google-drive-public")
        if update_hosting == "google-drive-public":
            parsed_download = urlparse(index["downloadUrl"])
            if (
                parsed_download.hostname != "drive.usercontent.google.com"
                or parsed_download.path != "/download"
                or parse_qs(parsed_download.query).get("id")
                != [distribution["driveFileId"]]
            ):
                raise ValueError(
                    f"{dictionary_id}: public downloadUrl differs from Drive file"
                )
        elif update_hosting == "github-release":
            release_tag = distribution.get("releaseTag")
            release_asset_name = distribution.get("releaseAssetName")
            if (
                not isinstance(release_tag, str)
                or not RELEASE_COMPONENT.fullmatch(release_tag)
                or not isinstance(release_asset_name, str)
                or not RELEASE_COMPONENT.fullmatch(release_asset_name)
            ):
                raise ValueError(f"{dictionary_id}: invalid Release metadata")
            expected_download_url = (
                f"https://github.com/{repository}/releases/download/"
                f"{release_tag}/{release_asset_name}"
            )
            if index["downloadUrl"] != expected_download_url:
                raise ValueError(
                    f"{dictionary_id}: public downloadUrl differs from Release asset"
                )
        else:
            raise ValueError(f"{dictionary_id}: unsupported updateHosting")
        expected_index_path = f"/manifests/{dictionary_id}/index.json"
        if not index["indexUrl"].endswith(expected_index_path):
            raise ValueError(f"{dictionary_id}: indexUrl path mismatch")

        archive_bytes = archive_path.stat().st_size
        archive_hash = sha256(archive_path)
        if distribution.get("bytes") not in (None, archive_bytes):
            raise ValueError(f"{dictionary_id}: catalog byte size differs from ZIP")
        if distribution.get("sha256") not in (None, archive_hash):
            raise ValueError(f"{dictionary_id}: catalog SHA-256 differs from ZIP")

        results.append(
            {
                "id": dictionary_id,
                "title": index["title"],
                "revision": index["revision"],
                "assetName": asset_name,
                "bytes": archive_bytes,
                "sha256": archive_hash,
                "indexUrl": index["indexUrl"],
                "downloadUrl": index["downloadUrl"],
            }
        )

    print(json.dumps({"updateArchivesValid": True, "archives": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
