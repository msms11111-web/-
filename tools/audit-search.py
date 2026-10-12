#!/usr/bin/env python3
"""تدقيق البحث: يكتب كلمات في مربع البحث الحقيقي ويقرأ ما يظهر.

أداة صيانة محلية، ليست جزءًا من النشر. تحتاج خادمًا يعمل ومتصفحًا:

    python3 -m http.server 8099 &
    python3 tools/audit-search.py

لماذا في المتصفح لا في بايثون؟ لأن قواعد التطبيع والمكافِئات وحدّ الكلمة
مكتوبة في assets/app.js. وأيُّ محاكاة لها في فحصٍ خارجي تفترق عنها، فتمرّ
العلّة أو يُبلَّغ عن علّة لا وجود لها. هنا يُستعمل الكود نفسه.

وُجد به أول مرة: «Cenicafé» لا تجدها كتابةُ «cenicafe»، لأن الطيّ كان يردّ
الهمزة العربية إلى أصلها ولا يردّ العلامات اللاتينية.

ولكل حالةٍ موجبة شاهدٌ سالب: عبارةٌ يجب ألا تُرجع شيئًا. فاختبارٌ لا يستطيع
أن يفشل لا يُثبت شيئًا حين ينجح.

والترتيب يُفحص لا الوجود وحده: كلمةٌ هي موضوع صفحةٍ بعينها يجب أن تتصدّر بها.
وُجد بهذا أن «canephora» كانت تُرجع صفحة الروبوستا سادسةَ ستٍّ، لأن الاسم
العلمي لم يكن في عنوانها ولا وصفها، فتساوت بصفحةٍ ذكرته مرةً عابرة.
"""
import os
import sys

from playwright.sync_api import sync_playwright

