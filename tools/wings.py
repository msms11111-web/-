#!/usr/bin/env python3
"""يبني شبكة «أجنحة الموسوعة» في الصفحة الرئيسية من محتوى الموقع نفسه.

الاستخدام:
    python3 tools/wings.py

نمت الموسوعة من عشر صفحات إلى ستٍّ وثلاثين، وبقيت الصفحة الرئيسية تعرض ما
كان. فكانت اثنتان وعشرون صفحة لا تُرى من الباب: لا من الرئيسية ولا من شريط
التنقل، وإنما من الفهرس وشبكة «اقرأ أيضًا» وحدهما.

وتُكتب الأجنحة هنا لا في HTML، وتُحصى صفحاتها آليًّا: عددٌ مكتوب باليد يصير
كذبًا في أول إضافة، كما صار عنوان «منهج قطرة» على ثماني عشرة صفحة.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

START = "<!--qatra:wings-->"
END = "<!--/qatra:wings-->"
BLOCK = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)

# (المدخل، الاسم، الوصف، البادئات التي تُحسب ضمن الجناح)
WINGS = [
    ("origins/ethiopia/", "المناشئ",
     "أرضٌ ومناخ واقتصاد، لا نكهة تُنسب إلى بلد.",
     ("origins/",)),
    ("species/arabica/", "الأنواع والسلالات",
     "ما تعنيه أسماء النباتات، وما لا تعنيه على العبوة.",
     ("species/", "varieties/", "regions/")),
    ("processes/", "عائلة المعالجات",
     "أيُّ طبقة من الثمرة تُنزع، ومتى تُنزع.",
     ("processes/",)),
    ("roasting/", "التحميص والتحضير",
     "من الحرارة إلى الاستخلاص، ثم إلى الحكم.",
     ("roasting", "evaluation", "brewing/")),
    ("science/water/", "العلم",
     "الماء والاستخلاص والكافيين والتخزين وأمراض البن.",
     ("science/",)),
    ("saudi-coffee/", "القهوة السعودية",
     "البنّ المزروع في جازان، والدلة والفنجان.",
     ("saudi-coffee",)),
]


def pages() -> list[str]:
    out = []
    for file in CONTENT.glob("*.json"):
        out.append(json.loads(file.read_text(encoding="utf-8"))["path"].strip("/") + "/")
    return out


def count(prefixes: tuple[str, ...], all_pages: list[str]) -> int:
    return sum(
        1 for p in all_pages if any(p.startswith(x.strip("/") + "/") or p.strip("/") == x.strip("/") for x in prefixes)
    )


def counted(n: int) -> str:
    """تمييز العدد في العربية: مفردٌ للواحد، مثنًّى للاثنين، جمعٌ من ثلاثة إلى
    عشرة، ثم مفردٌ منصوب فيما فوقها. وكتابة «6 صفحة» خطأ يراه كل قارئ عربي."""
    if n == 1:
        return "صفحة واحدة"
    if n == 2:
        return "صفحتان"
    if 3 <= n <= 10:
        return f"{n} صفحات"
    return f"{n} صفحة"


def build() -> str:
    all_pages = pages()
    cards = []
    for href, name, note, prefixes in WINGS:
        n = count(prefixes, all_pages)
        cards.append(
            f'<a class="card fade" href="{href}">'
            f'<span class="num">{counted(n)}</span>'
            f"<h3>{name}</h3><p>{note}</p></a>"
        )
    return (
        f"{START}"
        f'<section class="tight" id="wings"><div class="container">'
        f'<div class="head fade"><div>'
        f'<span class="kicker" style="color:var(--gold-ink);border-color:var(--lead-line)">'
        f"أجنحة الموسوعة</span><h2>أين تبدأ؟</h2></div>"
        f"<p>الموسوعة ليست قائمة مقالات، بل أجنحة يحيل بعضها إلى بعض. "
        f'وكل مدخل فيها يحمل حالة توثيقه ظاهرةً، على ما يشرحه <a href="methodology/">المنهج</a>.</p>'
        f'</div><div class="grid g3">{"".join(cards)}</div></div></section>'
        f"{END}"
    )


def main() -> int:
    index = ROOT / "index.html"
    html = BLOCK.sub("", index.read_text(encoding="utf-8"))
    markup = build()
    anchor = '<section class="tight"><div class="container"><div class="head fade"><div><span class="kicker"'
    if anchor in html:
        html = html.replace(anchor, markup + anchor, 1)
    elif "</main>" in html:
        html = html.replace("</main>", markup + "</main>", 1)
    index.write_text(html, encoding="utf-8")
    print(f"بُنيت شبكة الأجنحة: {len(WINGS)} أجنحة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
