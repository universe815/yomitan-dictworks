import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from lxml import html
from mdict_utils.base.readmdict import MDX


def clean_key(value: bytes, encoding: str) -> str:
    return value.decode(encoding, errors='replace').strip('\x00\r\n ')


def sound_file(href: str) -> str | None:
    if not href.lower().startswith('sound://'):
        return None
    value = unquote(href[8:]).replace('\\', '/').rsplit('/', 1)[-1].strip()
    return value if value.lower().endswith('.mp3') else None


def class_tokens(element) -> set[str]:
    return set((element.get('class') or '').split())


def audio_name(element, *, example: bool) -> str:
    classes = class_tokens(element)
    accent = 'UK' if 'pron-uk' in classes else 'US' if 'pron-us' in classes else 'Audio'
    return f'OALD {accent} example' if example else f'OALD {accent}'


def audio_accent(element) -> str | None:
    classes = class_tokens(element)
    if 'pron-uk' in classes:
        return 'UK'
    if 'pron-us' in classes:
        return 'US'
    return None


def unique_sources(values: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    seen = set()
    for value in values:
        marker = (value['file'].casefold(), value['name'])
        if marker not in seen:
            seen.add(marker)
            result.append(value)
    return result


def extract_audio(source: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    try:
        document = html.fromstring(source)
    except Exception:
        return [], []

    all_sources = []
    for anchor in document.xpath("//a[starts-with(translate(@href, 'SOUND', 'sound'), 'sound://')]"):
        filename = sound_file(anchor.get('href') or '')
        if not filename:
            continue
        example = 'app' in class_tokens(anchor)
        source = {'file': filename, 'name': audio_name(anchor, example=example)}
        accent = audio_accent(anchor)
        if accent:
            source['accent'] = accent
        all_sources.append(source)

    # The main pronunciation block is a direct child of each webtop. This excludes
    # inflected-form tables nested under the collapse panel.
    headword_sources = []
    xpath = (
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' webtop ')]"
        "/*[contains(concat(' ', normalize-space(@class), ' '), ' phonetics ')]"
        "//a[starts-with(translate(@href, 'SOUND', 'sound'), 'sound://')]"
    )
    for anchor in document.xpath(xpath):
        filename = sound_file(anchor.get('href') or '')
        if filename:
            source = {'file': filename, 'name': audio_name(anchor, example=False)}
            accent = audio_accent(anchor)
            if accent:
                source['accent'] = accent
            headword_sources.append(source)

    return unique_sources(headword_sources), unique_sources(all_sources)


def resolve_redirect(key: str, direct: set[str], redirects: dict[str, str]) -> str | None:
    seen = set()
    current = key
    while current and current not in seen:
        if current in direct:
            return current
        seen.add(current)
        current = redirects.get(current, '')
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description='Build an OALD term-to-MDD audio index.')
    parser.add_argument('--mdx', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()

    mdx = MDX(str(args.mdx), '', False, None)
    stats: Counter[str] = Counter()
    terms: dict[str, dict[str, list[dict[str, str]]]] = {}
    redirects: dict[str, str] = {}

    for key_bytes, value_bytes in mdx.items():
        stats['records_seen'] += 1
        key = clean_key(key_bytes, mdx._encoding)
        source = value_bytes.decode(mdx._encoding, errors='replace').strip('\x00\r\n ')
        if source.startswith('@@@LINK='):
            redirects.setdefault(key, source.partition('=')[2].strip())
            stats['redirects_seen'] += 1
            continue

        headword, all_sources = extract_audio(source)
        if not headword and not all_sources:
            continue
        terms[key] = {'headword': headword, 'all': all_sources}
        stats['terms_with_audio'] += 1
        stats['headword_audio_links'] += len(headword)
        stats['all_audio_links'] += len(all_sources)
        if stats['records_seen'] % 10000 == 0:
            print(f"Scanned {stats['records_seen']:,} MDX records...", flush=True)

    direct = set(terms)
    resolved_redirects = {}
    for alias, target in redirects.items():
        if not alias or alias in direct:
            continue
        resolved = resolve_redirect(target, direct, redirects)
        if resolved:
            resolved_redirects[alias] = resolved

    payload = {
        'format': 1,
        'source': str(args.mdx),
        'terms': terms,
        'redirects': resolved_redirects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    headword_files = {item['file'].casefold() for entry in terms.values() for item in entry['headword']}
    all_files = {item['file'].casefold() for entry in terms.values() for item in entry['all']}
    report = {
        'source': str(args.mdx),
        'output': str(args.output),
        'stats': dict(stats),
        'direct_terms_with_audio': len(terms),
        'resolved_audio_redirects': len(resolved_redirects),
        'unique_headword_audio_files': len(headword_files),
        'unique_all_audio_files': len(all_files),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