# (ما يُكتب، ما يجب أن يظهر، هل يجب أن يتصدّر)
CASES = [
    ("cenicafe", "كولومبيا", True),
    ("Cenicafé", "كولومبيا", True),
    ("fairtrade", "الشهادات", True),
    ("فيرتريد", "الشهادات", True),
    ("lexicon", "عجلة", True),
    ("المعجم الحسي", "عجلة", True),
    ("cupping", "التقييم", False),
    ("CVA", "تقييم قيمة", True),
    ("minas", "البرازيل", False),
    ("decaf", "الكافيين", True),
    ("Brewing Control Chart", "الاستخلاص", True),
    ("natural process", "المجففة", True),
    ("yemen", "اليمن", True),
    ("canephora", "الروبوستا", True),
    ("typica", "تيبيكا", True),
    ("TDS", "الاستخلاص", True),
    ("٢٠٢٢", "الخولاني", False),
    ("cold brew", "المنقوع", True),
    ("كولد برو", "المنقوع", True),
    ("chlorogenic", "أحماض", False),
    ("حمض الستريك", "أحماض", True),
    ("iced coffee", "المنقوع", True),
    ("cafetiere", "المكبس", True),
    ("cafetière", "المكبس", True),
    ("cafestol", "المكبس", True),
    ("كافستول", "المكبس", True),
    ("costa rica", "كوستاريكا", True),
    ("ICAFE", "كوستاريكا", True),
    # كانت تتصدّر بها كوستاريكا حين كانت أوسعَ من ذكرها، ثم فُتحت صفحةُ
    # هجائن الجيل الأول وفيها فصلٌ للسلالة. فالتصدُّرُ انتقل انتقالًا صحيحًا،
    # فصُحِّح التوقُّع ولم يُلوَ المحتوى. وكوستاريكا ما زالت جوابًا وجيهًا فتُشترط ظهورًا.
    ("centroamericano", "الهجائن", True),
    ("centroamericano", "كوستاريكا", False),
    ("guatemala", "غواتيمالا", True),
    ("anacafe", "غواتيمالا", True),
    ("india", "الهند", True),
    ("الهند", "الهند", True),
    ("Coorg", "الهند", True),
    ("كارناتاكا", "الهند", True),
    ("Mysore", "الهند", True),
    ("honduras", "هندوراس", True),
    ("lempira", "هندوراس", True),
    ("parainema", "هندوراس", True),
    ("uganda", "أوغندا", True),
    ("NaCORI", "أوغندا", True),
    ("Innovea", "أوغندا", False),
    # لواحق الكلمة القصيرة: تُقبل صيغُ النسبة والإعراب ويُرفض جذرٌ جديد
    ("jimma", "إثيوبيا", True),
    ("حسي", "عجلة", True),
    ("سعر", "سعر القهوة", True),
    ("هند", "الهند", True),
    ("potato taste defect", "البطاطس", True),
    ("Antestia", "البطاطس", True),
    ("IPMP", "البطاطس", True),
    ("fines", "الطحن", True),
    ("نواعم", "الطحن", True),
    ("bimodal", "الطحن", True),
    ("monsooned", "المَمطورة", True),
    ("malabar", "المَمطورة", True),
    ("rwanda", "رواندا", True),
    ("RAB C15", "رواندا", True),
    ("core collection", "رواندا", True),
    ("SCA-103", "تقييم قيمة", True),
    ("Coffee Value Assessment", "تقييم قيمة", True),
    ("انطباعي", "تقييم قيمة", True),
    # الجناحُ وصفحةُ التسمية كلاهما وجيهٌ لهذا الطلب، والأول عنوانُه مطابق.
    # فلا يُشترط التصدّر ولا يُلوى المحتوى لكسب تعادلٍ بين صفحتين كلتاهما صحيحة.
    ("عام القهوة السعودية", "تسمية", False),
    ("وزارة التجارة", "تسمية", True),
    ("الهرري", "زراعة البن", True),
    ("longberry", "زراعة البن", True),
    ("مدينة البن", "زراعة البن", True),
    ("عسير", "زراعة البن", False),
    ("EUDR", "إزالة الغابات", True),
    ("drying", "التجفيف", True),
    ("water activity", "التجفيف", True),
    ("ochratoxin", "التجفيف", True),
    ("توزيع القيمة", "توزيع القيمة", True),
    ("Grounds for Sharing", "توزيع القيمة", True),
    ("2023/1115", "إزالة الغابات", True),
    ("geolocation", "إزالة الغابات", True),
    # رقمٌ يتبعه فاصلةٌ عربية — كان يُرفض لأن الفاصلة حُسبت حرفَ كلمة
    ("476", "منظمة القهوة الدولية", True),
    ("ICO", "منظمة القهوة الدولية", True),
    ("melanoidins", "الميلانويدينات", True),
    ("ميلارد", "الميلانويدينات", True),
    ("green grading", "تصنيف البن الأخضر", True),
    ("Green Arabica Coffee Classification", "تصنيف البن الأخضر", True),
    ("الدرجة المختصة", "تصنيف البن الأخضر", True),
    ("العيب الكامل", "تصنيف البن الأخضر", True),
    ("أعضاء منتسبين", "منظمة القهوة الدولية", True),
    ("f1", "الهجائن", True),
    # «هجين تيمور وكاتيمور» يحمل الكلمة في عنوانه، وهو جوابٌ وجيهٌ لمن كتب
    # «hybrid» كما أن صفحة الجيل الأول وجيهة. فلا يُشترط التصدّر لأحدهما.
    # أما «f1» فلا تُسوّى بـ«هجين» في المكافئات، ولذلك تُشترط فيها.
    ("hybrid", "الهجائن", False),
    ("ستارمايا", "الهجائن", True),
    ("Starmaya", "الهجائن", True),
    ("مارسيليسا", "الهجائن", True),
    ("العقم الذكري", "الهجائن", True),
    ("روميه سودان", "الهجائن", True),
    ("degassing", "إزالة الغاز", True),
    ("إزالة الغاز", "إزالة الغاز", True),
    ("لانغمير", "إزالة الغاز", True),
    ("أيام الراحة", "إزالة الغاز", True),
    ("البنية المسامية", "إزالة الغاز", True),
    ("KC", "عقد القهوة الآجل", True),
    ("37,500", "عقد القهوة الآجل", True),
    ("eCOPS", "عقد القهوة الآجل", True),
    ("فروق العقد", "عقد القهوة الآجل", True),
    ("المخزون المصدَّق", "عقد القهوة الآجل", True),
    ("ويلكوكسون", "التخمير", True),
    ("بكتين", "التخمير", True),
    ("pectin", "التخمير", True),
    ("بادئات مختارة", "التخمير", True),
    ("fermentation", "التخمير", True),
    ("بكتيريا حمض اللبن", "التخمير", False),
    ("liberica", "الليبيريكا", True),
    ("excelsa", "الليبيريكا", True),
    ("dewevrei", "الليبيريكا", True),
    ("klainei", "الليبيريكا", True),
    ("الليبيرويدية", "الليبيريكا", True),
    ("ليبكس", "الليبيريكا", True),
    ("GSO 2197", "المواصفات الخليجية", True),
    ("لائحة فنية", "المواصفات الخليجية", True),
    ("سريعة الذوبان", "المواصفات الخليجية", True),
    ("11294", "المواصفات الخليجية", True),
    ("furfural", "المركَّبات الطيّارة", True),
    ("غواياكول", "المركَّبات الطيّارة", True),
    ("furaneol", "المركَّبات الطيّارة", True),
    ("AEDA", "المركَّبات الطيّارة", True),
    ("حد الشم", "المركَّبات الطيّارة", True),
    ("volatile", "المركَّبات الطيّارة", True),
    ("189.7", "أرقام القهوة", True),
    ("سنة تسويقية", "أرقام القهوة", True),
    ("مليون كيس", "أرقام القهوة", True),
    ("الاستهلاك العالمي", "أرقام القهوة", True),
    ("peru", "بيرو", True),
    ("بيرو", "بيرو", True),
    ("المجلس الوطني للقهوة", "بيرو", True),
    ("mexico", "المكسيك", True),
    ("chiapas", "المكسيك", True),
    ("veracruz", "المكسيك", True),
    ("coatepec", "المكسيك", True),
    ("550 مليون", "المكسيك", True),
    ("cascara", "قشر القهوة", True),
    ("الكسكرة", "قشر القهوة", True),
    ("غذاء جديد", "قشر القهوة", True),
    ("15 مايو 1997", "قشر القهوة", True),
    ("600 مللغرام", "قشر القهوة", True),
    ("RC", "عقد الروبوستا", True),
    ("عشرة أطنان", "عقد الروبوستا", True),
    ("FIBC", "عقد الروبوستا", True),
    ("830 كيسًا", "عقد الروبوستا", True),
]

