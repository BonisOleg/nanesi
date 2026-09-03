/* Hero-слайдер: fade, автопрокрутка 5с, фон/блюр через JS (CSP блокує inline style). */
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
    var timer = null;
    var leavingTimer = null;

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
        slides.forEach(function (s) { s.classList.remove("is-leaving"); });
      }

      prev.classList.remove("is-active");
      prev.classList.add("is-leaving");
      prev.setAttribute("aria-hidden", "true");

      curr.classList.add("is-active");
      curr.setAttribute("aria-hidden", "false");
      applySlideFx(curr);

      index = next;
      setDotState(index);

      leavingTimer = window.setTimeout(function () {
        prev.classList.remove("is-leaving");
        leavingTimer = null;
      }, prefersReducedMotion() ? 0 : 560);
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
  }

  function boot() {
    document.querySelectorAll("[data-hero-slider]").forEach(initSlider);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
