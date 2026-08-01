"""Check dictionary CSS for selectors that break Hibiki-style scoping.

Hibiki prefixes dictionary selectors with ``[data-dictionary=...]``.  A
dictionary stylesheet must therefore consume inherited theme variables instead
of trying to reach the host's html/body/root element.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLESHEETS = (
    ROOT / "styles" / "oald.css",
    ROOT / "styles" / "onomatopoeia.css",
)


def main() -> int:
    errors: list[str] = []
    for stylesheet in STYLESHEETS:
        raw = stylesheet.read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
        if not re.search(r"var\(--text-color(?:[,)]|\s)", css):
            errors.append(f"{stylesheet.name}: missing inherited text-color variable")
        if not re.search(r"var\(--background-color(?:[,)]|\s)", css):
            errors.append(f"{stylesheet.name}: missing inherited background-color variable")
        forbidden = (
            "html[data-theme",
            "body[data-theme",
            ":root[data-theme",
            " & [data-sc-",
        )
        for token in forbidden:
            if token in css:
                errors.append(f"{stylesheet.name}: forbidden scoped selector {token!r}")
        if "@media (prefers-color-scheme: dark)" not in css:
            errors.append(f"{stylesheet.name}: missing standalone dark-mode fallback")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Hibiki CSS scope QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
