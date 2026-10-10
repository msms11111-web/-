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
        ("species/arabica/", "النوع الذي تحتفظ إثيوبيا بأوسع تنوع له"),
        ("origins/yemen/", "مركز الانتشار الثانوي الذي خرجت منه الأرابيكا المزروعة"),
        ("origins/kenya/", "منشأ انتُخبت فيه سلالات من قاعدة التنوع الإثيوبية الضيقة"),
        ("methodology/", "كيف تُصنَّف المعلومة في هذه الصفحة بين موثق ومعلن واستنتاجي"),
    ],
    "origins/brazil/": [
        ("origins/colombia/", "منشأ مجاور في الحجم، ومختلف عنه في بنية الحيازة"),
        ("origins/vietnam/", "المنتج الثاني عالميًّا، بلغ موقعه في جيل واحد"),
        ("varieties/caturra/", "طفرة رُصدت في ميناس جيرايس وغيّرت القارة"),
        ("species/arabica/", "النوع الذي يقوم عليه أغلب إنتاجه"),
        ("species/canephora/", "النوع الثاني في إنتاجه، ويُعرف محليًا بالكونيلون"),
        ("processes/natural/", "المعالجة السائدة فيه، بسبب المناخ لا بسبب تفضيل حسي"),
        ("evaluation/", "لماذا لا يُقرأ حجم الإنتاج ولا المكننة حكمًا على الجودة"),
    ],
    "origins/colombia/": [
        ("origins/brazil/", "منشأ مجاور في الحجم، ومختلف عنه في بنية الحيازة"),
        ("processes/washed/", "المعالجة السائدة فيه تاريخيًا"),
        ("varieties/typica-bourbon/", "المجموعتان التي تنحدر منهما سلالاته المطوَّرة"),
        ("varieties/timor-catimor/", "النسب الذي جاءت منه كاستيو"),
        ("science/diseases/", "صدأ الأوراق الذي أعاد تشكيل زراعته"),
        ("saudi-coffee/khawlani/", "المقارنة بين إدراج موقع في التراث العالمي وإدراج معارف في القائمة التمثيلية"),
    ],
    "origins/kenya/": [
        ("varieties/typica-bourbon/", "المجموعة التي انتُخبت منها SL28 وSL34"),
        ("origins/ethiopia/", "قاعدة التنوع التي خرجت منها السلالات المنتخبة"),
        ("processes/washed/", "المعالجة السائدة فيه، ونظام الفرز المرتبط بها"),
        ("evaluation/", "لماذا لا تدل درجات AA وAB على الجودة بل على الحجم"),
        ("science/diseases/", "الأمراض التي دفعت إلى رويرو ١١ وباتيان"),
    ],
    "origins/indonesia/": [
        ("species/canephora/", "النوع الذي يغلب على إنتاجه"),
        ("processes/washed/", "الأصل الذي يتفرع منه التقشير الرطب"),
        ("processes/", "موضع التقشير الرطب في جدول المعالجات"),
        ("processes/natural/", "الطرف الآخر الذي يفارقه التقشير الرطب كذلك"),
        ("methodology/", "لماذا تُستبعد قهوة الزباد من المعرفة القهوية في هذا الموقع"),
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
    "processes/": [
        ("processes/natural/", "الطرف الذي تبقى فيه الثمرة كاملة طوال التجفيف"),
        ("processes/washed/", "الطرف المقابل: تُنزع الطبقات ثم يجفّ البرشمان وحده"),
        ("processes/honey/", "الوسط بينهما، ومقداره هو المتغيّر"),
        ("processes/anaerobic/", "طورٌ يُضاف إلى واحدة منها، لا بديلٌ عنها"),
        ("origins/indonesia/", "التقشير الرطب: ترتيب لا يوجد في غيره"),
        ("methodology/", "لماذا يُفصل تعريف المعالجة عن أثرها الحسي"),
    ],
    "processes/natural/": [
        ("processes/washed/", "النقيض في الترتيب: نزع الطبقات قبل التجفيف"),
        ("processes/", "طبقات الثمرة الست، وجدول يقارن الطرق الأربع"),
        ("processes/honey/", "الوسط بين المجففة والمغسولة"),
        ("crops/guji-dega-natural/", "محصول معالَج بهذه الطريقة، ببيانات تجفيف ناقصة"),
        ("origins/brazil/", "المنشأ الذي تسود فيه، لأسباب مناخية لا حسية"),
        ("science/storage/", "التجفيف أول ضبط لرطوبة البنّ، والتخزين تاليه"),
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
        ("brewing/espresso/", "طريقة أخرى: ضغط وزمن قصير بدل الصب والجاذبية"),
        ("crops/guji-dega-natural/", "المحصول الذي وُضعت له هذه الوصفة"),
        ("processes/natural/", "المعالجة التي تسبق التحضير وتؤثر في الاستخلاص"),
        ("evaluation/", "كيف يُحكم على نتيجة الوصفة دون خلط الوصف بالحكم"),
        ("science/extraction/", "ما تعنيه أرقام الوصفة: استخلاصًا وتركيزًا"),
        ("science/water/", "الماء الذي تُحضَّر به، ومعاييره المنشورة"),
        ("methodology/", "متى تنتقل وصفة من تأسيسية إلى معتمدة"),
    ],
    "roasting/": [
        ("processes/natural/", "ما يسبق التحميص ويحدّ ما يمكنه إظهاره"),
        ("brewing/v60/", "الخطوة التالية، وتتأثر بقابلية الاستخلاص بعد التحميص"),
        ("evaluation/", "كيف يُقاس أثر التحميص دون خلط الوصف بالحكم"),
        ("science/storage/", "ما يجري للحبة بعد التحميص: أكسجين وحرارة ورطوبة"),
    ],
    "evaluation/": [
        ("roasting/", "المرحلة التي يُقيَّم أثرها غالبًا"),
        ("brewing/v60/", "متى تنتقل وصفة من تأسيسية إلى معتمدة"),
        ("methodology/", "الفصل بين المُدرَك والمُفضَّل، وهو أصل التقييم"),
        ("science/extraction/", "النافذة المنشورة للاستخلاص، وحدودها كحكم"),
    ],
    "origins/yemen/": [
        ("origins/ethiopia/", "الموطن الطبيعي الذي خرجت منه الأرابيكا قبل اليمن"),
        ("saudi-coffee/khawlani/", "الجوار الجغرافي والزراعي عبر جبال الجزيرة"),
        ("varieties/dega/", "المشكلة نفسها: اسم محلي موثق لا يثبت هوية وراثية"),
        ("varieties/typica-bourbon/", "المجموعتان اللتان خرجتا من ميناء المخا إلى العالم"),
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
    "species/arabica/": [
        ("species/canephora/", "أحد أبوَي الأرابيكا، لا منافسها في درجة الجودة"),
        ("origins/ethiopia/", "الموطن الذي بقي فيه تنوع النوع كاملًا"),
        ("varieties/typica-bourbon/", "المجموعتان اللتان خرجتا من هذا النوع إلى العالم"),
        ("science/caffeine/", "الكافيين في الفنجان وفي الجسم، لا في الحبة وحدها"),
    ],
    "species/canephora/": [
        ("species/arabica/", "النوع الذي نشأ من تهجين هذا النوع بغيره"),
        ("origins/indonesia/", "منشأ يغلب هذا النوع على إنتاجه"),
        ("origins/vietnam/", "أكبر منتج له في العالم، وثاني أكبر منتج للقهوة"),
        ("origins/brazil/", "ثاني أكبر منتج له، ويُعرف فيه بالكونيلون"),
        ("science/diseases/", "جيناته مصدر مقاومة الصدأ في سلالات الأرابيكا التجارية"),
        ("science/caffeine/", "نسبته الأعلى من الكافيين، وما يعنيه ذلك في الفنجان"),
        ("evaluation/", "لماذا لا يُحسم تفضيل نوع على نوع بالقياس وحده"),
        ("methodology/", "الفصل بين القياس والحكم التسويقي"),
    ],
    "varieties/typica-bourbon/": [
        ("origins/yemen/", "المحطة التي ضاقت فيها قاعدة التنوع قبل انتشارها"),
        ("species/arabica/", "النوع الذي تنتمي إليه المجموعتان"),
        ("origins/kenya/", "المنشأ الذي انتُخبت فيه SL28 وSL34 من هذه القاعدة"),
        ("varieties/caturra/", "طفرة خرجت من بوربون وغيّرت أمريكا اللاتينية"),
        ("varieties/dega/", "المشكلة نفسها: اسم يدل على أشياء مختلفة بحسب السياق"),
    ],
    "varieties/geisha/": [
        ("origins/ethiopia/", "المنشأ الحقيقي للسلالة قبل شهرتها البنمية"),
        ("varieties/dega/", "المشكلة نفسها: اسم محلي تعددت صوره وتفرّق ما يدل عليه"),
        ("evaluation/", "لماذا السعر إشارة سوق لا قياس جودة"),
    ],
    "processes/washed/": [
        ("processes/natural/", "النقيض في الترتيب: التجفيف قبل نزع الطبقات"),
        ("processes/", "طبقات الثمرة الست، وجدول يقارن الطرق الأربع"),
        ("processes/honey/", "الوسط بينهما: نزع القشرة مع إبقاء بعض اللب"),
        ("processes/anaerobic/", "طور تخمير يُضاف إلى هذه المعالجة أو غيرها"),
        ("origins/indonesia/", "منشأ تتفرع منه نسخة محلية: التقشير الرطب"),
        ("origins/kenya/", "منشأ تقترن فيه هذه المعالجة بنظام فرز بالحجم"),
    ],
    "processes/honey/": [
        ("processes/washed/", "منها تُؤخذ خطوة نزع القشرة"),
        ("processes/", "طبقات الثمرة الست، وموضع العسلية بينها"),
        ("processes/natural/", "ومنها يُؤخذ بقاء المادة اللزجة أثناء التجفيف"),
        ("processes/anaerobic/", "طور تخمير يُضاف إليها كذلك"),
    ],
    "processes/anaerobic/": [
        ("processes/natural/", "معالجة يُضاف إليها هذا الطور كثيرًا"),
        ("processes/", "لماذا لا يُعدّ هذا الطور معالجةً مستقلة"),
        ("processes/washed/", "ويُضاف إليها كذلك قبل الغسل"),
        ("evaluation/", "لماذا لا تُقبل الادعاءات الحسية قبل تكرار موثق"),
    ],
    "brewing/espresso/": [
        ("roasting/", "درجة التحميص وعمر القهوة يغيّران الاستخلاص والكريما"),
        ("brewing/v60/", "طريقة أخرى بمتغيّرات مختلفة من العائلة نفسها: الاستخلاص"),
        ("species/canephora/", "نسبتها في الخلطة تغيّر القوام والكريما"),
        ("science/extraction/", "تركيز عالٍ في زمن قصير، والفرق بينه وبين الجرعة"),
    ],
    "brewing/turkish/": [
        ("saudi-coffee/ritual/", "عنصر مُدرج آخر، والطريقتان تلتقيان في الغلي دون فلتر"),
        ("roasting/", "الطحن فائق النعومة يفرض اعتبارات في التحميص"),
        ("brewing/espresso/", "طريقة أخرى لا تفصل القهوة عن طحنها بالفلتر وحده"),
    ],
    "science/caffeine/": [
        ("species/canephora/", "النوع الأعلى كافيينًا، وفيه نِسب الحبة الخضراء بمصدرها"),
        ("species/arabica/", "النوع الأقل كافيينًا، وليس الخالي منه"),
        ("science/extraction/", "الفرق بين الجرعة الكلية والتركيز، وهو أصل مغالطة الإسبريسو"),
        ("roasting/", "لماذا لا يدل لون التحميص على الكافيين"),
    ],
    "science/water/": [
        ("science/extraction/", "ما يُقاس في الكوب بعد أن يعمل الماء عمله"),
        ("brewing/v60/", "الطريقة التي يظهر فيها أثر الماء بوضوح"),
        ("methodology/", "كيف يُسجَّل تعارض المصادر بدل طمسه"),
    ],
    "science/extraction/": [
        ("science/water/", "الوسط الذي يجري فيه الاستخلاص، وليس محايدًا"),
        ("brewing/v60/", "تطبيق المقابض على وصفة مقطَّرة"),
        ("brewing/espresso/", "الطرف الآخر: تركيز عالٍ وزمن ثوانٍ"),
        ("evaluation/", "لماذا النافذة إجماع مهني لا حكم ذوق"),
    ],
    "science/storage/": [
        ("roasting/", "ما يسبق التخزين، ويحدّد سرعة التقادم بعده"),
        ("science/diseases/", "الوجه الآخر لخطر الرطوبة: ما يصيب المحصول قبل حصاده"),
        ("processes/natural/", "التجفيف أول موضع تُضبط فيه رطوبة البنّ"),
    ],
    "science/diseases/": [
        ("origins/kenya/", "منشأ خرج من ضغط هذه الأمراض ببرنامج تربية"),
        ("origins/colombia/", "منشأ أعاد تشكيل زراعته حول مقاومة الصدأ"),
        ("species/canephora/", "النوع الذي جاءت منه جينات المقاومة"),
        ("varieties/timor-catimor/", "النسب الذي حمل المقاومة، وعلامات تآكلها"),
        ("varieties/typica-bourbon/", "المجموعات التي تفتقر إلى المقاومة، ومنها كاتورا"),
    ],
    "origins/vietnam/": [
        ("species/canephora/", "النوع الذي يقوم عليه إنتاجه كله تقريبًا"),
        ("origins/brazil/", "المنتج الأكبر، والقصّة نفسها بوتيرة أبطأ"),
        ("varieties/timor-catimor/", "من الروبوستا جاءت مقاومة الصدأ في نصف سلالات العالم"),
        ("evaluation/", "لماذا لا يُقرأ حجم الإنتاج حكمًا على الجودة"),
    ],
    "varieties/caturra/": [
        ("varieties/typica-bourbon/", "المجموعة التي طفرت عنها"),
        ("varieties/timor-catimor/", "ما هُجّنت به لتُكسَب المقاومة"),
        ("origins/brazil/", "الولاية التي رُصدت فيها الطفرة"),
        ("science/diseases/", "الصدأ الذي كشف ضعفها فغيّر خريطة السلالات"),
    ],
    "varieties/timor-catimor/": [
        ("species/canephora/", "مصدر جينات المقاومة في هذا النسب"),
        ("varieties/caturra/", "الطرف الآخر في تهجين مجموعة كاتيمور"),
        ("origins/colombia/", "منشأ بنى زراعته على كاستيو، وهي من هذا النسب"),
        ("science/diseases/", "المرض الذي وُجد هذا النسب لمقاومته"),
        ("species/arabica/", "ضيق قاعدة التنوع الذي يجعل المقاومة قصيرة العمر"),
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
