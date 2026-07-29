#!/usr/bin/env python3
"""يتحقق من أن كل رابط داخلي ومورد في الموقع يشير إلى ملف موجود.

الاستخدام:
    python3 tools/check-links.py

يخرج برمز 1 عند وجود رابط مكسور، ليوقف النشر في GitHub Actions.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://msms11111-web.github.io/-/"
BASE_PATH = "/" + SITE_URL.split("/", 3)[3]
REF = re.compile(r'(?:href|src)="([^"]+)"')


def resolve(page: Path, ref: str) -> Path | None:
    """يحوّل رابطًا إلى مسار على القرص، أو None إذا كان خارجيًا."""
    url = urlsplit(ref)
    if url.scheme or url.netloc or not url.path:
        return None
    path = url.path
    if path.startswith(BASE_PATH):
        target = ROOT / path[len(BASE_PATH) :]
    elif path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = page.parent / path
    return target


def main() -> int:
    broken = []
    pages = sorted(ROOT.rglob("*.html"))

    for page in pages:
        for ref in REF.findall(page.read_text(encoding="utf-8")):
            target = resolve(page, ref)
            if target is None:
                continue
            if not (target.exists() or (target / "index.html").exists()):
                broken.append(f"{page.relative_to(ROOT)} ← {ref}")

    for item in broken:
        print(f"رابط مكسور: {item}")

    print(f"فُحصت {len(pages)} صفحة، ووُجد {len(broken)} رابط مكسور.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
