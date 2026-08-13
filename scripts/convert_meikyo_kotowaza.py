import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

from lxml import html


WHITESPACE_RE = re.compile(r"\s+")
COUNT_SUFFIX_RE = re.compile(r"\s*\(\d+\)$")
GAIJI_PLACEHOLDER_RE = re.compile(r"〓\[[^\]]+:([0-9A-Fa-f]{4,5})\]")
GAIJI_URL_RE = re.compile(r"(?:[?&]|^)name=([0-9A-Fa-f]{4,5})(?:&|$)", re.IGNORECASE)
BLOCK_TAGS = {"html", "body", "div", "section", "article", "p", "h1", "h2", "h3"}
SKIP_TAGS = {"style", "layout", "script", "link", "meta"}


def replace_gaiji(value: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        try:
            return chr(int(match.group(1), 16))
        except ValueError:
            return match.group(0)

    return GAIJI_PLACEHOLDER_RE.sub(replacement, value)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = replace_gaiji(value).replace("\u200b", "")
    return WHITESPACE_RE.sub(" ", value).strip()


def clean_title(value: str | None) -> str:
    return clean_text(value).lstrip("■ \u3000")


def strip_count(value: str) -> str:
    return COUNT_SUFFIX_RE.sub("", clean_text(value))


def compact_content(parts: list[Any]) -> Any:
    values = [part for part in parts if part not in (None, "", [])]
    if not values:
        return None
    return values[0] if len(values) == 1 else values


def normalized_classes(element: Any) -> list[str]:
    values: list[str] = []
    for value in (element.get("class") or "").split():
        token = re.sub(r"[^a-z0-9-]+", "-", value.replace("_", "-").lower()).strip("-")
        if token and token not in values:
            values.append(token)
    return values


def marker_tokens(element: Any, extra: list[str] | None = None) -> list[str]:
    values = normalized_classes(element)
    style = (element.get("style") or "").lower()
    if "font-size:140%" in style or "font-size: 140%" in style:
        values.append("headword")
    if "font-weight:bold" in style or "font-weight: bold" in style:
        values.append("bold")
    if element.get("data-txt-len") is not None:
        values.append("label")
    if element.get("data-wordanal") == "outword":
        values.append("label-text")
    if (element.get("align") or "").lower() == "right":
        values.append("align-right")
    for value in extra or []:
        if value not in values:
            values.append(value)
    return list(dict.fromkeys(values))


def element_content(
    element: Any,
    id_to_term: dict[str, str],
    stats: Counter[str],
) -> Any:
    parts: list[Any] = []
    text = clean_text(element.text)
    if text:
        parts.append(text)
    for child in element:
        converted = convert_element(child, id_to_term, stats)
        if converted is not None:
            parts.append(converted)
        tail = clean_text(child.tail)
        if tail:
            parts.append(tail)
    return compact_content(parts)


def convert_image(element: Any, stats: Counter[str]) -> Any:
    src = element.get("src") or ""
    match = GAIJI_URL_RE.search(src)
    if not match:
        stats["unsupported_images"] += 1
        return clean_text(element.get("alt")) or None
    name = match.group(1).upper()
    if name in {"0006", "0008"}:
        stats["image_nodes"] += 1
        return {
            "tag": "img",
            "path": f"img/mkw/{name}.png",
            "alt": clean_text(element.get("alt")) or f"原辞典图像 {name}",
            "title": clean_text(element.get("title")) or f"原辞典图像 {name}",
            "height": 1.25,
            "sizeUnits": "em",
            "verticalAlign": "middle",
            "background": False,
        }
    try:
        stats["gaiji_replacements"] += 1
        return chr(int(name, 16))
    except ValueError:
        stats["unsupported_images"] += 1
        return None


def convert_element(
    element: Any,
    id_to_term: dict[str, str],
    stats: Counter[str],
) -> Any:
    tag = str(element.tag).lower() if isinstance(element.tag, str) else ""
    if tag in SKIP_TAGS:
        return None
    if tag == "br":
        return {"tag": "br"}
    if tag == "img":
        return convert_image(element, stats)

    content = element_content(element, id_to_term, stats)
    if content is None:
        return None

    classes = normalized_classes(element)
    if "netdicitemlink" in classes:
        target_id = element.get("itemid") or element.get("ItemID") or ""
        target = id_to_term.get(target_id)
        if target:
            stats["internal_links"] += 1
            return {
                "tag": "a",
                "href": f"?query={quote(target)}",
                "lang": "ja",
                "content": content,
            }
        stats["unresolved_internal_links"] += 1
        return content

    if tag == "rb":
        node: dict[str, Any] = {"tag": "span", "content": content, "lang": "ja"}
    elif tag in {"ruby", "rt"}:
        node = {"tag": tag, "content": content, "lang": "ja"}
        if tag == "ruby":
            stats["ruby_nodes"] += 1
    elif tag == "sup":
        node = {
            "tag": "span",
            "content": content,
            "style": {"fontSize": "65%", "verticalAlign": "super"},
        }
    else:
        is_inline_label = element.get("data-wordanal") == "outword"
        node = {
            "tag": "span" if is_inline_label else ("div" if tag in BLOCK_TAGS else "span"),
            "content": content,
        }

    tokens = marker_tokens(element)
    if tokens:
        node["data"] = {"mkw": " ".join(tokens)}
    return node


def reading_from_head(source: str, fallback: str) -> str:
    try:
        root = html.fragment_fromstring(source, create_parent="div")
    except Exception:
        return fallback
    candidates = root.xpath(
        ".//div[contains(translate(@style, ' ', ''), 'font-size:140%')]"
    )
    node = candidates[0] if candidates else root

    def collect(element: Any) -> str:
        tag = str(element.tag).lower() if isinstance(element.tag, str) else ""
        if tag == "ruby":
            readings = [clean_text("".join(value.itertext())) for value in element.xpath("./rt")]
            return "".join(value for value in readings if value)
        parts = [clean_text(element.text)] if clean_text(element.text) else []
        for child in element:
            parts.append(collect(child))
            if clean_text(child.tail):
                parts.append(clean_text(child.tail))
        return "".join(parts)

    reading = clean_title(collect(node))
    return reading or fallback


def node_path(tree: dict[str, Any], node_id: str) -> list[tuple[str, str]]:
    path: list[tuple[str, str]] = []
    current = node_id
    seen: set[str] = set()
    while current and current in tree and current not in seen:
        seen.add(current)
        node = tree[current]
        path.append((current, strip_count(node.get("title", ""))))
        current = node.get("parent_id") or ""
    path.reverse()
    return path


def collect_indexes(
    tree: dict[str, Any],
) -> tuple[dict[str, list[str]], dict[str, list[tuple[str, list[str]]]], Counter[str]]:
    aliases: dict[str, list[str]] = defaultdict(list)
    paths: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    stats: Counter[str] = Counter()
    for node_id, node in tree.items():
        base_path = node_path(tree, node_id)
        if not base_path:
            continue
        root_id = base_path[0][0]
        root_title = base_path[0][1]
        category_path = [title for _, title in base_path[1:] if title]
        for child in node.get("children") or []:
            item_id = clean_text(child.get("item_id"))
            if not item_id:
                continue
            alias = clean_title(child.get("title"))
            if alias and len(alias) <= 200 and alias not in aliases[item_id]:
                aliases[item_id].append(alias)
                stats[f"aliases:{root_id}"] += 1
            display_path = [*category_path]
            if root_id != "M2" and alias:
                display_path.append(alias)
            marker = (root_title, display_path)
            if root_id != "M2" and marker not in paths[item_id]:
                paths[item_id].append(marker)
                stats[f"paths:{root_id}"] += 1
    return aliases, paths, stats


def index_node(paths: list[tuple[str, list[str]]]) -> dict[str, Any] | None:
    if not paths:
        return None
    rows: list[Any] = []
    for root_title, values in paths:
        rows.append(
            {
                "tag": "div",
                "data": {"mkw": "index-path"},
                "content": [
                    {
                        "tag": "span",
                        "data": {"mkw": "index-kind"},
                        "content": root_title,
                    },
                    "：",
                    " › ".join(values) if values else root_title,
                ],
            }
        )
    return {
        "tag": "details",
        "data": {"mkw": "index-info"},
        "content": [
            {
                "tag": "summary",
                "data": {"mkw": "index-summary"},
                "content": "原书索引",
            },
            *rows,
        ],
    }


def make_definition(
    row: dict[str, Any],
    id_to_term: dict[str, str],
    paths: list[tuple[str, list[str]]],
    stats: Counter[str],
) -> dict[str, Any]:
    root = html.fragment_fromstring(
        (row.get("Head") or "") + (row.get("Body") or ""),
        create_parent="div",
    )
    converted = element_content(root, id_to_term, stats)
    content: list[Any] = []
    if converted is not None:
        content.append(converted)
    indexes = index_node(paths)
    if indexes is not None:
        content.append(indexes)
        stats["entries_with_index_paths"] += 1
    stats["articles"] += 1
    return {
        "type": "structured-content",
        "content": {
            "tag": "div",
            "data": {"mkw": "entry"},
            "lang": "ja",
            "content": content,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Meikyo Kotowaza/Seiku source JSONL to Yomitan NDJSON."
    )
    parser.add_argument("--jsonl", type=Path, required=True)
    parser.add_argument("--index-tree", type=Path, required=True)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--resources-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    rows = [
        json.loads(line)
        for line in args.jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    tree = json.loads(args.index_tree.read_text(encoding="utf-8"))
    aliases_by_item, paths_by_item, index_stats = collect_indexes(tree)
    stats: Counter[str] = Counter(index_stats)

    id_to_term = {
        clean_text(row.get("ItemID")): clean_title(row.get("Title"))
        for row in rows
        if clean_text(row.get("ItemID")) and clean_title(row.get("Title"))
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.resources_dir.mkdir(parents=True, exist_ok=True)
    for name in ("0006.png", "0008.png"):
        source = args.images_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"missing source image: {source}")
        shutil.copyfile(source, args.resources_dir / name)
        stats["resources_copied"] += 1

    emitted: set[tuple[str, int]] = set()
    all_terms: set[str] = set()
    all_link_targets: set[str] = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for sequence, row in enumerate(rows, start=1):
            item_id = clean_text(row.get("ItemID"))
            title = clean_title(row.get("Title"))
            reading = reading_from_head(row.get("Head") or "", title)
            terms = list(
                dict.fromkeys(
                    value
                    for value in [title, reading, *aliases_by_item.get(item_id, [])]
                    if value
                )
            )
            definition = make_definition(
                row,
                id_to_term,
                paths_by_item.get(item_id, []),
                stats,
            )
            for term in terms:
                marker = (term, sequence)
                if marker in emitted:
                    continue
                emitted.add(marker)
                output.write(
                    json.dumps(
                        {
                            "term": term,
                            "reading": reading,
                            "sequence": sequence,
                            "definition": definition,
                            "sourceKey": item_id,
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                all_terms.add(term)
                stats["terms_emitted"] += 1
            all_link_targets.update(id_to_term.values())

    missing_index_items = sorted(
        item_id for item_id in set(aliases_by_item) | set(paths_by_item) if item_id not in id_to_term
    )
    report = {
        "source_jsonl": str(args.jsonl),
        "source_index_tree": str(args.index_tree),
        "output": str(args.output),
        "source_entries": len(rows),
        "index_nodes": len(tree),
        "unique_terms": len(all_terms),
        "stats": dict(stats),
        "missing_index_items": missing_index_items,
        "known_link_targets": len(all_link_targets),
    }
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
