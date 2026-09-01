/* GTM / GA4 / Meta Pixel / TikTok Pixel — конфіг з data-* атрибутів цього <script>
   (значення з SiteSettings, керовані з адмінки). Дані подій читаються з
   <script type="application/json" data-dl-events> — не інлайн-JS, щоб не порушувати
   CSP script-src 'self' (без 'unsafe-inline'). */
(function () {
  'use strict';

  var cfg = (document.currentScript && document.currentScript.dataset) || {};
  window.dataLayer = window.dataLayer || [];

  function loadScript(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  if (cfg.gtmId) {
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    loadScript('https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(cfg.gtmId));
  }

  if (cfg.ga4Id) {
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    loadScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(cfg.ga4Id));
    window.gtag('js', new Date());
    window.gtag('config', cfg.ga4Id, { send_page_view: true });
  }

  if (cfg.metaPixelId) {
    (function (f) {
      if (f.fbq) return;
      var n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      f._fbq = n;
      n.push = n;
      n.loaded = true;
      n.version = '2.0';
      n.queue = [];
    })(window);
    loadScript('https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', cfg.metaPixelId);
    window.fbq('track', 'PageView');
  }

  if (cfg.tiktokPixelId) {
    (function (w, d, t) {
      w.TiktokAnalyticsObject = t;
      var ttq = w[t] = w[t] || [];
      ttq.methods = ['page', 'track', 'identify', 'instances', 'debug', 'on', 'off', 'once', 'ready', 'alias', 'group', 'enableCookie', 'disableCookie'];
      ttq.setAndDefer = function (o, n) {
        o[n] = function () { o.push([n].concat(Array.prototype.slice.call(arguments, 0))); };
      };
      for (var i = 0; i < ttq.methods.length; i++) ttq.setAndDefer(ttq, ttq.methods[i]);
      ttq.load = function (id) {
        loadScript('https://analytics.tiktok.com/i18n/pixel/events.js?sdkid=' + id + '&lib=' + t);
      };
      ttq.load(cfg.tiktokPixelId);
      ttq.page();
    })(window, document, 'ttq');
  }

  /* GA4 event -> Meta/TikTok відповідник (основні ecommerce-події, Доповнення §1). */
  var EVENT_MAP = {
    view_item: { meta: 'ViewContent', tiktok: 'ViewContent' },
    add_to_cart: { meta: 'AddToCart', tiktok: 'AddToCart' },
    begin_checkout: { meta: 'InitiateCheckout', tiktok: 'InitiateCheckout' },
    purchase: { meta: 'Purchase', tiktok: 'CompletePayment' },
  };

  function mirrorToPixels(ev) {
    var map = EVENT_MAP[ev.event];
    if (!map) return;
    var ec = ev.ecommerce || {};
    if (window.fbq) {
      window.fbq('track', map.meta, {
        value: ec.value,
        currency: ec.currency,
        content_ids: (ec.items || []).map(function (item) { return item.item_id; }),
        content_type: 'product',
      });
    }
    if (window.ttq) {
      window.ttq.track(map.tiktok, {
        value: ec.value,
        currency: ec.currency,
        contents: (ec.items || []).map(function (item) {
          return { content_id: item.item_id, content_name: item.item_name, price: item.price, quantity: item.quantity };
        }),
      });
    }
  }

  /* purchase не повинен рахуватись повторно при F5 на «Дякуємо за замовлення» —
     дедуплікація через localStorage за transaction_id (best-effort, не серверна гарантія). */
  function alreadyTracked(ev) {
    if (ev.event !== 'purchase') return false;
    var id = ev.ecommerce && ev.ecommerce.transaction_id;
    if (!id) return false;
    try {
      var key = 'nanesi_tracked_purchase';
      var tracked = JSON.parse(window.localStorage.getItem(key) || '[]');
      if (tracked.indexOf(id) !== -1) return true;
      tracked.push(id);
      window.localStorage.setItem(key, JSON.stringify(tracked));
    } catch (e) {
      return false;
    }
    return false;
  }

  function pushEvents(events) {
    events.forEach(function (ev) {
      if (alreadyTracked(ev)) return;
      window.dataLayer.push({ ecommerce: null });
      window.dataLayer.push(ev);
      mirrorToPixels(ev);
    });
  }

  function readEventBlocks(root) {
    (root || document).querySelectorAll('script[data-dl-events]').forEach(function (node) {
      try {
        pushEvents(JSON.parse(node.textContent || '[]'));
      } catch (e) { /* невалідний JSON-блок — ігноруємо */ }
      node.parentNode.removeChild(node);
    });
  }

  document.addEventListener('DOMContentLoaded', function () { readEventBlocks(document); });
  document.addEventListener('htmx:afterSwap', function (event) { readEventBlocks(event.target); });
})();
