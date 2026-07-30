import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from mdict_utils.base.readmdict import MDD
from mdict_utils.reader import get_record


RESOURCE_ALIASES = {
    # Renamed between this MDX and its companion MDD revision.
    'healthcare__gb_1.mp3': 'health_care_1_gb_2.mp3',
    'healthcare__us_5.mp3': 'health_care_1_us_1.mp3',
    'xhosas_1_gb_1.mp3': 'xhosa__gb_1.mp3',
    'xhosas_1_gb_2.mp3': 'xhosa__gb_2.mp3',
}


def normalize_resource(value: str) -> str:
    return unquote(value).replace('\\', '/').rsplit('/', 1)[-1].strip().casefold()


def resource_family(value: str) -> str:
    return re.sub(r'_\d+(?=(?:_rr)?\.mp3$)', '_*', normalize_resource(value))


def resource_number(value: str) -> int:
    match = re.search(r'_(\d+)(?=(?:_rr)?\.mp3$)', normalize_resource(value))
    return int(match.group(1)) if match else 999999


def normalize_accent(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r'[^a-z]', '', value.casefold())
    if normalized in {'uk', 'gb', 'bre', 'british', 'britishenglish'}:
        return 'UK'
    if normalized in {'us', 'usa', 'ame', 'american', 'americanenglish', 'na'}:
        return 'US'
    return None


