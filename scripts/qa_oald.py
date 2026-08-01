import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote


REQUIRED_TOKENS = {
    'language': {
        'headword',
        'pos',
        'phonetics',
        'sense',
        'def',
        'deft',
        'examples',
        'xt',
        'collapse',
        'box_title',
        'topic_cefr',
        'idioms',
        'idm',
        'phrase-section',
        'phrase_heading',
        'phrase-back',
        'phrase_body',
        'senses_single',
        'source-oald',
        'unboxx',
        'ref',
        'collapse-synonyms',
        'collapse-wordfinder',
        'collapse-extra_examples',
        'collapse-snippet',
        'collapse-wordorigin',
    },
    'plague': {
        'headword',
        'pos',
        'phonetics',
        'sense',
        'def',
        'deft',
        'examples',
        'xt',
        'collapse',
        'box_title',
        'topic_cefr',
        'idioms',
        'idm',
        'phrase-section',
        'phrase_heading',
        'phrase-back',
        'phrase_body',
        'verb_forms_table',
        'senses_single',
        'source-oald',
        'source-ai',
        'unboxx',
        'labelx',
        'form-root',
        'collapse-extra_examples',
        'collapse-snippet',
        'collapse-wordorigin',
        'collapse-verbforms',
    },
}

EXPECTED_PHRASES = {
    'language': (
        'It takes a long time to learn to speak a language well.',
        'All the children must learn a foreign language.',
        'German is my native language.',
        'Is English an official language in your country?',
        'She has a good command of the Spanish language.',
        'Good language skills are essential in this job.',
        'They fell in love in spite of the language barrier',
    ),
    'plague': (
        'a disease spread by rats that causes a high temperature',
        'a decline in population following outbreaks of plague',
        'avoid somebody/something like the plague',
        'Financial problems are plaguing the company.',
    ),
}

FORBIDDEN_JOINED_TEXT = (
    'tospeak',
    'languagewell',
    'aforeign',
    'mynative',
    'anofficial',
    'languagein your',
    'theSpanishlanguage',
    'Goodlanguage',
    'thelanguage barrier',
)

SPECIAL_TERMS = {
    'OALD Idioms · language',
    'OALD Idioms · plague',
}

METADATA_TITLE_PREFIXES = {
    'pos': '词性：',
    'grammar': '语法标签：',
    'opal_symbol': '牛津学术词汇 OPAL：',
    'phons_br': '英式英语发音',
    'phons_n_am': '美式英语发音',
    'phon_label': '地区发音：',
    'topic_cefr': '主题词汇 CEFR 难度：',
}


