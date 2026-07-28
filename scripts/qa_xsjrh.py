import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path


def walk_content(value, image_paths: set[str], stats: Counter[str]):
    if isinstance(value, list):
        for item in value:
            walk_content(item, image_paths, stats)
    elif isinstance(value, dict):
        tag = value.get('tag')
        if tag:
            stats[f'tag:{tag}'] += 1
        if tag == 'img' and isinstance(value.get('path'), str):
            image_paths.add(value['path'])
        walk_content(value.get('content'), image_paths, stats)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('zip', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = {'zip': str(args.zip), 'errors': [], 'samples': {}}
    image_refs = set()
    stats = Counter()
    terms = set()
    with zipfile.ZipFile(args.zip) as archive:
        names = set(archive.namelist())
        index = json.loads(archive.read('index.json'))
        result['index'] = index
        banks = sorted(name for name in names if name.startswith('term_bank_') and name.endswith('.json'))
        for bank in banks:
            values = json.loads(archive.read(bank))
            stats['terms'] += len(values)
            for entry in values:
                terms.add(entry[0])
                for definition in entry[5]:
                    if isinstance(definition, dict) and definition.get('type') == 'structured-content':
                        walk_content(definition.get('content'), image_refs, stats)
        archived_images = {name for name in names if name.startswith('img/xsjrh/') and not name.endswith('/')}
        missing = sorted(image_refs - names)
        result.update({
            'term_banks': len(banks),
            'stats': dict(stats),
            'unique_terms': len(terms),
            'referenced_images': len(image_refs),
            'archived_images': len(archived_images),
            'missing_images': missing,
            'has_styles': 'styles.css' in names,
            'has_font': any(name.startswith('fonts/') for name in names),
        })
        for sample in ['愛', '食べる', '見る', '明日', 'あい']:
            result['samples'][sample] = sample in terms
        if missing:
            result['errors'].append(f'{len(missing)} referenced images are missing')
        if not result['has_styles']:
            result['errors'].append('styles.css is missing')
        if stats['terms'] == 0:
            result['errors'].append('no terms found')
    result['passed'] = not result['errors']
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
