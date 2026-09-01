document.addEventListener('DOMContentLoaded', function () {
  var tabs = document.querySelectorAll('[data-auth-tab]');
  var panels = document.querySelectorAll('[data-auth-panel]');

  function activate(name) {
    tabs.forEach(function (tab) {
      tab.classList.toggle('is-active', tab.getAttribute('data-auth-tab') === name);
    });
    panels.forEach(function (panel) {
      panel.classList.toggle('is-hidden', panel.getAttribute('data-auth-panel') !== name);
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function (e) {
      e.preventDefault();
      activate(tab.getAttribute('data-auth-tab'));
    });
  });

  /* Гостьове обране (localStorage) передається на сервер разом із формою входу/
     реєстрації — синк відбувається одразу під час логіну (Підетап 2). */
  var wishlistIds = [];
  try {
    var raw = window.localStorage.getItem('nanesi_wishlist');
    wishlistIds = raw ? JSON.parse(raw) : [];
  } catch (e) {
    wishlistIds = [];
  }
  document.querySelectorAll('[data-wishlist-ids-field]').forEach(function (input) {
    input.value = wishlistIds.join(',');
  });
});
