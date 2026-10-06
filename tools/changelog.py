#!/usr/bin/env python3
"""يملأ صفحة سجل التغييرات ويولّد تغذية Atom، من نفس بيانات المراجعات.

الاستخدام:
    python3 tools/changelog.py https://example.com/

يقرأ assets/revisions.json (ينتجه tools/revisions.py) ويكتب:
  changelog/index.html  — السجل الظاهر للقارئ
  feed.xml              — تغذية Atom لمتابعة تحديثات الموسوعة

السجل تنفيذ لسياسة التصحيح في منهج الموقع: لا تُعدَّل الصفحات بصمت.
"""

import html as esc
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

START = "<!--qatra:log-->"
END = "<!--/qatra:log-->"
BLOCK = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)

FEED_ENTRIES = 25


def titles() -> dict[str, str]:
    """عناوين الصفحات من الصفحات نفسها، فلا تتكرر في مكانين."""
    found = {}
    for file in sorted(ROOT.rglob("index.html")):
        url = file.relative_to(ROOT).as_posix()[: -len("index.html")]
        match = re.search(r"<h1[^>]*>(.*?)</h1>", file.read_text(encoding="utf-8"), re.S)
        if match:
            found[url] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()
    return found


def render_log(history: list[dict], names: dict[str, str]) -> str:
    rows = []
    for record in history:
        pages = "".join(
            f'<li><a href="../{page}">{esc.escape(names.get(page, page or "الرئيسية"))}</a></li>'
            for page in record["pages"]
        )
        rows.append(
            '<li class="entry">'
            f'<time datetime="{record["date"]}" dir="ltr">{record["date"]}</time>'
            f'<h2>{esc.escape(record["subject"])}</h2>'
            f'<ul class="touched">{pages}</ul>'
            f'<a class="commit" href="{esc.escape(record["commit"])}" '
            'target="_blank" rel="noopener noreferrer">'
            'عرض التغيير<span aria-hidden="true"> ↗</span></a>'
            "</li>"
        )
    return START + f'<ol class="log">{"".join(rows)}</ol>' + END


def render_feed(base: str, history: list[dict], names: dict[str, str]) -> str:
    updated = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    entries = []
    for record in history[:FEED_ENTRIES]:
        pages = "، ".join(names.get(p, p or "الرئيسية") for p in record["pages"])
        summary = esc.escape(f"الصفحات التي تغيّرت: {pages}")
        entries.append(
            "<entry>"
            f"<title>{esc.escape(record['subject'])}</title>"
            f'<link href="{base}changelog/"/>'
            f"<id>{esc.escape(record['commit'])}</id>"
            f"<updated>{record['date']}T00:00:00Z</updated>"
            f"<summary>{summary}</summary>"
            "</entry>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="ar">\n'
        "<title>قطرة — سجل التغييرات</title>\n"
        "<subtitle>تحديثات موسوعة القهوة العربية</subtitle>\n"
        f'<link href="{base}"/>\n'
        f'<link rel="self" href="{base}feed.xml"/>\n'
        f"<id>{base}</id>\n"
        f"<updated>{updated}</updated>\n"
        "<author><name>قطرة</name></author>\n"
        + "\n".join(entries)
        + "\n</feed>\n"
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    base = sys.argv[1]
    if not base.endswith("/"):
        base += "/"

    data_file = ROOT / "assets" / "revisions.json"
    if not data_file.exists():
        print("لا توجد بيانات مراجعات. شغّل tools/revisions.py أولًا.", file=sys.stderr)
        return 1

    data = json.loads(data_file.read_text(encoding="utf-8"))
    history = data.get("history", [])
    names = titles()

    page = ROOT / "changelog" / "index.html"
    if page.exists():
        source = page.read_text(encoding="utf-8")
        if BLOCK.search(source):
            page.write_text(BLOCK.sub(render_log(history, names), source), encoding="utf-8")
        else:
            print("تحذير: لم توجد علامة السجل في changelog/index.html", file=sys.stderr)

    (ROOT / "feed.xml").write_text(render_feed(base, history, names), encoding="utf-8")
    print(f"السجل: {len(history)} تغييرًا | التغذية: {min(len(history), FEED_ENTRIES)} مدخلًا.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
