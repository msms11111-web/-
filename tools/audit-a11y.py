#!/usr/bin/env python3
"""تدقيق وصولية: تباين الألوان وترتيب العناوين وتسميات الحقول وأثر التركيز.

أداة صيانة محلية، ليست جزءًا من النشر. تحتاج خادمًا يعمل ومتصفحًا:

    python3 -m http.server 8099 &
    pip install playwright && playwright install chromium
    python3 tools/audit-a11y.py

تقرأ الخلفيات المتدرجة: تستخرج ألوان محطات التدرج وتحسب أسوأ حالة. بدون ذلك
يُحسب النص الفاتح على تدرّج أخضر داكن كأنه على خلفية فاتحة، فتظهر عشرات
الأخطاء الوهمية.

أثر التركيز يُفحص بالضغط الفعلي على Tab لا بنداء focus() البرمجي، لأن
‏:focus-visible لا يُفعَّل إلا بالتنقل بلوحة المفاتيح.
"""
import os
import sys
from playwright.sync_api import sync_playwright

PAGES = ["", "encyclopedia/", "origins/ethiopia/", "origins/yemen/", "origins/brazil/", "origins/colombia/", "origins/kenya/", "origins/indonesia/", "saudi-coffee/khawlani/", "saudi-coffee/ritual/", "origins/vietnam/", "varieties/caturra/", "varieties/timor-catimor/", "regions/guji/", "varieties/dega/", "varieties/typica-bourbon/", "varieties/geisha/", "species/arabica/", "species/canephora/",
         "processes/", "processes/natural/", "processes/washed/", "processes/honey/", "processes/anaerobic/", "brewing/espresso/", "brewing/turkish/", "crops/guji-dega-natural/", "roasting/", "evaluation/", "brewing/v60/", "methodology/",
         "science/caffeine/", "science/water/", "science/extraction/", "science/storage/", "science/diseases/",
         "saudi-coffee/", "changelog/", "404.html"]

AUDIT = r"""
() => {
  const lum = (c) => { const [r,g,b]=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});
    return .2126*r+.7152*g+.0722*b; };
  const nums = (s) => (s.match(/[\d.]+/g)||[]).map(Number);
  const parse = (s) => { const n=nums(s); return n.length>=3?n.slice(0,3):null; };
  const alphaOf = (s) => { const n=nums(s); return n.length>3?n[3]:1; };
  const ratio = (a,b) => { const l1=lum(a),l2=lum(b); return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05); };

  // كل ألوان الخلفية المحتملة: اللون الصريح ومحطات التدرجات
  // حدّ معلوم: الخلفية تُلتمس في الآباء فقط. نصٌّ فوق شكل SVG شقيق (مثل تسمية
  // داخل مستطيل ملوَّن) يُقاس على خلفية المقال لا على الشكل، فيخرج الرقم متفائلًا
  // أو متشائمًا. كل شكل فيه نص فوق تعبئة يحتاج قياسًا مستقلًا عند إضافته.
  const bgCandidates = (el) => {
    let e = el;
    while (e) {
      const cs = getComputedStyle(e);
      const out = [];
      const bc = cs.backgroundColor;
      if (bc && alphaOf(bc) > 0.55) out.push(parse(bc));
      const bi = cs.backgroundImage || "";
      (bi.match(/rgba?\([^)]+\)/g) || []).forEach(c => { if (alphaOf(c) > 0.55) out.push(parse(c)); });
      if (out.length) return out.filter(Boolean);
      e = e.parentElement;
    }
    return [[255,255,255]];
  };

  /* رابطٌ داخل الكلام لا يُفرَّق عنه إلا باللون يُخفي نفسه عن ثلاثة: من لا
     يميّز الألوان، ومن يقرأ في ضوء ساطع، ومن لا يخطر له أن الكلمة رابط.
     والتسطير علامةٌ لا تعتمد على البصر اللوني، فهو المطلوب هنا. */
  const plain = [];
  document.querySelectorAll('.article p a, .article li a, .article td a, .article blockquote a').forEach(a => {
    if (!a.textContent.trim() || a.getBoundingClientRect().width === 0) return;
    const cs = getComputedStyle(a);
    const ps = getComputedStyle(a.parentElement);
    const underlined = (cs.textDecorationLine || "").includes("underline");
    const bolder = parseInt(cs.fontWeight) > parseInt(ps.fontWeight);
    const bordered = parseFloat(cs.borderBottomWidth) > 0;
    if (!underlined && !bolder && !bordered)
      plain.push(a.textContent.trim().slice(0, 30));
  });
  const low = [];
  document.querySelectorAll('p,li,a,h1,h2,h3,h4,small,span,strong,td,th,button,label,mark,text').forEach(el => {
    const svg = el.ownerSVGElement != null;
    // نص SVG لا يملك offsetParent، وظهوره يُقاس بمساحته لا بذلك
    if (!el.textContent.trim()) return;
    if (svg ? el.getBoundingClientRect().width === 0 : el.offsetParent === null) return;
    if (el.querySelector('p,li,h1,h2,h3,h4,div,a')) return;
    const cs = getComputedStyle(el);
    // لون نص SVG في fill لا في color، فقراءة color تمرّره دون فحص
    const fg = parse(svg ? cs.fill : cs.color); if (!fg) return;
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
    const worst = Math.min(...bgCandidates(el).map(bg => ratio(fg, bg)));
    if (worst < need) low.push({t: el.textContent.trim().slice(0,30), tag: el.tagName,
                                r: +worst.toFixed(2), need, size: +size.toFixed(1)});
  });

  const heads = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]);
  const noLabel = [];
  document.querySelectorAll('input,select,textarea').forEach(i => {
    if (!(i.labels?.length || i.getAttribute('aria-label') || i.getAttribute('aria-labelledby')))
      noLabel.push(i.name || i.type);
  });
  return {plain, low, heads, noLabel};
}
"""

