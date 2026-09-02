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

  function boot() {
    initMobileMenu();
    initCatalogMenu();
    initWishlist();
    cleanupAfterLogin();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
