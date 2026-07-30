import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


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
        'verb_forms_table',
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

    records: dict[str, dict[str, Any]] = {}
    with args.input.open(encoding='utf-8') as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            term = record.get('term')
            if term in REQUIRED_TOKENS and 'definition' in record:
                records.setdefault(term, record)
            if len(records) == len(REQUIRED_TOKENS):
                break
            if not isinstance(record, dict):
                raise ValueError(f'line {line_number}: record is not an object')

    failures: list[str] = []
    report: dict[str, Any] = {}
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

        report[term] = {
            'details': tags['details'],
            'semanticTokens': sum(tokens.values()),
            'examples': tokens['examples'],
            'englishTranslations': tokens['xt'] + tokens['unxt'],
            'chineseNodes': tokens['zh'],
        }

    if failures:
        raise ValueError('\n'.join(failures))
    print(json.dumps({'oaldQaPassed': True, 'entries': report}, indent=2))


if __name__ == '__main__':
    main()
