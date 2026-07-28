import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, unquote

from lxml import html
from mdict_utils.base.readmdict import MDD, MDX


GAIJI = {
    'F0A3': '仿', 'F0BB': '噛', 'F0BD': '嚢', 'F0C6': '壒',
    'F0D1': '剥', 'F0E1': '掻', 'F0E2': '掴', 'F0E5': '欹',
    'F0F2': '栱', 'F0FA': '楤', 'F144': '燗', 'F15E': '烤',
    'F178': '瓚', 'F182': '癤', 'F183': '癭', 'F18D': '〔和製英語〕', 'F199': '箪',
    'F1AF': '芩', 'F1BD': '蒴', 'F1CA': '虬', 'F1D0': '蝉',
    'F1D4': '蠟', 'F1D9': '襀', 'F1E3': '軀', 'F1F0': '醬',
    'F1F3': '鈸', 'F246': '頫', 'F247': '頬', 'F24B': '顛',
    'F263': '鹼', 'F266': '麹', 'F26D': '窶', 'F27E': '婕',
    'F280': '孒', 'F2B6': '篊', 'F2D5': '蜱', 'F2E0': '豇',
    'F34B': '鰱', 'F34C': '鰶', 'F35D': '鷟', 'F368': '痩',
    'F36F': '扈', 'F371': '湮', 'F379': '逢', 'F38B': '麺',
    'F3A2': '駢', 'F3E9': '芍', 'F3EB': '硼', 'F3ED': '鱈',
    'F3F1': '錆', 'F446': '豹', 'F465': '繋', 'F467': '捩',
    'F46F': '繭', 'F470': '菟', 'F47D': '蝙', 'F493': '溯',
    'F495': '歎',
}

WHITESPACE_RE = re.compile(r'\s+')
GAIJI_RE = re.compile(r'\[GAIJI:([0-9A-Fa-f]+)(?:\s*)\]?')
GAIJI_LINK_RE = re.compile(
    r'<a(?P<before>[^>]*?)href="entry://\[GAIJI:(?P<code>[0-9A-Fa-f]+)"(?P<after>[^>]*)>'
    r'\[GAIJI:(?P=code)</a>(?P<content>.*?)\]',
    re.DOTALL | re.IGNORECASE,
)
BRACKET_KEY_RE = re.compile(r'^(.*?)【(.*)】$')
PAREN_KEY_RE = re.compile(r'^(.*?)\((.*)\)$')
BLOCK_TAGS = {'html', 'body', 'div', 'section', 'article', 'p', 'h1', 'h2', 'h3'}
TABLE_TAGS = {'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th'}
LIST_TAGS = {'ol', 'ul', 'li'}
SUPPORTED_CONTAINER_TAGS = {'ruby', 'rt', 'table', 'thead', 'tbody', 'tfoot', 'tr',
                            'td', 'th', 'ol', 'ul', 'li', 'details', 'summary'}


def replace_gaiji(value: str) -> str:
    def link_replacement(match: re.Match[str]) -> str:
        code = match.group('code').upper()
        character = GAIJI.get(code, f'〔外字{code}〕')
        content = match.group('content')
        without_reading = re.sub(r'<rt\b[^>]*>.*?</rt>', '', content, flags=re.DOTALL | re.IGNORECASE)
        plain = clean_text(re.sub(r'<[^>]+>', '', without_reading)) or ''
        target = f'{character}{plain}'
        return (
            f'<a{match.group("before")}href="entry://{target}"{match.group("after")}>'
            f'{character}{content}</a>'
        )

    value = GAIJI_LINK_RE.sub(link_replacement, value)

    def replacement(match: re.Match[str]) -> str:
        code = match.group(1).upper()
        return GAIJI.get(code, f'〔外字{code}〕')
    return GAIJI_RE.sub(replacement, value)


