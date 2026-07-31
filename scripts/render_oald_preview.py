import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


SAFE_TAGS = {
    'a',
    'br',
    'details',
    'div',
    'img',
    'li',
    'ol',
    'ruby',
    'rp',
    'rt',
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
VOID_TAGS = {'br', 'img'}
CAMEL_BOUNDARY = re.compile(r'(?<!^)(?=[A-Z])')


def style_name(name: str) -> str:
    return CAMEL_BOUNDARY.sub('-', name).lower()


def render_node(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return html.escape(value)
    if isinstance(value, list):
        return ''.join(render_node(item) for item in value)
    if not isinstance(value, dict):
        raise TypeError(f'unsupported structured-content value: {value!r}')

    tag = value.get('tag')
    if tag not in SAFE_TAGS:
        raise ValueError(f'unsupported tag: {tag!r}')
    attributes: list[str] = []
    for name, data_value in value.get('data', {}).items():
        attributes.append(
            f'data-sc-{html.escape(name, quote=True)}='
            f'"{html.escape(str(data_value), quote=True)}"'
        )
    for source_name, html_name in (
        ('href', 'href'),
        ('lang', 'lang'),
        ('title', 'title'),
        ('path', 'src'),
        ('colSpan', 'colspan'),
        ('rowSpan', 'rowspan'),
    ):
        attribute_value = value.get(source_name)
        if attribute_value is not None:
            attributes.append(
                f'{html_name}="{html.escape(str(attribute_value), quote=True)}"'
            )
    if value.get('open') is True:
        attributes.append('open')
    if value.get('style'):
        declarations = ';'.join(
            f'{style_name(name)}:{style_value}'
            for name, style_value in value['style'].items()
        )
        attributes.append(f'style="{html.escape(declarations, quote=True)}"')

    opening = f'<{tag}'
    if attributes:
        opening += f" {' '.join(attributes)}"
    opening += '>'
    if tag in VOID_TAGS:
        return opening
    return f"{opening}{render_node(value.get('content'))}</{tag}>"


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Render converted OALD entries into a standalone QA preview.'
    )
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--styles', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--term', action='append', dest='terms')
    parser.add_argument(
        '--expand-all',
        action='store_true',
        help='Open every details section for visual QA.',
    )
    parser.add_argument(
        '--dark',
        action='store_true',
        help='Render using Yomitan data-theme="dark".',
    )
    args = parser.parse_args()

    requested = set(args.terms or [])
    entries: list[tuple[str, Any]] = []
    with args.input.open(encoding='utf-8') as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            term = record.get('term')
            definition = record.get('definition')
            if (
                isinstance(term, str)
                and isinstance(definition, dict)
                and (not requested or term in requested)
            ):
                entries.append((term, definition.get('content')))

    found = {term for term, _ in entries}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"preview terms not found: {', '.join(missing)}")
    styles = args.styles.read_text(encoding='utf-8')
    cards = '\n'.join(
        (
            '<article class="dictionary-result">'
            '<div class="dictionary-label">'
            f'{index}. OALDPE En-Cn · {html.escape(term)}'
            '</div>'
            f'{render_node(content)}'
            '</article>'
        )
        for index, (term, content) in enumerate(entries, start=1)
    )
    document = f'''<!doctype html>
<html lang="zh-CN"{' data-theme="dark"' if args.dark else ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OALD Yomitan layout preview</title>
<style>
html {{ background: {'#181c20' if args.dark else '#eef1f4'}; }}
body {{
  color: {'#d4d4d4' if args.dark else '#202a31'};
  font-family: "Segoe UI", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  margin: 0 auto;
  max-width: 780px;
  padding: 24px 14px 80px;
}}
.dictionary-result {{
  background: {'#202428' if args.dark else 'white'};
  border: 1px solid {'#3b444b' if args.dark else '#d9dfe5'};
  border-radius: 12px;
  box-shadow: 0 4px 18px rgba(31, 48, 61, 0.08);
  margin: 0 0 24px;
  padding: 16px 18px;
}}
.dictionary-label {{
  background: #a85bd0;
  border-radius: 6px;
  color: white;
  display: inline-block;
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 12px;
  padding: 5px 9px;
}}
{styles}
</style>
</head>
<body>
{cards}
{'<script>document.querySelectorAll("details").forEach((detail) => { detail.open = true; });</script>' if args.expand_all else ''}
</body>
</html>
'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding='utf-8', newline='\n')
    print(
        json.dumps(
            {
                'preview': str(args.output),
                'entries': [term for term, _ in entries],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
