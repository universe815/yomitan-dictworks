import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"
ALLOWED_CATEGORIES = {"term", "frequency", "grammar", "kanji"}
ALLOWED_BUILD_STATUSES = {"planned", "ready", "retired"}
ALLOWED_DISTRIBUTION_STATUSES = {"public", "retired"}
ALLOWED_RIGHTS_STATUSES = {"third-party", "licensed", "public-domain"}
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]+)*$")
DRIVE_FILE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
RELEASE_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")


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
    if catalog.get("schemaVersion") != 2 or not isinstance(dictionaries, list):
        raise ValueError("catalog must use schemaVersion 2 and contain dictionaries[]")
    repository = catalog.get("repository")
    if not isinstance(repository, str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
    ):
        raise ValueError("catalog repository must use owner/name format")

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
        if status == "public":
            required_public_fields = (
                "rightsStatus",
                "rightsStatement",
                "archivePath",
                "driveFileId",
                "driveFolderUrl",
                "driveFileUrl",
                *required_update_fields,
            )
            missing = [field for field in required_public_fields if not distribution.get(field)]
            if missing:
                raise ValueError(f"{dictionary_id}: public entry lacks {', '.join(missing)}")
            if distribution.get("rightsStatus") not in ALLOWED_RIGHTS_STATUSES:
                raise ValueError(f"{dictionary_id}: invalid rightsStatus")
            if distribution["rightsStatus"] == "licensed":
                for field in ("contentLicense", "rightsEvidence"):
                    if not distribution.get(field):
                        raise ValueError(f"{dictionary_id}: licensed entry lacks {field}")
            if distribution.get("hosting") != "google-drive-public":
                raise ValueError(
                    f"{dictionary_id}: public entry must use public Google Drive hosting"
                )
            archive_path = distribution.get("archivePath")
            if not isinstance(archive_path, str) or not archive_path:
                raise ValueError(f"{dictionary_id}: public entry lacks archivePath")
            if Path(archive_path).is_absolute() or ".." in Path(archive_path).parts:
                raise ValueError(
                    f"{dictionary_id}: archivePath must stay inside the Drive archive root"
                )
            if Path(archive_path).suffix.lower() != ".zip":
                raise ValueError(f"{dictionary_id}: archivePath must end in .zip")
            drive_file_id = distribution.get("driveFileId")
            if (
                not isinstance(drive_file_id, str)
                or not DRIVE_FILE_ID.fullmatch(drive_file_id)
            ):
                raise ValueError(f"{dictionary_id}: invalid driveFileId")
            drive_folder_url = distribution.get("driveFolderUrl")
            if (
                not isinstance(drive_folder_url, str)
                or not drive_folder_url.startswith(
                    "https://drive.google.com/drive/folders/"
                )
            ):
                raise ValueError(f"{dictionary_id}: invalid driveFolderUrl")
            expected_file_url = (
                f"https://drive.google.com/file/d/{drive_file_id}/view?usp=sharing"
            )
            if distribution.get("driveFileUrl") != expected_file_url:
                raise ValueError(f"{dictionary_id}: driveFileUrl differs from driveFileId")
            update_hosting = distribution.get(
                "updateHosting", "google-drive-public"
            )
            if update_hosting not in {"google-drive-public", "github-release"}:
                raise ValueError(f"{dictionary_id}: invalid updateHosting")
            download_url = distribution.get("downloadUrl")
            if not isinstance(download_url, str):
                raise ValueError(f"{dictionary_id}: downloadUrl must be a string")
            if update_hosting == "google-drive-public":
                parsed_download = urlparse(download_url)
                if (
                    parsed_download.scheme != "https"
                    or parsed_download.hostname != "drive.usercontent.google.com"
                    or parsed_download.path != "/download"
                    or parse_qs(parsed_download.query).get("id") != [drive_file_id]
                    or parse_qs(parsed_download.query).get("export") != ["download"]
                ):
                    raise ValueError(f"{dictionary_id}: invalid Drive downloadUrl")
            else:
                release_tag = distribution.get("releaseTag")
                release_asset_name = distribution.get("releaseAssetName")
                if (
                    not isinstance(release_tag, str)
                    or not RELEASE_COMPONENT.fullmatch(release_tag)
                ):
                    raise ValueError(f"{dictionary_id}: invalid releaseTag")
                if (
                    not isinstance(release_asset_name, str)
                    or not RELEASE_COMPONENT.fullmatch(release_asset_name)
                    or not release_asset_name.endswith(".zip")
                ):
                    raise ValueError(f"{dictionary_id}: invalid releaseAssetName")
                expected_download_url = (
                    f"https://github.com/{repository}/releases/download/"
                    f"{release_tag}/{release_asset_name}"
                )
                if download_url != expected_download_url:
                    raise ValueError(
                        f"{dictionary_id}: Release downloadUrl differs from release metadata"
                    )
            if config.get("indexUrl") != distribution.get("indexUrl"):
                raise ValueError(f"{dictionary_id}: catalog indexUrl differs from config")
            if config.get("downloadUrl") != download_url:
                raise ValueError(f"{dictionary_id}: catalog downloadUrl differs from config")
            manifest = ROOT / "manifests" / dictionary_id / "index.json"
            if not manifest.is_file():
                raise ValueError(f"{dictionary_id}: public entry lacks {manifest.relative_to(ROOT)}")
            manifest_index = json.loads(manifest.read_text(encoding="utf-8"))
            for field in ("title", "revision", "indexUrl", "downloadUrl"):
                if manifest_index.get(field) != config.get(field):
                    raise ValueError(
                        f"{dictionary_id}: manifest {field} differs from config"
                    )
        elif any(
            distribution.get(field)
            for field in (
                *required_update_fields,
                "contentLicense",
                "rightsEvidence",
                "driveFileId",
                "driveFileUrl",
            )
        ):
            raise ValueError(
                f"{dictionary_id}: retired entries must not expose live distribution fields"
            )

    print(f"Dictionary catalog check passed ({len(dictionaries)} editions).")


if __name__ == "__main__":
    main()