def split_chinese_marker(content: Any) -> Any:
    if isinstance(content, str):
        if '颐' not in content:
            return content
        before, _, after = content.partition('颐')
        values: list[Any] = []
        if before:
            values.append(before)
        values.append({'tag': 'br'})
        if after:
            values.append({
                'tag': 'span',
                'data': {'xsjrh': 'xsjrh-c'},
                'lang': 'zh',
                'content': after,
            })
        return compact_content(values)
    if not isinstance(content, list):
        return content
    for index, value in enumerate(content):
        if isinstance(value, str) and '颐' in value:
            before, _, after = value.partition('颐')
            chinese_parts: list[Any] = []
            if after:
                chinese_parts.append(after)
            chinese_parts.extend(content[index + 1:])
            result = content[:index]
            if before:
                result.append(before)
            result.extend([
                {'tag': 'br'},
                {
                    'tag': 'span',
                    'data': {'xsjrh': 'xsjrh-c'},
                    'lang': 'zh',
                    'content': compact_content(chinese_parts),
                },
            ])
            return compact_content(result)
    return content


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = WHITESPACE_RE.sub(' ', value.replace('\u200b', '')).strip()
    return normalized or None


def clean_reading(value: str) -> str:
    return re.sub(r'[・･·\s]', '', value).strip('【】')


def resource_path(value: str) -> str | None:
    normalized = unquote(value).replace('\\', '/').lstrip('/')
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or '..' in path.parts:
        return None
    return path.as_posix()


def query_target(value: str) -> str:
    target = replace_gaiji(unquote(value)).strip()
    bracket = BRACKET_KEY_RE.match(target)
    if bracket:
        variants = split_terms(bracket.group(2))
        return variants[0] if variants else bracket.group(1)
    paren = PAREN_KEY_RE.match(target)
    if paren and paren.group(2):
        return paren.group(2)
    return target


def compact_content(parts: list[Any]) -> Any:
    values = [part for part in parts if part not in (None, '', [])]
    if not values:
        return None
    return values[0] if len(values) == 1 else values


def element_content(element: Any, stats: Counter[str], images: set[str]) -> Any:
    parts: list[Any] = []
    text = clean_text(element.text)
    if text:
        parts.append(text)
    for child in element:
        converted = convert_element(child, stats, images)
        if converted is not None:
            parts.append(converted)
        tail = clean_text(child.tail)
        if tail:
            parts.append(tail)
    return compact_content(parts)


def class_data(element: Any) -> dict[str, str] | None:
    classes = sorted(set((element.get('class') or '').split()))
    return {'xsjrh': ' '.join(classes)} if classes else None


