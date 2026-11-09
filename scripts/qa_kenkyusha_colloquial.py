import argparse
import collections
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    stats: collections.Counter[str] = collections.Counter()
    terms: list[str] = []
    sequences: set[int] = set()
    link_targets: list[str] = []

    with zipfile.ZipFile(args.zip) as archive:
        names = set(archive.namelist())
        index = json.loads(archive.read("index.json"))
        styles = archive.read("styles.css").decode("utf-8")
        if index.get("revision") != "2026.08.08.1":
            errors.append(f"版本号异常：{index.get('revision')}")
        if index.get("sourceLanguage") != "ja" or index.get("targetLanguage") != "ja":
            errors.append("词典语言方向不是 ja → ja")
        if "img/kqcol/cover.png" not in names:
            errors.append("词典包缺少封面资源")
        if '[data-sc-kqcol~="meaning-text"]' not in styles:
            errors.append("styles.css 缺少释义选择器")
        if "var(--fg-color" not in styles or "var(--meikyo-gray" not in styles:
            errors.append("styles.css 未兼容 Lapis/明镜夜间变量")
        theme_styles = re.sub(r"/\*.*?\*/", "", styles, flags=re.DOTALL)
        if any(token in theme_styles for token in ("html[data-theme", "body[data-theme", ":root[data-theme", " & [data-sc-kqcol")):
            errors.append("styles.css 包含不兼容词典作用域的根节点主题选择器")

        for name in sorted(
            value for value in names if value.startswith("term_bank_") and value.endswith(".json")
        ):
            stats["term_banks"] += 1
            for row in json.loads(archive.read(name)):
                stats["terms"] += 1
                terms.append(row[0])
                sequences.add(row[6])
                if not row[1]:
                    stats["empty_readings"] += 1
                for node in walk(row[5]):
                    marker_data = node.get("data")
                    marker = marker_data.get("kqcol") if isinstance(marker_data, dict) else ""
                    for value in marker.split():
                        stats[f"marker:{value}"] += 1
                    if node.get("tag") == "ruby":
                        stats["ruby"] += 1
                    if node.get("tag") == "a":
                        href = node.get("href", "")
                        if href.startswith("?query="):
                            query = parse_qs(urlparse(href).query).get("query", [""])[0]
                            if query:
                                link_targets.append(query)

    term_set = set(terms)
    for sample in [
        "ああ言えばこう言う",
        "愛嬌がある",
        "愛敬がある",
        "あざとい",
        "b級グルメ",
        "凡例・付録",
        "著作権",
    ]:
        if sample not in term_set:
            errors.append(f"缺少样例词条：{sample}")
    if stats["terms"] != 7162:
        errors.append(f"词条记录数量异常：{stats['terms']}")
    if len(sequences) != 3342:
        errors.append(f"正文/附录序列数量异常：{len(sequences)}")
    if stats["marker:dic-item"] == 0 or stats["marker:meaning-text"] == 0:
        errors.append("缺少正文结构标记")
    if stats["marker:example-text"] == 0 or stats["ruby"] == 0:
        errors.append("会话例或 Ruby 未保留")
    numeric_terms = sorted(term for term in term_set if term.isdigit())
    if numeric_terms:
        errors.append(f"存在 {len(numeric_terms)} 个数字 ID 词头")
    bracketed_terms = sorted(term for term in term_set if "【" in term or "】" in term)
    if bracketed_terms:
        errors.append(f"存在 {len(bracketed_terms)} 个未拆分的复合检索词头")
    broken_targets = sorted(set(link_targets) - term_set)
    if broken_targets:
        errors.append(f"存在 {len(broken_targets)} 个未收录的内部链接目标")

    result = {
        "zip": str(args.zip),
        "sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest().upper(),
        "bytes": args.zip.stat().st_size,
        "index": index,
        "stats": dict(stats),
        "unique_terms": len(term_set),
        "unique_sequences": len(sequences),
        "internal_link_targets": len(link_targets),
        "broken_internal_link_targets": broken_targets,
        "errors": errors,
        "passed": not errors,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
