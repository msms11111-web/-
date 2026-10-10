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
    bare = len(re.findall(r"<th(?![^>]*scope=)", h))
    if bare:
        note("ترويسة بلا scope", page, f"{bare} خلية")

    # ٦) نصّ لاتيني داخل صفحة عربية بلا lang
    for m in re.finditer(r'<span dir="ltr"[^>]*>', h):
        if "lang=" not in m.group(0):
            note("لاتيني بلا lang", page, m.group(0)[:50])

    # ٧) المعالم الأساسية
    for landmark, pat in [("main", r"<main\b"), ("header", r"<header\b"), ("footer", r"<footer\b")]:
        if not re.search(pat, h):
            note("معلَم ناقص", page, landmark)

print(f"فُحصت {len(list(ROOT.rglob('*.html')))} صفحة.\n")
for line in detail:
    print(line)
print("\nالحصيلة:", dict(findings) if findings else "لا شيء")
raise SystemExit(1 if findings else 0)
