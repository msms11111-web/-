#!/usr/bin/env python3
"""يولّد روابط «اقرأ أيضًا» بين صفحات الموسوعة.

الاستخدام:
    python3 tools/relations.py

الموقع يَعِد في صفحته الرئيسية بأن يربط المعرفة بدل عرضها كجزر منفصلة، وكانت
الصفحات شبه معزولة. هنا تُعرَّف العلاقات صراحةً، ولكل علاقة سبب يوضح صلتها لا
رابط مجرد، فتكون شبكة معرفة لا قائمة «مواضيع ذات صلة».

العناوين تُقرأ من الصفحات نفسها، فلا تتكرر في مكانين ولا تفترق عند التعديل.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

START = "<!--qatra:rel-->"
END = "<!--/qatra:rel-->"
BLOCK = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)

# من صفحة ← إلى صفحة: سبب الصلة. الاتجاه مقصود: السبب يختلف باختلاف المنطلق.
RELATIONS: dict[str, list[tuple[str, str]]] = {
    "origins/ethiopia/": [
        ("regions/guji/", "منطقة داخل أوروميا، وأحد مواقع الإنتاج المنسوبة إلى إثيوبيا"),
        ("varieties/dega/", "اسم محلي يظهر على محاصيل إثيوبية، وهويته الوراثية غير محسومة"),
        ("origins/yemen/", "مركز الانتشار الثانوي الذي خرجت منه الأرابيكا المزروعة"),
        ("methodology/", "كيف تُصنَّف المعلومة في هذه الصفحة بين موثق ومعلن واستنتاجي"),
    ],
    "regions/guji/": [
        ("origins/ethiopia/", "الدولة التي تقع فيها المنطقة، ولا تُختزل فيها"),
        ("crops/guji-dega-natural/", "ملف محصول منسوب إلى هذه المنطقة، بحدود تتبع معلنة"),
        ("varieties/dega/", "الاسم المحلي الذي يرافق كثيرًا من محاصيل المنطقة"),
    ],
    "varieties/dega/": [
        ("regions/guji/", "المنطقة التي يتكرر فيها الاسم تجاريًا"),
        ("origins/ethiopia/", "السياق الوطني لأسماء السلالات المحلية"),
        ("crops/guji-dega-natural/", "محصول معلن بهذا الاسم، دون إثبات وراثي"),
    ],
    "processes/natural/": [
        ("crops/guji-dega-natural/", "محصول معالَج بهذه الطريقة، ببيانات تجفيف ناقصة"),
        ("roasting/", "خطوة لاحقة تكشف أثر المعالجة أو تطمسه"),
        ("brewing/v60/", "خطوة لاحقة تتأثر بالمعالجة ولا تُحدَّد بها وحدها"),
        ("methodology/", "لماذا لا تُنسب نكهة ثابتة إلى اسم معالجة"),
    ],
    "crops/guji-dega-natural/": [
        ("regions/guji/", "المنطقة المعلنة في بيانات المحمصة"),
        ("varieties/dega/", "السلالة المعلنة، وحدود ما يثبته الاسم"),
        ("processes/natural/", "المعالجة المعلنة، وما لا يحدده اسمها"),
        ("brewing/v60/", "الوصفة التأسيسية المرتبطة بهذا المحصول"),
    ],
    "brewing/v60/": [
        ("crops/guji-dega-natural/", "المحصول الذي وُضعت له هذه الوصفة"),
        ("processes/natural/", "المعالجة التي تسبق التحضير وتؤثر في الاستخلاص"),
        ("evaluation/", "كيف يُحكم على نتيجة الوصفة دون خلط الوصف بالحكم"),
        ("methodology/", "متى تنتقل وصفة من تأسيسية إلى معتمدة"),
    ],
    "roasting/": [
        ("processes/natural/", "ما يسبق التحميص ويحدّ ما يمكنه إظهاره"),
        ("brewing/v60/", "الخطوة التالية، وتتأثر بقابلية الاستخلاص بعد التحميص"),
        ("evaluation/", "كيف يُقاس أثر التحميص دون خلط الوصف بالحكم"),
    ],
    "evaluation/": [
        ("roasting/", "المرحلة التي يُقيَّم أثرها غالبًا"),
        ("brewing/v60/", "متى تنتقل وصفة من تأسيسية إلى معتمدة"),
        ("methodology/", "الفصل بين المُدرَك والمُفضَّل، وهو أصل التقييم"),
    ],
    "origins/yemen/": [
        ("origins/ethiopia/", "الموطن الطبيعي الذي خرجت منه الأرابيكا قبل اليمن"),
        ("saudi-coffee/khawlani/", "الجوار الجغرافي والزراعي عبر جبال الجزيرة"),
        ("varieties/dega/", "المشكلة نفسها: اسم محلي موثق لا يثبت هوية وراثية"),
    ],
    "saudi-coffee/khawlani/": [
        ("saudi-coffee/", "الجناح الذي يفصل البنّ المزروع عن الشراب والثقافة"),
        ("saudi-coffee/ritual/", "الوجه الآخر: القهوة شرابًا وأدب ضيافة"),
        ("origins/yemen/", "الجوار الذي تشترك معه المنطقة في تاريخ الزراعة الجبلية"),
    ],
    "saudi-coffee/ritual/": [
        ("saudi-coffee/khawlani/", "الوجه الآخر: البنّ المزروع في الأرض السعودية"),
        ("saudi-coffee/", "الجناح الذي يفصل المسارين"),
        ("roasting/", "التحميص هنا يجري أمام الضيوف، ويُقرأ بالمعنى التقني أيضًا"),
    ],
    "methodology/": [
        ("encyclopedia/", "الفهرس حيث تظهر حالة التوثيق بجانب كل مدخل"),
        ("origins/ethiopia/", "مثال مطبَّق: سجل تعارض مفتوح حول عدد الأصناف"),
        ("varieties/dega/", "مثال مطبَّق: حالة «غير محسوم» وما يلزم لإغلاقها"),
    ],
    "saudi-coffee/": [
        ("saudi-coffee/khawlani/", "البنّ المزروع في جازان، ومعارفه المُدرجة في اليونسكو"),
        ("saudi-coffee/ritual/", "القهوة شرابًا وأدب ضيافة، وعنصرًا مُدرجًا منذ 2015"),
        ("origins/yemen/", "الجوار الذي تشترك معه المنطقة في تاريخ القهوة"),
    ],
}


def title_of(path: str) -> str:
    file = ROOT / path / "index.html"
    if not file.exists():
        return ""
    html = file.read_text(encoding="utf-8")
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def relative(src: str, dst: str) -> str:
    return "../" * src.count("/") + dst


def block(src: str, targets: list[tuple[str, str]]) -> str:
    items = []
    for dst, why in targets:
        name = title_of(dst)
        if not name:
            continue
        items.append(
            f'<li><a href="{relative(src, dst)}">{name}</a><small>{why}</small></li>'
        )
    if not items:
        return ""
    return (
        f"{START}"
        f'<section class="section tight-rel"><div class="container">'
        f'<nav class="related" aria-labelledby="related-h">'
        f'<h2 id="related-h">اقرأ أيضًا</h2>'
        f'<ul>{"".join(items)}</ul></nav>'
        f"</div></section>"
        f"{END}"
    )


def place(html: str, markup: str) -> str:
    """في آخر المحتوى.

    لا يصلح الإدراج بعد «</article>»: المقال والشريط الجانبي عنصران في شبكة
    تخطيط واحدة، فيصير القسم عمودًا ثالثًا ويكسر الصفحة.
    """
    return html.replace("</main>", markup + "</main>", 1) if "</main>" in html else html


def main() -> int:
    linked = 0
    for src, targets in RELATIONS.items():
        file = ROOT / src / "index.html"
        if not file.exists():
            print(f"  تخطٍّ: {src} غير موجودة")
            continue
        html = BLOCK.sub("", file.read_text(encoding="utf-8"))
        markup = block(src, targets)
        if markup:
            html = place(html, markup)
            linked += 1
        file.write_text(html, encoding="utf-8")

    print(f"رُبطت {linked} صفحة بشبكة «اقرأ أيضًا».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
