/* Встановлення прогрес-бару безкоштовної доставки через CSSOM (element.style),
   а не через HTML style="" — щоб не порушувати CSP style-src 'self' (без unsafe-inline). */
function applyShippingFill(root) {
  (root || document).querySelectorAll('[data-js="shipping-fill"]').forEach(function (el) {
    var fill = parseFloat(el.getAttribute('data-fill') || '0');
    el.style.width = Math.min(100, Math.max(0, fill)) + '%';
  });
}

document.addEventListener('DOMContentLoaded', function () {
  applyShippingFill(document);
});

document.addEventListener('htmx:afterSwap', function (event) {
  applyShippingFill(event.target);
});

/* Делеговані обробники подій замість onchange="" у HTML (CSP script-src 'self' —
   без 'unsafe-inline' інлайн event-атрибути заблоковані). */
document.addEventListener('change', function (event) {
  if (event.target.matches('[data-js="qty-autosubmit"]')) {
    event.target.form.requestSubmit();
  }
});
