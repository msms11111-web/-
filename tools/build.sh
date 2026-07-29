#!/bin/sh
# أمر البناء لـ Cloudflare Pages (وأي استضافة تشغّل أمرًا قبل النشر).
#
# في لوحة Cloudflare Pages:
#   Build command:        sh tools/build.sh
#   Build output directory: /
#
# CF_PAGES_URL يوفره Cloudflare وقت البناء. عند غيابه يُستخدم الوسيط الأول،
# فيمكن تشغيل السكربت يدويًا:  sh tools/build.sh https://example.com/
set -e

SITE_URL="${CF_PAGES_URL:-$1}"

if [ -z "$SITE_URL" ]; then
  echo "لم يُحدَّد عنوان الموقع. مرّره كوسيط أو اضبط CF_PAGES_URL." >&2
  exit 1
fi

python3 tools/set-site-url.py "$SITE_URL"
python3 tools/check-links.py
