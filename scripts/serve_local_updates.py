import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "dictionaries.json"


def load_routes(output_dir: Path) -> dict[str, Path]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    routes: dict[str, Path] = {}
    for entry in catalog["dictionaries"]:
        distribution = entry["distribution"]
        if distribution["status"] != "personal":
            continue
        asset_name = distribution["assetName"]
        route = f"/{entry['id']}/{asset_name}"
        archive = (output_dir / asset_name).resolve()
        if not archive.is_file():
            raise FileNotFoundError(f"Missing archive for {entry['id']}: {archive}")
        routes[route] = archive
    return routes


def make_handler(routes: dict[str, Path]) -> type[BaseHTTPRequestHandler]:
    class UpdateHandler(BaseHTTPRequestHandler):
        server_version = "YomitanLocalUpdateServer/1.0"

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_common_headers()
            self.end_headers()

        def do_HEAD(self) -> None:
            self.serve_file(include_body=False)

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/health":
                body = b'{"ok":true}\n'
                self.send_response(200)
                self.send_common_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.serve_file(include_body=True)

        def serve_file(self, *, include_body: bool) -> None:
            route = unquote(urlparse(self.path).path)
            archive = routes.get(route)
            if archive is None:
                self.send_error(404, "Unknown dictionary archive")
                return

            size = archive.stat().st_size
            self.send_response(200)
            self.send_common_headers()
            content_type = mimetypes.guess_type(archive.name)[0] or "application/zip"
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'attachment; filename="{archive.name}"')
            self.end_headers()
            if include_body:
                with archive.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        self.wfile.write(chunk)

        def send_common_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Cache-Control", "no-cache")

        def log_message(self, format_string: str, *args: object) -> None:
            print(f"{self.address_string()} - {format_string % args}")

    return UpdateHandler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve personal Yomitan dictionary ZIPs from localhost."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory containing the built ZIP files.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    routes = load_routes(output_dir)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(routes))

    print(f"Serving {len(routes)} dictionary editions from {output_dir}")
    for route, archive in routes.items():
        print(f"http://{args.host}:{args.port}{route} -> {archive.name}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local update server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
