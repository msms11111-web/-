#!/usr/bin/env python3
"""يتحقق أن كل مصدر خارجي مُحال إليه في الموقع ما زال يستجيب.

الاستخدام:
    python3 tools/check-external-links.py

يُشغَّل في GitHub Actions لأن بيئة التطوير قد لا تصل إلى الإنترنت.
الخروج برمز 1 عند وجود رابط ميت، ورمز 0 مع تنبيه عند تعذّر الوصول للشبكة
أصلًا — فرق مهم: موقع ميت خطأ، وشبكة محجوبة ليست خطأ في الموقع.

بعض المواقع ترفض HEAD أو ترفض العملاء غير المتصفحات، فتُعاد المحاولة بـ GET
وترويسة User-Agent، ويُقبل أي رد يعني أن العنوان موجود.

وهذا الفحص هو الحكم الوحيد على المصادر، لأن بيئة التحرير لا تفتح الشبكة.
وكلُّ رابطٍ ميت وقع حتى الآن كانت علّته واحدة: عنوانٌ أُخذ من قائمة نتائج
بحثٍ لا من الصفحة نفسها، فنقص منه مقطعٌ أو بادئة. أمثلة مسجَّلة:

  sca.coffee/.../how-to-use-the-flavor-wheel-in-eight-steps      ← 404
  sca.coffee/.../how-to-use-the-flavor-wheel-in-eight-steps-ab2hy ← 200
  worldcoffeeportal.com/Latest/News/2018/Costa-Rica-...          ← 404
  www.worldcoffeeportal.com/Latest/News/2018/February/Costa-...  ← 404 كذلك

والثاني درسٌ أثقل: جُرّب عنوانٌ «مصحَّح» من نتيجة بحثٍ أخرى فأخفق هو أيضًا،
لأن الموقع أعاد بناء مساراته فلم يبقَ للمقال عنوانٌ من ذلك النمط. فالتصحيح
بالتخمين مرتين أسوأ من حذف المصدر مرة.

فالقاعدة العملية: عنوانٌ لم يُفتَح لا يُكتب في مصدر. وإن أخفق مرةً فلا
يُستبدَل بعنوانٍ مخمَّن، بل يُحذف المصدر ويُقلَّص ما كان يسنده إلى ما تسنده
مصادرُ حيّة وحدها.

وأخفق كذلك سجلّ المؤشرات الجغرافية الهندي بمسارَيه:

  search.ipindia.gov.in/GIRPublic/Application/Details/85  ← 404
  search.ipindia.gov.in/GIRPublic/Application/Details/114 ← 404

فحُذف المصدران، وقُلّص ما كانا يسندانه: سقطت تواريخُ الشهادات ومدةُ سريانها
وحالُ التسجيل، وبقي ما تحمله وثيقتا طلب التسجيل وحدهما. ودرسُه أن سجلًّا
حكوميًّا ليس أدومَ من غيره: المواقع الحكومية تعيد بناء مساراتها كما يفعل
الناشرون، والحكمُ هو الاستجابةُ لا نوعُ المالك.

وأخفق كذلك موقع جمعية القهوة المختصة بمسارين، وهو ثالثُ إخفاقٍ له:

  sca.coffee/research/protocols-best-practices                 ← 404
  sca.coffee/sca-news/25/issue-24-grounding-green-grading      ← 404
  sca.coffee/sca-news/25/issue-24-grounding-green-grading-2btb6 ← البديل المُفهرَس

والفرقُ بين «بديلٍ مُفهرَس» و«عنوانٍ مخمَّن» هو ما يُجيز الأول ويمنع الثاني:
العنوان الذي يظهر نتيجةَ بحثٍ مستقلةً دليلٌ على وجوده، والعنوان الذي يُبنى
بالقياس على عنوانٍ آخر تخمين. وقد نجح هذا في «-ab2hy» من قبل، وأخفق التخمين
في كوستاريكا مرتين.

وأخفق فحصٌ كامل برابطٍ لم يَمُت: أعاد سجلُّ التراث العالمي لليونسكو

  whc.unesco.org/en/list/1121/ ← HTTP 503

وكان يستجيب 200 في كل جَرْيةٍ قبلها. و503 معناه أن الخادم عاجزٌ الآن، لا أن
العنوان ذهب. وعدُّه موتًا يُحوّل عطلًا عارضًا عند جهةٍ أخرى إلى بناءٍ فاشل،
ويدفع إلى حذف مصدرٍ حيّ — وحذفُ الحيّ أسوأ من إبقاء الميت جَرْيةً واحدة.
فصارت ردودُ الخادم العاجز (500 و502 و503 و504) تُعامَل معاملةَ الشبكة
المحجوبة: تُعاد المحاولة مرةً، ثم يُبلَّغ عنها «تعذّر الوصول» ولا يفشل الفحص.
وهذا هو المبدأُ المكتوب في أول هذا الملف مطبَّقًا على حالةٍ لم تكن ملحوظة.

وأخفق كذلك خبرٌ عند منظمة أبحاث القهوة العالمية:

  worldcoffeeresearch.org/news/2024/f1-precommercial ← 404

وهذا أدقُّ ما سُجّل في الباب، لأنه يُضيّق قاعدةَ «البديل المُفهرَس»: العنوانُ
جاء نتيجةَ بحثٍ مستقلةً — أي كان مُفهرَسًا — وأخفق مع ذلك. فظهورُ العنوان في
نتائج البحث دليلٌ على أنه كان، لا على أنه ما زال؛ والفهرسةُ تتأخّر عن إعادة
بناء المسارات. فحُذف المصدر وقُلّص ما كان يحمله: سقط أصلُ المرشَّحين وعددُ
القطع التجريبية والدولُ وعددُ النباتات وسنةُ انتهاء المرحلة، وسقطت معها علاقةٌ
في شبكة «اقرأ أيضًا» كانت تستند إليه وحده.

والأولُ حُذف ولم يُستبدَل: ولوَّجنا موضعَه وثيقةَ المعايير نفسها
‏(sca.coffee/s/Coffee-Standards-compressed.pdf) وهي أوّليةٌ لا صفحةُ فهرسة.
فإخفاقُ صفحةِ فهرسةٍ فرصةٌ لاستبدالها بالوثيقة التي كانت تدلّ عليها.

وأخفقت صفحةُ محميةٍ عند اليونسكو جَريتين متتاليتين، وكانت قد نجحت قبلهما:

  unesco.org/en/mab/kafa ← 404 على المشغِّل، 200 للمتصفّح وللجالب

و404 غيرُ 503: الخادمُ لا يقول «عاجزٌ الآن» بل «لا شيء هنا» — وهو يقولها
للمشغِّل وحده. فلم يُعامَل معاملةَ العطل العارض، ولم يُستثنَ المضيفُ في هذا
الملف: استثناءُ مضيفٍ يُعمي الفحصَ عن موتٍ حقيقيٍّ فيه بعد ذلك. فاستُبدل
بالرابط نظيرُه من الجهة نفسِها — مقالةٌ في مجلّتها تحمل الخبرين نفسَيهما —
وكُتب السببُ في خانة المصدر.
"""

