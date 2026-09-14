/* Спільна UI-логіка сайту: мобільне меню, обране (гість → localStorage).
   Авторизовані користувачі — реальний сервер-синк додається в кабінеті (Підетап 2). */
(function () {
  var WISH_KEY = "nanesi_wishlist";

  function readWishlist() {
    try {
      var raw = window.localStorage.getItem(WISH_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function writeWishlist(ids) {
    try {
      window.localStorage.setItem(WISH_KEY, JSON.stringify(ids));
    } catch (e) {
      /* localStorage недоступний (приватний режим тощо) — тихо ігноруємо */
    }
  }

  function paintWishButton(btn, active) {
    btn.classList.toggle("is-active", active);
    var svg = btn.querySelector("svg");
    if (svg) svg.setAttribute("fill", active ? "currentColor" : "none");
    var on = btn.getAttribute("data-label-on");
    var off = btn.getAttribute("data-label-off");
    var label = btn.querySelector("[data-wish-label]");
    if (label && on && off) label.textContent = active ? on : off;
  }

  function paintWishById(id, active) {
    document.querySelectorAll("[data-wish=\"" + id + "\"]").forEach(function (btn) {
      paintWishButton(btn, active);
    });
  }

  function setBadgeCount(count) {
    var badge = document.querySelector("[data-wishlist-count]");
    if (!badge) return;
    badge.textContent = String(count);
    badge.classList.toggle("is-hidden", count === 0);
  }

  function updateBadge() {
    var badge = document.querySelector("[data-wishlist-count]");
    if (!badge || badge.dataset.serverManaged === "1") return;
    setBadgeCount(readWishlist().length);
  }

  function cleanupAfterLogin() {
    /* Після входу гостьовий localStorage вже синкнуто на сервері формою
       вхід/реєстрація (auth.js) — тут лише прибираємо, щоб не тримати дублікат. */
    var badge = document.querySelector("[data-wishlist-count]");
    if (badge && badge.dataset.serverManaged === "1") {
      writeWishlist([]);
    }
  }

  function syncButtonsState() {
    var ids = readWishlist().map(String);
    document.querySelectorAll("[data-wish]").forEach(function (btn) {
      var id = btn.getAttribute("data-wish");
      paintWishButton(btn, ids.indexOf(id) !== -1);
    });
  }

  function initGuestWishlist() {
    var badge = document.querySelector("[data-wishlist-count]");
    if (badge && badge.dataset.serverManaged === "1") return;
    syncButtonsState();
    updateBadge();
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-wish]");
      if (!btn || btn.closest("[data-wish-form]")) return;
      e.preventDefault();
      var id = String(btn.getAttribute("data-wish"));
      var ids = readWishlist().map(String);
      var idx = ids.indexOf(id);
      var active = idx === -1;
      if (active) ids.push(id);
      else ids.splice(idx, 1);
      writeWishlist(ids);
      paintWishById(id, active);
      updateBadge();
    });
  }

  function initAuthWishlist() {
    var badge = document.querySelector("[data-wishlist-count]");
    if (!badge || badge.dataset.serverManaged !== "1") return;
    document.addEventListener("submit", function (e) {
      var form = e.target.closest("[data-wish-form]");
      if (!form) return;
      e.preventDefault();
      if (form.dataset.wishBusy === "1") return;
      var token = form.querySelector("[name=csrfmiddlewaretoken]");
      var btn = form.querySelector("[data-wish]");
      if (!token || !btn) return;
      form.dataset.wishBusy = "1";
      btn.disabled = true;
      fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
          "X-CSRFToken": token.value,
        },
        body: new FormData(form),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("wish");
          return res.json();
        })
        .then(function (data) {
          paintWishById(btn.getAttribute("data-wish"), Boolean(data.active));
          setBadgeCount(data.count);
        })
        .catch(function () {
          form.submit();
        })
        .finally(function () {
          form.dataset.wishBusy = "";
          btn.disabled = false;
        });
    });
  }

  function initWishlist() {
    initGuestWishlist();
    initAuthWishlist();
  }

  function initCatalogMenu() {
    var toggle = document.querySelector("[data-catalog-toggle]");
    var panel = document.querySelector("[data-catalog-panel]");
    if (!toggle || !panel || toggle.dataset.catalogBound === "1") return;
    toggle.dataset.catalogBound = "1";

    function isOpen() {
      return !panel.hasAttribute("hidden");
    }

    function onKey(e) {
      if (e.key === "Escape") closeMenu();
    }

    function openMenu() {
      if (isOpen()) return;
      panel.removeAttribute("hidden");
      toggle.setAttribute("aria-expanded", "true");
      document.addEventListener("keydown", onKey);
    }

    function closeMenu() {
      if (!isOpen()) return;
      panel.setAttribute("hidden", "");
      toggle.setAttribute("aria-expanded", "false");
      document.removeEventListener("keydown", onKey);
    }

    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (isOpen()) closeMenu();
      else openMenu();
    });

    document.addEventListener("click", function (e) {
      if (!isOpen()) return;
      if (toggle.contains(e.target) || panel.contains(e.target)) return;
      closeMenu();
    });
  }

  function initMobileMenu() {
    var panel = document.querySelector("[data-mobile-panel]");
    var openBtn = document.querySelector("[data-open-menu]");
    var closeBtn = document.querySelector("[data-close-menu]");
    if (!panel || !openBtn || openBtn.dataset.menuBound === "1") return;
    openBtn.dataset.menuBound = "1";

    function open() {
      panel.classList.add("is-open");
      document.body.style.overflow = "hidden";
    }
    function close() {
      panel.classList.remove("is-open");
      document.body.style.overflow = "";
    }

    openBtn.addEventListener("click", open);
    if (closeBtn) closeBtn.addEventListener("click", close);
    var backdrop = panel.querySelector("[data-mobile-backdrop]");
    if (backdrop) backdrop.addEventListener("click", close);

    panel.querySelectorAll("[data-mobile-acc-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var group = btn.closest("[data-mobile-acc]");
        if (!group) return;
        var willOpen = !group.classList.contains("is-open");
        panel.querySelectorAll("[data-mobile-acc].is-open").forEach(function (other) {
          if (other === group) return;
          other.classList.remove("is-open");
          var otherBtn = other.querySelector("[data-mobile-acc-toggle]");
          var otherPanel = other.querySelector(".mobile-panel__children");
          if (otherBtn) otherBtn.setAttribute("aria-expanded", "false");
          if (otherPanel) otherPanel.hidden = true;
        });
        group.classList.toggle("is-open", willOpen);
        btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
        var children = group.querySelector(".mobile-panel__children");
        if (children) children.hidden = !willOpen;
      });
    });
  }

  function initTopbarScroll() {
    var chrome = document.querySelector("[data-site-chrome]");
    var topbar = chrome && chrome.querySelector(".topbar");
    if (!chrome || !topbar || chrome.dataset.topbarBound === "1") return;
    chrome.dataset.topbarBound = "1";

    /* Hide потребує більшого «наміру» вниз; show — вгору або майже top.
       Lock після toggle глушить зворотний зв’язок від зміни висоти sticky. */
    var HIDE_AFTER = 48;
    var SHOW_AFTER = 72;
    var TOP = 16;
    /* трохи довше за CSS transition (0.28s), щоб layout-стрибок не гойдав стан */
    var LOCK_MS = 320;
    var lastY = window.pageYOffset || 0;
    var acc = 0;
    var hidden = false;
    var ticking = false;
    var lockedUntil = 0;

    function setHidden(next) {
      if (next === hidden) return;
      hidden = next;
      chrome.classList.toggle("is-topbar-hidden", hidden);
      topbar.setAttribute("aria-hidden", hidden ? "true" : "false");
      if (hidden) topbar.setAttribute("inert", "");
      else topbar.removeAttribute("inert");
      lockedUntil = performance.now() + LOCK_MS;
      acc = 0;
      window.requestAnimationFrame(function () {
        window.requestAnimationFrame(function () {
          lastY = yPos();
          acc = 0;
        });
      });
    }

    function yPos() {
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      return y < 0 ? 0 : y;
    }

    function update() {
      ticking = false;
      var y = yPos();
      var now = performance.now();
      if (now < lockedUntil) {
        lastY = y;
        acc = 0;
        return;
      }

      var delta = y - lastY;
      lastY = y;

      if (y <= TOP) {
        acc = 0;
        setHidden(false);
        return;
      }

      /* Ігноруємо субпіксельний шум трекпада / iOS */
      if (delta > -0.5 && delta < 0.5) return;

      if ((acc > 0 && delta < 0) || (acc < 0 && delta > 0)) acc = 0;
      acc += delta;

      if (!hidden && acc >= HIDE_AFTER) {
        setHidden(true);
      } else if (hidden && acc <= -SHOW_AFTER) {
        setHidden(false);
      }
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initHeaderSearch() {
    var header = document.querySelector("[data-site-header]");
    var toggle = document.querySelector("[data-search-toggle]");
    var form = document.querySelector("[data-header-search]");
    var closeBtn = form && form.querySelector("[data-search-close]");
    var input = form && form.querySelector("input[type='search']");
    if (!header || !toggle || !form || toggle.dataset.searchBound === "1") return;
    toggle.dataset.searchBound = "1";

    var desktop = window.matchMedia("(min-width: 900px)");

    function isOpen() {
      return header.classList.contains("is-search-open");
    }

    function closeSearch() {
      if (!isOpen()) return;
      header.classList.remove("is-search-open");
      toggle.setAttribute("aria-expanded", "false");
      if (form) form.dispatchEvent(new Event("close-suggest"));
    }

    function openSearch() {
      if (desktop.matches) return;
      header.classList.add("is-search-open");
      toggle.setAttribute("aria-expanded", "true");
      window.setTimeout(function () {
        if (input) input.focus();
      }, 50);
    }

    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      if (isOpen()) closeSearch();
      else openSearch();
    });

    if (closeBtn) closeBtn.addEventListener("click", closeSearch);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeSearch();
    });

    if (desktop.addEventListener) {
      desktop.addEventListener("change", function () {
        if (desktop.matches) closeSearch();
      });
    }
  }

  function boot() {
    initMobileMenu();
    initCatalogMenu();
    initWishlist();
    cleanupAfterLogin();
    initTopbarScroll();
    initHeaderSearch();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
