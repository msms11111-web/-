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

if [ "$BRANCH" = "$PRODUCTION_BRANCH" ] && [ -n "$SITE_URL" ]; then
  URL="$SITE_URL"
else
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
