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
REF = re.compile(r'(?:href|src)="([^"]+)"')
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')


def base_path() -> str:
    """يستنتج مسار الموقع من وسم canonical، فلا يحتاج تعديلًا عند تغيير النطاق."""
    match = CANONICAL.search((ROOT / "index.html").read_text(encoding="utf-8"))
    return urlsplit(match.group(1)).path if match else "/"


BASE_PATH = base_path()


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


TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def duplicate_titles(pages: list[Path]) -> list[str]:
    """عنوانان متطابقان لصفحتين مختلفتين خطأٌ لا اختيار.

    صفحة جديدة تُنسخ من قالب ترث عنوانه، فحملت ثماني عشرة صفحة عنوان صفحة
    واحدة في تبويب المتصفح وفي نتائج البحث وبطاقة المشاركة. لم يظهر الخطأ لأن
    شيئًا لم يكن يفحصه.
    """
    seen: dict[str, list[str]] = {}
    for page in pages:
        match = TITLE.search(page.read_text(encoding="utf-8"))
        if not match:
            continue
        name = re.sub(r"\s+", " ", match.group(1)).strip()
        seen.setdefault(name, []).append(str(page.relative_to(ROOT)))
    return [
        f"{name} ← {', '.join(where)}" for name, where in seen.items() if len(where) > 1
    ]


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

    dupes = duplicate_titles(pages)
    for item in dupes:
        print(f"عنوان مكرر: {item}")

    print(
        f"فُحصت {len(pages)} صفحة، ووُجد {len(broken)} رابط مكسور"
        f"، و{len(dupes)} عنوانًا مكررًا."
    )
    return 1 if broken or dupes else 0


if __name__ == "__main__":
    sys.exit(main())