# عباراتٌ يجب أن تُرجع لا شيء. وجودُ نتيجةٍ لها يعني أن المطابقة متراخية.
NEGATIVE = ["زنجبيل مخلل", "qqqzz", "حافلة مدرسية"]


def results(pg, query: str) -> list[str]:
    """عناوين النتائج بالترتيب المعروض، من اللوحة أو من البطاقات."""
    box = pg.query_selector("[data-search]")
    box.fill("")
    box.type(query, delay=12)
    pg.wait_for_timeout(320)
    return pg.evaluate(
        """() => {
          const panel = document.querySelector('[data-results]');
          if (panel && !panel.hidden)
            return [...panel.querySelectorAll('a.result h3')].map(h => h.textContent.trim());
          return [...document.querySelectorAll('.entity')]
            .filter(e => e.offsetParent !== null)
            .map(e => (e.querySelector('h3')?.textContent || '').trim());
        }"""
    )


def main() -> int:
    chrome = os.environ.get("CHROME_PATH")
    site = os.environ.get("SITE", "http://localhost:8099")
    bad = 0
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(f"{site}/encyclopedia/", wait_until="networkidle")
        pg.wait_for_timeout(600)

        for query, want, first in CASES:
            got = results(pg, query)
            where = next((i for i, t in enumerate(got) if want in t), -1)
            ok = where == 0 if first else where >= 0
            bad += 0 if ok else 1
            rank = "غائبة" if where < 0 else f"المرتبة {where + 1}"
            need = "يتصدّر" if first else "يظهر"
            print(f"  {'✓' if ok else '✗'} «{query}» ← {need} «{want}» ({rank} من {len(got)})")
            if not ok:
                print(f"      الترتيب: {got[:5]}")

        for query in NEGATIVE:
            got = results(pg, query)
            bad += 0 if not got else 1
            print(f"  {'✓' if not got else '✗'} شاهد سالب «{query}» ← يُفترض لا شيء")
            if got:
                print(f"      ظهر: {got[:5]}")
        b.close()

    print(f"\nفشل: {bad}" if bad else "\nكل حالات البحث سليمة.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
