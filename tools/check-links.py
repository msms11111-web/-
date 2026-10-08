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


ENTITY = re.compile(
    r'<a class="entity"[^>]*href="\.\./([^"]*)"[^>]*>.*?'
    r'<span class="status (\w+)">([^<]*)</span>',
    re.S,
)
PAGE_STATUS = re.compile(r'class="status (\w+) status-link"')


def status_drift() -> list[str]:
    """شارة الفهرس يجب أن توافق حالة الصفحة نفسها.

    الفهرس يُحرَّر يدويًّا والحالة تُبنى من content/، فيفترقان بلا أثر ظاهر.
    وُجدت بطاقة تَعِد بـ«موثق» وصفحتها تقول «وصفة تأسيسية غير مختبرة»، وهو
    ادّعاءٌ في الواجهة تنفيه الصفحة — وأسوأ ما يصيب موسوعةً تقوم على حالات
    التوثيق أن تكذب فهرستها صفحاتها.
    """
    index = ROOT / "encyclopedia" / "index.html"
    if not index.exists():
        return []
    out = []
    for href, kind, label in ENTITY.findall(index.read_text(encoding="utf-8")):
        page = ROOT / href / "index.html"
        if not page.exists():
            continue
        found = PAGE_STATUS.search(page.read_text(encoding="utf-8"))
        if found and found.group(1) != kind:
            out.append(f"{href} ← الفهرس «{kind}» والصفحة «{found.group(1)}»")
    return out


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

    drift = status_drift()
    for item in drift:
        print(f"حالة متضاربة: {item}")

    print(
        f"فُحصت {len(pages)} صفحة، ووُجد {len(broken)} رابط مكسور"
        f"، و{len(dupes)} عنوانًا مكررًا، و{len(drift)} حالةً متضاربة."
    )
    return 1 if broken or dupes or drift else 0


if __name__ == "__main__":
    sys.exit(main())
