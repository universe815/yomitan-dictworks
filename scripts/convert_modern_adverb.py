import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote


WHITESPACE_RE = re.compile(r"[\t\r\f\v ]+")
HEADWORD_RE = re.compile(r"^(.+?)\[([^\[\]]+)\]$")
INLINE_RE = re.compile(
    r"\*\*(?P<bold>.+?)\*\*"
    r"|__(?P<underline>.+?)__"
    r"|‾‾(?P<overline>.+?)‾‾"
    r"|(?P<ruby_base>[一-龯々〆ヵヶ〻]+|[^\s\[\]])"
    r"\[(?P<ruby_reading>[ぁ-ゖァ-ヺー]+)\]"
)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return WHITESPACE_RE.sub(" ", value.replace("\u200b", "")).strip()


def compact_content(parts: list[Any]) -> Any:
    values = [part for part in parts if part not in (None, "", [])]
    if not values:
        return ""
    return values[0] if len(values) == 1 else values


def parse_inline(value: str, stats: Counter[str]) -> Any:
    parts: list[Any] = []
    position = 0
    for match in INLINE_RE.finditer(value):
        if match.start() > position:
            parts.append(value[position : match.start()])
        if match.group("bold") is not None:
            parts.append(
                {
                    "tag": "span",
                    "data": {"madv": "emphasis"},
                    "content": parse_inline(match.group("bold"), stats),
                }
            )
            stats["emphasis_nodes"] += 1
        elif match.group("underline") is not None:
            parts.append(
                {
                    "tag": "span",
                    "data": {"madv": "contrast"},
                    "content": parse_inline(match.group("underline"), stats),
                }
            )
            stats["contrast_nodes"] += 1
        elif match.group("overline") is not None:
            parts.append(
                {
                    "tag": "span",
                    "data": {"madv": "overline"},
                    "content": parse_inline(match.group("overline"), stats),
                }
            )
            stats["overline_nodes"] += 1
        else:
            parts.append(
                {
                    "tag": "ruby",
                    "lang": "ja",
                    "content": [
                        match.group("ruby_base"),
                        {
                            "tag": "rt",
                            "lang": "ja",
                            "content": match.group("ruby_reading"),
                        },
                    ],
                }
            )
            stats["ruby_nodes"] += 1
        position = match.end()
    if position < len(value):
        parts.append(value[position:])
    return compact_content(parts)


