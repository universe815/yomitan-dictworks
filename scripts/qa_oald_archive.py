import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote


ALLOWED_TAGS = {
    'a',
    'br',
    'details',
    'div',
    'img',
    'li',
    'ol',
    'rp',
    'rt',
    'ruby',
    'span',
    'summary',
    'table',
    'tbody',
    'td',
    'tfoot',
    'th',
    'thead',
    'tr',
    'ul',
}

REQUIRED_SPECIAL_TERMS = {
    'OALD Idioms · language',
    'OALD Idioms · plague',
    'OALD Phrasal Verbs · take',
}


def walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, dict):
        yield value
        yield from walk(value.get('content'))


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run fast archive-wide structural QA for an OALD Yomitan ZIP.'
    )
    parser.add_argument('dictionary', type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--expect-images', type=int, default=0)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()

    counters: Counter[str] = Counter()
    image_references: set[str] = set()
    with zipfile.ZipFile(args.dictionary) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f'CRC failure in {bad_member}')
        archive_names = set(archive.namelist())
        index = json.loads(archive.read('index.json'))
        if index.get('revision') != args.revision:
            raise ValueError('index revision differs from expected revision')
        if index.get('format') != 3:
            raise ValueError('index format is not Yomitan v3')
        if index.get('isUpdatable') is not True:
            raise ValueError('index is not marked updatable')
        if 'styles.css' not in archive_names:
            raise ValueError('archive contains no styles.css')
        styles = archive.read('styles.css').decode('utf-8')
        if '[data-sc-oald' not in styles:
            raise ValueError(
                'styles.css lacks Yomitan data-sc-oald selectors'
            )
        if '[data-oald' in styles:
            raise ValueError(
                'styles.css contains non-rendering data-oald selectors'
            )
        for required_selector in (
            '[data-sc-oald~="headword"]',
            '[data-sc-oald~="badge"]',
            '[data-sc-oald~="iteration"]',
            '[data-sc-oald~="deft"]',
            '[data-sc-oald~="examples"]',
            '[data-sc-oald~="collapse"]',
            '[data-sc-oald~="idioms"]',
            '[data-sc-oald~="entry-actions"]',
            '[data-sc-oald~="auxiliary-entry"]',
        ):
            if required_selector not in styles:
                raise ValueError(
                    f'styles.css lacks required selector {required_selector}'
                )

        term_banks = sorted(
            name
            for name in archive_names
            if name.startswith('term_bank_') and name.endswith('.json')
        )
        if not term_banks:
            raise ValueError('archive contains no term banks')
        found_special_terms: set[str] = set()
        required_links = {
            f'?query={quote(term)}'
            for term in REQUIRED_SPECIAL_TERMS
        }
        found_required_links: set[str] = set()
        for member in term_banks:
            rows = json.loads(archive.read(member))
            if not isinstance(rows, list):
                raise ValueError(f'{member}: root is not an array')
            for row_number, row in enumerate(rows, start=1):
                counters['rows'] += 1
                if not isinstance(row, list) or len(row) != 8:
                    raise ValueError(f'{member} row {row_number}: invalid row')
                if not isinstance(row[0], str) or not row[0]:
                    raise ValueError(
                        f'{member} row {row_number}: invalid headword'
                    )
                if row[0] in REQUIRED_SPECIAL_TERMS:
                    found_special_terms.add(row[0])
                if not isinstance(row[5], list) or not row[5]:
                    raise ValueError(
                        f'{member} row {row_number}: definitions are empty'
                    )
                for definition in row[5]:
                    counters['definitions'] += 1
                    if not isinstance(definition, dict):
                        continue
                    if definition.get('type') != 'structured-content':
                        continue
                    counters['structured_definitions'] += 1
                    for node in walk(definition.get('content')):
                        tag = node.get('tag')
                        if tag not in ALLOWED_TAGS:
                            raise ValueError(
                                f'{member} row {row_number}: invalid tag {tag!r}'
                            )
                        counters[f'tag_{tag}'] += 1
                        data = node.get('data')
                        if data is not None and (
                            not isinstance(data, dict)
                            or any(
                                not isinstance(key, str)
                                or not isinstance(value, str)
                                for key, value in data.items()
                            )
                        ):
                            raise ValueError(
                                f'{member} row {row_number}: invalid data object'
                            )
                        if tag == 'details':
                            content = node.get('content')
                            if (
                                not isinstance(content, list)
                                or len(content) < 2
                                or not isinstance(content[0], dict)
                                or content[0].get('tag') != 'summary'
                            ):
                                raise ValueError(
                                    f'{member} row {row_number}: invalid details'
                                )
                        if tag == 'a':
                            href = node.get('href')
                            if href in required_links:
                                found_required_links.add(href)
                        if tag == 'img':
                            path = node.get('path')
                            if not isinstance(path, str) or not path:
                                raise ValueError(
                                    f'{member} row {row_number}: invalid image'
                                )
                            image_references.add(path)

        missing_special_terms = sorted(
            REQUIRED_SPECIAL_TERMS - found_special_terms
        )
        if missing_special_terms:
            raise ValueError(
                'missing OALD navigation entries: '
                + ', '.join(missing_special_terms)
            )
        missing_required_links = sorted(required_links - found_required_links)
        if missing_required_links:
            raise ValueError(
                'missing OALD navigation links: '
                + ', '.join(missing_required_links)
            )
        missing_images = sorted(image_references - archive_names)
        if missing_images:
            raise ValueError(
                f'{len(missing_images)} referenced images are absent'
            )
        packaged_images = {
            name
            for name in archive_names
            if name.startswith('img/oald/') and not name.endswith('/')
        }
        if len(packaged_images) != args.expect_images:
            raise ValueError(
                f'expected {args.expect_images} packaged images, '
                f'found {len(packaged_images)}'
            )
        if image_references != packaged_images:
            raise ValueError(
                'packaged image set differs from structured-content references'
            )

    result = {
        'oaldArchiveQaPassed': True,
        'dictionary': str(args.dictionary),
        'revision': args.revision,
        'termBanks': len(term_banks),
        'rows': counters['rows'],
        'structuredDefinitions': counters['structured_definitions'],
        'details': counters['tag_details'],
        'summaries': counters['tag_summary'],
        'navigationEntries': len(found_special_terms),
        'navigationLinks': len(found_required_links),
        'stylesUseYomitanDataPrefix': True,
        'imageReferences': len(image_references),
        'packagedImages': args.expect_images,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
