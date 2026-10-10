# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""فحص بنيوي للصفحات المبنيّة.

الاستخدام:
    python3 tools/check-structure.py

يرصد ما لا يراه القارئ المبصر ولا يقيسه فاحص التباين: معرّفات مكررة تُفسد
المراسي، ومراسيَ بلا هدف، وعناوين وروابط فارغة، ورسومًا بلا اسم متاح،
وخلايا ترويسة بلا نطاق، ونصًّا لاتينيًّا داخل صفحة عربية بلا lang — فينطقه
القارئ الآلي بصوتٍ عربي فيخرج هذيانًا.

وُجد به أول مرة: 92 نصًّا لاتينيًّا بلا lang، و17 جدولًا بلا نطاق.
"""
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
findings = Counter()
detail = []


def note(kind, page, msg):
    findings[kind] += 1
    if len(detail) < 60:
        detail.append(f"  [{kind}] {page}: {msg}")


for p in sorted(ROOT.rglob("*.html")):
    page = p.relative_to(ROOT).as_posix()
    h = p.read_text(encoding="utf-8")

    # ١) معرّفات مكررة — تُفسد المراسي وتُبطل الصفحة
    ids = re.findall(r'\sid="([^"]+)"', h)
    for i, c in Counter(ids).items():
        if c > 1:
            note("معرّف مكرر", page, f"«{i}» ×{c}")

    # ٢) مرساة داخل الصفحة لا هدف لها
    for a in set(re.findall(r'href="#([^"]+)"', h)):
        if a and a not in ids:
            note("مرساة معطَّلة", page, f"#{a}")

    # ٣) عنوان أو رابط فارغ
    for tag in ["h1", "h2", "h3"]:
        for m in re.finditer(rf"<{tag}[^>]*>(.*?)</{tag}>", h, re.S):
            if not re.sub(r"<[^>]+>", "", m.group(1)).strip():
                note("عنوان فارغ", page, tag)
    for m in re.finditer(r"<a\s[^>]*>(.*?)</a>", h, re.S):
        inner = m.group(1)
        if not re.sub(r"<[^>]+>", "", inner).strip() and "aria-label" not in m.group(0):
            note("رابط بلا نصّ", page, m.group(0)[:60])

    # ٤) صورة أو رسم بلا اسم متاح
    for m in re.finditer(r"<img\s[^>]*>", h):
        if "alt=" not in m.group(0):
            note("صورة بلا بديل", page, m.group(0)[:60])
    for m in re.finditer(r"<svg\s[^>]*>", h):
        tag = m.group(0)
        if "aria-label" not in tag and "aria-labelledby" not in tag and 'aria-hidden="true"' not in tag:
            note("رسم بلا اسم", page, tag[:70])

    # ٥) كل خلية ترويسة على حدة. وفحصُ الجدول جملةً يمرّر خليةً واحدة
    #    ناقصة بين أخواتها السليمة، وهي بالضبط حالة التعديل اليدوي.
    # حدّ الكلمة ضروري: «<thead>» يبدأ بـ<th فيُحسب خليةً ناقصة بدونه،
    # وهو ما أوقع سكربت الإصلاح في تشويه كل وسوم thead في الموقع.
    bare = len(re.findall(r"<th(?=[\s>])(?![^>]*scope=)", h))
    if bare:
        note("ترويسة بلا scope", page, f"{bare} خلية")

    # ٦) وسمٌ مشوَّه: اسم العنصر ملتصق بسمة. نشأ من استبدال بلا حدّ كلمة،
    #    ويمرّ من كل الفحوص الأخرى لأنه يبدو وسمًا سليمًا فيه سمات.
    for m in re.finditer(r'<[a-z]+ [a-z-]+="[^"]*"[a-z]+>', h):
        note("وسم مشوَّه", page, m.group(0)[:50])

    # ٧) نصّ لاتيني داخل صفحة عربية بلا lang
    for m in re.finditer(r'<span dir="ltr"[^>]*>', h):
        if "lang=" not in m.group(0):
            note("لاتيني بلا lang", page, m.group(0)[:50])

    # ٨) المعالم الأساسية
    for landmark, pat in [("main", r"<main\b"), ("header", r"<header\b"), ("footer", r"<footer\b")]:
        if not re.search(pat, h):
            note("معلَم ناقص", page, landmark)

# ٩) وعدُ البطاقة: كل مرادف في data-entity يجب أن يوجد في نصّ صفحته.
#
# بطاقة الفهرس تَعِد القارئ بكلمات. فإن بحث عن كلمةٍ وعدتْه بها البطاقة ثم
# فتح الصفحة فلم يجدها، فالبطاقة كذبت عليه. وُجد هذا باليد لا بفحص، فصار فحصًا.
#
# حدٌّ معلوم: هنا تُحاكى قاعدتان من assets/app.js — الطيّ وحدّ الكلمة — فهما
# مكتوبتان مرتين وقد تتفرّقان. وتُقرأ المكافِئات من app.js نفسه لا تُنسخ،
# لأنها هي المتغيّرة باستمرار. وأيُّ تعديل في fold() هناك يُنقل هنا.
DIAC = re.compile(r"[ً-ْـ]")
LATIN = str.maketrans("áàâäãåéèêëíìîïóòôöõúùûüñçý", "aaaaaaeeeeiiiiooooouuuuncy")
PREFIX = re.compile(r"^[وفبكل]{0,2}(ال)?$")
WORDCH = re.compile(r"[0-9a-z؀-ۿ]")


def fold(s: str) -> str:
    out = []
    for c in s.lower().translate(LATIN):
        if DIAC.match(c):
            continue
        if c in "أإآٱ":
            c = "ا"
        elif c == "ى":
            c = "ي"
        elif c == "ة":
            c = "ه"
        elif c in "ؤئ":
            c = "ء"
        elif c.isspace():
            if not out or out[-1] == " ":
                continue
            c = " "
        else:
            d = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹".find(c)
            if d >= 0:
                c = str(d % 10)
        out.append(c)
    return "".join(out).strip()


def aliases() -> list[list[str]]:
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    block = re.search(r"const ALIASES = \[(.*?)\n  \]", js, re.S)
    if not block:
        return []
    return [
        [fold(w) for w in re.findall(r'"([^"]+)"', line)]
        for line in block.group(1).splitlines()
        if '"' in line
    ]


def at_word(hay: str, word: str) -> bool:
    """مطابقةٌ في بداية كلمة، والسوابق المتصلة (و/ف/ب/ك/ل وال) تُعدّ حدًّا."""
    i = hay.find(word)
    while i >= 0:
        start = i
        while start > 0 and WORDCH.match(hay[start - 1]):
            start -= 1
        if PREFIX.match(hay[start:i]):
            return True
        i = hay.find(word, i + 1)
    return False


def card_promises() -> None:
    index_file = ROOT / "assets" / "search-index.json"
    cards_file = ROOT / "encyclopedia" / "index.html"
    if not (index_file.exists() and cards_file.exists()):
        return
    import json

    haystack = {}
    for e in json.loads(index_file.read_text(encoding="utf-8")):
        haystack[e["url"].strip("/")] = fold(
            " ".join([e["title"], e["desc"], *e.get("headings", []), e.get("text", "")])
        )
    groups = aliases()
    cards = re.findall(
        r'<a class="entity" data-entity="([^"]*)"[^>]*href="\.\./([^"]*)"', cards_file.read_text(encoding="utf-8")
    )
    for promise, href in cards:
        hay = haystack.get(href.strip("/"))
        if hay is None:
            continue
        for word in {w for w in fold(promise).split(" ") if len(w) > 1}:
            forms = next((g for g in groups if word in g), [word])
            if not any(at_word(hay, f) for f in forms):
                note("وعدٌ لا يسنده نصّ", f"encyclopedia → {href}", f"«{word}»")


card_promises()

print(f"فُحصت {len(list(ROOT.rglob('*.html')))} صفحة.\n")
for line in detail:
    print(line)
print("\nالحصيلة:", dict(findings) if findings else "لا شيء")
raise SystemExit(1 if findings else 0)
