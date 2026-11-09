import argparse
import html as html_module
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mdict_utils.base.readmdict import MDX


WHITESPACE_RE = re.compile(r"\s+")
BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
WRAPPER_RE = re.compile(r"`[12]`")
BRACKETED_TERM_RE = re.compile(r"^(.+?)【(.+)】$")
SECTION_RE = re.compile(r"^《(.+?)》$")
KANJI_RE = re.compile(r"[一-龯々〆ヵヶ〻]")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html_module.unescape(TAG_RE.sub("", value))
    return WHITESPACE_RE.sub(" ", value.replace("\u200b", "")).strip()


def resolve_redirect(value: str, redirects: dict[str, str]) -> str:
    current = value
    seen: set[str] = set()
    while current in redirects and current not in seen:
        seen.add(current)
        current = redirects[current]
    return current


def split_source(source: str) -> list[str]:
    source = WRAPPER_RE.sub("", source)
    return [clean_text(part) for part in BREAK_RE.split(source)]


def split_orthographies(value: str) -> list[str]:
    if not KANJI_RE.search(value):
        return []
    values = re.split(r"[・／/]", value)
    return [clean_text(item) for item in values if clean_text(item)]


def parse_heading(key: str) -> tuple[str, list[str]]:
    match = BRACKETED_TERM_RE.match(key)
    if not match:
        return clean_text(key), []
    reading = clean_text(match.group(1))
    orthographies = split_orthographies(clean_text(match.group(2)))
    return reading, orthographies


def searchable_terms(
    key: str,
    redirects: dict[str, str],
    aliases_by_target: dict[str, list[str]],
) -> tuple[str, list[str]]:
    reading, orthographies = parse_heading(key)
    values = [*orthographies, reading]
    for alias in aliases_by_target.get(key, []):
        alias = clean_text(alias)
        if not alias or BRACKETED_TERM_RE.match(alias):
            continue
        if alias.startswith("#") or "［英語では" in alias:
            continue
        values.append(alias)
    terms = list(dict.fromkeys(value for value in values if value))
    return reading or (terms[0] if terms else key), terms


def heading_node(key: str, reading: str) -> dict[str, Any]:
    _, orthographies = parse_heading(key)
    content: list[Any] = [
        {
            "tag": "span",
            "data": {"kexpr": "headword-reading"},
            "lang": "ja",
            "content": reading,
        }
    ]
    if orthographies:
        content.append(
            {
                "tag": "span",
                "data": {"kexpr": "headword-kanji"},
                "lang": "ja",
                "content": "【" + "・".join(orthographies) + "】",
            }
        )
    return {
        "tag": "div",
        "data": {"kexpr": "headword"},
        "content": content,
    }


def line_node(line: str, marker: str) -> dict[str, Any]:
    content: list[Any] = []
    number = re.match(r"^(［[^］]+］|・)", line)
    if number:
        content.append(
            {
                "tag": "span",
                "data": {"kexpr": "line-marker"},
                "content": number.group(1),
            }
        )
        line = clean_text(line[number.end() :])
    if line:
        content.append(
            {
                "tag": "span",
                "data": {"kexpr": "line-text"},
                "lang": "ja",
                "content": line,
            }
        )
    return {
        "tag": "div",
        "data": {"kexpr": marker},
        "content": content,
    }


def make_definition(key: str, source: str, stats: Counter[str]) -> dict[str, Any]:
    reading, _ = parse_heading(key)
    lines = split_source(source)
    while lines and not lines[0]:
        lines.pop(0)
    if lines and lines[0].startswith("■"):
        lines.pop(0)

    content: list[Any] = [heading_node(key, reading)]
    current_title = "搭配"
    current_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_lines
        values = [value for value in current_lines if value]
        if not values:
            current_lines = []
            return
        section_marker = {
            "搭配": "patterns",
            "例 文": "examples",
            "例文": "examples",
            "慣用句": "idioms",
            "複合語": "compounds",
            "名 詞": "nouns",
            "名詞": "nouns",
        }.get(current_title, "section")
        nodes: list[Any] = [
            {
                "tag": "div",
                "data": {"kexpr": "section-title"},
                "lang": "ja",
                "content": f"《{current_title}》" if current_title != "搭配" else "搭配",
            }
        ]
        nodes.extend(line_node(value, "section-line") for value in values)
        content.append(
            {
                "tag": "div",
                "data": {"kexpr": f"section {section_marker}"},
                "content": nodes,
            }
        )
        stats[f"section:{section_marker}"] += 1
        stats["content_lines"] += len(values)
        current_lines = []

    for line in lines:
        match = SECTION_RE.match(line.replace("\u3000", " "))
        if match:
            flush_section()
            current_title = clean_text(match.group(1))
        elif line:
            current_lines.append(line)
    flush_section()

    stats["articles"] += 1
    return {
        "type": "structured-content",
        "content": {
            "tag": "div",
            "data": {"kexpr": "entry"},
            "content": content,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Kenkyusha Japanese Expression Usage Dictionary MDX to Yomitan NDJSON."
    )
    parser.add_argument("--mdx", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--resources-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
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
    unresolved_redirects: list[str] = []
    direct_keys = {key for key, _ in direct_records}
    for alias in redirects:
        target = resolve_redirect(alias, redirects)
        if target not in direct_keys:
            unresolved_redirects.append(alias)
        elif alias not in aliases_by_target[target]:
            aliases_by_target[target].append(alias)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.resources_dir.mkdir(parents=True, exist_ok=True)

    emitted: set[tuple[str, int]] = set()
    all_terms: set[str] = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        for sequence, (key, source) in enumerate(direct_records, start=1):
            reading, terms = searchable_terms(key, redirects, aliases_by_target)
            if not terms:
                stats["empty_terms"] += 1
                continue
            definition = make_definition(key, source, stats)
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
                            "sourceKey": key,
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                all_terms.add(term)
                stats["terms_emitted"] += 1

    report = {
        "source_mdx": str(args.mdx),
        "output": str(args.output),
        "direct_records": len(direct_records),
        "redirect_records": len(redirects),
        "unique_terms": len(all_terms),
        "stats": dict(stats),
        "unresolved_redirects": sorted(unresolved_redirects),
    }
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
