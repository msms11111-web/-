#!/usr/bin/env python3
"""جلبُ صورٍ موثّقة من Wikimedia Commons وتحويلُها إلى WebP، مع سجلٍّ كامل.

المصدر: API الرسمي https://commons.wikimedia.org/w/api.php للبحث والبيانات،
و upload.wikimedia.org لتنزيل المصغَّرة التي يُرجعها API في thumburl (iiurlwidth=1280، ثم 960
إن تكرّر 429) — لا الأصل، ولا رابطٌ مصوغٌ باليد، ولا مضيفٌ غيرهما.

التشغيل (بالخيار -I لأن الملفّات المنزَّلة بياناتٌ غير موثوقة):
  python3 -I fetch.py search "<طلب بحث>" [العدد]      # مرشّحون مع بياناتهم
  python3 -I fetch.py cat "Category:Coffea arabica" [العدد]   # ملفّات تصنيف
  python3 -I fetch.py info "File:A.jpg" "File:B.jpg"   # بياناتٌ كاملة
  python3 -I fetch.py build selection.json <مجلّد تنزيلٍ خارج المستودع> <جذر الخرج>
      (يكتب <جذر الخرج>/assets/images/*.webp و <جذر الخرج>/tools/dev/commons/manifest.json)
  python3 -I fetch.py plan selection.json <جذر الخرج>   # سجلٌّ بلا تنزيل (pending_download)

selection.json:
  {"accepted": [{"batch":1, "target_page":"…", "title":"File:…", "name":"latin-name",
                 "what_page_states":"…", "identity_check":"…"}],
   "skipped": [...], "not_found": [...]}
يحتاج Pillow (مع دعم WebP) لأمر build وحده؛ والباقي من المكتبة القياسية.
"""
import datetime, hashlib, html, io, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

API = "https://commons.wikimedia.org/w/api.php"
UA = "static-encyclopedia-image-fetch/1.0"
MIN_GAP = 1.2            # ثانيةٌ وزيادة بين كل طلبين من API
UPLOAD_GAP = 6.0         # وستُّ ثوانٍ بين كل تنزيلين من upload.wikimedia.org
MAX_W, MAX_BYTES = 1200, 150000
_last = [0.0]
THUMB_WIDTHS = (1280, 960)   # مقاسان قياسيّان من https://w.wiki/GHai — الثاني بعد تكرّر 429 على الأول
THUMB_HOST = "upload.wikimedia.org"

class Upload429(Exception):
    def __init__(self, retry_after, url):
        super().__init__(retry_after, url)
        self.retry_after, self.url = retry_after, url

def _get(url, binary=False):
    host = urllib.parse.urlsplit(url).hostname
    if host not in ("commons.wikimedia.org", "upload.wikimedia.org"):
        raise SystemExit("مضيفٌ غير مسموح: %s" % host)
    for attempt in range(4):
        wait = (UPLOAD_GAP if host.startswith("upload.") else MIN_GAP) - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and host.startswith("upload."):
                # لا يُكرَّر هنا: يقرّر المستدعي (build) انتظارَ Retry-After مرّةً واحدة أو النزولَ إلى مقاسٍ قياسيٍّ آخر
                raise Upload429(e.headers.get("Retry-After"), url)
            if e.code == 429 and attempt < 3:      # تحديدُ معدّل API: ننتظر ولا نلتفّ
                ra = e.headers.get("Retry-After", "")
                time.sleep(min(int(ra) if ra.isdigit() else 30 * (attempt + 1), 120))
                continue
            raise SystemExit("رُفض الاتصال: HTTP %s عند %s" % (e.code, url))
    raise SystemExit("تعذّر الاتصال")

