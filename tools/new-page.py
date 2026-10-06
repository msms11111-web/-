#!/usr/bin/env python3
"""ينشئ صفحة مدخل جديدة بقالب الموقع، فارغةً من المحتوى.

الاستخدام:
    python3 tools/new-page.py roasting "التحميص"

ينسخ القالب (الترويسة والتذييل والتنقل والتذييل) من صفحة قائمة، فلا يتفرّق
القالب بين الصفحات، ثم ينشئ ملف محتوى في content/ يملؤه tools/render.py.

المحتوى يُكتب بعدها في content/<slug>.json أو من لوحة التحرير.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = "methodology"

GENERATED = [
    re.compile(r"<!--qatra:meta-->.*?<!--/qatra:meta-->", re.S),
    re.compile(r"<!--qatra:rev-->.*?<!--/qatra:rev-->", re.S),
    re.compile(r"<!--qatra:rel-->.*?<!--/qatra:rel-->", re.S),
]


def retarget(html: str, depth_from: int, depth_to: int) -> str:
    """يصحّح عمق الروابط النسبية عند اختلاف عمق الصفحة عن القالب."""
    if depth_from == depth_to:
        return html
    old, new = "../" * depth_from, "../" * depth_to
    return re.sub(rf'((?:href|src)=["\']){re.escape(old)}', rf"\1{new}", html)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    path, title = sys.argv[1].strip("/"), sys.argv[2]

    target = ROOT / path / "index.html"
    if target.exists():
        print(f"{path} موجودة بالفعل.", file=sys.stderr)
        return 1

    html = (ROOT / TEMPLATE / "index.html").read_text(encoding="utf-8")
    for pattern in GENERATED:
        html = pattern.sub("", html)
    html = retarget(html, TEMPLATE.count("/") + 1, path.count("/") + 1)
    html = html.replace('class="active"', 'class=""')

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

    slug = path.replace("/", "--")
    up = "../" * (path.count("/") + 1)
    content = {
        "slug": slug,
        "path": path,
        "title": title,
        "description": "",
        "lead": "",
        "status": {"kind": "research", "label": "قيد البناء"},
        "crumbs": [
            {"label": "الرئيسية", "href": f"{up}index.html"},
            {"label": "الموسوعة", "href": f"{up}encyclopedia/"},
        ],
        "crumb_current": title,
        "sections": [],
        "lede_before_sections": "",
    }
    (ROOT / "content" / f"{slug}.json").write_text(
        json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"أُنشئت {path}/ — اكتب محتواها في content/{slug}.json ثم شغّل البناء.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
