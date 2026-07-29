import argparse
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"
USER_AGENT = "yomitan-dictworks-link-check/1.0"


def request(url: str, *, method: str, timeout: float):
    return urllib.request.urlopen(
        urllib.request.Request(
            url,
            method=method,
            headers={"User-Agent": USER_AGENT},
        ),
        timeout=timeout,
    )


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
            if distribution.get("bytes") not in (None, content_length):
                raise ValueError(f"{entry['id']}: public byte size differs from catalog")
            if content_type not in {"application/octet-stream", "application/zip"}:
                raise ValueError(
                    f"{entry['id']}: unexpected download content type {content_type!r}"
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