def source_accent(item: dict[str, str]) -> str | None:
    accent = normalize_accent(item.get('accent'))
    if accent:
        return accent
    match = re.search(r'\b(UK|US)\b', item.get('name', ''), flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


class AudioLibrary:
    def __init__(self, index_path: Path, mdd_paths: list[Path], public_port: int):
        self.index = json.loads(index_path.read_text(encoding='utf-8'))
        self.terms = self.index['terms']
        self.redirects = self.index.get('redirects', {})
        self.folded_terms = {key.casefold(): key for key in self.terms}
        self.folded_redirects = {key.casefold(): value for key, value in self.redirects.items()}
        self.public_port = public_port
        self.mdds = []
        self.resources = {}
        self.resource_families = {}
        self.lock = threading.RLock()

        for mdd_path in mdd_paths:
            mdd = MDD(str(mdd_path), None)
            mdd_number = len(self.mdds)
            self.mdds.append(mdd)
            for position, (offset, key_bytes) in enumerate(mdd._key_list):
                filename = key_bytes.decode('utf-8', errors='replace')
                length = mdd._key_list[position + 1][0] - offset if position + 1 < len(mdd._key_list) else -1
                normalized = normalize_resource(filename)
                descriptor = (mdd_number, key_bytes, offset, length)
                self.resources.setdefault(normalized, descriptor)
                self.resource_families.setdefault(resource_family(normalized), []).append((
                    resource_number(normalized), normalized, descriptor,
                ))

        for values in self.resource_families.values():
            values.sort(key=lambda value: (value[0], value[1]))

    def resource_descriptor(self, filename: str):
        normalized = normalize_resource(filename)
        exact = self.resources.get(normalized)
        if exact:
            return exact
        renamed = self.resources.get(RESOURCE_ALIASES.get(normalized, ''))
        if renamed:
            return renamed
        # A small number of links in this MDX revision use an older numeric suffix
        # than the paired MDD. Fall back to the first same-name/accent variant.
        family = self.resource_families.get(resource_family(normalized), [])
        return family[0][2] if family else None

    def resolve_term(self, term: str) -> str | None:
        if term in self.terms:
            return term
        if term in self.redirects:
            return self.redirects[term]
        folded = term.casefold()
        return self.folded_terms.get(folded) or self.folded_redirects.get(folded)

    def sources(
        self,
        term: str,
        scope: str,
        accent: str | None = None,
    ) -> list[dict[str, str]]:
        resolved = self.resolve_term(term.strip())
        if not resolved:
            return []
        group = 'all' if scope == 'all' else 'headword'
        normalized_accent = normalize_accent(accent)
        result = []
        for item in self.terms[resolved].get(group, []):
            if normalized_accent and source_accent(item) != normalized_accent:
                continue
            filename = item['file']
            if not self.resource_descriptor(filename):
                continue
            result.append({
                'name': item['name'],
                'url': f"http://127.0.0.1:{self.public_port}/audio/{quote(filename, safe='')}",
            })
        return result

    def read_audio(self, filename: str) -> bytes | None:
        descriptor = self.resource_descriptor(filename)
        if not descriptor:
            return None
        mdd_number, key_bytes, offset, length = descriptor
        # mdict-utils opens the MDD for every record, but its decompressor is not
        # documented as thread-safe. Serialize reads to keep behavior predictable.
        with self.lock:
            return get_record(self.mdds[mdd_number], key_bytes, offset, length)


class Handler(BaseHTTPRequestHandler):
    server_version = 'OALDAudio/1.1'

    def send_common_headers(self, content_type: str, content_length: int) -> None:
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(content_length))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=86400')

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        library: AudioLibrary = self.server.library
        if parsed.path.startswith('/audio/'):
            filename = unquote(parsed.path[len('/audio/'):])
            content = library.read_audio(filename)
            if content is None:
                self.send_error(404, 'Audio resource not found')
                return
            self.send_response(200)
            self.send_common_headers('audio/mpeg', len(content))
            self.end_headers()
            self.wfile.write(content)
            return

        query = parse_qs(parsed.query)
        term = query.get('term', [''])[0]
        scope = query.get('scope', ['headword'])[0]
        accent = query.get('accent', query.get('user', [None]))[0]
        if term:
            payload = {
                'type': 'audioSourceList',
                'audioSources': library.sources(term, scope, accent),
            }
            content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_common_headers('application/json; charset=utf-8', len(content))
            self.end_headers()
            self.wfile.write(content)
            return

        content = (
            'OALD audio server is running. Use /?term=take, '
            '/?term=take&accent=UK, or /?term=take&accent=US'
        ).encode('utf-8')
        self.send_response(200)
        self.send_common_headers('text/plain; charset=utf-8', len(content))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    project = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description='Serve OALD MDD pronunciation audio to Yomitan.')
    parser.add_argument('--index', type=Path, default=project / 'generated' / 'oald-audio-index.json')
    parser.add_argument(
        '--mdd',
        type=Path,
        action='append',
        required=True,
        help='audio MDD path; repeat this option for companion MDD files',
    )
    parser.add_argument('--port', type=int, default=5051)
    parser.add_argument('--self-test', metavar='TERM')
    parser.add_argument(
        '--require-accent',
        action='append',
        choices=('UK', 'US'),
        default=[],
        help='with --self-test, require and read at least one source for this accent',
    )
    args = parser.parse_args()
    mdd_paths = args.mdd

    print('Loading audio index and MDD resource tables...', flush=True)
    library = AudioLibrary(args.index, mdd_paths, args.port)
    print(f"Ready: {len(library.terms):,} direct terms, {len(library.redirects):,} redirects, "
          f"{len(library.resources):,} MDD audio resources.", flush=True)

    if args.self_test:
        sources = library.sources(args.self_test, 'headword')
        if not sources:
            raise SystemExit(f'No headword audio found for {args.self_test!r}')
        tested_sources = []
        required_accents = args.require_accent or [
            accent
            for accent in ('UK', 'US')
            if library.sources(args.self_test, 'headword', accent)
        ]
        for accent in required_accents:
            accent_sources = library.sources(args.self_test, 'headword', accent)
            if not accent_sources:
                raise SystemExit(
                    f'No {accent} headword audio found for {args.self_test!r}'
                )
            source = accent_sources[0]
            filename = unquote(urlparse(source['url']).path.rsplit('/', 1)[-1])
            content = library.read_audio(filename)
            if (
                not content
                or not content.startswith(b'ID3')
                and content[:2] not in {b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'}
            ):
                raise SystemExit(
                    f'Audio self-test failed: {accent} resource is not recognizable MP3 data'
                )
            tested_sources.append({
                'accent': accent,
                'source': source,
                'audioBytes': len(content),
            })
        print(json.dumps({
            'term': args.self_test,
            'sources': sources,
            'testedSources': tested_sources,
        }, ensure_ascii=False, indent=2))
        return

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.library = library
    print(f'Listening on http://127.0.0.1:{args.port}/ (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
