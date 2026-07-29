import argparse
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
                f"{dictionary_id}: download server ignored the bounded byte range "
                f"(returned {response.status})"
            )
        content_range = response.headers.get("Content-Range", "")
        match = CONTENT_RANGE.fullmatch(content_range)
        if match is None:
            raise ValueError(
                f"{dictionary_id}: invalid Content-Range {content_range!r}"
            )
        actual_start, actual_end, actual_total = map(int, match.groups())
        if (actual_start, actual_end, actual_total) != (
            start,
            end,
            expected_bytes,
        ):
            raise ValueError(
                f"{dictionary_id}: ranged download size differs from catalog"
            )
        tail = response.read(ZIP_TAIL_BYTES + 1)

    expected_tail_bytes = end - start + 1
    if len(tail) != expected_tail_bytes:
        raise ValueError(
            f"{dictionary_id}: ranged download returned {len(tail)} bytes, "
            f"expected {expected_tail_bytes}"
        )

    eocd_offset = tail.rfind(ZIP_EOCD_SIGNATURE)
    if eocd_offset < 0 or len(tail) - eocd_offset < ZIP_EOCD_MIN_BYTES:
        raise ValueError(f"{dictionary_id}: ZIP end-of-central-directory not found")
    comment_length = int.from_bytes(
        tail[eocd_offset + 20 : eocd_offset + 22],
        byteorder="little",
    )
    if eocd_offset + ZIP_EOCD_MIN_BYTES + comment_length != len(tail):
        raise ValueError(
            f"{dictionary_id}: ZIP end-of-central-directory is truncated or misplaced"
        )
    return len(tail)


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
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    checked_folders: set[str] = set()
    results: list[dict[str, object]] = []

    for entry in catalog["dictionaries"]:
        distribution = entry["distribution"]
        if distribution["status"] != "public":
            continue

        checked_folders.add(distribution["driveFolderUrl"])
        expected_bytes = distribution["bytes"]

        with request(
            distribution["downloadUrl"],
            method="HEAD",
            timeout=args.timeout,
        ) as response:
            content_length = int(response.headers.get("Content-Length", "-1"))
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200:
                raise ValueError(
                    f"{entry['id']}: download returned {response.status}"
                )
            if expected_bytes != content_length:
                raise ValueError(f"{entry['id']}: public byte size differs from catalog")
            if content_type.split(";", 1)[0] not in {
                "application/octet-stream",
                "application/zip",
            }:
                raise ValueError(
                    f"{entry['id']}: unexpected download content type {content_type!r}"
                )

        zip_tail_bytes = verify_zip_tail(
            entry["id"],
            distribution["downloadUrl"],
            expected_bytes=expected_bytes,
            timeout=args.timeout,
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
                "downloadStatus": 200,
                "bytes": content_length,
                "zipTailBytesChecked": zip_tail_bytes,
                "zipTailValid": True,
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
