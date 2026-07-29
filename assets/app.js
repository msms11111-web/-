(() => {
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

  // تطبيع النص العربي: تشكيل وتطويل وهمزات وألف مقصورة وتاء مربوطة
  const normalize = (s) =>
    (s || "")
      .toLowerCase()
      .replace(/[ً-ْـ]/g, "")
      .replace(/[أإآٱ]/g, "ا")
      .replace(/ى/g, "ي")
      .replace(/ة/g, "ه")
      .replace(/[ؤئ]/g, "ء")
      .replace(/\s+/g, " ")
      .trim();

  // بحث الموسوعة: يقبل ?q= القادم من نموذج الصفحة الرئيسية
  const search = document.querySelector("[data-search]");
  if (search) {
    const entities = [...document.querySelectorAll("[data-entity]")];
    const count = document.querySelector("[data-count]");
    const empty = document.querySelector("[data-empty]");

    const filter = () => {
      const raw = search.value.trim();
      const terms = normalize(raw).split(" ").filter(Boolean);
      let hits = 0;
      entities.forEach((el) => {
        const hay = normalize((el.dataset.entity || "") + " " + el.textContent);
        const match = terms.every((t) => hay.includes(t));
        el.hidden = !match;
        if (match) hits++;
      });
      if (count) count.textContent = raw ? hits + " نتيجة" : entities.length + " مدخلًا";
      if (empty) empty.hidden = hits > 0;
    };

    const q = new URLSearchParams(location.search).get("q");
    if (q) search.value = q;
    search.addEventListener("input", filter);
    const btn = search.parentElement && search.parentElement.querySelector("button");
    if (btn) btn.addEventListener("click", () => { search.focus(); filter(); });
    filter();
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