import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r'href="(https?://[^"]+)"')
UA = "Mozilla/5.0 (compatible; QatraLinkCheck/1.0; +https://github.com/msms11111-web/qatra)"
TIMEOUT = 25

# ردود تعني أن العنوان موجود لكن الخادم يمانع الفحص الآلي
TOLERATED = {401, 403, 405, 406, 429, 999}

# ردود تعني أن الخادم عاجزٌ الآن، لا أن العنوان ذهب. تُعاد المحاولة ثم تُعَدّ
# «تعذّر الوصول» لا موتًا — كالشبكة المحجوبة.
TRANSIENT = {500, 502, 503, 504}
RETRY_WAIT = 4


def probe(url: str, method: str) -> int:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status


def check(url: str) -> tuple[str, str]:
    """يعيد (الحالة، التفصيل): ok أو tolerated أو dead أو unreachable."""
    last = ""
    for method in ("HEAD", "GET", "GET"):
        if method == "GET" and last.startswith("HTTP 5"):
            time.sleep(RETRY_WAIT)
        try:
            status = probe(url, method)
            return ("ok", str(status))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in TOLERATED:
                return ("tolerated", last)
            if e.code in TRANSIENT:
                continue  # يُعاد مرةً، ثم يسقط إلى «تعذّر الوصول»
            if method == "GET":
                return ("dead", last)
        except urllib.error.URLError as e:
            last = f"شبكة: {e.reason}"
        except Exception as e:  # مهلة أو TLS أو ما شابه
            last = f"{type(e).__name__}: {e}"
    return ("unreachable", last)


def annotate(url: str, detail: str, pages: list[str]) -> str:
    """سطرُ «أمرِ سَيرِ عمل» يجعل الرابطَ الميت تعليقًا على الجَرْية.

    السببُ عمليّ: سجلُّ الجَرْية يُقرأ من خادمِ ملفّاتٍ لا تبلغه كلُّ الأدوات،
    أما التعليقاتُ فتُقرأ من واجهة البرمجة. وبلا هذا كان العنوانُ الميت
    يَظهر في السجلّ وحده، فيُقال في الواجهة «انتهت العملية برمز 1» ولا أكثر.
    """
    if not os.environ.get("GITHUB_ACTIONS"):
        return ""
    where = ", ".join(pages)
    return f"::error title=رابط ميت::{url} ({detail}) في {where}"


def own_origin() -> str:
    """أصل الموقع نفسه، ليُستثنى: canonical و og:url ليست مصادر خارجية."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<link rel="canonical" href="(https?://[^/"]+)', home)
    return match.group(1) if match else ""


def main() -> int:
    mine = own_origin()
    urls: dict[str, set[str]] = {}
    for page in sorted(ROOT.rglob("*.html")):
        for url in LINK.findall(page.read_text(encoding="utf-8")):
            if mine and url.startswith(mine):
                continue
            urls.setdefault(url, set()).add(page.relative_to(ROOT).as_posix())

    if not urls:
        print("لا توجد روابط خارجية.")
        return 0

    dead, unreachable = [], []
    for url in sorted(urls):
        state, detail = check(url)
        marks = {"ok": "✓", "tolerated": "~", "dead": "✗", "unreachable": "?"}
        print(f"  {marks[state]} {detail:22} {url}")
        if state == "dead":
            dead.append((url, detail, sorted(urls[url])))
        elif state == "unreachable":
            unreachable.append((url, detail))

    print(f"\nفُحص {len(urls)} رابطًا خارجيًا.")

    for url, detail, pages in dead:
        print(f"رابط ميت: {url} ({detail}) في {', '.join(pages)}", file=sys.stderr)
        line = annotate(url, detail, pages)
        if line:
            print(line, flush=True)

    if dead:
        return 1

    if unreachable:
        print(
            f"تعذّر الوصول إلى {len(unreachable)} رابط. لم يُحكم عليها بالموت: "
            "قد تكون الشبكة محجوبة في هذه البيئة.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
