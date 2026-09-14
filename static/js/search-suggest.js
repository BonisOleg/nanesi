/* Підказки пошуку в хедері: назва / бренд / SKU → перехід на картку товару. */
(function () {
  var MIN_CHARS = 2;
  var DEBOUNCE_MS = 220;
  var LIMIT_HINT = 8;

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function initSuggest(form) {
    if (!form || form.dataset.suggestBound === "1") return;
    var url = form.getAttribute("data-suggest-url");
    var input = form.querySelector("[data-search-input]");
    var list = form.querySelector("[data-search-suggest]");
    if (!url || !input || !list) return;
    form.dataset.suggestBound = "1";

    var timer = 0;
    var controller = null;
    var active = -1;

    function hide() {
      list.hidden = true;
      list.innerHTML = "";
      active = -1;
      input.removeAttribute("aria-activedescendant");
    }

    function items() {
      return Array.prototype.slice.call(list.querySelectorAll("[data-suggest-index]"));
    }

    function setActive(index) {
      var rows = items();
      rows.forEach(function (row, i) {
        var on = i === index;
        row.classList.toggle("is-active", on);
        if (on) input.setAttribute("aria-activedescendant", row.id);
      });
      active = index;
    }

    function render(results) {
      if (!results.length) {
        hide();
        return;
      }
      list.innerHTML = results
        .slice(0, LIMIT_HINT)
        .map(function (item, i) {
          var brand = item.brand
            ? '<span class="search-suggest__brand">' + escapeHtml(item.brand) + "</span>"
            : "";
          return (
            '<li class="search-suggest__item" role="option" id="search-suggest-' +
            i +
            '" data-suggest-index="' +
            i +
            '">' +
            '<a class="search-suggest__link" href="' +
            escapeHtml(item.url) +
            '">' +
            '<span class="search-suggest__name">' +
            escapeHtml(item.name) +
            "</span>" +
            brand +
            "</a></li>"
          );
        })
        .join("");
      list.hidden = false;
      active = -1;
    }

    function fetchSuggest(q) {
      if (controller) controller.abort();
      controller = window.AbortController ? new AbortController() : null;
      var opts = { credentials: "same-origin", headers: { Accept: "application/json" } };
      if (controller) opts.signal = controller.signal;
      fetch(url + "?q=" + encodeURIComponent(q), opts)
        .then(function (res) {
          if (!res.ok) throw new Error("suggest");
          return res.json();
        })
        .then(function (data) {
          render((data && data.results) || []);
        })
        .catch(function (err) {
          if (err && err.name === "AbortError") return;
          hide();
        });
    }

    function schedule() {
      window.clearTimeout(timer);
      var q = (input.value || "").trim();
      if (q.length < MIN_CHARS) {
        hide();
        return;
      }
      timer = window.setTimeout(function () {
        fetchSuggest(q);
      }, DEBOUNCE_MS);
    }

    input.addEventListener("input", schedule);
    input.addEventListener("focus", schedule);

    input.addEventListener("keydown", function (e) {
      var rows = items();
      if (list.hidden || !rows.length) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive(active < rows.length - 1 ? active + 1 : 0);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive(active > 0 ? active - 1 : rows.length - 1);
      } else if (e.key === "Enter" && active >= 0) {
        var link = rows[active].querySelector("a");
        if (link) {
          e.preventDefault();
          window.location.href = link.href;
        }
      } else if (e.key === "Escape") {
        hide();
      }
    });

    document.addEventListener("click", function (e) {
      if (!form.contains(e.target)) hide();
    });

    form.addEventListener("close-suggest", hide);
  }

  function boot() {
    document.querySelectorAll("[data-header-search]").forEach(initSuggest);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
