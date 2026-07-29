(() => {
  // مسار مجلد assets وجذر الموقع، مشتقان من مسار هذا الملف نفسه
  const SCRIPT_DIR = new URL(".", (document.currentScript && document.currentScript.src) || location.href);
  const SITE_ROOT = new URL("../", SCRIPT_DIR);

  // القائمة الجانبية على الشاشات الصغيرة
  const menuBtn = document.querySelector("[data-menu]");
  const drawer = document.querySelector("[data-drawer]");
  if (menuBtn && drawer) {
    const setOpen = (open) => {
      drawer.classList.toggle("open", open);
      menuBtn.setAttribute("aria-expanded", String(open));
    };
    menuBtn.addEventListener("click", () => setOpen(!drawer.classList.contains("open")));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") setOpen(false);
    });
  }

  /* تطبيع النص العربي مع خريطة مواضع.
     التشكيل والتطويل يُحذفان، فيتغير طول النص. بدون الخريطة تنزلق مواضع
     التعليم على النص الأصلي، ويُعلَّم حرف غير الذي طابق. */
  const fold = (input) => {
    const source = input || "";
    let text = "";
    const map = [];
    for (let i = 0; i < source.length; i++) {
      let c = source[i].toLowerCase();
      if (/[ً-ْـ]/.test(c)) continue;
      if (/[أإآٱ]/.test(c)) c = "ا";
      else if (c === "ى") c = "ي";
      else if (c === "ة") c = "ه";
      else if (/[ؤئ]/.test(c)) c = "ء";
      else if (/\s/.test(c)) {
        if (!text || text.endsWith(" ")) continue;
        c = " ";
      } else {
        // الأرقام العربية والفارسية تُوحَّد، ليجد «٢١٠٠» النص المكتوب «2100»
        const d = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹".indexOf(c);
        if (d >= 0) c = String(d % 10);
      }
      text += c;
      map.push(i);
    }
    return { text, map };
  };

  const normalize = (s) => fold(s).text.trim();

  /* أسماء تُكتب بالرسمين: المصادر لاتينية والقارئ يكتب بالعربية.
     بدون هذا لا تجد «يونسكو» صفحةً تكتبها UNESCO. */
  const ALIASES = [
    ["يونسكو", "unesco"],
    ["هاريو", "hario"],
    ["اثيوبيا", "ethiopia"],
    ["قوجي", "guji"],
    ["ديجا", "ديغا", "dega", "deiga"],
    ["ارابيكا", "arabica"],
    ["جازان", "jazan", "jizan"],
    ["خولاني", "khawlani"],
    ["جما", "jimma", "jma"],
    ["اوروميا", "oromia"],
  ].map((group) => group.map(normalize));

  // كل كلمة تتوسع إلى صيغها المكافئة، وتكفي واحدة منها للمطابقة
  const expand = (word) => {
    for (const group of ALIASES) if (group.includes(word)) return group;
    return [word];
  };

  const terms = (s) => normalize(s).split(" ").filter(Boolean);

  const escape = (s) =>
    s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // مواضع كل مطابقة على النص الأصلي، مرتبة وغير متداخلة
  const spans = (text, words) => {
    const f = fold(text);
    const found = [];
    words.forEach((w) => {
      for (let i = f.text.indexOf(w); i >= 0; i = f.text.indexOf(w, i + w.length)) {
        found.push([f.map[i], f.map[i + w.length - 1] + 1]);
      }
    });
    found.sort((a, b) => a[0] - b[0]);
    return found.filter((s, i) => i === 0 || s[0] >= found[i - 1][1]);
  };

  const highlight = (text, words, from, to) => {
    let out = "";
    let cursor = from;
    for (const [s, e] of spans(text, words)) {
      if (e <= from || s >= to || s < cursor) continue;
      out += escape(text.slice(cursor, s)) + "<mark>" + escape(text.slice(s, e)) + "</mark>";
      cursor = e;
    }
    return out + escape(text.slice(cursor, to));
  };

  // مقتطف حول أول مطابقة، مع تعليم كل المطابقات داخل النافذة
  const excerpt = (text, words) => {
    const hit = spans(text, words)[0];
    const start = hit ? Math.max(0, hit[0] - 60) : 0;
    const end = Math.min(text.length, (hit ? hit[0] : 0) + 150);
    return (
      (start > 0 ? "…" : "") + highlight(text, words, start, end) + (end < text.length ? "…" : "")
    );
  };

  const search = document.querySelector("[data-search]");
  if (search) initSearch(search);

  function initSearch(input) {
    const entities = [...document.querySelectorAll("[data-entity]")];
    const grid = document.querySelector(".entities");
    const panel = document.querySelector("[data-results]");
    const count = document.querySelector("[data-count]");
    const empty = document.querySelector("[data-empty]");

    // فهرس نص كل الصفحات، يُبنى وقت النشر. لو تعذّر تحميله يعمل البحث على البطاقات.
    let index = null;

    /* مطابقة الأجزاء وحدها تخلط كلمات لا علاقة بينها: «دلة» تُطبَّع «دله»
       وهي جزء من «أدلة». فتُرصد بداية الكلمة، ويُعدّ «ال» التعريف حدًّا،
       لتبقى «مجففة» تجد «المجففة». */
    // السوابق المتصلة في العربية تتراكم: و + ال + الكلمة («والدلة»)، ف/ب/ك/ل كذلك
    const PREFIX = /^[وفبكل]{0,2}(ال)?$/;

    const findIn = (hay, w) => {
      let any = false;
      for (let i = hay.indexOf(w); i >= 0; i = hay.indexOf(w, i + 1)) {
        any = true;
        const start = hay.lastIndexOf(" ", i - 1) + 1;
        if (PREFIX.test(hay.slice(start, i))) return { any: true, atWord: true };
      }
      return { any, atWord: false };
    };

    const FIELDS = [["title", 6], ["headings", 3], ["desc", 2], ["text", 1]];

    const score = (page, groups) => {
      let total = 0;
      for (const group of groups) {
        // تكفي صيغة واحدة من صيغ الكلمة، لكن كل كلمة مطلوبة
        let best = 0;
        for (const w of group) {
          // الكلمات القصيرة تُقبل عند بداية كلمة فقط، وإلا امتلأت النتائج بمطابقات عابرة
          const needWord = w.length <= 3;
          let sum = 0;
          for (const [field, weight] of FIELDS) {
            const r = findIn(page.n[field], w);
            if (!r.any || (needWord && !r.atWord)) continue;
            sum += weight * (r.atWord ? 2 : 1);
          }
          if (sum > best) best = sum;
        }
        if (!best) return 0; // لا صيغة من هذه الكلمة موجودة
        total += best;
      }
      // الرئيسية تلمّح إلى كل شيء فتتصدر كل بحث، وهي صفحة هبوط لا مدخل موسوعي
      return page.url === "" ? total * 0.45 : total;
    };

    const showBrowse = () => {
      if (panel) {
        panel.hidden = true;
        panel.innerHTML = "";
      }
      if (grid) grid.hidden = false;
      entities.forEach((el) => (el.hidden = false));
      if (count) count.textContent = entities.length + " مدخلًا";
      if (empty) empty.hidden = true;
    };

    const renderResults = (groups) => {
      const words = groups.flat(); // التعليم يشمل كل الصيغ، فتُبرز الصيغة الموجودة فعلًا
      const hits = index
        .map((page) => ({ page, s: score(page, groups) }))
        .filter((x) => x.s > 0)
        .sort((a, b) => b.s - a.s);

      if (grid) grid.hidden = true;
      panel.hidden = false;
      panel.innerHTML = hits
        .map(
          ({ page }) =>
            `<a class="result" href="${escape(page.href)}">` +
            `<h3>${highlight(page.title, words, 0, page.title.length)}</h3>` +
            `<p>${excerpt(page.text || page.desc, words)}</p></a>`
        )
        .join("");

      if (count) count.textContent = hits.length + " نتيجة";
      if (empty) empty.hidden = hits.length > 0;
    };

    const filterCards = (words) => {
      let hits = 0;
      entities.forEach((el) => {
        const hay = normalize((el.dataset.entity || "") + " " + el.textContent);
        const match = words.every((w) => hay.includes(w));
        el.hidden = !match;
        if (match) hits++;
      });
      if (count) count.textContent = hits + " نتيجة";
      if (empty) empty.hidden = hits > 0;
    };

    const run = () => {
      const words = terms(input.value);
      if (!words.length) return showBrowse();
      if (index && panel) renderResults(words.map(expand));
      else filterCards(words);
    };

    const q = new URLSearchParams(location.search).get("q");
    if (q) input.value = q;
    input.addEventListener("input", run);
    const btn = input.parentElement && input.parentElement.querySelector("button");
    if (btn)
      btn.addEventListener("click", () => {
        input.focus();
        run();
      });
    run();

    fetch(new URL("search-index.json", SCRIPT_DIR))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!Array.isArray(data)) return;
        index = data.map((p) => ({
          ...p,
          href: new URL(p.url, SITE_ROOT).href,
          n: {
            title: normalize(p.title),
            desc: normalize(p.desc),
            headings: normalize((p.headings || []).join(" ")),
            text: normalize(p.text),
          },
        }));
        run();
      })
      .catch(() => {});
  }

  // ظهور تدريجي للعناصر عند التمرير
  const faders = document.querySelectorAll(".fade");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.1 }
    );
    faders.forEach((x) => io.observe(x));
  } else {
    faders.forEach((x) => x.classList.add("in"));
  }

  document.querySelectorAll("[data-year]").forEach((x) => {
    x.textContent = new Date().getFullYear();
  });
})();
