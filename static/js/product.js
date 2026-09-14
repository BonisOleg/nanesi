(function () {
  var mainImg = document.querySelector("[data-gallery-main]");
  document.querySelectorAll("[data-thumb]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (mainImg) mainImg.setAttribute("src", btn.getAttribute("data-thumb"));
      document.querySelectorAll("[data-thumb]").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
    });
  });

  document.querySelectorAll("[data-tab]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tab = btn.getAttribute("data-tab");
      document.querySelectorAll("[data-tab]").forEach(function (b) {
        var active = b === btn;
        b.classList.toggle("is-active", active);
        b.setAttribute("aria-selected", active ? "true" : "false");
      });
      document.querySelectorAll("[data-panel]").forEach(function (panel) {
        panel.classList.toggle("is-active", panel.getAttribute("data-panel") === tab);
      });
    });
  });

  var qtyInput = document.querySelector("[data-qty-value]");
  if (qtyInput) {
    var max = parseInt(qtyInput.getAttribute("max"), 10) || 999;
    document.querySelector("[data-qty-minus]")?.addEventListener("click", function () {
      var val = Math.max(1, (parseInt(qtyInput.value, 10) || 1) - 1);
      qtyInput.value = String(val);
    });
    document.querySelector("[data-qty-plus]")?.addEventListener("click", function () {
      var val = Math.min(max, (parseInt(qtyInput.value, 10) || 1) + 1);
      qtyInput.value = String(val);
    });
  }
  document.querySelectorAll("[data-review-file]").forEach(function (wrap) {
    var input = wrap.querySelector('input[type="file"]');
    var nameEl = wrap.querySelector("[data-review-file-name]");
    if (!input || !nameEl) return;
    var emptyText = nameEl.getAttribute("data-empty") || nameEl.textContent;
    input.addEventListener("change", function () {
      var files = input.files;
      if (!files || !files.length) {
        nameEl.textContent = emptyText;
        return;
      }
      var names = Array.prototype.map.call(files, function (f) {
        return f.name;
      });
      nameEl.textContent = names.join(", ");
    });
  });
})();
