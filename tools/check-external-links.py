#!/usr/bin/env python3
"""يتحقق أن كل مصدر خارجي مُحال إليه في الموقع ما زال يستجيب.

الاستخدام:
    python3 tools/check-external-links.py

يُشغَّل في GitHub Actions لأن بيئة التطوير قد لا تصل إلى الإنترنت.
الخروج برمز 1 عند وجود رابط ميت، ورمز 0 مع تنبيه عند تعذّر الوصول للشبكة
أصلًا — فرق مهم: موقع ميت خطأ، وشبكة محجوبة ليست خطأ في الموقع.

بعض المواقع ترفض HEAD أو ترفض العملاء غير المتصفحات، فتُعاد المحاولة بـ GET
وترويسة User-Agent، ويُقبل أي رد يعني أن العنوان موجود.
"""

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r'href="(https?://[^"]+)"')
UA = "Mozilla/5.0 (compatible; QatraLinkCheck/1.0; +https://github.com/msms11111-web/qatra)"
TIMEOUT = 25

# ردود تعني أن العنوان موجود لكن الخادم يمانع الفحص الآلي
TOLERATED = {401, 403, 405, 406, 429, 999}


def probe(url: str, method: str) -> int:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status


def check(url: str) -> tuple[str, str]:
    """يعيد (الحالة، التفصيل): ok أو tolerated أو dead أو unreachable."""
    last = ""
    for method in ("HEAD", "GET"):
        try:
            status = probe(url, method)
            return ("ok", str(status))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in TOLERATED:
                return ("tolerated", last)
            if method == "GET":
                return ("dead", last)
        except urllib.error.URLError as e:
            last = f"شبكة: {e.reason}"
        except Exception as e:  # مهلة أو TLS أو ما شابه
            last = f"{type(e).__name__}: {e}"
    return ("unreachable", last)


def own_origin() -> str:
    """أصل الموقع نفسه، ليُستثنى: canonical و og:url ليست مصادر خارجية."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<link rel="canonical" href="(https?://[^/"]+)', home)
    return match.group(1) if match else ""


def main() -> int:
    mine = own_origin()
    urls: dict[str, set[str]] = {}
    for page in sorted(ROOT.rglob("*.html")):
        for url in LINK.findall(page.read_text(encoding="utf-8")):
            if mine and url.startswith(mine):
                continue
            urls.setdefault(url, set()).add(page.relative_to(ROOT).as_posix())

    if not urls:
        print("لا توجد روابط خارجية.")
        return 0

    dead, unreachable = [], []
    for url in sorted(urls):
        state, detail = check(url)
        marks = {"ok": "✓", "tolerated": "~", "dead": "✗", "unreachable": "?"}
        print(f"  {marks[state]} {detail:22} {url}")
        if state == "dead":
            dead.append((url, detail, sorted(urls[url])))
        elif state == "unreachable":
            unreachable.append((url, detail))

    print(f"\nفُحص {len(urls)} رابطًا خارجيًا.")

    for url, detail, pages in dead:
        print(f"رابط ميت: {url} ({detail}) في {', '.join(pages)}", file=sys.stderr)

    if dead:
        return 1

    if unreachable:
        print(
            f"تعذّر الوصول إلى {len(unreachable)} رابط. لم يُحكم عليها بالموت: "
            "قد تكون الشبكة محجوبة في هذه البيئة.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
