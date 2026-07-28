import argparse
import json
import zipfile
from pathlib import Path

import fastjsonschema


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate every term_bank_*.json in a Yomitan dictionary."
    )
    parser.add_argument("dictionary", type=Path, help="Yomitan ZIP archive")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/dictionary-term-bank-v3-schema.json"),
        help="official Yomitan term bank v3 schema",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validate = fastjsonschema.compile(schema)

    validated = []
    with zipfile.ZipFile(args.dictionary) as archive:
        for name in sorted(
            name
            for name in archive.namelist()
            if name.startswith("term_bank_") and name.endswith(".json")
        ):
            validate(json.loads(archive.read(name)))
            validated.append(name)

    if not validated:
        raise ValueError("archive contains no term_bank_*.json files")

    result = {"official_schema_valid": True, "validated_files": validated}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
