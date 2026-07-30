import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from lxml import html
from mdict_utils.base.readmdict import MDX


WHITESPACE_RE = re.compile(r'\s+')
OXFORD_SYMBOL_RE = re.compile(
    r'^ox(?P<list>[35])ksym(?:sub)?_(?P<level>[abc][12])$'
)
SKIP_TAGS = {'script', 'style', 'link', 'meta'}
BLOCK_TAGS = {'html', 'body', 'oaldpe', 'div', 'aside', 'section', 'article', 'p',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
TABLE_TAGS = {'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th'}
LIST_TAGS = {'ol', 'ul', 'li'}
SEMANTIC_CLASSES = {
    'entry', 'top-container', 'top-g', 'webtop', 'symbols', 'opal_symbol',
    'headword', 'pos', 'phonetics', 'phons_br', 'phons_n_am', 'phon',
    'jumplinks', 'jumplink', 'grammar', 'labels', 'senses_multiple',
    'senses_single', 'sense_single', 'shcut-g', 'shcut', 'sense', 'sensetop',
    'iteration',
    'variants', 'v-g', 'v', 'def', 'deft', 'examples', 'x', 'xt', 'unx',
    'unxt', 'cl', 'gloss', 'cf', 'xrefs', 'prefix', 'xr-g', 'xh', 'sep',
    'collapse', 'unbox', 'box_title', 'body', 'closed', 'p', 'deflist',
    'defpara', 'eb', 'ei', 'bulletsep', 'un', 'patterns', 'bullet', 'li',
    'collocs_list', 'topic-g', 'topic', 'topic_name', 'topic_cefr', 'idioms',
    'idioms_heading', 'idm-g', 'idm', 'phrasalverb', 'phrasal_verb_links',
    'verb_forms_table', 'verb_form', 'vf_prefix', 'verb_phons', 'inflections',
    'use', 'xref', 'single', 'app', 'ndv', 'belong-to', 'dis-g', 'dtxt',
    'subj', 'inflected_form', 'st', 'pv-g', 'pv', 'ebi', 'inline', 'dh',
    'xw', 'wfp', 'wfw', 'pvarr', 'xs', 'pvrefs', 'idmsep', 'def_qt', 'wx',
    'wfo', 'lisep', 'blockquote', 'p-g', 'hm', 'eph', 'phons_we',
    'phon_label', 'alt', 'sup', 'xhm', 'xh_bold', 've', 'esc', 'er', 'sub',
    'alt-g', 'frac-g', 'num', 'den', 'footer', 'h4',
}
CLASS_TOKEN_ALIASES = {
    'Ref': ('ref',),
    'sense_single': ('sense_single', 'senses_single'),
}
TAG_TOKEN_ALIASES = {
    'chn': ('zh',),
    'chn_sc': ('zh', 'zh-sc'),
    'chn_tc': ('zh', 'zh-tc'),
    'deft': ('deft', 'translation', 'definition-translation', 'zh'),
    'dtxtx': ('dtxt', 'translation', 'inline-translation', 'zh'),
    'xt': ('xt', 'translation', 'example-translation', 'zh'),
    'unxt': ('unxt', 'translation', 'example-translation', 'zh'),
    'undt': ('undt', 'translation', 'note-translation', 'zh'),
    'ubx': ('ubx', 'translation', 'box-translation', 'zh'),
    'labelx': ('labelx', 'zh'),
    'unboxx': ('unboxx', 'zh'),
    'uset': ('uset', 'zh'),
    'shcut': ('shortcut-zh', 'zh'),
    'oald': ('source-oald', 'zh'),
    'leon': ('source-leon', 'zh'),
    'ai': ('source-ai', 'zh'),
}
CHINESE_TAGS = {
    'chn', 'chn_sc', 'chn_tc', 'deft', 'dtxtx', 'xt', 'unxt', 'undt',
    'ubx', 'labelx', 'unboxx', 'uset', 'shcut', 'oald', 'ai', 'leon',
}
ITALIC_CLASSES = {'ei'}
BOLD_CLASSES = {'eb'}
CONFIG_TERM = 'OALD Yomitan 设置'
PHRASE_SECTION_LABELS = {
    'idioms': 'Idioms',
    'phrasal_verb_links': 'Phrasal Verbs',
}


def normalize_text(
    value: str | None,
    *,
    preserve_edges: bool = False,
) -> str | None:
    if not value:
        return None
    cleaned = value.replace('\u200b', '')
    leading_space = cleaned[0].isspace()
    trailing_space = cleaned[-1].isspace()
    normalized = WHITESPACE_RE.sub(' ', cleaned).strip()
    if not normalized:
        return ' ' if preserve_edges and (leading_space or trailing_space) else None
    if preserve_edges:
        if leading_space:
            normalized = f' {normalized}'
        if trailing_space:
            normalized = f'{normalized} '
    return normalized


def content_value(parts: list[Any]) -> Any:
    compact = [part for part in parts if part not in (None, '', [])]
    if not compact:
        return None
    return compact[0] if len(compact) == 1 else compact


def element_content(element: Any, stats: Counter[str], include_images: bool,
                    referenced_images: set[str]) -> Any:
    parts: list[Any] = []
    text = normalize_text(element.text, preserve_edges=True)
    if text:
        parts.append(text)
    for child in element:
        converted = convert_element(child, stats, include_images, referenced_images)
        if converted is not None:
            parts.append(converted)
        tail = normalize_text(child.tail, preserve_edges=True)
        if tail:
            parts.append(tail)
    return content_value(parts)


def element_content_without(
    element: Any,
    excluded_child: Any,
    stats: Counter[str],
    include_images: bool,
    referenced_images: set[str],
) -> Any:
    parts: list[Any] = []
    text = normalize_text(element.text, preserve_edges=True)
    if text:
        parts.append(text)
    for child in element:
        if child is not excluded_child:
            converted = convert_element(
                child,
                stats,
                include_images,
                referenced_images,
            )
            if converted is not None:
                parts.append(converted)
        tail = normalize_text(child.tail, preserve_edges=True)
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


def data_tokens(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    data = value.get('data')
    if not isinstance(data, dict):
        return set()
    marker = data.get('oald')
    return set(marker.split()) if isinstance(marker, str) else set()


def find_first_token(value: Any, token: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if token in data_tokens(value):
            return value
        return find_first_token(value.get('content'), token)
    if isinstance(value, list):
        for item in value:
            found = find_first_token(item, token)
            if found is not None:
                return found
    return None


def phrase_sections(value: Any) -> dict[str, list[dict[str, Any]]]:
    sections: dict[str, list[dict[str, Any]]] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            tokens = data_tokens(node)
            if 'phrase-section' in tokens:
                for section_kind in PHRASE_SECTION_LABELS:
                    if section_kind in tokens:
                        sections.setdefault(section_kind, []).append(node)
            visit(node.get('content'))
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return sections


def phrase_query_term(term: str, section_kind: str) -> str:
    label = PHRASE_SECTION_LABELS[section_kind]
    return f'OALD {label} · {term}'


def query_link(label: str, target: str, marker: str) -> dict[str, Any]:
    return {
        'tag': 'span',
        'data': {'oald': marker},
        'content': {
            'tag': 'a',
            'href': f'?query={quote(target)}',
            'content': label,
        },
    }


def wire_entry_navigation(
    structured: Any,
    term: str,
    sections: dict[str, list[dict[str, Any]]],
) -> None:
    webtop = find_first_token(structured, 'webtop')
    if webtop is None:
        return
    navigation: list[Any] = []
    for section_kind, label in PHRASE_SECTION_LABELS.items():
        if section_kind not in sections:
            continue
        navigation.append(
            query_link(
                label,
                phrase_query_term(term, section_kind),
                f'jumplink phrase-query-link {section_kind}-query-link',
            )
        )
    navigation.append(
        query_link('O10', CONFIG_TERM, 'jumplink o10-link')
    )
    navigation_node = {
        'tag': 'span',
        'data': {'oald': 'jumplinks entry-actions'},
        'content': navigation,
    }

    content = webtop.get('content')
    items = content if isinstance(content, list) else [content]
    replaced = False
    for index, item in enumerate(items):
        if 'jumplinks' in data_tokens(item):
            items[index] = navigation_node
            replaced = True
            break
    if not replaced:
        items.append(navigation_node)
    webtop['content'] = content_value(items)


def auxiliary_phrase_content(
    term: str,
    section_kind: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    label = PHRASE_SECTION_LABELS[section_kind]
    expanded_sections = copy.deepcopy(sections)
    for section in expanded_sections:
        section['open'] = True
    return {
        'tag': 'div',
        'data': {'oald': 'entry auxiliary-entry phrase-result'},
        'content': [
            {
                'tag': 'div',
                'data': {'oald': 'auxiliary-header'},
                'content': [
                    {
                        'tag': 'span',
                        'data': {'oald': 'headword'},
                        'content': term,
                    },
                    ' · ',
                    {
                        'tag': 'span',
                        'data': {'oald': 'auxiliary-kind'},
                        'content': label,
                    },
                ],
            },
            *expanded_sections,
        ],
    }


def config_content() -> dict[str, Any]:
    def panel(title: str, body: list[Any], *, open_panel: bool = False) -> dict[str, Any]:
        node: dict[str, Any] = {
            'tag': 'details',
            'data': {'oald': 'config-panel'},
            'content': [
                {
                    'tag': 'summary',
                    'data': {'oald': 'config-panel-title'},
                    'content': title,
                },
                {
                    'tag': 'div',
                    'data': {'oald': 'config-panel-body'},
                    'content': body,
                },
            ],
        }
        if open_panel:
            node['open'] = True
        return node

    return {
        'tag': 'div',
        'data': {'oald': 'entry config-entry'},
        'content': [
            {
                'tag': 'div',
                'data': {'oald': 'config-header'},
                'content': [
                    {
                        'tag': 'span',
                        'data': {'oald': 'o10-logo'},
                        'content': 'O10',
                    },
                    {
                        'tag': 'span',
                        'data': {'oald': 'config-title'},
                        'content': 'OALD · Yomitan 配置说明',
                    },
                ],
            },
            {
                'tag': 'div',
                'data': {'oald': 'config-notice'},
                'content': (
                    'Yomitan 词典内容不能运行原版 JavaScript、表单或持久化开关；'
                    '本页保留能够在 Yomitan 中实际使用的设置与操作说明。'
                ),
            },
            panel(
                '显示与颜色',
                [
                    '请在 Yomitan 中启用词典样式；主题、字号、弹窗宽度和缩放由 '
                    'Yomitan 的外观设置控制。本词典已分别配色显示主词、词性、'
                    '英美音、义项、中文释义、例句、搭配、词源和用法模块。'
                ],
                open_panel=True,
            ),
            panel(
                '中文来源',
                [
                    'OALD、AI 与 Leon 中文内容使用来源徽章区分。Yomitan 不允许'
                    '词条内部保存“显示/隐藏某一来源”的开关，因此不提供无效按钮。'
                ],
            ),
            panel(
                '发音与口音',
                [
                    '在 Yomitan 的音频设置中调整音频来源和优先顺序。此转换版的'
                    '数 GB 原词典音频由本地音频伴侣提供；英音和美音在词条中以'
                    '“英”“美”徽章区分。'
                ],
            ),
            panel(
                '折叠与导航',
                [
                    'Synonyms、Wordfinder、Extra Examples、Collocations、'
                    'Word Origin 等模块使用 Yomitan 原生折叠。顶部 Idioms 和 '
                    'Phrasal Verbs 会打开当前单词对应的专用结果。'
                ],
            ),
            panel(
                '原版中无法移植的功能',
                [
                    '欧路相关笔记、在线抓取、词条内 TTS 开关、动态口音切换、'
                    'JavaScript 配置面板和按词性即时过滤不能由 Yomitan 词典包'
                    '直接实现，应使用 Yomitan 自身设置或本地音频服务。'
                ],
            ),
        ],
    }


def semantic_tokens(element: Any, classes: set[str], tag: str) -> list[str]:
    tokens: set[str] = set()
    for class_name in classes:
        if class_name in SEMANTIC_CLASSES:
            tokens.add(class_name)
        tokens.update(CLASS_TOKEN_ALIASES.get(class_name, ()))
    tokens.update(TAG_TOKEN_ALIASES.get(tag, ()))

    form = (element.get('form') or '').strip().lower()
    if form and re.fullmatch(r'[a-z0-9_-]+', form):
        tokens.add(f'form-{form}')
    un_kind = (element.get('un') or '').strip().lower()
    if un_kind and re.fullmatch(r'[a-z0-9_-]+', un_kind):
        tokens.add(f'un-{un_kind}')
    type_name = (element.get('type') or '').strip().lower()
    if type_name and re.fullmatch(r'[a-z0-9_-]+', type_name):
        tokens.add(f'type-{type_name}')
    return sorted(tokens)


def convert_collapse(
    element: Any,
    stats: Counter[str],
    include_images: bool,
    referenced_images: set[str],
) -> Any:
    wrapper = next(
        (
            child
            for child in element
            if 'unbox' in set((child.get('class') or '').split())
        ),
        None,
    )
    if wrapper is None:
        return None
    title = next(
        (
            child
            for child in wrapper
            if 'box_title' in set((child.get('class') or '').split())
        ),
        None,
    )
    if title is None:
        return None

    title_content = element_content(
        title,
        stats,
        include_images,
        referenced_images,
    )
    body_content = element_content_without(
        wrapper,
        title,
        stats,
        include_images,
        referenced_images,
    )
    if title_content is None or body_content is None:
        return None

    section_kind = (wrapper.get('unbox') or 'section').strip().lower()
    section_kind = re.sub(r'[^a-z0-9_-]+', '-', section_kind).strip('-')
    if not section_kind:
        section_kind = 'section'
    details: dict[str, Any] = {
        'tag': 'details',
        'data': {'oald': f'collapse collapse-{section_kind}'},
        'content': [
            {
                'tag': 'summary',
                'data': {'oald': 'box_title'},
                'content': title_content,
            },
            {
                'tag': 'div',
                'data': {'oald': 'collapse_body'},
                'content': body_content,
            },
        ],
    }
    if section_kind == 'wordorigin':
        details['open'] = True
    stats['collapsible_sections'] += 1
    return details


def convert_phrase_section(
    element: Any,
    stats: Counter[str],
    include_images: bool,
    referenced_images: set[str],
    section_kind: str,
) -> Any:
    heading_class = 'idioms_heading' if section_kind == 'idioms' else 'unbox'
    heading = next(
        (
            child
            for child in element
            if heading_class in set((child.get('class') or '').split())
        ),
        None,
    )
    if heading is None:
        return None
    heading_content = element_content(
        heading,
        stats,
        include_images,
        referenced_images,
    )
    body_content = element_content_without(
        element,
        heading,
        stats,
        include_images,
        referenced_images,
    )
    if heading_content is None or body_content is None:
        return None
    stats[f'{section_kind}_sections'] += 1
    return {
        'tag': 'details',
        'data': {'oald': f'phrase-section {section_kind}'},
        'content': [
            {
                'tag': 'summary',
                'data': {
                    'oald': f'phrase_heading {heading_class}',
                },
                'content': heading_content,
            },
            {
                'tag': 'div',
                'data': {'oald': 'phrase_body'},
                'content': body_content,
            },
        ],
    }


def convert_element(element: Any, stats: Counter[str], include_images: bool,
                    referenced_images: set[str]) -> Any:
    tag = str(element.tag).lower() if isinstance(element.tag, str) else ''
    classes = set((element.get('class') or '').split())

    if tag in SKIP_TAGS or 'pseudo-footer' in classes or 'oaldpe-nav' in classes:
        return None
    if tag == 'a' and ('sound' in classes or (element.get('href') or '').startswith('sound://')):
        stats['audio_links_removed'] += 1
        return None
    for class_name in classes:
        symbol_match = OXFORD_SYMBOL_RE.fullmatch(class_name)
        if symbol_match is not None:
            list_number = symbol_match.group('list')
            level = symbol_match.group('level').upper()
            stats['frequency_badges_preserved'] += 1
            return {
                'tag': 'span',
                'content': f'🔑 {level}',
                'data': {
                    'oald': (
                        f'badge oxford-list list-{list_number}000 '
                        f'level-{level.lower()}'
                    )
                },
            }
    if 'idioms' in classes:
        phrase_section = convert_phrase_section(
            element,
            stats,
            include_images,
            referenced_images,
            'idioms',
        )
        if phrase_section is not None:
            return phrase_section
    if 'phrasal_verb_links' in classes:
        phrase_section = convert_phrase_section(
            element,
            stats,
            include_images,
            referenced_images,
            'phrasal_verb_links',
        )
        if phrase_section is not None:
            return phrase_section
    if 'collapse' in classes:
        collapse = convert_collapse(
            element,
            stats,
            include_images,
            referenced_images,
        )
        if collapse is not None:
            return collapse
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
            image_tokens = semantic_tokens(element, classes, tag)
            if image_tokens:
                node['data'] = {'oald': ' '.join(image_tokens)}
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

    data_tokens = semantic_tokens(element, classes, tag)
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
        if tag in CHINESE_TAGS:
            node['lang'] = 'zh'
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
            node = {'tag': 'a', 'content': content, 'href': converted_href}
            if data:
                return {'tag': 'span', 'content': node, 'data': data}
            return node
        if href.startswith(('http://', 'https://')):
            node = {'tag': 'a', 'content': content, 'href': href}
            if data:
                return {'tag': 'span', 'content': node, 'data': data}
            return node

    node_tag = 'div' if tag in BLOCK_TAGS else 'span'
    node = {'tag': node_tag, 'content': content}
    if data:
        node['data'] = data
    title = normalize_text(element.get('title'))
    if title:
        node['title'] = title
    if tag in CHINESE_TAGS:
        node['lang'] = 'zh'
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
    parser.add_argument(
        '--term',
        action='append',
        dest='terms',
        help='Only convert the exact headword; repeat to select multiple terms.',
    )
    parser.add_argument('--include-images', action='store_true')
    args = parser.parse_args()

    mdx = MDX(str(args.mdx), '', False, None)
    requested_terms = {
        term.strip().casefold()
        for term in (args.terms or [])
        if term.strip()
    }
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
            if requested_terms and key.casefold() not in requested_terms:
                stats['unselected_direct_skipped'] += 1
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

            sections = phrase_sections(structured)
            wire_entry_navigation(structured, key, sections)

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

            for section_kind, section_values in sections.items():
                auxiliary_term = phrase_query_term(key, section_kind)
                auxiliary_sequence = direct_sequences.setdefault(
                    auxiliary_term,
                    next_sequence,
                )
                if auxiliary_sequence == next_sequence:
                    next_sequence += 1
                auxiliary_record = {
                    'term': auxiliary_term,
                    'sequence': auxiliary_sequence,
                    'definition': {
                        'type': 'structured-content',
                        'content': auxiliary_phrase_content(
                            key,
                            section_kind,
                            section_values,
                        ),
                    },
                }
                output.write(
                    json.dumps(
                        auxiliary_record,
                        ensure_ascii=False,
                        separators=(',', ':'),
                    )
                    + '\n'
                )
                stats[f'{section_kind}_query_entries_written'] += 1

        config_sequence = direct_sequences.setdefault(CONFIG_TERM, next_sequence)
        if config_sequence == next_sequence:
            next_sequence += 1
        config_record = {
            'term': CONFIG_TERM,
            'sequence': config_sequence,
            'definition': {
                'type': 'structured-content',
                'content': config_content(),
            },
        }
        output.write(
            json.dumps(
                config_record,
                ensure_ascii=False,
                separators=(',', ':'),
            )
            + '\n'
        )
        stats['config_entries_written'] += 1

        if args.limit_direct is None and not requested_terms:
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
        'terms_requested': sorted(requested_terms),
        'terms_missing': sorted(requested_terms - {
            term.casefold()
            for term in direct_sequences
        }),
        'output_bytes': args.output.stat().st_size,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
