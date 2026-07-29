import argparse
import json
import os
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"
INDEX_FIELDS = (
    "title",
    "revision",
    "author",
    "description",
    "attribution",
    "url",
)


def load_entry(dictionary_id: str) -> tuple[dict[str, object], dict[str, object]]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    try:
        entry = next(
            item
            for item in catalog["dictionaries"]
            if item["id"] == dictionary_id
        )
    except StopIteration as error:
        raise ValueError(f"unknown dictionary ID: {dictionary_id}") from error
    config = json.loads((ROOT / entry["config"]).read_text(encoding="utf-8"))
    return entry, config


def updated_index(
    current: dict[str, object],
    entry: dict[str, object],
    config: dict[str, object],
) -> dict[str, object]:
    distribution = entry["distribution"]
    if not isinstance(distribution, dict):
        raise ValueError(f"{entry['id']}: distribution must be an object")
    for field in INDEX_FIELDS:
        value = config.get(field)
        if value is None:
            current.pop(field, None)
        else:
            current[field] = value
    current["isUpdatable"] = True
    current["indexUrl"] = distribution["indexUrl"]
    current["downloadUrl"] = distribution["downloadUrl"]
    return current


def repack(
    source_path: Path,
    output_path: Path,
    *,
    entry: dict[str, object],
    config: dict[str, object],
) -> None:
    if source_path.resolve() == output_path.resolve():
        raise ValueError("source and output paths must differ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    temporary_path.unlink(missing_ok=True)

    try:
        with zipfile.ZipFile(source_path, "r") as source:
            source_members = source.infolist()
            source_fingerprints = [
                (
                    member.filename,
                    member.CRC,
                    member.file_size,
                    member.compress_type,
                )
                for member in source_members
            ]
            index_members = [
                info for info in source_members if info.filename == "index.json"
            ]
            if len(index_members) != 1:
                raise ValueError(
                    f"{source_path}: expected one index.json, found "
                    f"{len(index_members)}"
                )
            current_index = json.loads(source.read(index_members[0]))
            new_index = updated_index(current_index, entry, config)
            index_bytes = (
                json.dumps(new_index, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")

            with zipfile.ZipFile(
                temporary_path,
                "w",
                allowZip64=True,
            ) as target:
                target.comment = source.comment
                for member in source_members:
                    data = (
                        index_bytes
                        if member.filename == "index.json"
                        else source.read(member)
                    )
                    target.writestr(member, data)

        with zipfile.ZipFile(temporary_path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"{output_path}: CRC failure in {bad_member}")
            output_members = archive.infolist()
            if [member.filename for member in output_members] != [
                fingerprint[0] for fingerprint in source_fingerprints
            ]:
                raise ValueError(f"{output_path}: ZIP member order changed")
            for source_fingerprint, output_member in zip(
                source_fingerprints,
                output_members,
                strict=True,
            ):
                source_name, source_crc, source_size, source_compression = (
                    source_fingerprint
                )
                if source_name == "index.json":
                    continue
                if (
                    source_crc,
                    source_size,
                    source_compression,
                ) != (
                    output_member.CRC,
                    output_member.file_size,
                    output_member.compress_type,
                ):
                    raise ValueError(
                        f"{output_path}: non-index member changed: "
                        f"{source_name}"
                    )
            written_index = json.loads(archive.read("index.json"))
        for field in ("title", "revision", "indexUrl", "downloadUrl"):
            expected = (
                entry[field]
                if field in {"title", "revision"}
                else entry["distribution"][field]
            )
            if written_index.get(field) != expected:
                raise ValueError(f"{output_path}: index {field} mismatch")
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Repack an existing Yomitan ZIP with current catalog update metadata."
        )
    )
    parser.add_argument("--dictionary-id", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    entry, config = load_entry(args.dictionary_id)
    output_file = config.get("outputFile")
    if not isinstance(output_file, str) or not output_file.endswith(".zip"):
        raise ValueError(f"{args.dictionary_id}: config outputFile must end in .zip")
    output_path = args.output_dir / output_file
    repack(
        args.source,
        output_path,
        entry=entry,
        config=config,
    )
    print(
        json.dumps(
            {
                "dictionaryId": args.dictionary_id,
                "source": str(args.source),
                "output": str(output_path),
                "bytes": output_path.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
