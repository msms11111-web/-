#!/usr/bin/env python3
"""يضبط سطرَ الإصدار في تذييل كل صفحة — وهو نصٌّ من القالب، لا من ملفات المحتوى.

الاستخدام:
    python3 tools/set-version.py "الإصدار 1.0"

يُشغَّل مرّةً عند اعتماد الموسوعة، ثم يُبنى الموقع ويُلتزَم. آمنٌ للتكرار.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# السطرُ الثاني في تذييل الحقوق: <div class="copyright"><span>©…</span><span>الإصدار…</span></div>
LINE = re.compile(r'(<div class="copyright"><span>.*?</span><span>)([^<]*)(</span></div>)', re.S)


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print(__doc__)
        return 1
    label = sys.argv[1].strip()
    changed = missing = 0
    files = sorted(ROOT.rglob("index.html")) + [ROOT / "404.html"]
    for file in files:
        if "tools" in file.relative_to(ROOT).parts:
            continue
        html = file.read_text(encoding="utf-8")
        new, n = LINE.subn(lambda m: m.group(1) + label + m.group(3), html, count=1)
        if n == 0:
            missing += 1
            print(f"لا سطرَ إصدارٍ في: {file.relative_to(ROOT)}", file=sys.stderr)
        elif new != html:
            file.write_text(new, encoding="utf-8")
            changed += 1
    print(f"سطرُ الإصدار «{label}»: غُيّر في {changed} صفحة، وغاب عن {missing}.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
