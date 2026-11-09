import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from lxml import html
from mdict_utils.base.readmdict import MDX


WHITESPACE_RE = re.compile(r"\s+")
BRACKETED_TERM_RE = re.compile(r"^(.+?)【(.+)】$")
KANJI_RE = re.compile(r"[一-龯々〆ヵヶ]")
BLOCK_TAGS = {"html", "body", "div", "section", "article", "p", "h1", "h2", "h3"}
SUPPORTED_CONTAINER_TAGS = {
    "ruby", "rt", "table", "thead", "tbody", "tfoot", "tr", "td", "th",
    "ol", "ul", "li", "details", "summary",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return WHITESPACE_RE.sub(" ", value.replace("\u200b", "")).strip()


def compact_content(parts: list[Any]) -> Any:
    values = [part for part in parts if part not in (None, "", [])]
    if not values:
        return None
    return values[0] if len(values) == 1 else values


def marker_data(element: Any) -> dict[str, str] | None:
    classes = [value.replace("_", "-") for value in (element.get("class") or "").split()]
    classes = sorted(set(classes))
    return {"kqcol": " ".join(classes)} if classes else None


def element_content(element: Any, id_to_term: dict[str, str], stats: Counter[str]) -> Any:
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


def convert_element(element: Any, id_to_term: dict[str, str], stats: Counter[str]) -> Any:
    tag = str(element.tag).lower() if isinstance(element.tag, str) else ""
    if tag in {"link", "script", "style", "meta"}:
        return None
    if tag == "br":
        return {"tag": "br"}
    if tag == "hr":
        return {"tag": "div", "content": "", "data": {"kqcol": "rule"}}

    content = element_content(element, id_to_term, stats)
    if content is None:
        return None
    data = marker_data(element)

    if tag == "a":
        href = unquote(element.get("href") or "")
        if href.lower().startswith("entry://"):
            source_target = href[8:]
            target = id_to_term.get(source_target, source_target)
            stats["internal_links"] += 1
            return {
                "tag": "a",
                "href": f"?query={quote(target)}",
                "content": content,
                "lang": "ja",
            }
        return content

    if tag == "rb":
        node: dict[str, Any] = {"tag": "span", "content": content}
    elif tag in SUPPORTED_CONTAINER_TAGS:
        node = {"tag": tag, "content": content}
        if tag == "details" and element.get("open") is not None:
            node["open"] = True
        if tag in {"td", "th"}:
            if (element.get("colspan") or "").isdigit():
                node["colSpan"] = int(element.get("colspan"))
            if (element.get("rowspan") or "").isdigit():
                node["rowSpan"] = int(element.get("rowspan"))
    else:
        node = {"tag": "div" if tag in BLOCK_TAGS else "span", "content": content}

    if data:
        node["data"] = data
    if tag in {"ruby", "rt", "rb"}:
        node["lang"] = "ja"
    if tag in {"b", "strong"}:
        node["style"] = {"fontWeight": "bold"}
    elif tag in {"i", "em"}:
        node["style"] = {"fontStyle": "italic"}
    elif tag == "sub":
        node["style"] = {"fontSize": "65%", "verticalAlign": "sub"}
    elif tag == "sup":
        node["style"] = {"fontSize": "65%", "verticalAlign": "super"}
    return node


def class_nodes(root: Any, class_name: str) -> list[Any]:
    return root.xpath(
        ".//*[contains(concat(' ', normalize-space(@class), ' '), $needle)]",
        needle=f" {class_name} ",
    )


def heading(root: Any, fallback: str) -> tuple[str, str]:
    kana_nodes = class_nodes(root, "headword_kana")
    hyoki_nodes = class_nodes(root, "headword_hyoki")
    kana = clean_text("".join(kana_nodes[0].itertext())) if kana_nodes else fallback
    hyoki = clean_text("".join(hyoki_nodes[0].itertext())).strip("【】") if hyoki_nodes else ""
    return kana, hyoki


def resolve_redirect(value: str, redirects: dict[str, str]) -> str:
    current = value
    seen: set[str] = set()
    while current in redirects and current not in seen:
        seen.add(current)
        current = redirects[current]
    return current


def searchable_aliases(target: str, kana: str, aliases: list[str]) -> list[str]:
    values: list[str] = []
    for value in [kana, *aliases]:
        value = clean_text(value)
        if not value or value == target or value.startswith("#"):
            continue
        if value.startswith("kqcolex2_") or BRACKETED_TERM_RE.match(value):
            continue
        if value not in values:
            values.append(value)
    return values


def canonical_term(kana: str, aliases: list[str], fallback: str) -> str:
    for value in aliases:
        if KANJI_RE.search(value):
            return value
    return aliases[0] if aliases else (kana or fallback)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Kenkyusha Japanese Colloquial Expressions 2nd MDX to Yomitan NDJSON."
    )
    parser.add_argument("--mdx", type=Path, required=True)
    parser.add_argument("--cover", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--resources-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mdx = MDX(str(args.mdx), "", False, None)
    stats: Counter[str] = Counter()
    redirects: dict[str, str] = {}
    direct_records: list[tuple[str, str]] = []

    for key_bytes, value_bytes in mdx.items():
        key = clean_text(key_bytes.decode(mdx._encoding, errors="replace").strip("\x00"))
        source = value_bytes.decode(mdx._encoding, errors="replace").strip("\x00\r\n ")
        stats["records_seen"] += 1
        if source.startswith("@@@LINK="):
            redirects[key] = clean_text(source.partition("=")[2])
            stats["redirect_records"] += 1
        else:
            direct_records.append((key, source))

    aliases_by_target: dict[str, list[str]] = defaultdict(list)
    for alias in redirects:
        resolved = resolve_redirect(alias, redirects)
        if alias not in aliases_by_target[resolved]:
            aliases_by_target[resolved].append(alias)

    parsed: list[dict[str, Any]] = []
    id_to_term: dict[str, str] = {}
    for key, source in direct_records:
        root = html.fragment_fromstring(source, create_parent="div")
        entries = class_nodes(root, "dic_item")
        if entries:
            item = entries[0]
            target = item.get("id") or key
            kana, hyoki = heading(item, key)
            terms = searchable_aliases(target, kana, aliases_by_target.get(target, []))
            primary = canonical_term(kana, terms, hyoki or key)
            parsed.append({"key": key, "target": target, "root": item, "kana": kana, "terms": terms, "primary": primary})
            id_to_term[target] = primary
            id_to_term[key] = primary
            stats["articles"] += 1
        else:
            title_nodes = class_nodes(root, "midashi_info_appendix")
            title = clean_text("".join(title_nodes[0].itertext())) if title_nodes else key
            if key == "kqcolex2_index":
                title = "凡例・付録"
            parsed.append({"key": key, "target": key, "root": root, "kana": title, "terms": [title], "primary": title, "appendix": True})
            id_to_term[key] = title
            stats["appendices"] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.resources_dir.mkdir(parents=True, exist_ok=True)
    if args.cover:
        shutil.copyfile(args.cover, args.resources_dir / "cover.png")
        stats["cover_resources"] = 1

    emitted_terms: set[tuple[str, int]] = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        sequence = 0
        for record in parsed:
            sequence += 1
            try:
                content = convert_element(record["root"], id_to_term, stats)
            except Exception as error:
                stats["parse_errors"] += 1
                print(f"WARN parse failed for {record['key']!r}: {error}", flush=True)
                continue
            if content is None:
                stats["empty_articles"] += 1
                continue
            if record.get("appendix") and record["key"] == "kqcolex2_copyright" and args.cover:
                content = {
                    "tag": "div",
                    "data": {"kqcol": "entry appendix-entry"},
                    "lang": "ja",
                    "content": [
                        {
                            "tag": "img",
                            "path": "img/kqcol/cover.png",
                            "width": 8,
                            "sizeUnits": "em",
                            "verticalAlign": "middle",
                            "alt": "研究社 日本語口語表現辞典 第2版",
                            "title": "研究社 日本語口語表現辞典 第2版",
                        },
                        content,
                    ],
                }
            elif isinstance(content, dict):
                content["lang"] = "ja"

            definition = {"type": "structured-content", "content": content}
            for term in record["terms"]:
                marker = (term, sequence)
                if marker in emitted_terms:
                    continue
                emitted_terms.add(marker)
                output.write(
                    json.dumps(
                        {
                            "term": term,
                            "reading": record["kana"],
                            "sequence": sequence,
                            "definition": definition,
                            "sourceKey": record["key"],
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                stats["terms_emitted"] += 1

    report = {
        "source_mdx": str(args.mdx),
        "output": str(args.output),
        "stats": dict(stats),
        "direct_records": len(direct_records),
        "redirect_records": len(redirects),
        "unresolved_redirects": sorted(
            alias for alias in redirects if resolve_redirect(alias, redirects) not in id_to_term
        ),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
