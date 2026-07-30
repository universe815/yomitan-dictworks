import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"
USER_AGENT = "yomitan-dictworks-link-check/1.0"
ZIP_EOCD_SIGNATURE = b"PK\x05\x06"
ZIP_EOCD_MIN_BYTES = 22
ZIP_MAX_COMMENT_BYTES = 65_535
ZIP_TAIL_BYTES = ZIP_EOCD_MIN_BYTES + ZIP_MAX_COMMENT_BYTES
CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def request(
    url: str,
    *,
    method: str,
    timeout: float,
    headers: dict[str, str] | None = None,
):
    return urllib.request.urlopen(
        urllib.request.Request(
            url,
            method=method,
            headers={"User-Agent": USER_AGENT, **(headers or {})},
        ),
        timeout=timeout,
    )


def verify_zip_tail(
    dictionary_id: str,
    channel: str,
    url: str,
    *,
    expected_bytes: int,
    timeout: float,
) -> int:
    """Fetch the smallest valid ZIP tail and verify its end-of-directory record."""
    start = max(0, expected_bytes - ZIP_TAIL_BYTES)
    end = expected_bytes - 1
    with request(
        url,
        method="GET",
        timeout=timeout,
        headers={"Range": f"bytes={start}-{end}"},
    ) as response:
        if response.status != 206:
            raise ValueError(
                f"{dictionary_id} {channel}: download server ignored the bounded byte range "
                f"(returned {response.status})"
            )
        content_range = response.headers.get("Content-Range", "")
        match = CONTENT_RANGE.fullmatch(content_range)
        if match is None:
            raise ValueError(
                f"{dictionary_id} {channel}: invalid Content-Range {content_range!r}"
            )
        actual_start, actual_end, actual_total = map(int, match.groups())
        if (actual_start, actual_end, actual_total) != (
            start,
            end,
            expected_bytes,
        ):
            raise ValueError(
                f"{dictionary_id} {channel}: ranged download size differs from catalog"
            )
        tail = response.read(ZIP_TAIL_BYTES + 1)

    expected_tail_bytes = end - start + 1
    if len(tail) != expected_tail_bytes:
        raise ValueError(
            f"{dictionary_id} {channel}: ranged download returned {len(tail)} bytes, "
            f"expected {expected_tail_bytes}"
        )

    eocd_offset = tail.rfind(ZIP_EOCD_SIGNATURE)
    if eocd_offset < 0 or len(tail) - eocd_offset < ZIP_EOCD_MIN_BYTES:
        raise ValueError(
            f"{dictionary_id} {channel}: ZIP end-of-central-directory not found"
        )
    comment_length = int.from_bytes(
        tail[eocd_offset + 20 : eocd_offset + 22],
        byteorder="little",
    )
    if eocd_offset + ZIP_EOCD_MIN_BYTES + comment_length != len(tail):
        raise ValueError(
            f"{dictionary_id} {channel}: ZIP end-of-central-directory is "
            "truncated or misplaced"
        )
    return len(tail)


def verify_full_hash(
    dictionary_id: str,
    channel: str,
    url: str,
    *,
    expected_bytes: int,
    expected_sha256: str,
    timeout: float,
) -> str:
    digest = hashlib.sha256()
    downloaded_bytes = 0
    with request(url, method="GET", timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(
                f"{dictionary_id} {channel}: full download returned "
                f"{response.status}"
            )
        while chunk := response.read(1024 * 1024):
            downloaded_bytes += len(chunk)
            digest.update(chunk)
    if downloaded_bytes != expected_bytes:
        raise ValueError(
            f"{dictionary_id} {channel}: full download size differs from catalog"
        )
    actual_sha256 = digest.hexdigest().upper()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"{dictionary_id} {channel}: SHA-256 differs from catalog"
        )
    return actual_sha256


