#!/usr/bin/env python3
"""يستخرج تاريخ آخر مراجعة فعلية لكل صفحة من تاريخ المستودع.

الاستخدام:
    python3 tools/revisions.py

المشكلة التي يحلها: أمر البناء يعيد كتابة كتلة الوسوم في كل صفحة مع كل نشر،
فكل التزام يلمس كل الملفات، ويصبح «تاريخ آخر تعديل» في Git بلا معنى. هنا
تُستبعد الكتلة المولَّدة قبل المقارنة، فلا يُحتسب إلا تغيّر المحتوى نفسه.

يكتب assets/revisions.json: لكل صفحة تاريخ آخر مراجعة ورقم الالتزام وعنوانه.

يتدهور بلطف: إن غاب Git أو كان التاريخ مبتورًا، يُستخدم أقدم ما هو متاح
ويُعلَّم بـ approximate، فلا يتعطل البناء ولا يُنشر تاريخ كاذب بثقة.
"""

import hashlib
import os
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# الكتل التي يولّدها أمر البناء، وتُستبعد من مقارنة المحتوى
GENERATED = [
    re.compile(r"<!--qatra:meta-->.*?<!--/qatra:meta-->", re.S),
    re.compile(r"<!--qatra:base=[^>]*-->"),
    re.compile(r"<!--qatra:rev-->.*?<!--/qatra:rev-->", re.S),
    re.compile(r"<!--qatra:rel-->.*?<!--/qatra:rel-->", re.S),
]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def content_hash(html: str) -> str:
    """بصمة المحتوى بعد إزالة ما يولّده البناء وتوحيد المسافات."""
    for pattern in GENERATED:
        html = pattern.sub("", html)
    return hashlib.sha256(re.sub(r"\s+", " ", html).strip().encode()).hexdigest()


def repo_url() -> str:
    """المستودع العلني الذي تُعرض منه التغييرات.

    الترتيب: متغيّر REPO_URL صريح، ثم بعيد اسمه qatra (موجود محليًا حيث
    origin مستودع احتياطي)، ثم origin (وهو الصحيح في بيئة البناء).
    """
    explicit = os.environ.get("REPO_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")

    for remote in ("qatra", "origin"):
        match = re.search(
            r"github\.com[:/]+([^/]+)/([^/.\s]+)", git("remote", "get-url", remote)
        )
        if match:
            return f"https://github.com/{match.group(1)}/{match.group(2)}"

    return "https://github.com/msms11111-web/qatra"


def last_content_change(path: str) -> dict | None:
    """أحدث التزام تغيّر فيه محتوى الصفحة، لا كتلتها المولَّدة."""
    log = git("log", "--format=%H%x1f%ad%x1f%s", "--date=short", "--", path)
    commits = [line.split("\x1f") for line in log.strip().splitlines() if line]
    if not commits:
        return None

    newer = None
    for sha, date, subject in commits:
        blob = git("show", f"{sha}:{path}")
        if not blob:
            continue
        current = content_hash(blob)
        if newer is None:
            newer = (sha, date, subject, current)
            continue
        if current != newer[3]:
            # المحتوى اختلف عند هذا الالتزام، فالمراجعة هي الالتزام الأحدث منه
            return {"date": newer[1], "sha": newer[0], "subject": newer[2]}
        newer = (sha, date, subject, current)

    # لم يتغيّر المحتوى قط منذ أول التزام
    return {"date": newer[1], "sha": newer[0], "subject": newer[2]} if newer else None


def main() -> int:
    base = repo_url()
    shallow = (ROOT / ".git" / "shallow").exists()
    revisions = {}

    for file in sorted(ROOT.rglob("index.html")):
        path = file.relative_to(ROOT).as_posix()
        url = path[: -len("index.html")]
        entry = last_content_change(path)
        if entry is None:
            # ملف جديد لم يُلتزم بعد
            revisions[url] = {"date": "", "sha": "", "subject": "", "approximate": True}
            continue
        entry["url"] = url
        entry["commit"] = f"{base}/commit/{entry['sha']}"
        entry["approximate"] = shallow
        revisions[url] = entry

    out = ROOT / "assets" / "revisions.json"
    out.write_text(json.dumps(revisions, ensure_ascii=False, indent=1), encoding="utf-8")

    dated = sum(1 for r in revisions.values() if r["date"])
    note = " (تاريخ مبتور، التواريخ تقريبية)" if shallow else ""
    print(f"سُجّلت مراجعات {dated} من {len(revisions)} صفحة{note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
