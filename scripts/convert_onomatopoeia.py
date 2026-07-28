import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

from lxml import html
from mdict_utils.base.readmdict import MDX


WHITESPACE_RE = re.compile(r"\s+")
MARKER_RE = re.compile(r"^[*◯○]+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return WHITESPACE_RE.sub(" ", value.replace("\u200b", "")).strip()


def node_text(node: Any) -> str:
    return clean_text("".join(node.itertext()))


def lookup_term(value: str) -> str:
    return MARKER_RE.sub("", clean_text(value))


def data(name: str) -> dict[str, str]:
    return {"onomato": name}


def text_span(content: str, name: str, lang: str | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {"tag": "span", "content": content, "data": data(name)}
    if lang:
        node["lang"] = lang
    return node


def example_node(example: Any) -> dict[str, Any]:
    ja_nodes = example.xpath("./ja")
    zh_nodes = example.xpath("./zh")
    content: list[Any] = []
    if ja_nodes:
        content.append(
            {
                "tag": "div",
                "content": node_text(ja_nodes[0]),
                "data": data("example-ja"),
                "lang": "ja",
            }
        )
    if zh_nodes:
        content.append(
            {
                "tag": "div",
                "content": node_text(zh_nodes[0]),
                "data": data("example-zh"),
                "lang": "zh",
            }
        )
    return {"tag": "div", "content": content, "data": data("example")}


def examples_node(container: Any) -> dict[str, Any] | None:
    examples = container.xpath("./examples/example")
    if not examples:
        return None
    return {
        "tag": "div",
        "content": [example_node(example) for example in examples],
        "data": data("examples"),
    }


def meaning_nodes(container: Any) -> list[dict[str, Any]]:
    return [
        {
            "tag": "div",
            "content": node_text(node),
            "data": data("meaning"),
            "lang": "zh",
        }
        for node in container.xpath("./meaning")
        if node_text(node)
    ]


def sense_node(sense: Any, position: int, total: int) -> dict[str, Any]:
    index = clean_text(sense.get("index"))
    if not index and total > 1:
        index = f"({position})"
    body: list[Any] = meaning_nodes(sense)
    examples = examples_node(sense)
    if examples:
        body.append(examples)
    content: list[Any] = []
    if index:
        content.append(text_span(index, "sense-number"))
    content.append({"tag": "div", "content": body, "data": data("sense-body")})
    return {"tag": "div", "content": content, "data": data("sense")}


def subentry_node(subentry: Any) -> tuple[str, dict[str, Any]]:
    headwords = subentry.xpath("./headword")
    display = node_text(headwords[0]) if headwords else ""
    term = lookup_term(display)
    body: list[Any] = meaning_nodes(subentry)
    examples = examples_node(subentry)
    if examples:
        body.append(examples)
    return term, {
        "tag": "div",
        "content": [
            {
                "tag": "div",
                "content": display.lstrip("◯○"),
                "data": data("subentry-headword"),
                "lang": "ja",
            },
            {"tag": "div", "content": body, "data": data("subentry-body")},
        ],
        "data": data("subentry"),
    }


def word_group_node(entry: Any) -> dict[str, Any] | None:
    groups = entry.xpath(
        ".//div[contains(concat(' ', normalize-space(@class), ' '), "
        "' word-group-links ')]"
    )
    if not groups:
        return None
    links: list[Any] = [text_span("词群", "group-label")]
    for anchor in groups[0].xpath("./a"):
        display = node_text(anchor)
        target = lookup_term((anchor.get("href") or "").removeprefix("entry://"))
        if not target:
            target = lookup_term(display)
        links.append(
            {
                "tag": "a",
                "href": f"?query={quote(target)}",
                "content": display,
                "lang": "ja",
            }
        )
    return {"tag": "div", "content": links, "data": data("word-group")}


def main_definition(
    term: str,
    display: str,
    category: str,
    entry: Any,
    subentries: list[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    head_content: list[Any] = [
        {
            "tag": "span",
            "content": term,
            "data": data("headword"),
            "lang": "ja",
        }
    ]
    if display.startswith("*"):
        head_content.append(text_span("关联变体", "variant-badge", "zh"))
    head_content.append(text_span(category, "category", "zh"))

    senses = entry.xpath("./senses/sense")
    content: list[Any] = [
        {"tag": "div", "content": head_content, "data": data("header")},
        {
            "tag": "div",
            "content": [
                sense_node(sense, index, len(senses))
                for index, sense in enumerate(senses, start=1)
            ],
            "data": data("senses"),
        },
    ]
    if subentries:
        content.append(
            {
                "tag": "div",
                "content": [
                    text_span("相关词形", "subentries-label", "zh"),
                    *[node for _, node in subentries],
                ],
                "data": data("subentries"),
            }
        )
    word_group = word_group_node(entry)
    if word_group:
        content.append(word_group)
    return {
        "type": "structured-content",
        "content": {"tag": "div", "content": content, "data": data("entry")},
    }


def subentry_definition(
    term: str, parent: str, category: str, node: dict[str, Any]
) -> dict[str, Any]:
    return {
        "type": "structured-content",
        "content": {
            "tag": "div",
            "content": [
                {
                    "tag": "div",
                    "content": [
                        {
                            "tag": "span",
                            "content": term,
                            "data": data("headword"),
                            "lang": "ja",
                        },
                        text_span("相关词形", "variant-badge", "zh"),
                        text_span(category, "category", "zh"),
                    ],
                    "data": data("header"),
                },
                node,
                {
                    "tag": "div",
                    "content": [
                        "收录于 ",
                        {
                            "tag": "a",
                            "href": f"?query={quote(parent)}",
                            "content": parent,
                            "lang": "ja",
                        },
                    ],
                    "data": data("parent-link"),
                },
            ],
            "data": data("entry"),
        },
    }


def normalize_category(value: str) -> str:
    normalized = clean_text(value).strip("[]")
    return normalized.replace("拟声拟-态", "拟声拟态") or "未分类"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mdx", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--resources-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mdx = MDX(str(args.mdx), "", False, None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.resources_dir.mkdir(parents=True, exist_ok=True)

    stats: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    sequence = 0
    for key_bytes, value_bytes in mdx.items():
        key = clean_text(key_bytes.decode(mdx._encoding, errors="replace").strip("\x00"))
        source = value_bytes.decode(mdx._encoding, errors="replace").strip("\x00\r\n ")
        stats["records_seen"] += 1
        if source.startswith("@@@LINK="):
            stats["redirect_records"] += 1
            continue
        root = html.fragment_fromstring(source, create_parent="div")
        entries = root.xpath("./entry")
        if not entries:
            stats["missing_entry"] += 1
            continue
        entry = entries[0]
        headwords = entry.xpath("./headword")
        display = node_text(headwords[0]) if headwords else key
        term = key or lookup_term(display)
        category_nodes = entry.xpath("./category")
        category = normalize_category(node_text(category_nodes[0]) if category_nodes else "")
        if "拟声拟-态" in source:
            stats["category_typos_fixed"] += 1

        parsed_subentries = [
            subentry_node(node) for node in entry.xpath("./subentries/subentry")
        ]
        parsed_subentries = [(name, node) for name, node in parsed_subentries if name]
        sequence += 1
        records.append(
            {
                "term": term,
                "reading": term,
                "sequence": sequence,
                "definition": main_definition(
                    term, display, category, entry, parsed_subentries
                ),
                "sourceKey": key,
            }
        )
        stats["main_terms"] += 1
        stats["senses"] += len(entry.xpath("./senses/sense"))
        stats["examples"] += len(entry.xpath(".//example"))
        if display.startswith("*"):
            stats["variant_terms"] += 1
        if word_group_node(entry):
            stats["word_groups"] += 1

        for subterm, node in parsed_subentries:
            sequence += 1
            records.append(
                {
                    "term": subterm,
                    "reading": subterm,
                    "sequence": sequence,
                    "definition": subentry_definition(
                        subterm, term, category, node
                    ),
                    "sourceKey": key,
                }
            )
            stats["searchable_subentries"] += 1

    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            output.write("\n")

    report = {
        "source_mdx": str(args.mdx),
        "output": str(args.output),
        "stats": dict(stats),
        "terms_emitted": len(records),
        "resources": 0,
    }
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
