import argparse
import json
import zipfile
from pathlib import Path


def walk(value, stats):
    if isinstance(value, list):
        for item in value:
            walk(item, stats)
    elif isinstance(value, dict):
        tag = value.get("tag")
        if tag:
            stats[tag] = stats.get(tag, 0) + 1
        walk(value.get("content"), stats)


def is_redirect(value):
    if isinstance(value, list):
        return any(is_redirect(item) for item in value)
    if isinstance(value, dict):
        if value.get("data", {}).get("xsjrh") == "redirect":
            return True
        return is_redirect(value.get("content"))
    return False


def main():
    parser = argparse.ArgumentParser(description="QA NINJAL V-V compound verb archive")
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()

    errors = []
    with zipfile.ZipFile(args.zip) as archive:
        names = set(archive.namelist())
        if "index.json" not in names or "styles.css" not in names:
            errors.append("index.json/styles.css 缺失")
        banks = sorted(name for name in names if name.startswith("term_bank_") and name.endswith(".json"))
        if banks != ["term_bank_1.json"]:
            errors.append(f"term bank 不符合预期: {banks}")
        terms = []
        stats = {}
        direct = 0
        redirects = 0
        for bank in banks:
            values = json.loads(archive.read(bank))
            for entry in values:
                terms.append(entry[0])
                definitions = entry[5]
                if any(isinstance(d, dict) and is_redirect(d.get("content")) for d in definitions):
                    redirects += 1
                else:
                    direct += 1
                    for definition in definitions:
                        if isinstance(definition, dict):
                            walk(definition.get("content"), stats)
        for sample in ("仰ぎ見る", "塗り固める", "割り戻す"):
            if sample not in terms:
                errors.append(f"缺少代表词条: {sample}")
        if len(terms) < 3000:
            errors.append(f"词条数异常: {len(terms)}")

    result = {
        "zip": str(args.zip),
        "terms": len(terms),
        "direct": direct,
        "redirects": redirects,
        "structuredTags": stats,
        "errors": errors,
        "passed": not errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
