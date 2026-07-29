#!/usr/bin/env python3
"""يضبط عنوان الموقع النهائي في كل الملفات التي تحتاج رابطًا مطلقًا.

الاستخدام:
    python3 tools/set-site-url.py https://qatra.example/

يعيد كتابة: robots.txt، sitemap.xml، ووسوم canonical/Open Graph في كل صفحة،
وروابط صفحة 404 (التي يجب أن تكون مطلقة لأنها تُعرض من أي مسار).
السكربت آمن للتشغيل أكثر من مرة.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    ("", "الرئيسية"),
    ("encyclopedia/", "فهرس الموسوعة"),
    ("origins/ethiopia/", "إثيوبيا"),
    ("regions/guji/", "قوجي"),
    ("varieties/dega/", "ديجا"),
    ("processes/natural/", "المعالجة المجففة"),
    ("crops/guji-dega-natural/", "قوجي — ديجا — مجففة"),
    ("brewing/v60/", "وصفة V60"),
    ("methodology/", "منهج قطرة"),
    ("saudi-coffee/", "القهوة السعودية"),
]

# كل ما يضيفه السكربت يوضع بين هذين العلامتين ليمكن استبداله لاحقًا
START = "<!--qatra:meta-->"
END = "<!--/qatra:meta-->"
BLOCK = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)

# يسجل الأساس المطبَّق على صفحة 404، ليُزال قبل تطبيق أساس جديد
BASE_MARK = re.compile(r"<!--qatra:base=([^>]*)-->")


def page_url(base: str, path: str) -> str:
    return base + path


def json_ld(base: str) -> str:
    """بيانات منظمة للصفحة الرئيسية. تُولَّد هنا كي لا تتعارض مع canonical."""
    return (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"WebSite",'
        '"name":"قطرة","alternateName":"موسوعة القهوة العربية",'
        '"description":"موسوعة عربية عالمية تروي رحلة القهوة من الأرض إلى الكوب.",'
        f'"url":"{base}","inLanguage":"ar",'
        '"potentialAction":{"@type":"SearchAction",'
        f'"target":{{"@type":"EntryPoint","urlTemplate":"{base}encyclopedia/?q={{search_term_string}}"}},'
        '"query-input":"required name=search_term_string"}}'
        "</script>"
    )


def meta(html: str, name: str) -> str:
    match = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    return match.group(1) if match else ""


def text_of(html: str, pattern: str) -> str:
    """نص أول مطابقة بعد إزالة الوسوم."""
    match = re.search(pattern, html, re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def breadcrumbs(url: str, html: str) -> list[dict]:
    """مسار التنقل مأخوذ من فتات الصفحة الظاهر، لا مُخمَّنًا من المسار."""
    block = re.search(r'<div class="crumbs">(.*?)</div>', html, re.S)
    if not block:
        return []
    items = []
    for link, name in re.findall(r"""<a href=['"]([^'"]+)['"]>([^<]+)</a>""", block.group(1)):
        target = urljoin(url, link)
        if target.endswith("/index.html"):
            target = target[: -len("index.html")]
        items.append({"name": name.strip(), "item": target})
    current = re.search(r"<b>([^<]+)</b>", block.group(1))
    if current:
        items.append({"name": current.group(1).strip(), "item": url})
    return items


def page_schema(base: str, url: str, path: str, html: str) -> str:
    """مقال موسوعي ومسار تنقل لكل صفحة محتوى."""
    title = text_of(html, r"<h1[^>]*>(.*?)</h1>") or text_of(html, r"<title>(.*?)</title>")
    kind = "CollectionPage" if path == "encyclopedia/" else "Article"

    blocks = [
        {
            "@context": "https://schema.org",
            "@type": kind,
            "headline": title,
            "name": title,
            "description": meta(html, "description"),
            "url": url,
            "inLanguage": "ar",
            "isPartOf": {"@type": "WebSite", "name": "قطرة", "url": base},
        }
    ]

    trail = breadcrumbs(url, html)
    if trail:
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "name": c["name"], "item": c["item"]}
                    for i, c in enumerate(trail, 1)
                ],
            }
        )

    return "".join(
        '<script type="application/ld+json">'
        + json.dumps(b, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
        for b in blocks
    )


def meta_block(
    base: str, url: str, prefix: str, home: bool = False, schema: str = "", noindex: bool = False
) -> str:
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return (
        f"{START}"
        f"{json_ld(base) if home else schema}"
        f"{robots}"
        f'<link rel="canonical" href="{url}">'
        f'<meta property="og:url" content="{url}">'
        f'<meta property="og:site_name" content="قطرة">'
        f'<meta property="og:locale" content="ar_SA">'
        f'<meta property="og:image" content="{base}assets/og-image.png">'
        f'<meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630">'
        f'<meta property="og:image:alt" content="قطرة — موسوعة القهوة العربية">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{base}assets/og-image.png">'
        # بدون تحميل مسبق يُرسم النص بخط بديل ثم يقفز عند وصول الخط، فينزاح
        # التصميم (قيس 0.0627 قبل، و0.0001 بعد). crossorigin لازم للخطوط
        # حتى على النطاق نفسه.
        f'<link rel="preload" href="{prefix}assets/fonts/amiri-700.woff2" as="font" type="font/woff2" crossorigin>'
        f'<link rel="preload" href="{prefix}assets/fonts/plex-ar-400.woff2" as="font" type="font/woff2" crossorigin>'
        f'<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">'
        f"<noscript><style>.fade{{opacity:1;transform:none}}</style></noscript>"
        f"{END}"
    )


def patch_html(
    file: Path, base: str, url: str, prefix: str, home: bool = False, path: str = "", noindex: bool = False
) -> None:
    html = file.read_text(encoding="utf-8")
    html = BLOCK.sub("", html)
    # صفحة 404 ليست مقالًا، فلا مخطط لها
    schema = "" if home or noindex else page_schema(base, url, path, html)
    block = meta_block(base, url, prefix, home, schema, noindex)
    html = html.replace("</head>", block + "</head>", 1)
    file.write_text(html, encoding="utf-8")


def patch_404(base_path: str) -> None:
    """صفحة 404 تُعرض من أي مسار، فلا تصلح فيها الروابط النسبية.

    يُسجَّل الأساس المطبَّق داخل الصفحة، لتُعاد الروابط إلى صيغتها النسبية
    قبل تطبيق أساس جديد. بدون ذلك يتراكم الأساس القديم عند تغيير النطاق.
    """
    file = ROOT / "404.html"
    html = file.read_text(encoding="utf-8")

    previous = BASE_MARK.search(html)
    if previous:
        old = previous.group(1)
        html = re.sub(
            rf'(href|src)="{re.escape(old)}([^"]*)"',
            lambda m: f'{m.group(1)}="{m.group(2) or "index.html"}"',
            html,
        )
        html = BASE_MARK.sub("", html)

    html = re.sub(r'(href|src)="(?!https?:|//|/|#|data:)([^"]+)"', rf'\1="{base_path}\2"', html)
    html = html.replace(f'href="{base_path}index.html"', f'href="{base_path}"')
    html = html.replace("</head>", f"<!--qatra:base={base_path}--></head>", 1)
    file.write_text(html, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    base = sys.argv[1]
    if not base.startswith(("http://", "https://")):
        print("العنوان يجب أن يبدأ بـ http:// أو https://")
        return 1
    if not base.endswith("/"):
        base += "/"
    base_path = "/" + base.split("/", 3)[3] if len(base.split("/", 3)) > 3 else "/"

    for path, _ in PAGES:
        file = ROOT / path / "index.html"
        depth = path.count("/")
        patch_html(file, base, page_url(base, path), "../" * depth, home=(path == ""), path=path)

    # الخادم يردّ 404 فلا تُفهرس عادةً، لكنها ملف حقيقي يردّ 200 لمن يطلبه مباشرة
    patch_html(ROOT / "404.html", base, base + "404.html", "", noindex=True)
    patch_404(base_path)

    today = date.today().isoformat()
    urls = "\n".join(
        f"  <url><loc>{page_url(base, p)}</loc><lastmod>{today}</lastmod></url>" for p, _ in PAGES
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n", encoding="utf-8"
    )

    print(f"تم ضبط الموقع على: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
