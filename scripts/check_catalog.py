import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"
ALLOWED_CATEGORIES = {"term", "frequency", "grammar", "kanji"}
ALLOWED_BUILD_STATUSES = {"planned", "ready", "retired"}
ALLOWED_DISTRIBUTION_STATUSES = {"personal", "published", "retired"}
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]+)*$")


def require_relative_file(value: object, field: str, dictionary_id: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{dictionary_id}: {field} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{dictionary_id}: {field} must stay inside the repository")
    full_path = ROOT / path
    if not full_path.is_file():
        raise ValueError(f"{dictionary_id}: {field} does not exist: {value}")
    return full_path


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    dictionaries = catalog.get("dictionaries")
    if catalog.get("schemaVersion") != 1 or not isinstance(dictionaries, list):
        raise ValueError("catalog must use schemaVersion 1 and contain dictionaries[]")

    ids: set[str] = set()
    asset_names: set[str] = set()
    for entry in dictionaries:
        dictionary_id = entry.get("id")
        if not isinstance(dictionary_id, str) or not re.fullmatch(r"[a-z0-9-]+", dictionary_id):
            raise ValueError(f"invalid dictionary id: {dictionary_id!r}")
        if dictionary_id in ids:
            raise ValueError(f"duplicate dictionary id: {dictionary_id}")
        ids.add(dictionary_id)

        for field in ("title", "revision", "buildCommand"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise ValueError(f"{dictionary_id}: {field} must be a non-empty string")
        for field in ("sourceLanguage", "targetLanguage"):
            value = entry.get(field)
            if not isinstance(value, str) or not LANGUAGE_CODE.fullmatch(value):
                raise ValueError(f"{dictionary_id}: invalid {field}: {value!r}")
        if entry.get("category") not in ALLOWED_CATEGORIES:
            raise ValueError(f"{dictionary_id}: invalid category")
        if entry.get("buildStatus") not in ALLOWED_BUILD_STATUSES:
            raise ValueError(f"{dictionary_id}: invalid buildStatus")

        require_relative_file(entry.get("page"), "page", dictionary_id)
        config_path = require_relative_file(entry.get("config"), "config", dictionary_id)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("title") != entry["title"] or config.get("revision") != entry["revision"]:
            raise ValueError(f"{dictionary_id}: catalog title/revision differs from config")

        distribution = entry.get("distribution")
        if not isinstance(distribution, dict):
            raise ValueError(f"{dictionary_id}: distribution must be an object")
        status = distribution.get("status")
        if status not in ALLOWED_DISTRIBUTION_STATUSES:
            raise ValueError(f"{dictionary_id}: invalid distribution status")
        asset_name = distribution.get("assetName")
        if not isinstance(asset_name, str) or not asset_name.endswith(".zip"):
            raise ValueError(f"{dictionary_id}: assetName must end in .zip")
        if config.get("outputFile") != asset_name:
            raise ValueError(f"{dictionary_id}: assetName differs from config outputFile")
        if asset_name in asset_names:
            raise ValueError(f"duplicate archive assetName: {asset_name}")
        asset_names.add(asset_name)

        required_update_fields = ("hosting", "indexUrl", "downloadUrl")
        if status == "published":
            required_public_fields = (
                "contentLicense",
                "rightsEvidence",
                *required_update_fields,
            )
            missing = [field for field in required_public_fields if not distribution.get(field)]
            if missing:
                raise ValueError(f"{dictionary_id}: published entry lacks {', '.join(missing)}")
            manifest = ROOT / "manifests" / dictionary_id / "index.json"
            if not manifest.is_file():
                raise ValueError(f"{dictionary_id}: published entry lacks {manifest.relative_to(ROOT)}")
        elif status == "personal":
            missing = [field for field in required_update_fields if not distribution.get(field)]
            if missing:
                raise ValueError(f"{dictionary_id}: personal entry lacks {', '.join(missing)}")
            if distribution.get("hosting") != "google-drive-sync":
                raise ValueError(
                    f"{dictionary_id}: personal entry must use Google Drive sync hosting"
                )
            archive_path = distribution.get("archivePath")
            if not isinstance(archive_path, str) or not archive_path:
                raise ValueError(f"{dictionary_id}: personal entry lacks archivePath")
            if Path(archive_path).is_absolute() or ".." in Path(archive_path).parts:
                raise ValueError(
                    f"{dictionary_id}: archivePath must stay inside the Drive archive root"
                )
            if Path(archive_path).name != asset_name:
                raise ValueError(f"{dictionary_id}: archivePath filename mismatch")
            drive_file_url = distribution.get("driveFileUrl")
            if (
                not isinstance(drive_file_url, str)
                or not drive_file_url.startswith("https://drive.google.com/file/d/")
            ):
                raise ValueError(f"{dictionary_id}: invalid driveFileUrl")
            manifest = ROOT / "manifests" / dictionary_id / "index.json"
            if not manifest.is_file():
                raise ValueError(f"{dictionary_id}: personal entry lacks {manifest.relative_to(ROOT)}")
        elif any(distribution.get(field) for field in (*required_update_fields, "contentLicense", "rightsEvidence")):
            raise ValueError(
                f"{dictionary_id}: retired entries must not expose live distribution fields"
            )

    print(f"Dictionary catalog check passed ({len(dictionaries)} editions).")


if __name__ == "__main__":
    main()
