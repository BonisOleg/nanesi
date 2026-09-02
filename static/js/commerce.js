/* Встановлення прогрес-бару безкоштовної доставки через CSSOM (element.style),
   а не через HTML style="" — щоб не порушувати CSP style-src 'self' (без unsafe-inline). */
function applyShippingFill(root) {
  (root || document).querySelectorAll('[data-js="shipping-fill"]').forEach(function (el) {
    var fill = parseFloat(el.getAttribute("data-fill") || "0");
    el.style.width = Math.min(100, Math.max(0, fill)) + "%";
  });
}

function setCartCount(count) {
  var badge = document.querySelector("[data-cart-count]");
  if (!badge) return;
  badge.textContent = String(count);
  badge.classList.toggle("is-hidden", !count);
}

function markInCart(productId, variantId) {
  var pid = String(productId || "");
  var vid = String(variantId || "");
  if (pid) {
    document.querySelectorAll('[data-cart-product="' + pid + '"]').forEach(function (el) {
      if (el.matches(".btn--icon, .btn--primary, [data-cart-pick-toggle]")) {
        el.classList.add("is-in-cart");
        var labelIn = el.getAttribute("data-label-in");
        if (labelIn) el.setAttribute("aria-label", labelIn);
      }
    });
  }
  if (vid) {
    document.querySelectorAll('[data-cart-variant="' + vid + '"]').forEach(function (el) {
      if (el.matches(".product-card__pick-option, .btn--primary")) {
        el.classList.add("is-in-cart");
      }
    });
  }
}

function closeCartPicks() {
  document.querySelectorAll("[data-cart-pick-root].is-open").forEach(function (root) {
    root.classList.remove("is-open");
    var panel = root.querySelector("[data-cart-pick]");
    var toggle = root.querySelector("[data-cart-pick-toggle]");
    if (panel) panel.hidden = true;
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    var card = root.closest(".product-card");
    if (card) card.classList.remove("is-picking");
  });
}

function openCartPick(root) {
  closeCartPicks();
  var panel = root.querySelector("[data-cart-pick]");
  var toggle = root.querySelector("[data-cart-pick-toggle]");
  var err = root.querySelector("[data-cart-error]");
  if (!panel) return;
  root.classList.add("is-open");
  panel.hidden = false;
  if (toggle) toggle.setAttribute("aria-expanded", "true");
  if (err) {
    err.hidden = true;
    err.textContent = "";
  }
  var card = root.closest(".product-card");
  if (card) card.classList.add("is-picking");
}

function flashCartButton(form) {
  var root = form.closest("[data-cart-pick-root]");
  var btn =
    form.querySelector(".btn--icon, .btn--primary[type=submit]") ||
    (root && root.querySelector("[data-cart-pick-toggle]"));
  if (!btn) return;
  btn.classList.add("is-added");
  var labelDone = btn.getAttribute("data-label-done");
  var labelIn = btn.getAttribute("data-label-in");
  var prevText = btn.textContent;
  if (labelDone && btn.matches(".btn--primary")) btn.textContent = labelDone;
  window.setTimeout(function () {
    btn.classList.remove("is-added");
    if (labelIn && btn.matches(".btn--primary")) btn.textContent = labelIn;
    else if (labelDone && btn.matches(".btn--primary")) btn.textContent = prevText;
  }, 1200);
}

function submitCartForm(form) {
  if (form.dataset.cartBusy === "1") return;
  var token = form.querySelector("[name=csrfmiddlewaretoken]");
  if (!token) return;
  form.dataset.cartBusy = "1";
  var body = new FormData(form);
  body.append("ajax", "1");
  fetch(form.action, {
    method: "POST",
    credentials: "same-origin",
    redirect: "manual",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "fetch",
      "X-CSRFToken": token.value,
    },
    body: body,
  })
    .then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok && data.ok !== false, data: data };
      });
    })
    .then(function (result) {
      if (!result.ok) {
        var message = (result.data && result.data.error) || "";
        var root = form.closest("[data-cart-pick-root]");
        var box = root && root.querySelector("[data-cart-error]");
        if (box && message) {
          box.textContent = message;
          box.hidden = false;
          return;
        }
        throw new Error("cart");
      }
      setCartCount(result.data.count);
      markInCart(
        result.data.product_id || form.getAttribute("data-cart-product"),
        result.data.variant_id || form.getAttribute("data-cart-variant")
      );
      flashCartButton(form);
      closeCartPicks();
    })
    .catch(function () {
      form.submit();
    })
    .finally(function () {
      form.dataset.cartBusy = "";
    });
}

document.addEventListener("DOMContentLoaded", function () {
  applyShippingFill(document);
});

document.addEventListener("htmx:afterSwap", function (event) {
  applyShippingFill(event.target);
  var summary = event.target.id === "cart-summary" ? event.target : null;
  if (summary) {
    var raw = summary.getAttribute("data-cart-items-count");
    if (raw !== null) setCartCount(parseInt(raw, 10) || 0);
  }
});

/* Делеговані обробники подій замість onchange="" у HTML (CSP script-src 'self' —
   без 'unsafe-inline' інлайн event-атрибути заблоковані). */
document.addEventListener("change", function (event) {
  if (event.target.matches('[data-js="qty-autosubmit"]')) {
    event.target.form.requestSubmit();
  }
});

document.addEventListener("submit", function (event) {
  var form = event.target.closest("[data-cart-form]");
  if (!form) return;
  event.preventDefault();
  submitCartForm(form);
});

document.addEventListener("click", function (event) {
  var toggle = event.target.closest("[data-cart-pick-toggle]");
  if (toggle) {
    event.preventDefault();
    event.stopPropagation();
    var root = toggle.closest("[data-cart-pick-root]");
    if (!root) return;
    if (root.classList.contains("is-open")) closeCartPicks();
    else openCartPick(root);
    return;
  }
  if (!event.target.closest("[data-cart-pick-root]")) closeCartPicks();
});

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") closeCartPicks();
});
