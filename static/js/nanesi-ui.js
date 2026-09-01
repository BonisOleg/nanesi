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

  function updateBadge() {
    var badge = document.querySelector("[data-wishlist-count]");
    if (!badge || badge.dataset.serverManaged === "1") return;
    var count = readWishlist().length;
    badge.textContent = String(count);
    badge.classList.toggle("is-hidden", count === 0);
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
      btn.classList.toggle("is-active", ids.indexOf(id) !== -1);
    });
  }

  function initWishlist() {
    var badge = document.querySelector("[data-wishlist-count]");
    if (badge && badge.dataset.serverManaged === "1") return;
    syncButtonsState();
    updateBadge();
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-wish]");
      if (!btn) return;
      e.preventDefault();
      var id = String(btn.getAttribute("data-wish"));
      var ids = readWishlist().map(String);
      var idx = ids.indexOf(id);
      if (idx === -1) {
        ids.push(id);
      } else {
        ids.splice(idx, 1);
      }
      writeWishlist(ids);
      syncButtonsState();
      updateBadge();
    });
  }

  function initMobileMenu() {
    var panel = document.querySelector("[data-mobile-panel]");
    var openBtn = document.querySelector("[data-open-menu]");
    var closeBtn = document.querySelector("[data-close-menu]");
    if (!panel || !openBtn) return;

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
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMobileMenu();
    initWishlist();
    cleanupAfterLogin();
  });
})();