def api(**p):
    p.update(format="json", formatversion="2", maxlag="5")
    pages, cont = {}, {}
    while True:
        q = dict(p); q.update(cont)
        d = json.loads(_get(API + "?" + urllib.parse.urlencode(q)))
        if "error" in d:
            raise SystemExit("خطأ API: %s" % d["error"])
        for pg in d.get("query", {}).get("pages", []):
            cur = pages.setdefault(pg["title"], pg)
            if cur is not pg:
                cur.setdefault("categories", []).extend(pg.get("categories", []))
                if "imageinfo" in pg and "imageinfo" not in cur:
                    cur["imageinfo"] = pg["imageinfo"]
        if "continue" in d and any(k in d["continue"] for k in ("clcontinue", "iicontinue")):
            cont = d["continue"]
        else:
            return list(pages.values())

PROPS = dict(prop="imageinfo|categories", iiprop="url|size|mime|sha1|extmetadata", cllimit="max")

def strip(s):
    s = re.sub(r"<(br|/p|/div|/li)[^>]*>", "\n", s or "", flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"[ \t]*\n\s*", "\n", re.sub(r"[ \t]+", " ", s)).strip()

def meta(pg):
    ii = (pg.get("imageinfo") or [{}])[0]
    em = {k: v.get("value", "") for k, v in (ii.get("extmetadata") or {}).items()}
    cats = [c["title"] for c in pg.get("categories", [])]
    return dict(title=pg["title"], url=ii.get("url"), w=ii.get("width"), h=ii.get("height"),
                mime=ii.get("mime"), sha1=ii.get("sha1"), descurl=ii.get("descriptionurl"),
                author=strip(em.get("Artist")), credit=strip(em.get("Credit")),
                lic=em.get("LicenseShortName", ""), lic_code=em.get("License", ""),
                lic_url=em.get("LicenseUrl", ""), usage=em.get("UsageTerms", ""),
                attr_req=em.get("AttributionRequired", ""), restr=em.get("Restrictions", ""),
                desc=strip(em.get("ImageDescription")), date=strip(em.get("DateTimeOriginal")),
                cats=cats, thumburl=ii.get("thumburl"), thumbw=ii.get("thumbwidth"), thumbh=ii.get("thumbheight"))

OK_LIC = re.compile(r"^(CC0( 1\.0)?|Public domain|PD.*|CC BY(-SA)? \d\.\d( [a-z-]+)?)$", re.I)
BAD_LIC = re.compile(r"\b(NC|ND)\b|fair use", re.I)
AI = re.compile(r"(?i:AI[- ]generated|generated by AI|generative|stable diffusion|midjourney|artificial intelligence|"
                r"made with AI|upscal)|DALL[-· ]?E\b|Dall-E")
FLAG = re.compile(r"deletion|missing permission|disputed|copyright violation|without a license|no license|"
                  r"license review needed|unknown copyright|no source|possibly unfree|speedy", re.I)

def problems(m):
    out = []
    if not m["lic"] or not m["lic_code"]:
        out.append("الترخيص غير ظاهر في extmetadata")
    elif not OK_LIC.match(m["lic"].strip()) or BAD_LIC.search(m["lic"] + " " + m["lic_code"]):
        out.append("ترخيص غير مقبول: %s" % m["lic"])
    elif m["lic"].upper().startswith("CC") and not m["lic_url"]:
        out.append("لا LicenseUrl")
    if m["lic_code"].lower().startswith("gfdl"):
        out.append("GFDL وحدها")
    blob = " ".join(m["cats"]) + " " + m["desc"] + " " + m["title"]
    if AI.search(blob):
        out.append("دلالة توليد بالذكاء الاصطناعي")
    f = [c for c in m["cats"] if FLAG.search(c)]
    if f:
        out.append("تنبيه: %s" % "; ".join(f))
    if m["mime"] not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
        out.append("صيغة: %s" % m["mime"])
    return out