def walk(value: Any) -> Iterator[Any]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, dict):
        yield value
        yield from walk(value.get('content'))


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Check OALD structured-content hierarchy and spacing.'
    )
    parser.add_argument('input', type=Path)
    args = parser.parse_args()

    wanted_terms = set(REQUIRED_TOKENS) | SPECIAL_TERMS
    records: dict[str, dict[str, Any]] = {}
    metadata_counts: Counter[str] = Counter()
    metadata_title_failures: list[str] = []
    image_counts: Counter[str] = Counter()
    image_paths: set[str] = set()
    image_failures: list[str] = []
    with args.input.open(encoding='utf-8') as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            term = record.get('term')
            if term in wanted_terms and 'definition' in record:
                records.setdefault(term, record)
            if not isinstance(record, dict):
                raise ValueError(f'line {line_number}: record is not an object')
            definition = record.get('definition')
            if not isinstance(definition, dict):
                continue
            for node in walk(definition.get('content')):
                if not isinstance(node, dict):
                    continue
                tokens = set(node.get('data', {}).get('oald', '').split())
                title = node.get('title')
                for token, prefix in METADATA_TITLE_PREFIXES.items():
                    if token not in tokens:
                        continue
                    metadata_counts[token] += 1
                    if (
                        not isinstance(title, str)
                        or not title.startswith(prefix)
                    ) and len(metadata_title_failures) < 50:
                        metadata_title_failures.append(
                            f'{term}: {token} lacks a useful title: {title!r}'
                        )
                if 'oxford-list' in tokens:
                    metadata_counts['oxford-list'] += 1
                    if (
                        not isinstance(title, str)
                        or 'Oxford' not in title
                    ) and len(metadata_title_failures) < 50:
                        metadata_title_failures.append(
                            f'{term}: oxford-list lacks a useful title: {title!r}'
                        )
                if node.get('tag') != 'img':
                    continue
                image_counts['total'] += 1
                path = node.get('path', '')
                if isinstance(path, str) and path:
                    image_paths.add(path)
                if isinstance(path, str) and '/thumb_' in path:
                    image_counts['thumbnail'] += 1
                if 'fullsize' in tokens:
                    image_counts['fullsize'] += 1
                    valid = (
                        node.get('width') == 150
                        and node.get('sizeUnits') == 'px'
                        and node.get('collapsed') is not True
                        and node.get('collapsible') is not True
                        and node.get('title') == '点击查看原始大图'
                    )
                    if not valid and len(image_failures) < 50:
                        image_failures.append(
                            f'{term}: invalid full-size image node: {node!r}'
                        )

    failures: list[str] = []
    for token in (*METADATA_TITLE_PREFIXES, 'oxford-list'):
        if metadata_counts[token] == 0:
            failures.append(f'full corpus: metadata token is missing: {token}')
    failures.extend(metadata_title_failures)
    if image_counts['total']:
        if image_counts['total'] != image_counts['fullsize']:
            failures.append(
                'full corpus: every image occurrence must use the single '
                f'full-resolution node; got {image_counts["total"]} total and '
                f'{image_counts["fullsize"]} fullsize'
            )
        if len(image_paths) != 311:
            failures.append(
                'full corpus: expected 311 unique full-resolution resources, '
                f'got {len(image_paths)}'
            )
        if image_counts['thumbnail']:
            failures.append(
                'full corpus: redundant thumbnail image nodes remain: '
                f'{image_counts["thumbnail"]}'
            )
        failures.extend(image_failures)

    report: dict[str, Any] = {
        'metadataTooltips': dict(sorted(metadata_counts.items())),
        'images': {
            **dict(sorted(image_counts.items())),
            'uniquePaths': len(image_paths),
        },
    }
    for term in REQUIRED_TOKENS:
        record = records.get(term)
        if record is None:
            failures.append(f'{term}: representative entry is missing')
            continue
        definition = record.get('definition')
        if not isinstance(definition, dict):
            failures.append(f'{term}: definition is not an object')
            continue

        nodes = list(walk(definition.get('content')))
        text = ''.join(node for node in nodes if isinstance(node, str))
        tags = Counter(
            node.get('tag')
            for node in nodes
            if isinstance(node, dict)
        )
        tokens = Counter(
            token
            for node in nodes
            if isinstance(node, dict)
            for token in node.get('data', {}).get('oald', '').split()
        )

        missing_tokens = sorted(REQUIRED_TOKENS[term] - tokens.keys())
        if missing_tokens:
            failures.append(
                f"{term}: missing semantic tokens {', '.join(missing_tokens)}"
            )
        if tags['details'] < 1 or tags['details'] != tags['summary']:
            failures.append(f'{term}: collapsible section structure is invalid')
        if not any(
            isinstance(node, dict)
            and node.get('tag') == 'details'
            and node.get('open') is True
            and 'collapse-wordorigin'
            in node.get('data', {}).get('oald', '').split()
            for node in nodes
        ):
            failures.append(f'{term}: Word Origin is not open by default')
        for phrase in EXPECTED_PHRASES[term]:
            if phrase not in text:
                failures.append(f'{term}: spacing lost in {phrase!r}')
        for joined in FORBIDDEN_JOINED_TEXT:
            if joined in text:
                failures.append(f'{term}: joined text remains: {joined!r}')
        invalid_zh_nodes = [
            node
            for node in nodes
            if isinstance(node, dict)
            and 'zh' in node.get('data', {}).get('oald', '').split()
            and node.get('lang') != 'zh'
        ]
        if invalid_zh_nodes:
            failures.append(
                f'{term}: {len(invalid_zh_nodes)} Chinese nodes lack lang=zh'
            )
        anchors = {
            node.get('href')
            for node in nodes
            if isinstance(node, dict) and node.get('tag') == 'a'
        }
        expected_idiom_href = f'?query={quote(f"OALD Idioms · {term}")}'
        expected_back_href = f'?query={quote(term)}'
        if expected_idiom_href not in anchors:
            failures.append(f'{term}: Idioms query link is missing')
        if expected_back_href not in anchors:
            failures.append(f'{term}: Idioms return-to-headword link is missing')
        badge_texts = [
            ''.join(
                child
                for child in walk(node.get('content'))
                if isinstance(child, str)
            )
            for node in nodes
            if isinstance(node, dict)
            and 'oxford-list' in node.get('data', {}).get('oald', '').split()
        ]
        if term == 'language' and not any(
            text.startswith('🔑 ') for text in badge_texts
        ):
            failures.append(f'{term}: compact key CEFR badge is missing')
        if any('Oxford 3000' in text or 'Oxford 5000' in text for text in badge_texts):
            failures.append(f'{term}: verbose Oxford badge remains')
        if term == 'language':
            titles = {
                node.get('title', '')
                for node in nodes
                if isinstance(node, dict) and isinstance(node.get('title'), str)
            }
            for fragment in (
                'CEFR 难度：A1',
                '名词 (Noun)',
                '可数 (Countable)',
                '书面语词汇表 (Written words)',
                '口语词汇表 (Spoken words)',
            ):
                if not any(fragment in title for title in titles):
                    failures.append(
                        f'{term}: metadata tooltip is missing: {fragment}'
                    )

        report[term] = {
            'details': tags['details'],
            'semanticTokens': sum(tokens.values()),
            'examples': tokens['examples'],
            'englishTranslations': tokens['xt'] + tokens['unxt'],
            'chineseNodes': tokens['zh'],
            'queryLinks': len(anchors),
        }

    for term in ('language', 'plague'):
        auxiliary_term = f'OALD Idioms · {term}'
        record = records.get(auxiliary_term)
        if record is None:
            failures.append(f'{auxiliary_term}: auxiliary entry is missing')
            continue
        nodes = list(walk(record.get('definition', {}).get('content')))
        tokens = Counter(
            token
            for node in nodes
            if isinstance(node, dict)
            for token in node.get('data', {}).get('oald', '').split()
        )
        if not {'auxiliary-entry', 'phrase-result', 'idioms'} <= tokens.keys():
            failures.append(f'{auxiliary_term}: auxiliary structure is incomplete')
        if not any(
            isinstance(node, dict)
            and node.get('tag') == 'details'
            and node.get('open') is True
            and 'idioms' in node.get('data', {}).get('oald', '').split()
            for node in nodes
        ):
            failures.append(f'{auxiliary_term}: Idioms section is not open')
        anchors = {
            node.get('href')
            for node in nodes
            if isinstance(node, dict) and node.get('tag') == 'a'
        }
        if f'?query={quote(term)}' not in anchors:
            failures.append(
                f'{auxiliary_term}: return-to-headword link is missing'
            )

    if failures:
        raise ValueError('\n'.join(failures))
    print(json.dumps({'oaldQaPassed': True, 'entries': report}, indent=2))


if __name__ == '__main__':
    main()
