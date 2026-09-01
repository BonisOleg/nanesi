/* Popup зі знижкою за email (Доповнення §1, лист Nanesi п.10): показ 1 раз, більше
   не показується після закриття або успішної підписки — прапорець у localStorage. */
(function () {
  'use strict';

  var STORAGE_KEY = 'nanesi_promo_popup_dismissed';
  var SHOW_DELAY_MS = 4000;
  var popup = document.querySelector('[data-promo-popup]');
  if (!popup) return;

  function isDismissed() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === '1';
    } catch (e) {
      return false;
    }
  }

  function markDismissed() {
    try {
      window.localStorage.setItem(STORAGE_KEY, '1');
    } catch (e) { /* localStorage недоступний (приватний режим) — покажемо ще раз наступного разу */ }
  }

  function openPopup() {
    if (isDismissed()) return;
    popup.hidden = false;
    document.body.classList.add('has-open-popup');
  }

  function closePopup() {
    popup.hidden = true;
    document.body.classList.remove('has-open-popup');
    markDismissed();
  }

  popup.querySelectorAll('[data-promo-popup-close]').forEach(function (el) {
    el.addEventListener('click', closePopup);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !popup.hidden) closePopup();
  });

  document.addEventListener('htmx:afterSwap', function (event) {
    if (!popup.contains(event.target)) return;
    var subscribed = event.target.matches('[data-popup-subscribed]') || event.target.querySelector('[data-popup-subscribed]');
    if (subscribed) markDismissed();
  });

  if (!isDismissed()) {
    window.setTimeout(openPopup, SHOW_DELAY_MS);
  }
})();