def show(pages, full=False):
    for pg in pages:
        if "imageinfo" not in pg:
            print("--", pg["title"], "(لا بيانات)"); continue
        m = meta(pg); pr = problems(m)
        if not full and os.environ.get("MINW") and ((m["w"] or 0) < int(os.environ["MINW"]) or pr):
            continue
        if not full and os.environ.get("SHORT"):
            print("== %s | %sx%s | %s | %s | %s || %s" % (
                m["title"], m["w"], m["h"], m["lic"], m["author"][:40].replace("\n", " "),
                m["desc"][:int(os.environ["SHORT"])].replace("\n", " / "),
                "; ".join(c[9:] for c in m["cats"] if re.search(os.environ.get("CATRE", "offe"), c))))
            continue
        print("== %s\n   %sx%s %s | %s [%s] %s\n   by: %s | date: %s%s" % (
            m["title"], m["w"], m["h"], m["mime"], m["lic"], m["lic_code"], m["lic_url"],
            m["author"][:120].replace("\n", " / "), m["date"][:40],
            ("\n   !! " + " | ".join(pr)) if pr else ""))
        d = m["desc"].replace("\n", " / ")
        print("   desc:", d if full else d[:400])
        cs = [c[9:] for c in m["cats"]]
        if not full:
            cs = [c for c in cs if not re.match(r"(CC-|Self-pub|Files? |Uploaded|Media |Pages |Flickr|License|"
                  r"Photographs taken on|Taken with|Images with|GFDL|PD|Creative Commons|Quality|Valued|Featured|"
                  r"All |Author|Artworks|Template|Commons|Extracted|Retouched|Uploads|Nuvola|Location|Wiki|Photos by|Images by|Images from)", c)]
        print("   cats:", "; ".join(cs))
        if full:
            print("   credit:", m["credit"][:300], "| usage:", m["usage"], "| attr:", m["attr_req"],
                  "| restr:", m["restr"], "| sha1:", m["sha1"], "\n   url:", m["url"])

def convert(src, dst):
    from PIL import Image, ImageOps
    im = Image.open(src); im.load()
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:   # يُحوَّل إلى sRGB قبل حذف الملفّ اللوني كي لا تنحرف الألوان؛ ولا يُكتب في الخرج ملفٌّ لوني
        from PIL import ImageCms
        src_p = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        if im.mode not in ("RGB", "RGBA"):
            im = ImageCms.profileToProfile(im, src_p, ImageCms.createProfile("sRGB"), outputMode="RGB")
        else:
            im = ImageCms.profileToProfile(im, src_p, ImageCms.createProfile("sRGB"))
        im.info.pop("icc_profile", None)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") and "transparency" in im.info or im.mode == "RGBA" else "RGB")
    w0 = min(MAX_W, im.width)
    for w in [w0] + [x for x in (1100, 1000, 900, 800, 700, 600) if x < w0]:
        r = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        for q in (82, 78, 74, 70, 66, 62, 58, 54, 50):
            buf = io.BytesIO()
            r.save(buf, "WEBP", quality=q, method=6, exif=b"", icc_profile=None)
            if buf.tell() < MAX_BYTES:
                with open(dst, "wb") as f:
                    f.write(buf.getvalue())
                return r.width, r.height, buf.tell(), q
    raise SystemExit("تعذّر النزول تحت الحدّ: %s" % src)

def plan(sel_path, repo):
    """سجلٌّ بلا تنزيل: بياناتُ المرشّحين من API كما هي، تحت pending_download، و accepted فارغة."""
    sel = json.load(open(sel_path, encoding="utf-8"))
    pend = []
    for s in sel["accepted"]:
        m = meta(api(action="query", titles=s["title"], **PROPS)[0])
        pend.append({"batch": s["batch"], "target_page": s["target_page"],
                     "planned_file": "assets/images/%s.webp" % s["name"],
                     "commons_title": m["title"], "commons_url": m["descurl"], "original_url": m["url"].split("?")[0],
                     "original_width": m["w"], "original_height": m["h"], "original_sha1": m["sha1"],
                     "author": m["author"], "credit": m["credit"], "license_short": m["lic"],
                     "license_code": m["lic_code"], "license_url": m["lic_url"], "usage_terms": m["usage"],
                     "attribution_required": m["attr_req"], "restrictions": m["restr"],
                     "description": m["desc"], "date_original": m["date"], "categories": m["cats"],
                     "what_page_states": s["what_page_states"], "identity_check": s.get("identity_check", ""),
                     "automatic_checks": problems(m) or "سليم (الترخيص والتنبيهات ودلالات التوليد)",
                     "not_yet_checked": "لم تُعايَن الصورةُ بصريًّا: الوجوه والعلامات المائية والشعارات لم تُفحص",
                     "note": s.get("note", "")})
        print("pending", m["title"], m["lic"], problems(m))
    man = {"retrieved": datetime.date.today().isoformat(), "download_blocked": sel.get("download_blocked", {}),
           "accepted": [], "pending_download": pend,
           "skipped": sel.get("skipped", []), "not_found": sel.get("not_found", [])}
    d = os.path.join(repo, "tools", "dev", "commons"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1); f.write("\n")

