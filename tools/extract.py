#!/usr/bin/env python3
"""يفصل محتوى صفحات الموسوعة عن قالبها، مرة واحدة.

الاستخدام:
    python3 tools/extract.py

يقرأ صفحات المداخل الثمانية ويكتب لكل واحدة ملفًا في content/، ثم يتحقق
فورًا بأن tools/render.py يعيد بناء الصفحة كما هي حرفًا بحرف. إن اختلفت،
يتوقف ولا يكتب شيئًا: فصل المحتوى لا يجوز أن يغيّر ما يراه القارئ.

الصفحات البنيوية (الرئيسية، الفهرس، السجل، 404) تبقى في القالب، فمحتواها
بنية لا نصًّا يُحرَّر.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content"

PAGES = [
    "origins/ethiopia",
    "regions/guji",
    "varieties/dega",
    "processes/natural",
    "crops/guji-dega-natural",
    "brewing/v60",
    "methodology",
    "saudi-coffee",
]

GENERATED = [
    re.compile(r"<!--qatra:meta-->.*?<!--/qatra:meta-->", re.S),
    re.compile(r"<!--qatra:rev-->.*?<!--/qatra:rev-->", re.S),
    re.compile(r"<!--qatra:rel-->.*?<!--/qatra:rel-->", re.S),
]


def strip_generated(html: str) -> str:
    for pattern in GENERATED:
        html = pattern.sub("", html)
    return html


def extract(path: str) -> dict:
    html = strip_generated((ROOT / path / "index.html").read_text(encoding="utf-8"))

    meta = lambda name: (
        re.search(rf'<meta name="{name}" content="([^"]*)"', html).group(1)
    )

    hero = re.search(r'<section class="page-hero">(.*?)</section>', html, re.S).group(1)
    crumbs = re.search(r'<div class="crumbs">(.*?)</div>', hero, re.S).group(1)
    status = re.search(
        r'<(?:a|span) class="status (\w+)[^"]*"[^>]*>([^<]+)</(?:a|span)>', hero
    )
    title = re.search(r"<h1>(.*?)</h1>", hero, re.S).group(1)
    lead = re.search(r"<h1>.*?</h1>\s*<p>(.*?)</p>", hero, re.S).group(1)

    article = re.search(
        r'<article class="article">(.*?)</article>', html, re.S
    ).group(1)
    side = re.search(r'<aside class="side">(.*?)</aside>', html, re.S).group(1)
    nav = dict(re.findall(r'<a href="#([^"]+)">([^<]+)</a>', side))

    parts = re.split(r'<h2 id="([^"]+)">(.*?)</h2>', article, flags=re.S)
    sections = []
    for i in range(1, len(parts), 3):
        anchor, heading, body = parts[i], parts[i + 1], parts[i + 2]
        sections.append(
            {
                "id": anchor,
                "heading": heading,
                "nav": nav.get(anchor, heading),
                "body": body,
            }
        )

    return {
        "slug": path.replace("/", "--"),
        "path": path,
        "title": title,
        "description": meta("description"),
        "lead": lead,
        "status": {"kind": status.group(1), "label": status.group(2)} if status else None,
        "crumbs": [
            {"label": label, "href": href}
            for href, label in re.findall(r"""<a href=['"]([^'"]+)['"]>([^<]+)</a>""", crumbs)
        ],
        # الفتات الأخير قد يختلف عن العنوان: «ملف المحصول» مقابل «قوجي — ديجا — مجففة»
        "crumb_current": (re.search(r"<b>(.*?)</b>", crumbs, re.S) or re.match("(x)", "x")).group(1),
        "sections": sections,
        "lede_before_sections": parts[0],
    }


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    from render import render  # noqa: E402

    extracted = {}
    for path in PAGES:
        data = extract(path)
        original = strip_generated((ROOT / path / "index.html").read_text(encoding="utf-8"))
        rebuilt = render(data, original)
        if rebuilt != original:
            for i, (a, b) in enumerate(zip(original, rebuilt)):
                if a != b:
                    print(f"✗ {path}: اختلاف عند {i}", file=sys.stderr)
                    print(f"  الأصل:  …{original[max(0,i-70):i+70]!r}", file=sys.stderr)
                    print(f"  المولَّد: …{rebuilt[max(0,i-70):i+70]!r}", file=sys.stderr)
                    break
            else:
                print(f"✗ {path}: الأطوال مختلفة {len(original)} ≠ {len(rebuilt)}", file=sys.stderr)
            return 1
        extracted[path] = data

    OUT.mkdir(exist_ok=True)
    for path, data in extracted.items():
        name = path.replace("/", "--") + ".json"
        (OUT / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    print(f"فُصل محتوى {len(extracted)} صفحة، وكلها تُبنى كما هي حرفًا بحرف.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
