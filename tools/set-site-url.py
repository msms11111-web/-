#!/usr/bin/env python3
"""يضبط عنوان الموقع النهائي في كل الملفات التي تحتاج رابطًا مطلقًا.

الاستخدام:
    python3 tools/set-site-url.py https://qatra.example/

يعيد كتابة: robots.txt، sitemap.xml، ووسوم canonical/Open Graph في كل صفحة،
وروابط صفحة 404 (التي يجب أن تكون مطلقة لأنها تُعرض من أي مسار).
السكربت آمن للتشغيل أكثر من مرة.
"""

import re
import sys
from datetime import date
from pathlib import Path

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


def page_url(base: str, path: str) -> str:
    return base + path


def meta_block(base: str, url: str, prefix: str) -> str:
    return (
        f"{START}"
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
        f'<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">'
        f"<noscript><style>.fade{{opacity:1;transform:none}}</style></noscript>"
        f"{END}"
    )


def patch_html(file: Path, base: str, url: str, prefix: str) -> None:
    html = file.read_text(encoding="utf-8")
    html = BLOCK.sub("", html)
    html = html.replace("</head>", meta_block(base, url, prefix) + "</head>", 1)
    file.write_text(html, encoding="utf-8")


def patch_404(base_path: str) -> None:
    """صفحة 404 تُعرض من أي مسار، فلا تصلح فيها الروابط النسبية."""
    file = ROOT / "404.html"
    html = file.read_text(encoding="utf-8")
    html = re.sub(r'(href|src)="(?!https?:|//|/|#|data:)([^"]+)"', rf'\1="{base_path}\2"', html)
    html = html.replace(f'href="{base_path}index.html"', f'href="{base_path}"')
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
        patch_html(file, base, page_url(base, path), "../" * depth)

    patch_html(ROOT / "404.html", base, base + "404.html", "")
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