def paragraphs(
    value: str,
    marker: str,
    stats: Counter[str],
    *,
    lang: str | None = None,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for raw_line in value.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        tokens = [marker]
        if line.startswith(("×", "?")):
            tokens.append("usage-warning")
        elif line.startswith(("→", "△")):
            tokens.append("comparison-line")
        node: dict[str, Any] = {
            "tag": "div",
            "data": {"madv": " ".join(tokens)},
            "content": parse_inline(line, stats),
        }
        if lang:
            node["lang"] = lang
        nodes.append(node)
        stats[f"{marker}_lines"] += 1
    return nodes


def parse_headword(entry: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    main = clean_text(entry.get("main_headword"))
    readings = [clean_text(value) for value in entry.get("readings", [])]
    kanjis = [clean_text(value) for value in entry.get("kanjis", [])]
    match = HEADWORD_RE.match(main)
    if match:
        if match.group(1) not in readings:
            readings.insert(0, match.group(1))
        if match.group(2) not in kanjis:
            kanjis.insert(0, match.group(2))
    elif main and main not in readings and main not in kanjis:
        readings.insert(0, main)
    readings = list(dict.fromkeys(value for value in readings if value))
    kanjis = list(dict.fromkeys(value for value in kanjis if value))
    reading = readings[0] if readings else (kanjis[0] if kanjis else main)
    return reading, readings, kanjis


def make_definition(
    entry: dict[str, Any],
    stats: Counter[str],
    known_terms: set[str],
) -> dict[str, Any]:
    reading, readings, kanjis = parse_headword(entry)
    heading_content: list[Any] = [
        {
            "tag": "span",
            "data": {"madv": "headword-reading"},
            "lang": "ja",
            "content": reading,
        }
    ]
    if kanjis:
        heading_content.append(
            {
                "tag": "span",
                "data": {"madv": "headword-kanji"},
                "lang": "ja",
                "content": "【" + "・".join(kanjis) + "】",
            }
        )

    content: list[Any] = [
        {
            "tag": "div",
            "data": {"madv": "headword"},
            "content": heading_content,
        }
    ]

    definition = clean_text(entry.get("definition"))
    if definition:
        content.append(
            {
                "tag": "div",
                "data": {"madv": "definition"},
                "lang": "zh",
                "content": parse_inline(definition, stats),
            }
        )
        stats["definitions"] += 1

    examples = entry.get("examples") or []
    if examples:
        example_nodes: list[Any] = []
        for example in examples:
            group = clean_text(example.get("group"))
            items = example.get("items") if group else [example]
            group_content: list[Any] = []
            if group:
                group_content.append(
                    {
                        "tag": "div",
                        "data": {"madv": "example-group-heading"},
                        "content": compact_content(
                            [
                                {
                                    "tag": "span",
                                    "data": {"madv": "group-number"},
                                    "content": group,
                                },
                                parse_inline(clean_text(example.get("header")), stats),
                            ]
                        ),
                    }
                )
                stats["example_groups"] += 1
            for item in items or []:
                item_content: list[Any] = []
                item_id = clean_text(item.get("id"))
                if item_id:
                    item_content.append(
                        {
                            "tag": "span",
                            "data": {"madv": "example-number"},
                            "content": item_id,
                        }
                    )
                japanese = clean_text(item.get("ja"))
                if japanese:
                    item_content.append(
                        {
                            "tag": "span",
                            "data": {"madv": "example-ja"},
                            "lang": "ja",
                            "content": parse_inline(japanese, stats),
                        }
                    )
                chinese = clean_text(item.get("cn"))
                if chinese:
                    item_content.append(
                        {
                            "tag": "div",
                            "data": {"madv": "example-zh"},
                            "lang": "zh",
                            "content": parse_inline(chinese, stats),
                        }
                    )
                group_content.append(
                    {
                        "tag": "div",
                        "data": {"madv": "example-item"},
                        "content": item_content,
                    }
                )
                stats["example_items"] += 1
            example_nodes.append(
                {
                    "tag": "div",
                    "data": {"madv": "example-group" if group else "example-group ungrouped"},
                    "content": group_content,
                }
            )
        content.append(
            {
                "tag": "div",
                "data": {"madv": "examples"},
                "content": example_nodes,
            }
        )

    for section_name, section_text in (entry.get("sections") or {}).items():
        marker = {
            "解析": "analysis",
            "比较": "comparison",
            "解说": "commentary",
        }.get(section_name, "section")
        section_content: list[Any] = [
            {
                "tag": "div",
                "data": {"madv": "section-title"},
                "lang": "zh",
                "content": f"【{section_name}】",
            }
        ]
        section_content.extend(paragraphs(section_text, "section-line", stats))
        content.append(
            {
                "tag": "div",
                "data": {"madv": f"section {marker}"},
                "content": section_content,
            }
        )
        stats[f"section:{section_name}"] += 1

    references = [clean_text(value) for value in entry.get("references", [])]
    references = list(dict.fromkeys(value for value in references if value))
    if references:
        reference_content: list[Any] = [
            {
                "tag": "span",
                "data": {"madv": "reference-label"},
                "lang": "zh",
                "content": "参见",
            }
        ]
        for index, target in enumerate(references):
            if index:
                reference_content.append("、")
            if target in known_terms:
                reference_content.append(
                    {
                        "tag": "a",
                        "href": f"?query={quote(target)}",
                        "lang": "ja",
                        "content": target,
                    }
                )
                stats["reference_links"] += 1
            else:
                reference_content.append(
                    {
                        "tag": "span",
                        "data": {"madv": "reference-unresolved"},
                        "lang": "ja",
                        "content": target,
                    }
                )
                stats["unresolved_reference_labels"] += 1
        content.append(
            {
                "tag": "div",
                "data": {"madv": "references"},
                "content": reference_content,
            }
        )

    page = clean_text(entry.get("page"))
    if page:
        content.append(
            {
                "tag": "div",
                "data": {"madv": "page"},
                "content": f"P. {page}",
            }
        )

    stats["articles"] += 1
    return {
        "type": "structured-content",
        "content": {
            "tag": "div",
            "data": {"madv": "entry"},
            "content": content,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the Modern Japanese Adverb Usage Dictionary JSON to Yomitan NDJSON."
    )
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--resources-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    entries = json.loads(args.json.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("source JSON must contain an array")

    stats: Counter[str] = Counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.resources_dir.mkdir(parents=True, exist_ok=True)

    prepared: list[tuple[dict[str, Any], str, list[str]]] = []
    all_terms: set[str] = set()
    for entry in entries:
        reading, readings, kanjis = parse_headword(entry)
        terms = list(dict.fromkeys([*kanjis, *readings]))
        prepared.append((entry, reading, terms))
        all_terms.update(terms)

    all_references: set[str] = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for sequence, (entry, reading, terms) in enumerate(prepared, start=1):
            if not terms:
                stats["empty_terms"] += 1
                continue
            definition = make_definition(entry, stats, all_terms)
            for term in terms:
                output.write(
                    json.dumps(
                        {
                            "term": term,
                            "reading": reading,
                            "sequence": sequence,
                            "definition": definition,
                            "sourceKey": entry.get("main_headword", term),
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                stats["terms_emitted"] += 1
            all_references.update(
                clean_text(value) for value in entry.get("references", []) if clean_text(value)
            )

    report = {
        "source_json": str(args.json),
        "output": str(args.output),
        "source_entries": len(entries),
        "unique_terms": len(all_terms),
        "stats": dict(stats),
        "unresolved_references": sorted(all_references - all_terms),
    }
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
