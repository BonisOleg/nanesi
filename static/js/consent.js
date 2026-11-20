/* Consent Mode v2: default denied до GTM. Вибір у first-party cookie nanesi_consent. */
(function () {
  'use strict';

  var COOKIE = 'nanesi_consent';
  var MAX_AGE = 365 * 24 * 60 * 60;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('consent', 'default', {
    ad_storage: 'denied',
    analytics_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500,
  });

  function readConsent() {
    var match = document.cookie.match(/(?:^|; )nanesi_consent=([^;]*)/);
    if (!match) return null;
    try {
      return JSON.parse(decodeURIComponent(match[1]));
    } catch (e) {
      return null;
    }
  }

  function applyUpdate(consent) {
    var analyticsOn = !!(consent && consent.analytics);
    var marketingOn = !!(consent && consent.marketing);
    window.gtag('consent', 'update', {
      analytics_storage: analyticsOn ? 'granted' : 'denied',
      ad_storage: marketingOn ? 'granted' : 'denied',
      ad_user_data: marketingOn ? 'granted' : 'denied',
      ad_personalization: marketingOn ? 'granted' : 'denied',
    });
  }

  function persist(consent) {
    var value = encodeURIComponent(JSON.stringify({
      analytics: !!consent.analytics,
      marketing: !!consent.marketing,
    }));
    var cookie = COOKIE + '=' + value + ';path=/;max-age=' + MAX_AGE + ';SameSite=Lax';
    if (location.protocol === 'https:') cookie += ';Secure';
    document.cookie = cookie;
    applyUpdate(consent);
    document.dispatchEvent(new CustomEvent('nanesi:consent', { detail: consent }));
  }

  var stored = readConsent();
  if (stored) applyUpdate(stored);

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function setHidden(el, hidden) {
    if (!el) return;
    if (hidden) el.setAttribute('hidden', '');
    else el.removeAttribute('hidden');
  }

  function syncToggles(consent) {
    var analytics = qs('[data-consent-analytics]');
    var marketing = qs('[data-consent-marketing]');
    if (analytics) analytics.checked = !!(consent && consent.analytics);
    if (marketing) marketing.checked = !!(consent && consent.marketing);
  }

  function bind() {
    var banner = qs('[data-cookie-banner]');
    if (!banner) return;
    var panel = qs('[data-consent-panel]', banner);
    var reopen = qs('[data-consent-reopen]');

    if (!stored) setHidden(banner, false);

    function acceptAll() {
      persist({ analytics: true, marketing: true });
      setHidden(banner, true);
      setHidden(panel, true);
    }

    function necessaryOnly() {
      persist({ analytics: false, marketing: false });
      setHidden(banner, true);
      setHidden(panel, true);
    }

    function saveCustom() {
      persist({
        analytics: !!(qs('[data-consent-analytics]', banner) && qs('[data-consent-analytics]', banner).checked),
        marketing: !!(qs('[data-consent-marketing]', banner) && qs('[data-consent-marketing]', banner).checked),
      });
      setHidden(banner, true);
      setHidden(panel, true);
    }

    banner.addEventListener('click', function (event) {
      var target = event.target.closest('[data-consent-accept], [data-consent-necessary], [data-consent-customize], [data-consent-save]');
      if (!target) return;
      if (target.hasAttribute('data-consent-accept')) acceptAll();
      else if (target.hasAttribute('data-consent-necessary')) necessaryOnly();
      else if (target.hasAttribute('data-consent-customize')) {
        syncToggles(readConsent());
        setHidden(panel, false);
      } else if (target.hasAttribute('data-consent-save')) saveCustom();
    });

    if (reopen) {
      reopen.addEventListener('click', function () {
        syncToggles(readConsent());
        setHidden(banner, false);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
