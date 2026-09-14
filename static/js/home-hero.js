/* Hero-слайдер: crossfade 1с, автопрокрутка 5с, фон/блюр через JS (CSP блокує inline style). */
(function () {
  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function applySlideFx(slide) {
    if (!slide) return;
    var blur = parseInt(slide.getAttribute("data-hero-blur"), 10) || 0;
    if (blur > 40) blur = 40;
    var overlay = (slide.getAttribute("data-hero-overlay") || "").trim();
    var photo = slide.querySelector("[data-hero-bg-photo]");
    var layer = slide.querySelector("[data-hero-bg-overlay]");

    if (photo) {
      if (blur > 0) {
        photo.classList.add("is-blurred");
        photo.style.setProperty("filter", "blur(" + blur + "px)");
        photo.style.setProperty("-webkit-filter", "blur(" + blur + "px)");
      } else {
        photo.classList.remove("is-blurred");
        photo.style.removeProperty("filter");
        photo.style.removeProperty("-webkit-filter");
      }
    }

    if (layer) {
      var hasOverlay = overlay && !/,\s*0(?:\.0+)?\s*\)$/.test(overlay);
      if (hasOverlay) {
        layer.hidden = false;
        layer.style.setProperty("background-color", overlay);
      } else {
        layer.hidden = true;
        layer.style.removeProperty("background-color");
      }
    }
  }

  function initSlider(root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll("[data-hero-slide]"));
    slides.forEach(applySlideFx);
    if (slides.length < 2) return;

    var intervalMs = parseInt(root.getAttribute("data-interval"), 10) || 5000;
    var index = Math.max(0, slides.findIndex(function (s) { return s.classList.contains("is-active"); }));
    if (index < 0) index = 0;
    var FADE_MS = 1000;
    var timer = null;
    var leavingTimer = null;
    var enterFrame = 0;

    function allDots() {
      return Array.prototype.slice.call(root.querySelectorAll("[data-hero-dot]"));
    }

    function setDotState(i) {
      allDots().forEach(function (dot) {
        var di = parseInt(dot.getAttribute("data-hero-index"), 10);
        var on = di === i;
        dot.classList.toggle("is-active", on);
        dot.setAttribute("aria-selected", on ? "true" : "false");
      });
    }

    function goTo(next) {
      if (next === index || next < 0 || next >= slides.length) return;
      var prev = slides[index];
      var curr = slides[next];

      if (leavingTimer) {
        window.clearTimeout(leavingTimer);
        leavingTimer = null;
      }
      if (enterFrame) {
        window.cancelAnimationFrame(enterFrame);
        enterFrame = 0;
      }
      slides.forEach(function (s) {
        s.classList.remove("is-leaving");
        s.classList.remove("is-entering");
        if (s !== curr && s !== prev) s.classList.remove("is-active");
      });

      prev.classList.remove("is-active");
      prev.classList.add("is-leaving");
      prev.setAttribute("aria-hidden", "true");

      curr.setAttribute("aria-hidden", "false");
      applySlideFx(curr);

      index = next;
      setDotState(index);

    function activate() {
      curr.classList.remove("is-entering");
      curr.classList.add("is-active");
      fitSlideTitle(curr);
    }

      function finishLeave() {
        prev.classList.remove("is-leaving");
        leavingTimer = null;
      }

      if (prefersReducedMotion()) {
        activate();
        finishLeave();
        return;
      }

      curr.classList.add("is-entering");
      fitSlideTitle(curr);
      enterFrame = window.requestAnimationFrame(function () {
        enterFrame = window.requestAnimationFrame(function () {
          enterFrame = 0;
          activate();
        });
      });

      leavingTimer = window.setTimeout(finishLeave, FADE_MS);
    }

    function nextSlide() {
      goTo((index + 1) % slides.length);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function start() {
      stop();
      if (prefersReducedMotion()) return;
      timer = window.setInterval(nextSlide, intervalMs);
    }

    root.addEventListener("click", function (e) {
      var dot = e.target.closest("[data-hero-dot]");
      if (!dot || !root.contains(dot)) return;
      var di = parseInt(dot.getAttribute("data-hero-index"), 10);
      if (isNaN(di)) return;
      goTo(di);
      start();
    });

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", function (e) {
      if (!root.contains(e.relatedTarget)) start();
    });

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else start();
    });

    var touchX = null;
    root.addEventListener("touchstart", function (e) {
      if (!e.changedTouches || !e.changedTouches[0]) return;
      touchX = e.changedTouches[0].clientX;
      stop();
    }, { passive: true });

    root.addEventListener("touchend", function (e) {
      if (touchX == null || !e.changedTouches || !e.changedTouches[0]) {
        start();
        return;
      }
      var dx = e.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) > 40) {
        if (dx < 0) goTo((index + 1) % slides.length);
        else goTo((index - 1 + slides.length) % slides.length);
      }
      start();
    }, { passive: true });

    setDotState(index);
    start();
    fitSlideTitle(slides[index]);
  }

  var TITLE_MIN_PX = 18;
  var TITLE_MAX_LINES = 2;
  var TITLE_FIT_MAX = 1200;

  function titleLineHeight(el) {
    var cs = window.getComputedStyle(el);
    var fs = parseFloat(cs.fontSize) || 16;
    var lh = cs.lineHeight;
    if (!lh || lh === "normal") return fs * 1.15;
    if (lh.indexOf("px") !== -1) return parseFloat(lh) || fs * 1.15;
    var n = parseFloat(lh);
    if (!n) return fs * 1.15;
    return n < 5 ? n * fs : n;
  }

  function titleLineCount(el) {
    var lh = titleLineHeight(el);
    if (lh <= 0) return 1;
    return Math.round(el.scrollHeight / lh);
  }

  function titleFitsLines(el) {
    return titleLineCount(el) <= TITLE_MAX_LINES;
  }

  function fitSlideTitle(slide) {
    var el = slide && slide.querySelector(".hero__title");
    if (!el) return;
    el.style.removeProperty("font-size");
    var width = window.innerWidth;
    if (width < 768 || width >= TITLE_FIT_MAX) return;
    if (!el.offsetWidth) return;
    if (titleFitsLines(el)) return;

    var start = parseFloat(window.getComputedStyle(el).fontSize) || 24;
    var lo = TITLE_MIN_PX;
    var hi = start;
    var best = TITLE_MIN_PX;
    for (var i = 0; i < 10; i++) {
      var mid = (lo + hi) / 2;
      el.style.setProperty("font-size", mid + "px");
      if (titleFitsLines(el)) {
        best = mid;
        lo = mid;
      } else {
        hi = mid;
      }
    }
    el.style.setProperty("font-size", best + "px");
  }

  function fitHeroTitles(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-hero-slide].is-active, [data-hero-slide].is-entering").forEach(fitSlideTitle);
  }

  function initHeroTitleFit() {
    if (document.documentElement.dataset.heroTitleFit === "1") return;
    document.documentElement.dataset.heroTitleFit = "1";

    var timer = 0;
    function schedule() {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        document.querySelectorAll("[data-hero-slider]").forEach(fitHeroTitles);
      }, 80);
    }

    schedule();
    window.addEventListener("resize", schedule, { passive: true });
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", schedule);
    }
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(schedule);
    }
  }

  function boot() {
    document.querySelectorAll("[data-hero-slider]").forEach(initSlider);
    initHeroTitleFit();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
