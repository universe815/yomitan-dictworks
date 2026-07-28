import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from lxml import html
from mdict_utils.base.readmdict import MDX


WHITESPACE_RE = re.compile(r'\s+')
SKIP_TAGS = {'script', 'style', 'link', 'meta'}
BLOCK_TAGS = {'html', 'body', 'oaldpe', 'div', 'aside', 'section', 'article', 'p',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
TABLE_TAGS = {'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th'}
LIST_TAGS = {'ol', 'ul', 'li'}
SEMANTIC_CLASSES = {
    'entry', 'webtop', 'headword', 'pos', 'phonetics', 'phon', 'grammar',
    'labels', 'def', 'deft', 'x', 'xt', 'unx', 'unxt', 'cf', 'shcut',
    'idioms_heading', 'idm', 'phrasalverb', 'box_title', 'topic_name',
    'topic_cefr', 'xh', 'gloss', 'examples', 'sense', 'collapse', 'unbox',
    'patterns', 'verb_forms_table', 'prefix', 'iteration', 'xrefs', 'topic-g',
}
CHINESE_TAGS = {'chn', 'deft', 'xt', 'unxt', 'undt', 'ubx', 'labelx',
                'unboxx', 'shcut', 'oald', 'ai', 'leon'}
ITALIC_CLASSES = {'ei'}
BOLD_CLASSES = {'eb'}


def normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = WHITESPACE_RE.sub(' ', value.replace('\u200b', '')).strip()
    return normalized or None


def content_value(parts: list[Any]) -> Any:
    compact = [part for part in parts if part not in (None, '', [])]
    if not compact:
        return None
    return compact[0] if len(compact) == 1 else compact


def element_content(element: Any, stats: Counter[str], include_images: bool,
                    referenced_images: set[str]) -> Any:
    parts: list[Any] = []
    text = normalize_text(element.text)
    if text:
        parts.append(text)
    for child in element:
        converted = convert_element(child, stats, include_images, referenced_images)
        if converted is not None:
            parts.append(converted)
        tail = normalize_text(child.tail)
        if tail:
            parts.append(tail)
    return content_value(parts)


def internal_href(source_href: str) -> str | None:
    if not source_href.lower().startswith('entry://'):
        return None
    target = unquote(source_href[8:].split('#', 1)[0]).strip()
    if not target or target.startswith('@'):
        return None
    return f'?query={quote(target)}'


def convert_element(element: Any, stats: Counter[str], include_images: bool,
                    referenced_images: set[str]) -> Any:
    tag = str(element.tag).lower() if isinstance(element.tag, str) else ''
    classes = set((element.get('class') or '').split())

    if tag in SKIP_TAGS or 'pseudo-footer' in classes or 'oaldpe-nav' in classes:
        return None
    if tag == 'a' and ('sound' in classes or (element.get('href') or '').startswith('sound://')):
        stats['audio_links_removed'] += 1
        return None
    if tag == 'img':
        alt = normalize_text(element.get('alt') or element.get('title'))
        resource = unquote(element.get('data-src') or element.get('src') or '')
        resource = resource.replace('\\', '/').rsplit('/', 1)[-1]
        if include_images and resource.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            stats['images_preserved'] += 1
            referenced_images.add(resource)
            node: dict[str, Any] = {
                'tag': 'img',
                'path': f'img/oald/{resource}',
                'background': True,
            }
            if alt:
                node['alt'] = alt
                node['title'] = alt
            if classes:
                node['data'] = {'oald': ' '.join(sorted(classes))}
            if 'fullsize' in classes:
                node['collapsible'] = True
                node['collapsed'] = True
            return node
        stats['images_replaced'] += 1
        return {
            'tag': 'span',
            'content': f'〔图片：{alt}〕' if alt else '〔图片〕',
            'data': {'oald': 'image-placeholder'},
        }

    content = element_content(element, stats, include_images, referenced_images)
    if content is None:
        return None

    data_tokens = sorted(classes & SEMANTIC_CLASSES)
    if tag in CHINESE_TAGS:
        data_tokens.append('zh')
        if tag in {'deft', 'xt', 'unxt', 'undt', 'ubx'}:
            data_tokens.append(tag)
    data = {'oald': ' '.join(sorted(set(data_tokens)))} if data_tokens else None

    if tag == 'br':
        return {'tag': 'br'}
    if tag in TABLE_TAGS:
        node: dict[str, Any] = {'tag': tag, 'content': content}
        if tag in {'td', 'th'}:
            if element.get('colspan', '').isdigit():
                node['colSpan'] = int(element.get('colspan'))
            if element.get('rowspan', '').isdigit():
                node['rowSpan'] = int(element.get('rowspan'))
        if data:
            node['data'] = data
        return node
    if tag in LIST_TAGS:
        node = {'tag': tag, 'content': content}
        if data:
            node['data'] = data
        return node
    if tag == 'a':
        href = element.get('href') or ''
        converted_href = internal_href(href)
        if converted_href:
            return {'tag': 'a', 'content': content, 'href': converted_href}
        if href.startswith(('http://', 'https://')):
            return {'tag': 'a', 'content': content, 'href': href}

    node_tag = 'div' if tag in BLOCK_TAGS else 'span'
    node = {'tag': node_tag, 'content': content}
    if data:
        node['data'] = data
    if tag in {'b', 'strong'} or classes & BOLD_CLASSES:
        node['style'] = {'fontWeight': 'bold'}
    elif tag in {'i', 'em'} or classes & ITALIC_CLASSES:
        node['style'] = {'fontStyle': 'italic'}
    return node


def meaningful_entry(key: str, source_html: str) -> bool:
    return (
        bool(key.strip())
        and not key.startswith('@')
        and ('class="sense"' in source_html or "class='sense'" in source_html)
    )


def resolve_redirect(target: str, direct_sequences: dict[str, int],
                     redirects: dict[str, str]) -> tuple[str, int] | None:
    visited: set[str] = set()
    current = target
    for _ in range(32):
        if current in direct_sequences:
            return current, direct_sequences[current]
        if current in visited or current not in redirects:
            return None
        visited.add(current)
        current = redirects[current]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description='Convert OALD MDX into Yomitan-ready NDJSON.')
    parser.add_argument('--mdx', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--limit-direct', type=int)
    parser.add_argument('--include-images', action='store_true')
    args = parser.parse_args()

    mdx = MDX(str(args.mdx), '', False, None)
    stats: Counter[str] = Counter()
    direct_sequences: dict[str, int] = {}
    redirects: dict[str, str] = {}
    referenced_images: set[str] = set()
    next_sequence = 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='\n') as output:
        for key_bytes, value_bytes in mdx.items():
            stats['records_seen'] += 1
            key = key_bytes.decode(mdx._encoding, errors='replace').strip('\x00\r\n ')
            source = value_bytes.decode(mdx._encoding, errors='replace').strip('\x00\r\n ')
            if source.startswith('@@@LINK='):
                redirects.setdefault(key, source.partition('=')[2].strip())
                stats['redirects_seen'] += 1
                continue
            if not meaningful_entry(key, source):
                stats['non_dictionary_html_skipped'] += 1
                continue
            if args.limit_direct is not None and stats['direct_written'] >= args.limit_direct:
                continue
            try:
                document = html.fromstring(source)
                structured = convert_element(
                    document,
                    stats,
                    args.include_images,
                    referenced_images,
                )
            except Exception:
                stats['html_parse_errors'] += 1
                continue
            if structured is None:
                stats['empty_after_conversion'] += 1
                continue

            sequence = direct_sequences.setdefault(key, next_sequence)
            if sequence == next_sequence:
                next_sequence += 1
            record = {
                'term': key,
                'sequence': sequence,
                'definition': {'type': 'structured-content', 'content': structured},
            }
            output.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
            stats['direct_written'] += 1

        if args.limit_direct is None:
            for alias, target in redirects.items():
                if not alias or alias.startswith('@') or alias in direct_sequences:
                    stats['redirects_skipped'] += 1
                    continue
                resolved = resolve_redirect(target, direct_sequences, redirects)
                if resolved is None:
                    stats['redirects_unresolved'] += 1
                    continue
                final_target, sequence = resolved
                record = {
                    'term': alias,
                    'sequence': sequence,
                    'redirect': final_target,
                }
                output.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
                stats['redirects_written'] += 1

    report = {
        'source': str(args.mdx),
        'output': str(args.output),
        'stats': dict(stats),
        'unique_direct_terms': len(direct_sequences),
        'unique_redirect_keys': len(redirects),
        'unique_images_referenced': len(referenced_images),
        'images_referenced': sorted(referenced_images),
        'output_bytes': args.output.stat().st_size,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
