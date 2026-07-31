import argparse
import collections
import hashlib
import json
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


COMMON_CONTENT = {"tag", "content", "data", "style", "title", "open", "lang"}
ALLOWED_KEYS = {
    "br": {"tag", "data"},
    "ruby": {"tag", "content", "data", "lang"},
    "rt": {"tag", "content", "data", "lang"},
    "rp": {"tag", "content", "data", "lang"},
    "table": {"tag", "content", "data", "lang"},
    "thead": {"tag", "content", "data", "lang"},
    "tbody": {"tag", "content", "data", "lang"},
    "tfoot": {"tag", "content", "data", "lang"},
    "tr": {"tag", "content", "data", "lang"},
    "td": COMMON_CONTENT | {"colSpan", "rowSpan"},
    "th": COMMON_CONTENT | {"colSpan", "rowSpan"},
    "span": COMMON_CONTENT,
    "div": COMMON_CONTENT,
    "ol": COMMON_CONTENT,
    "ul": COMMON_CONTENT,
    "li": COMMON_CONTENT,
    "details": COMMON_CONTENT,
    "summary": COMMON_CONTENT,
    "a": {"tag", "content", "href", "lang"},
}


parser = argparse.ArgumentParser()
parser.add_argument("zip", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()

errors = []
stats = collections.Counter()
terms = []
definitions = {}
with zipfile.ZipFile(args.zip) as archive:
    names = set(archive.namelist())
    index = json.loads(archive.read("index.json"))
    styles = archive.read("styles.css").decode("utf-8")
    if "[data-sc-onomato" not in styles:
        errors.append("styles.css 缺少 data-sc-onomato 选择器")
    if "[data-onomato" in styles:
        errors.append("styles.css 包含错误的 data-onomato 选择器")
    if ':root[data-theme="dark"] & [data-sc-onomato~="entry"]' not in styles:
        errors.append('styles.css 未正确跳出 Yomitan 词典作用域以响应深色主题')
    for required_style in ["#c90000", "#0056b3", 'content: "／"', '"word-group"] a']:
        if required_style not in styles:
            errors.append(f"styles.css 缺少原版特色规则：{required_style}")
    for name in sorted(
        item for item in names if item.startswith("term_bank_") and item.endswith(".json")
    ):
        bank = json.loads(archive.read(name))
        stats["term_banks"] += 1
        for row in bank:
            term = row[0]
            terms.append(term)
            definitions.setdefault(term, []).append(row[5])
            stats["terms"] += 1
            for node in walk(row[5]):
                data = node.get("data")
                marker = data.get("onomato") if isinstance(data, dict) else ""
                if marker:
                    stats[f"marker:{marker}"] += 1
                if node.get("tag") == "a":
                    stats["links"] += 1

term_set = set(terms)
for sample in ["あたふた", "あっけらかん", "うっかり", "ぱちぱちっ", "うっかり者"]:
    if sample not in term_set:
        errors.append(f"缺少样例词条：{sample}")

all_nodes = []
for values in definitions.values():
    for value in values:
        all_nodes.extend(walk(value))

invalid_nodes = []
for node in all_nodes:
    tag = node.get("tag")
    if not tag:
        continue
    allowed = ALLOWED_KEYS.get(tag)
    if allowed is None:
        invalid_nodes.append({"tag": tag, "reason": "unsupported tag"})
        continue
    unexpected = sorted(set(node) - allowed)
    if unexpected:
        invalid_nodes.append({"tag": tag, "unexpected": unexpected})
if invalid_nodes:
    errors.append(f"存在 {len(invalid_nodes)} 个不符合结构化内容模式的节点")

link_targets = []
for node in all_nodes:
    if node.get("tag") != "a":
        continue
    href = node.get("href", "")
    if href.startswith("?query="):
        query = parse_qs(urlparse(href).query).get("query", [""])[0]
        if query:
            link_targets.append(query)
broken_targets = sorted(set(link_targets) - term_set)
if broken_targets:
    errors.append(f"存在 {len(broken_targets)} 个未收录的内部链接目标")

if stats["marker:example-ja"] != 6744:
    errors.append(f"日文例句数量异常：{stats['marker:example-ja']}")
if stats["marker:example-zh"] != 6744:
    errors.append(f"中文例句数量异常：{stats['marker:example-zh']}")
if stats["marker:subentry-headword"] < 237:
    errors.append(f"子词条结构数量异常：{stats['marker:subentry-headword']}")

digest = hashlib.sha256(args.zip.read_bytes()).hexdigest().upper()
result = {
    "zip": str(args.zip),
    "sha256": digest,
    "bytes": args.zip.stat().st_size,
    "index": index,
    "stats": dict(stats),
    "unique_terms": len(term_set),
    "internal_link_targets": len(link_targets),
    "broken_internal_link_targets": broken_targets,
    "invalid_structured_content_nodes": invalid_nodes[:20],
    "errors": errors,
    "passed": not errors,
}
text = json.dumps(result, ensure_ascii=False, indent=2)
print(text)
if args.output:
    args.output.write_text(text, encoding="utf-8")
raise SystemExit(0 if not errors else 1)