def verify_download(
    dictionary_id: str,
    channel: str,
    url: str,
    *,
    expected_bytes: int,
    expected_sha256: str,
    timeout: float,
    full_hash: bool,
) -> dict[str, object]:
    with request(url, method="HEAD", timeout=timeout) as response:
        content_length = int(response.headers.get("Content-Length", "-1"))
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200:
            raise ValueError(
                f"{dictionary_id} {channel}: download returned {response.status}"
            )
        if expected_bytes != content_length:
            raise ValueError(
                f"{dictionary_id} {channel}: public byte size differs from catalog"
            )
        if content_type.split(";", 1)[0] not in {
            "application/octet-stream",
            "application/zip",
        }:
            raise ValueError(
                f"{dictionary_id} {channel}: unexpected download content type "
                f"{content_type!r}"
            )

    zip_tail_bytes = verify_zip_tail(
        dictionary_id,
        channel,
        url,
        expected_bytes=expected_bytes,
        timeout=timeout,
    )
    result: dict[str, object] = {
        "url": url,
        "status": 200,
        "bytes": content_length,
        "zipTailBytesChecked": zip_tail_bytes,
        "zipTailValid": True,
    }
    if full_hash:
        result["sha256"] = verify_full_hash(
            dictionary_id,
            channel,
            url,
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
            timeout=timeout,
        )
        result["sha256Valid"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify public manifests and automatic-update ZIP downloads."
    )
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument(
        "--local-manifests",
        action="store_true",
        help="Check working-tree manifests before they are merged to the public URLs.",
    )
    parser.add_argument(
        "--full-hash",
        action="store_true",
        help=(
            "Download both the Release and Google Drive ZIPs and verify SHA-256. "
            "Use this before merging a dictionary update."
        ),
    )
    parser.add_argument(
        "--dictionary-id",
        action="append",
        dest="dictionary_ids",
        help="Check only the selected catalog edition; repeat as needed.",
    )
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    selected_ids = set(args.dictionary_ids or [])
    catalog_ids = {entry["id"] for entry in catalog["dictionaries"]}
    unknown_ids = sorted(selected_ids - catalog_ids)
    if unknown_ids:
        raise ValueError(
            f"unknown dictionary IDs: {', '.join(unknown_ids)}"
        )
    checked_folders: set[str] = set()
    results: list[dict[str, object]] = []

    for entry in catalog["dictionaries"]:
        if selected_ids and entry["id"] not in selected_ids:
            continue
        distribution = entry["distribution"]
        if distribution["status"] != "public":
            continue

        checked_folders.add(distribution["driveFolderUrl"])
        expected_bytes = distribution["bytes"]
        expected_sha256 = distribution["sha256"]
        release_result = verify_download(
            entry["id"],
            "release",
            distribution["downloadUrl"],
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
            timeout=args.timeout,
            full_hash=args.full_hash,
        )
        drive_download_url = (
            "https://drive.usercontent.google.com/download"
            f"?id={distribution['driveFileId']}&export=download&confirm=t"
        )
        drive_result = verify_download(
            entry["id"],
            "drive",
            drive_download_url,
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
            timeout=args.timeout,
            full_hash=args.full_hash,
        )

        if args.local_manifests:
            manifest_path = ROOT / "manifests" / entry["id"] / "index.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            with request(
                distribution["indexUrl"],
                method="GET",
                timeout=args.timeout,
            ) as response:
                manifest = json.load(response)
        for field in ("title", "revision", "indexUrl", "downloadUrl"):
            expected = (
                entry[field]
                if field in {"title", "revision"}
                else distribution[field]
            )
            if manifest.get(field) != expected:
                raise ValueError(
                    f"{entry['id']}: public manifest {field} differs from catalog"
                )

        results.append(
            {
                "id": entry["id"],
                "revision": entry["revision"],
                "channelsMatch": True,
                "release": release_result,
                "googleDrive": {
                    "fileUrl": distribution["driveFileUrl"],
                    **drive_result,
                },
            }
        )

    print(
        json.dumps(
            {
                "publicLinksValid": True,
                "folders": sorted(checked_folders),
                "dictionaries": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