# :focus-visible لا يُفعَّل بنداء focus() البرمجي، فيُفحص بالتنقل الفعلي
ACTIVE = r"""
() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const cs = getComputedStyle(el);
  const ring = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
  const wrap = el.closest('.search');
  const viaWrap = wrap ? getComputedStyle(wrap).boxShadow !== 'none' : false;
  return {tag: el.tagName, text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30),
          ring: ring || viaWrap};
}
"""


def weak_focus(pg, steps=30):
    pg.click("body", position={"x": 5, "y": 5})
    weak = []
    for _ in range(steps):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(40)
        r = pg.evaluate(ACTIVE)
        if r and not r["ring"]:
            weak.append(f"{r['tag']} «{r['text']}»")
    return weak


with sync_playwright() as p:
    chrome = os.environ.get("CHROME_PATH")
    b = p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
    scheme = os.environ.get("SCHEME", "light")
    pg = b.new_page(viewport={"width": 1280, "height": 900}, color_scheme=scheme)
    print(f"— الوضع: {scheme}")
    totals = {"low": 0, "skips": 0, "labels": 0, "focus": 0, "links": 0}
    for path in PAGES:
        pg.goto(f"{os.environ.get('SITE', 'http://localhost:8099')}/{path}", wait_until="networkidle")
        pg.wait_for_timeout(400)
        r = pg.evaluate(AUDIT)
        skips = [f"h{a}→h{c}" for a, c in zip(r["heads"], r["heads"][1:]) if c > a + 1]
        weak = weak_focus(pg)
        totals["low"] += len(r["low"]); totals["skips"] += len(skips)
        totals["labels"] += len(r["noLabel"]); totals["focus"] += len(weak)
        totals["links"] += len(r["plain"])
        flags = []
        if r["low"]: flags.append(f"تباين:{len(r['low'])}")
        if skips: flags.append(f"عناوين:{skips}")
        if r["noLabel"]: flags.append(f"بلا تسمية:{r['noLabel']}")
        if weak: flags.append(f"تركيز غير مرئي:{len(weak)}")
        if r["plain"]: flags.append(f"روابط بلا علامة:{len(r['plain'])}")
        print(f"  /{path or '':26} {'سليم ✓' if not flags else ' | '.join(flags)}")
        for x in r["low"][:3]:
            print(f"      ↳ {x['tag']} «{x['t']}» {x['r']} < {x['need']}")
        for x in weak[:3]:
            print(f"      ↳ تركيز: {x}")
        for x in r["plain"][:3]:
            print(f"      ↳ رابط لا يُميَّز عن النصّ: «{x}»")
    print("\nالإجمالي:", totals)
    b.close()