def convert_element(element: Any, stats: Counter[str], images: set[str]) -> Any:
    tag = str(element.tag).lower() if isinstance(element.tag, str) else ''
    if tag in {'link', 'script', 'style', 'meta'}:
        return None
    if tag == 'img':
        relative = resource_path(element.get('src') or element.get('data-src') or '')
        if not relative:
            stats['invalid_images'] += 1
            return '〔图片资源路径无效〕'
        images.add(relative)
        stats['image_nodes'] += 1
        classes = set((element.get('class') or '').split())
        node: dict[str, Any] = {
            'tag': 'img',
            'path': f'img/xsjrh/{relative}',
            'background': True,
        }
        data = class_data(element)
        if data:
            node['data'] = data
        if 'xsjrh-png' in classes or relative.lower().startswith('gaiji/'):
            node.update({'height': 1.2, 'sizeUnits': 'em', 'verticalAlign': 'middle'})
        else:
            node.update({'collapsible': True, 'collapsed': False})
        alt = clean_text(element.get('alt') or element.get('title'))
        if alt:
            node['alt'] = alt
            node['title'] = alt
        return node

    content = element_content(element, stats, images)
    if tag == 'br':
        return {'tag': 'br'}
    if content is None:
        return None

    data = class_data(element)
    lang = None
    classes = set((element.get('class') or '').split())
    if 'xsjrh-c' in classes:
        lang = 'zh'
    elif 'xsjrh-j' in classes or tag in {'ruby', 'rt', 'rb'}:
        lang = 'ja'
        content = split_chinese_marker(content)

    if tag == 'a':
        href = element.get('href') or ''
        if href.lower().startswith('entry://'):
            target = query_target(href[8:])
            node = {'tag': 'a', 'href': f'?query={quote(target)}', 'content': content}
            if lang:
                node['lang'] = lang
            return node
        return content

    if tag == 'rb':
        node = {'tag': 'span', 'content': content}
    elif tag in SUPPORTED_CONTAINER_TAGS:
        node = {'tag': tag, 'content': content}
        if tag == 'details' and element.get('open') is not None:
            node['open'] = True
        if tag in {'td', 'th'}:
            if (element.get('colspan') or '').isdigit():
                node['colSpan'] = int(element.get('colspan'))
            if (element.get('rowspan') or '').isdigit():
                node['rowSpan'] = int(element.get('rowspan'))
    else:
        # Chinese glosses are block-level in the source dictionary. Preserve that
        # structurally so the Japanese definition and Chinese translation cannot
        # run together even when custom CSS is unavailable. Example translations
        # stay inline inside their xsjrh-exbox row.
        in_example = any(
            'xsjrh-exbox' in set((ancestor.get('class') or '').split())
            for ancestor in element.iterancestors()
        )
        force_block = 'xsjrh-c' in classes and not in_example
        node = {'tag': 'div' if tag in BLOCK_TAGS or force_block else 'span', 'content': content}

    if data:
        node['data'] = data
    if lang:
        node['lang'] = lang
    if tag in {'b', 'strong'}:
        node['style'] = {'fontWeight': 'bold'}
    elif tag in {'i', 'em'}:
        node['style'] = {'fontStyle': 'italic'}
    elif tag == 'sub':
        node['style'] = {'fontSize': '65%', 'verticalAlign': 'sub'}
    elif tag == 'sup':
        node['style'] = {'fontSize': '65%', 'verticalAlign': 'super'}
    return node


def split_terms(value: str) -> list[str]:
    parts = [part.strip() for part in re.split(r'[･・]', value) if part.strip()]
    return list(dict.fromkeys(parts))


def heading(document: Any, key: str) -> tuple[list[str], str]:
    word1_nodes = document.xpath(
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' xsjrh-word1 ') "
        "or contains(concat(' ', normalize-space(@class), ' '), ' xsjrh-pword ')]"
    )
    word2_nodes = document.xpath(
        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' xsjrh-word2 ')]"
    )
    word1 = clean_text(word1_nodes[0].text_content()) if word1_nodes else None
    word2 = clean_text(word2_nodes[0].text_content()) if word2_nodes else None
    bracket = BRACKET_KEY_RE.match(key)

    if word2:
        terms = split_terms(word2.strip('【】'))
        reading = clean_reading(word1 or (bracket.group(1) if bracket else ''))
        return terms, reading
    if bracket:
        return split_terms(bracket.group(2)), clean_reading(bracket.group(1))
    term = word1 or key
    reading = clean_reading(term) if not re.search(r'[一-龯々〆ヵヶ]', term) else ''
    return [term], reading


def redirect_reading(alias: str, target: str) -> str:
    match = BRACKET_KEY_RE.match(target)
    if match:
        return clean_reading(match.group(1))
    if not re.search(r'[一-龯々〆ヵヶ]', alias):
        return clean_reading(alias)
    return ''


def resolve_redirect(target: str, direct: set[str], redirects: dict[str, list[str]]) -> str | None:
    queue = [target]
    seen = set()
    while queue:
        current = queue.pop(0)
        if current in direct:
            return current
        if current in seen:
            continue
        seen.add(current)
        queue.extend(redirects.get(current, []))
    return None


