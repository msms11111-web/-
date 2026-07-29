#!/bin/sh
# أمر البناء على Cloudflare Pages.
#
# في لوحة Cloudflare:
#   Build command:           sh tools/build.sh
#   Build output directory:  /
#
# متغير اختياري واحد يُضبط في Settings ← Environment variables:
#   SITE_URL = https://your-domain.com/
#
# لماذا؟ لأن CF_PAGES_URL يعطي عنوان pages.dev حتى بعد ربط نطاق مخصص، فتشير
# وسوم canonical إلى العنوان الخطأ ويُحسب الموقع محتوى مكررًا. عند ضبط SITE_URL
# يُعتمد في الإنتاج فقط، وتبقى معاينات الفروع على عنوانها الحقيقي.
#
# للتشغيل يدويًا:  sh tools/build.sh https://example.com/
set -e

BRANCH="${CF_PAGES_BRANCH:-main}"
PRODUCTION_BRANCH="${PRODUCTION_BRANCH:-main}"

# CF_PAGES_URL يعطي عنوان النشرة الواحدة (hash.project.pages.dev) وبادئته
# تتغير مع كل دفعة. العنوان الثابت للمشروع هو project.pages.dev، فتُحذف
# البادئة عند وجودها. أي مضيف آخر (نطاق مخصص) يُترك كما هو.
stable_url() {
  host=$(printf '%s' "$1" | sed -e 's|^https\{0,1\}://||' -e 's|/.*$||')
  case "$host" in
    *.pages.dev)
      if [ "$(printf '%s\n' "$host" | tr '.' '\n' | wc -l)" -ge 4 ]; then
        host="${host#*.}"
      fi
      ;;
  esac
  printf 'https://%s/' "$host"
}

if [ "$BRANCH" = "$PRODUCTION_BRANCH" ]; then
  # النطاق المخصص يتقدم دائمًا، لأن Cloudflare لا يمرره في أي متغير
  URL="${SITE_URL:-$(stable_url "${CF_PAGES_URL:-$1}")}"
else
  # المعاينات تبقى على عنوانها الفعلي، وهي ممنوعة من الأرشفة أصلًا
  URL="${CF_PAGES_URL:-${SITE_URL:-$1}}"
fi

if [ -z "$URL" ]; then
  echo "لم يُحدَّد عنوان الموقع. اضبط SITE_URL أو مرّره كوسيط." >&2
  exit 1
fi

python3 tools/set-site-url.py "$URL"

# معاينات الفروع يجب ألا تُؤرشف، وإلا نافست الإنتاج في نتائج البحث
if [ "$BRANCH" != "$PRODUCTION_BRANCH" ]; then
  printf 'User-agent: *\nDisallow: /\n' > robots.txt
  echo "معاينة الفرع «$BRANCH» — مُنعت الأرشفة."
fi

python3 tools/check-links.py
