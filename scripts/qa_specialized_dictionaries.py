import argparse
import collections
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


PROFILES: dict[str, dict[str, Any]] = {
    "modern-adverb": {
        "title": "現代日本語副詞用法辞典（中文版）",
        "revision": "2026.08.13.1",
        "source_language": "ja",
        "target_language": "zh",
        "data_key": "madv",
        "terms": 2222,
        "sequences": 972,
        "samples": ["相変わらず", "あいかわらず", "近く", "われもわれも"],
        "markers": ["entry", "definition", "example-ja", "example-zh", "analysis", "comparison"],
        "minimum_ruby": 100,
        "minimum_links": 5000,
        "images": [],
    },
    "kenkyusha-expression-usage": {
        "title": "研究社 日本語表現活用辞典",
        "revision": "2026.08.13.1",
        "source_language": "ja",
        "target_language": "ja",
        "data_key": "kexpr",
        "terms": 3527,
        "sequences": 1641,
        "samples": ["愛する", "あいする", "断つ", "絶つ", "裁つ", "ルーズ", "best"],
        "markers": ["entry", "patterns", "examples", "idioms", "compounds"],
        "minimum_ruby": 0,
        "minimum_links": 0,
        "images": [],
    },
    "meikyo-kotowaza": {
        "title": "明鏡 ことわざ成句使い方辞典",
        "revision": "2026.08.13.1",
        "source_language": "ja",
        "target_language": "ja",
        "data_key": "mkw",
        "terms": 10996,
        "sequences": 5540,
        "samples": ["まえがき", "著作権", "虎口を逃れて竜穴に入る", "「腕」を使う成句"],
        "markers": ["entry", "netdichead", "netdicbody", "index-info", "index-kind"],
        "minimum_ruby": 14000,
        "minimum_links": 10000,
        "images": ["img/mkw/0006.png", "img/mkw/0008.png"],
    },
}


def walk(value: Any):
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
    parser.add_argument("profile", choices=sorted(PROFILES))
    parser.add_argument("zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    profile = PROFILES[args.profile]

    errors: list[str] = []
    stats: collections.Counter[str] = collections.Counter()
    terms: list[str] = []
    sequences: set[int] = set()
    checked_sequences: set[int] = set()
    link_targets: list[str] = []
    referenced_images: set[str] = set()

    with zipfile.ZipFile(args.zip) as archive:
        names = set(archive.namelist())
        index = json.loads(archive.read("index.json"))
        styles = archive.read("styles.css").decode("utf-8")
        if index.get("title") != profile["title"]:
            errors.append(f"标题异常：{index.get('title')}")
        if index.get("revision") != profile["revision"]:
            errors.append(f"版本号异常：{index.get('revision')}")
        if index.get("sourceLanguage") != profile["source_language"]:
            errors.append(f"源语言异常：{index.get('sourceLanguage')}")
        if index.get("targetLanguage") != profile["target_language"]:
            errors.append(f"目标语言异常：{index.get('targetLanguage')}")

        data_key = profile["data_key"]
        if f'[data-sc-{data_key}~="entry"]' not in styles:
            errors.append("styles.css 缺少词典根选择器")
        if "var(--fg-color" not in styles or "@media (prefers-color-scheme: dark)" not in styles:
            errors.append("styles.css 缺少 Lapis/夜间模式回退")
        theme_styles = re.sub(r"/\*.*?\*/", "", styles, flags=re.DOTALL)
        if any(
            token in theme_styles
            for token in ("html[data-theme", "body[data-theme", ":root[data-theme")
        ):
            errors.append("styles.css 含不兼容的根节点主题选择器")

        for expected_image in profile["images"]:
            if expected_image not in names:
                errors.append(f"词典包缺少资源：{expected_image}")

        bank_names = sorted(
            name
            for name in names
            if name.startswith("term_bank_") and name.endswith(".json")
        )
        for name in bank_names:
            stats["term_banks"] += 1
            for row in json.loads(archive.read(name)):
                stats["term_records"] += 1
                terms.append(row[0])
                sequence = row[6]
                sequences.add(sequence)
                if sequence in checked_sequences:
                    continue
                checked_sequences.add(sequence)
                for node in walk(row[5]):
                    marker_data = node.get("data")
                    marker = marker_data.get(data_key) if isinstance(marker_data, dict) else ""
                    for value in marker.split():
                        stats[f"marker:{value}"] += 1
                    if node.get("tag") == "ruby":
                        stats["ruby_nodes"] += 1
                    elif node.get("tag") == "a":
                        href = node.get("href", "")
                        if href.startswith("?query="):
                            target = parse_qs(urlparse(href).query).get("query", [""])[0]
                            if target:
                                link_targets.append(target)
                    elif node.get("tag") == "img":
                        path = node.get("path", "")
                        if path:
                            referenced_images.add(path)

    term_set = set(terms)
    if stats["term_records"] != profile["terms"]:
        errors.append(
            f"检索记录数量异常：{stats['term_records']}（预期 {profile['terms']}）"
        )
    if len(sequences) != profile["sequences"]:
        errors.append(
            f"正文序列数量异常：{len(sequences)}（预期 {profile['sequences']}）"
        )
    for sample in profile["samples"]:
        if sample not in term_set:
            errors.append(f"缺少样例词条：{sample}")
    for marker in profile["markers"]:
        if stats[f"marker:{marker}"] == 0:
            errors.append(f"缺少结构标记：{marker}")
    if stats["ruby_nodes"] < profile["minimum_ruby"]:
        errors.append(
            f"Ruby 数量异常：{stats['ruby_nodes']}（至少 {profile['minimum_ruby']}）"
        )
    if len(link_targets) < profile["minimum_links"]:
        errors.append(
            f"内部链接数量异常：{len(link_targets)}（至少 {profile['minimum_links']}）"
        )

    broken_targets = sorted(set(link_targets) - term_set)
    if broken_targets:
        errors.append(f"存在 {len(broken_targets)} 个未收录的内部链接目标")
    missing_referenced_images = sorted(referenced_images - names)
    if missing_referenced_images:
        errors.append(f"存在 {len(missing_referenced_images)} 个缺失图片引用")

    result = {
        "profile": args.profile,
        "zip": str(args.zip),
        "sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest().upper(),
        "bytes": args.zip.stat().st_size,
        "index": index,
        "stats": dict(stats),
        "unique_terms": len(term_set),
        "unique_sequences": len(sequences),
        "internal_links": len(link_targets),
        "broken_internal_link_targets": broken_targets,
        "referenced_images": sorted(referenced_images),
        "missing_referenced_images": missing_referenced_images,
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
