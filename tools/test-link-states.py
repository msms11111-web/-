#!/usr/bin/env python3
"""إثباتُ تصنيف الردود في فحص المصادر، بردودٍ مصنوعة لا بالشبكة.

الاستخدام:
    python3 tools/test-link-states.py

لا يحتاج شبكةً: يُبدَّل نداءُ الفحص بردودٍ معلومة، ويُتحقَّق أن التصنيف
يقع كما يجب. وسببُ وجوده أن تصنيفَ الردود تغيّر مرةً — صار الخادمُ العاجز
‏(5xx) «تعذّر وصولٍ» لا موتًا — بعد أن أسقط ردُّ 503 عارضٌ من اليونسكو فحصًا
كاملًا. وتغييرٌ كهذا بلا إثباتٍ تخمين، وأخطرُ ما فيه أن يُعمي الفحصَ عن موتٍ
حقيقي. فالحالةُ «503 ثم 404 ← ميت» هي الشاهدُ على أنه لم يُعمَ.
"""
import importlib.util, sys, urllib.error
from pathlib import Path

# المسار من موضع هذا الملف لا من مسارٍ مطلق: المطلقُ صحيحٌ في بيئة التحرير
# وغائبٌ في CI، وقد أسقط الاختبارَ جَرْيةً كاملة بذلك وحده.
TARGET = Path(__file__).resolve().parent / "check-external-links.py"
spec = importlib.util.spec_from_file_location("cel", TARGET)
cel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cel)
cel.RETRY_WAIT = 0  # لا انتظارَ في الاختبار

CASES = [
    ("503 مرتين → تعذّر الوصول", [503, 503, 503], "unreachable"),
    ("503 ثم 200 → سليم", [503, 200], "ok"),
    ("503 ثم 404 → ميت", [503, 404, 404], "dead"),
    ("404 → ميت", [404, 404], "dead"),
    ("403 → مُمانَع", [403], "tolerated"),
    ("200 → سليم", [200], "ok"),
    ("500 ثم 500 → تعذّر الوصول", [500, 500, 500], "unreachable"),
]

bad = 0
for name, replies, want in CASES:
    seq = list(replies)
    def probe(url, method, seq=seq):
        code = seq.pop(0)
        if code >= 400:
            raise urllib.error.HTTPError(url, code, "x", None, None)
        return code
    cel.probe = probe
    got, detail = cel.check("https://example.invalid/x")
    ok = got == want
    bad += 0 if ok else 1
    print(f"  {'✓' if ok else '✗'} {name}: {got} ({detail})")

# وتعليقُ الجَرْية: يُكتب داخل بيئة GitHub وحدها، ولا يُكتب خارجَها
import os

os.environ.pop("GITHUB_ACTIONS", None)
quiet = cel.annotate("https://x.invalid/a", "HTTP 404", ["p/index.html"])
ok = quiet == ""
bad += 0 if ok else 1
print(f"  {'✓' if ok else '✗'} خارجَ GitHub: لا تعليق ({quiet!r})")

os.environ["GITHUB_ACTIONS"] = "true"
line = cel.annotate("https://x.invalid/a", "HTTP 404", ["p/index.html", "q/index.html"])
ok = (line.startswith("::error title=رابط ميت::")
      and "https://x.invalid/a" in line
      and "HTTP 404" in line
      and "p/index.html, q/index.html" in line
      and "\n" not in line)
bad += 0 if ok else 1
print(f"  {'✓' if ok else '✗'} داخلَ GitHub: سطرُ تعليقٍ واحد")
if not ok:
    print(f"      كُتب: {line!r}")
os.environ.pop("GITHUB_ACTIONS", None)

print("\nفشل:", bad)
sys.exit(1 if bad else 0)
