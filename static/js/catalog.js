(function () {
  var FILTER_LIMIT = 3;
  var DESKTOP_MQ = "(min-width: 960px)";
  var filtersRoot = document.querySelector("[data-filters]");
  var form = document.getElementById("catalog-filter-form");
  var filtersBody = filtersRoot && filtersRoot.querySelector(".filters__body");
  var applyBtn = form && form.querySelector("[data-filters-apply]");
  var resetLink = form && form.querySelector("[data-filters-reset]");
  var appliedState = null;

  function isDesktopFilters() {
    return window.matchMedia(DESKTOP_MQ).matches;
  }

  function serializeFilters(root) {
    var checks = {};
    root.querySelectorAll('input[type="checkbox"][name]').forEach(function (input) {
      checks[input.name + "\0" + input.value] = !!input.checked;
    });
    var prices = {};
    ["price_min", "price_max"].forEach(function (name) {
      var el = root.querySelector('input[name="' + name + '"]');
      prices[name] = el ? String(el.value || "").trim() : "";
    });
    return { checks: checks, prices: prices };
  }

  function statesEqual(a, b) {
    if (!a || !b) return false;
    var key;
    for (key in a.checks) {
      if (Object.prototype.hasOwnProperty.call(a.checks, key) && !!a.checks[key] !== !!b.checks[key]) {
        return false;
      }
    }
    for (key in b.checks) {
      if (Object.prototype.hasOwnProperty.call(b.checks, key) && !!a.checks[key] !== !!b.checks[key]) {
        return false;
      }
    }
    return a.prices.price_min === b.prices.price_min && a.prices.price_max === b.prices.price_max;
  }

  /** Дефолт: лише «В наявності» увімкнено, решта порожня. */
  function isDefaultState(state) {
    if (!state) return true;
    if (state.prices.price_min || state.prices.price_max) return false;
    var key;
    for (key in state.checks) {
      if (!Object.prototype.hasOwnProperty.call(state.checks, key)) continue;
      var on = !!state.checks[key];
      var isStock = key.indexOf("stock\0") === 0;
      if (isStock) {
        if (!on) return false;
      } else if (on) {
        return false;
      }
    }
    return true;
  }

  function hasDraftChanges() {
    if (!form || !appliedState) return false;
    return !statesEqual(serializeFilters(form), appliedState);
  }

  function hasAppliedFilters() {
    return !isDefaultState(appliedState);
  }

  function restoreAppliedState() {
    if (!form || !appliedState) return;
    form.querySelectorAll('input[type="checkbox"][name]').forEach(function (input) {
      var key = input.name + "\0" + input.value;
      input.checked = !!appliedState.checks[key];
    });
    ["price_min", "price_max"].forEach(function (name) {
      var el = form.querySelector('input[name="' + name + '"]');
      if (el) el.value = appliedState.prices[name] || "";
    });
  }

  function setResetEnabled(on) {
    if (!resetLink) return;
    resetLink.classList.toggle("is-disabled", !on);
    resetLink.setAttribute("aria-disabled", on ? "false" : "true");
    if (on) resetLink.removeAttribute("tabindex");
    else resetLink.setAttribute("tabindex", "-1");
  }

  function setApplyEnabled(on) {
    if (!applyBtn) return;
    applyBtn.disabled = !on;
  }

  function syncFilterActions() {
    var draft = hasDraftChanges();
    var applied = hasAppliedFilters();
    /* Застосувати — лише коли draft ≠ applied (моб/планшет). */
    setApplyEnabled(draft);
    /* Скинути — є applied-фільтри або незастосовані зміни в панелі. */
    setResetEnabled(applied || draft);
  }

  var toggleBtn = document.querySelector("[data-filters-toggle]");
  if (toggleBtn && filtersRoot) {
    toggleBtn.addEventListener("click", function () {
      var open = filtersRoot.classList.toggle("is-open");
      toggleBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  function initFilterCollapse() {
    if (!filtersBody) return;
    var moreLabel = filtersBody.getAttribute("data-filter-more-label") || "Показати ще";
    var lessLabel = filtersBody.getAttribute("data-filter-less-label") || "Згорнути";

    filtersBody.querySelectorAll("[data-filter-collapse]").forEach(function (group) {
      if (group.dataset.collapseBound === "1") return;
      var limit = parseInt(group.getAttribute("data-filter-limit") || String(FILTER_LIMIT), 10);
      var labels = Array.prototype.filter.call(group.children, function (el) {
        return el.tagName === "LABEL";
      });
      if (labels.length <= limit) return;

      var extra = document.createElement("div");
      extra.className = "filter-group__extra";
      extra.hidden = true;

      var hiddenSelected = false;
      labels.forEach(function (label, index) {
        if (index < limit) return;
        var input = label.querySelector('input[type="checkbox"]');
        if (input && input.checked) hiddenSelected = true;
        extra.appendChild(label);
      });

      var hiddenCount = extra.children.length;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "filter-group__more";
      btn.setAttribute("aria-expanded", "false");

      function setCollapsed(collapsed) {
        extra.hidden = collapsed;
        btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
        btn.textContent = collapsed
          ? moreLabel + " (" + hiddenCount + ")"
          : lessLabel;
        group.classList.toggle("is-expanded", !collapsed);
      }

      setCollapsed(!hiddenSelected);
      btn.addEventListener("click", function () {
        setCollapsed(!extra.hidden);
      });

      group.appendChild(extra);
      group.appendChild(btn);
      group.dataset.collapseBound = "1";
    });
  }

  initFilterCollapse();

  if (form) {
    appliedState = serializeFilters(form);
    syncFilterActions();

    form.addEventListener("change", function (e) {
      var target = e.target;
      if (target.matches('input[type="checkbox"]')) {
        syncFilterActions();
        if (isDesktopFilters()) form.requestSubmit();
      }
    });

    form.addEventListener("input", function (e) {
      if (e.target.matches("#price-min, #price-max")) syncFilterActions();
    });

    form.addEventListener("submit", function (e) {
      if (isDesktopFilters()) return;
      if (!hasDraftChanges()) e.preventDefault();
    });

    form.querySelectorAll("#price-min, #price-max").forEach(function (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key !== "Enter") return;
        e.preventDefault();
        if (!isDesktopFilters() && !hasDraftChanges()) return;
        form.requestSubmit();
      });
      input.addEventListener("blur", function () {
        if (!isDesktopFilters()) return;
        if (input.defaultValue === input.value) return;
        form.requestSubmit();
      });
    });

    if (resetLink) {
      resetLink.addEventListener("click", function (e) {
        if (resetLink.getAttribute("aria-disabled") === "true") {
          e.preventDefault();
          return;
        }
        var draft = hasDraftChanges();
        var applied = hasAppliedFilters();
        /* Лише незастосовані зміни при чистому applied — без reload. */
        if (draft && !applied) {
          e.preventDefault();
          restoreAppliedState();
          syncFilterActions();
          return;
        }
        /* Є застосовані фільтри — перехід на reset URL. */
        if (!applied && !draft) {
          e.preventDefault();
        }
      });
    }
  }

  var sortSelect = document.querySelector("[data-catalog-sort]");
  if (sortSelect && form) {
    sortSelect.addEventListener("change", function () {
      form.requestSubmit();
    });
  }
})();