def extract_resources(mdd_path: Path, output_dir: Path) -> dict[str, Any]:
    mdd = MDD(str(mdd_path), None)
    extensions = Counter()
    resources = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for key_bytes, content in mdd.items():
        key = key_bytes.decode('utf-8', errors='replace')
        relative = resource_path(key)
        if not relative:
            continue
        destination = output_dir.joinpath(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        extensions[destination.suffix.lower()] += 1
        resources.append(relative)
    return {'count': len(resources), 'extensions': dict(extensions), 'resources': resources}


def main() -> None:
    parser = argparse.ArgumentParser(description='Convert XSJRH MDX to Yomitan structured NDJSON.')
    parser.add_argument('--mdx', type=Path, required=True)
    parser.add_argument('--mdd', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resources-dir', type=Path, required=True)
    args = parser.parse_args()

    mdx = MDX(str(args.mdx), '', False, None)
    stats: Counter[str] = Counter()
    redirects: dict[str, list[str]] = defaultdict(list)
    direct_keys: set[str] = set()
    sequence_by_key: dict[str, int] = {}
    direct_records: list[tuple[str, str]] = []

    for key_bytes, value_bytes in mdx.items():
        key = replace_gaiji(key_bytes.decode(mdx._encoding, errors='replace').strip('\x00\r\n '))
        source = replace_gaiji(value_bytes.decode(mdx._encoding, errors='replace').strip('\x00\r\n '))
        stats['records_seen'] += 1
        if source.startswith('@@@LINK='):
            target = source.partition('=')[2].strip()
            if target and target not in redirects[key]:
                redirects[key].append(target)
            stats['redirect_records'] += 1
            continue
        if 'xsjrh-tbox-wb' in source:
            stats['index_html_skipped'] += 1
            continue
        direct_keys.add(key)
        direct_records.append((key, source))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    referenced_images: set[str] = set()
    with args.output.open('w', encoding='utf-8', newline='\n') as output:
        sequence = 0
        for key, source in direct_records:
            try:
                document = html.fromstring(source)
                terms, reading = heading(document, key)
                root_nodes = document.xpath(
                    ".//*[contains(concat(' ', normalize-space(@class), ' '), ' xsjrh-entry ')]"
                )
                root = root_nodes[0] if root_nodes else document
                content = convert_element(root, stats, referenced_images)
            except Exception as error:
                stats['parse_errors'] += 1
                print(f'WARN parse failed for {key!r}: {error}', flush=True)
                continue
            if not terms or content is None:
                stats['empty_direct_skipped'] += 1
                continue
            sequence += 1
            sequence_by_key[key] = sequence
            definition = {'type': 'structured-content', 'content': content}
            for term in terms:
                record = {'term': term, 'reading': reading, 'sequence': sequence,
                          'definition': definition, 'sourceKey': key}
                output.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
                stats['direct_terms_emitted'] += 1
            stats['direct_articles_emitted'] += 1
            if sequence % 20000 == 0:
                print(f'Converted {sequence:,} direct articles...', flush=True)

        emitted_redirects = set()
        for alias, targets in redirects.items():
            for target in targets:
                resolved = resolve_redirect(target, direct_keys, redirects)
                if not resolved or resolved not in sequence_by_key:
                    stats['redirects_unresolved'] += 1
                    continue
                display_target = query_target(resolved)
                marker = (alias, resolved)
                if not alias or marker in emitted_redirects:
                    continue
                emitted_redirects.add(marker)
                record = {
                    'term': alias,
                    'reading': redirect_reading(alias, resolved),
                    'sequence': sequence_by_key[resolved],
                    'redirect': display_target,
                    'sourceKey': resolved,
                }
                output.write(json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n')
                stats['redirects_emitted'] += 1

    resource_report = extract_resources(args.mdd, args.resources_dir)
    available = {value.casefold() for value in resource_report['resources']}
    missing = sorted(value for value in referenced_images if value.casefold() not in available)
    report = {
        'source_mdx': str(args.mdx),
        'source_mdd': str(args.mdd),
        'output': str(args.output),
        'stats': dict(stats),
        'direct_keys': len(direct_keys),
        'redirect_keys': len(redirects),
        'images_referenced': sorted(referenced_images),
        'unique_images_referenced': len(referenced_images),
        'missing_referenced_resources': missing,
        'resource_extraction': resource_report,
        'gaiji_replacements': GAIJI,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'images_referenced', 'resource_extraction', 'gaiji_replacements'}}, ensure_ascii=False, indent=2))
    print(f"Extracted {resource_report['count']:,} MDD resources; missing referenced resources: {len(missing)}")


if __name__ == '__main__':
    main()