def _manifest(repo, sel, acc, pend, thumbs, prev):
    man = {"retrieved": datetime.date.today().isoformat(), "thumbnails": thumbs}
    if prev.get("download_blocked"):
        man["originals_blocked_earlier"] = prev["download_blocked"]
    man.update(accepted=acc, pending_download=pend,
               skipped=sel.get("skipped", []), not_found=sel.get("not_found", []))
    d = os.path.join(repo, "tools", "dev", "commons"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1); f.write("\n")

def _thumb_meta(title, width):
    return meta(api(action="query", titles=title, iiurlwidth=str(width), **PROPS)[0])

def build(sel_path, dl_dir, repo):
    # تُنزَّل المصغّرةُ التي يُرجعها API في thumburl بمقاسٍ قياسيّ (iiurlwidth)، لا الأصل، ولا يُصاغ رابطٌ باليد.
    # dl_dir: مجلّدٌ خارج المستودع أُنشئ لهذا الغرض وحدَه؛ كلُّ ملفٍّ في مجلّدٍ فرعيٍّ باسم sha1 الأصل.
    rp, dp = os.path.realpath(repo), os.path.realpath(dl_dir)
    if dp == rp or dp.startswith(rp + os.sep):
        raise SystemExit("مجلّد التنزيل داخل المستودع: %s" % dl_dir)
    os.makedirs(dl_dir, exist_ok=True)
    sel = json.load(open(sel_path, encoding="utf-8"))
    mpath = os.path.join(repo, "tools", "dev", "commons", "manifest.json")
    prev = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
    plans = {p["commons_title"]: p for p in prev.get("pending_download", [])}
    out_dir = os.path.join(repo, "assets", "images"); os.makedirs(out_dir, exist_ok=True)
    wi = 0
    thumbs = {"source": "thumburl من API (prop=imageinfo، iiurlwidth)", "widths_tried": [THUMB_WIDTHS[0]],
              "required_host": THUMB_HOST, "host_seen": None, "events": []}
    acc, todo = [], list(sel["accepted"])

    def stop(msg):
        thumbs["stopped"] = msg
        _manifest(repo, sel, acc, [plans.get(s["title"], s) for s in todo], thumbs, prev)
        raise SystemExit(msg)

    while todo:
        s = todo[0]
        m = _thumb_meta(s["title"], THUMB_WIDTHS[wi])
        pr = problems(m)
        if pr:
            stop("مرفوضٌ آليًّا %s: %s" % (s["title"], pr))
        turl = m["thumburl"]
        host = urllib.parse.urlsplit(turl or "").hostname
        if thumbs["host_seen"] is None:
            print("thumburl (أول مرشَّح):", turl)
            thumbs["host_seen"], thumbs["first_thumburl"] = host, turl
        if host != THUMB_HOST:
            stop("مضيفُ المصغّر %s لا %s: توقّفنا قبل أي تنزيل ولم نجرّب مضيفًا آخر ولا رابطًا مصوغًا باليد (%s)"
                 % (host, THUMB_HOST, turl))
        sub = os.path.join(dl_dir, m["sha1"]); src = os.path.join(sub, "thumb-%d.bin" % m["thumbw"])
        if not os.path.exists(src):
            raw, waited = None, False
            while raw is None:
                try:
                    raw = _get(turl, True)
                except Upload429 as e:
                    ev = "HTTP 429 (Retry-After: %s) عند %s" % (e.retry_after, e.url)
                    thumbs["events"].append(ev); print(ev)
                    if not waited:
                        waited = True
                        ra = e.retry_after if (e.retry_after or "").isdigit() else "60"
                        print("ننتظر Retry-After كاملًا:", ra, "ثانية"); time.sleep(int(ra))
                        continue
                    if wi + 1 < len(THUMB_WIDTHS):
                        wi += 1; thumbs["widths_tried"].append(THUMB_WIDTHS[wi])
                        print("تكرّر 429؛ ننتقل إلى iiurlwidth=%d" % THUMB_WIDTHS[wi])
                        break
                    stop("تكرّر HTTP 429 على المصغّرات بالمقاسين %s: توقّفنا" % (THUMB_WIDTHS,))
            if raw is None:
                continue          # يُعاد الطلب من API بالمقاس الجديد لهذا المرشَّح نفسِه
            os.makedirs(sub, exist_ok=True)
            with open(src, "wb") as f:
                f.write(raw)
        dsha = hashlib.sha1(open(src, "rb").read()).hexdigest()
        rel = "assets/images/%s.webp" % s["name"]
        w, h, n, q = convert(src, os.path.join(repo, rel))
        dw = m["thumbw"]
        ch = "نُزِّلت نسخةُ ويكيميديا المصغَّرة بعرض %d، و" % dw
        ch += ("صُغِّرت إلى عرض %d بكسل وحُوِّلت" % w) if w < dw else ("لم تُصغَّر (عرضها %d بكسل) وحُوِّلت" % w)
        ch += " إلى WebP بجودة %d" % q
        if dw >= (m["w"] or 0):
            ch += " — والمقاسُ المطلوب أكبرُ من الأصل، فالرابطُ الذي أرجعه API هو الأصلُ نفسُه"
        acc.append({"batch": s["batch"], "target_page": s["target_page"], "file": rel, "width": w, "height": h,
                    "bytes": n, "downloaded_from": turl, "downloaded_width": dw, "downloaded_height": m["thumbh"],
                    "downloaded_sha1": dsha,
                    "commons_title": m["title"], "commons_url": m["descurl"], "original_url": m["url"],
                    "original_width": m["w"], "original_height": m["h"], "original_sha1": m["sha1"],
                    "author": m["author"], "credit": m["credit"], "license_short": m["lic"],
                    "license_code": m["lic_code"], "license_url": m["lic_url"], "usage_terms": m["usage"],
                    "attribution_required": m["attr_req"], "restrictions": m["restr"],
                    "description": m["desc"], "date_original": m["date"], "categories": m["cats"],
                    "what_page_states": s["what_page_states"], "identity_check": s.get("identity_check", ""),
                    "automatic_checks": "سليم (الترخيص والتنبيهات ودلالات التوليد)",
                    "visual_check": "", "changes": ch, "note": s.get("note", "")})
        print("ok", rel, w, h, n, "q", q, "from", dw)
        todo.pop(0)
    _manifest(repo, sel, acc, [], thumbs, prev)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["search"]:
        show(api(action="query", generator="search", gsrnamespace="6", gsrsearch=a[1],
                 gsrlimit=a[2] if len(a) > 2 else "15", **PROPS))
    elif a[:1] == ["cat"]:
        show(api(action="query", generator="categorymembers", gcmtitle=a[1], gcmtype="file",
                 gcmlimit=a[2] if len(a) > 2 else "30", **PROPS))
    elif a[:1] == ["info"]:
        show(api(action="query", titles="|".join(a[1:]), **PROPS), full=True)
    elif a[:1] == ["plan"]:
        plan(a[1], a[2])
    elif a[:1] == ["build"]:
        build(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)
