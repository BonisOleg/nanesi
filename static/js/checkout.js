document.addEventListener('DOMContentLoaded', function () {
  var deliveryInputs = document.querySelectorAll('input[name="delivery_method"]');
  var npFields = document.getElementById('np-fields');
  var ukrposhtaFields = document.getElementById('ukrposhta-fields');

  function toggleClass(el, isVisible) {
    if (!el) return;
    el.classList.toggle('is-hidden', !isVisible);
  }

  function selectedDelivery() {
    var checked = document.querySelector('input[name="delivery_method"]:checked');
    return checked ? checked.value : '';
  }

  function updateVisibility() {
    var value = selectedDelivery();
    toggleClass(npFields, value === 'np_warehouse');
    toggleClass(ukrposhtaFields, value === 'ukrposhta');
    var progress = document.querySelector('[data-shipping-progress]');
    if (progress) {
      var covers = value === 'np_warehouse'
        ? progress.getAttribute('data-covers-np') === '1'
        : value === 'ukrposhta'
          ? progress.getAttribute('data-covers-ukrposhta') === '1'
          : false;
      progress.hidden = !covers;
    }
  }

  deliveryInputs.forEach(function (input) {
    input.addEventListener('change', updateVisibility);
  });
  updateVisibility();

  function fillSuggestions(list, rows, onPick) {
    list.innerHTML = '';
    if (!rows || !rows.length) return;
    var ul = document.createElement('ul');
    ul.className = 'suggestions-list';
    rows.forEach(function (row) {
      var li = document.createElement('li');
      li.className = 'suggestions-list__item';
      if (row.kind === 'postomat') {
        li.classList.add('suggestions-list__item--postomat');
      }
      li.textContent = row.name;
      li.addEventListener('click', function () {
        onPick(row);
        clearList(list);
      });
      ul.appendChild(li);
    });
    list.appendChild(ul);
    if (list.id === 'np-city-suggestions') placeNpCitySuggestions();
  }

  var placeNpCitySuggestions = function () {};
  var silenceNpCityDrop = function () {};

  function clearList(el) {
    if (!el) return;
    el.innerHTML = '';
    if (el.id === 'np-city-suggestions') {
      el.classList.remove('is-above');
      silenceNpCityDrop();
    }
  }

  var selectedCityId = null;
  var cityInput = document.getElementById('id_np_city_name');
  var cityRefInput = document.getElementById('id_np_city_ref');
  var warehouseInput = document.getElementById('id_np_warehouse_name');
  var warehouseRefInput = document.getElementById('id_np_warehouse_ref');
  var warehouseList = document.getElementById('np-warehouse-suggestions');
  var warehouseFetchSeq = 0;
  var warehouseListOpen = false;

  function clearWarehouseSelection() {
    selectedCityId = null;
    warehouseListOpen = false;
    if (warehouseInput) warehouseInput.value = '';
    if (warehouseRefInput) warehouseRefInput.value = '';
    clearList(warehouseList);
  }

  function warehouseCityParam() {
    if (selectedCityId) {
      return 'city=' + encodeURIComponent(selectedCityId);
    }
    var ref = cityRefInput && cityRefInput.value ? cityRefInput.value.trim() : '';
    if (ref) {
      return 'city_ref=' + encodeURIComponent(ref);
    }
    return '';
  }

  function fetchWarehouses(query, opts) {
    opts = opts || {};
    var show = opts.show === true;
    if (!show && !warehouseListOpen) {
      clearList(warehouseList);
      return;
    }
    var cityParam = warehouseCityParam();
    if (!cityParam) {
      clearList(warehouseList);
      return;
    }
    if (show) warehouseListOpen = true;
    var seq = ++warehouseFetchSeq;
    fetch('/shipping/np/warehouses/?' + cityParam + '&q=' + encodeURIComponent(query || ''))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (seq !== warehouseFetchSeq || !warehouseListOpen) return;
        if (data.city_id) selectedCityId = data.city_id;
        if (!data.configured || !data.results.length) {
          clearList(warehouseList);
          return;
        }
        fillSuggestions(warehouseList, data.results, function (row) {
          warehouseInput.value = row.name;
          warehouseRefInput.value = row.ref;
          warehouseListOpen = false;
        });
      })
      .catch(function () {
        if (seq === warehouseFetchSeq) clearList(warehouseList);
      });
  }

  function setupCitySearch() {
    var list = document.getElementById('np-city-suggestions');
    if (!cityInput) return;
    var timer = null;
    var listening = false;
    var rafId = 0;
    var capKey = '';
    var capPx = 280;
    var dropMargin = 16;
    var minBelow = 200;
    cityInput.setAttribute('autocomplete', 'off');

    function dropFrame() {
      var vv = window.visualViewport;
      var top = vv ? vv.offsetTop : 0;
      var bottom = vv ? vv.offsetTop + vv.height : window.innerHeight;
      var chrome = document.querySelector('.site-chrome');
      if (chrome) {
        var chromeBottom = chrome.getBoundingClientRect().bottom;
        if (chromeBottom > top) top = chromeBottom;
      }
      return { top: top, bottom: bottom };
    }

    function cssCap(menu) {
      var vv = window.visualViewport;
      /* Крок 16px: на iOS висота visualViewport стрибає разом із панеллю Safari. */
      var height = vv ? Math.round(vv.height / 16) * 16 : window.innerHeight;
      var key = window.innerWidth + 'x' + height;
      if (key === capKey) return capPx;
      var prev = menu.style.maxHeight;
      menu.style.maxHeight = '';
      var parsed = parseFloat(window.getComputedStyle(menu).maxHeight);
      menu.style.maxHeight = prev;
      if (!isFinite(parsed) || parsed <= 0) parsed = 280;
      capKey = key;
      capPx = parsed;
      return parsed;
    }

    function onViewport() {
      if (rafId) return;
      rafId = window.requestAnimationFrame(function () {
        rafId = 0;
        placeNpCitySuggestions();
      });
    }

    function listenDrop() {
      if (listening) return;
      listening = true;
      window.addEventListener('resize', onViewport);
      window.addEventListener('orientationchange', onViewport);
      window.addEventListener('scroll', onViewport, { capture: true, passive: true });
      if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', onViewport);
        window.visualViewport.addEventListener('scroll', onViewport);
      }
    }

    silenceNpCityDrop = function () {
      if (!listening) return;
      listening = false;
      window.removeEventListener('resize', onViewport);
      window.removeEventListener('orientationchange', onViewport);
      window.removeEventListener('scroll', onViewport, true);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', onViewport);
        window.visualViewport.removeEventListener('scroll', onViewport);
      }
      if (rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
      }
    };

    placeNpCitySuggestions = function () {
      var menu = list.querySelector('.suggestions-list');
      if (!menu) {
        list.classList.remove('is-above');
        silenceNpCityDrop();
        return;
      }
      listenDrop();
      /* <=480px лишається на CSS: ширина поля, max-height min(260px, 50vh), overflow-y auto. */
      if (window.matchMedia('(max-width: 480px)').matches) {
        list.classList.remove('is-above');
        menu.style.maxHeight = '';
        return;
      }
      var field = cityInput.closest ? (cityInput.closest('.field') || cityInput) : cityInput;
      var rect = cityInput.getBoundingClientRect();
      var box = dropFrame();
      var spaceBelow = box.bottom - rect.bottom;
      var spaceAbove = field.getBoundingClientRect().top - box.top;
      var openUp = spaceBelow < minBelow && spaceAbove > spaceBelow;
      if (openUp) list.classList.add('is-above');
      else list.classList.remove('is-above');
      var room = openUp ? spaceAbove : spaceBelow;
      var maxH = Math.min(cssCap(menu), Math.max(0, room - dropMargin));
      var next = Math.floor(maxH) + 'px';
      if (menu.style.maxHeight !== next) menu.style.maxHeight = next;
    };

    cityInput.addEventListener('focus', function () {
      warehouseListOpen = false;
      clearList(warehouseList);
    });

    cityInput.addEventListener('input', function () {
      if (cityRefInput) cityRefInput.value = '';
      clearWarehouseSelection();
      clearTimeout(timer);
      /* Латиницю не підміняємо на кирилицю: у запит іде рівно те, що набрано. */
      var query = cityInput.value.trim();
      timer = setTimeout(function () {
        if (!query) {
          clearList(list);
          return;
        }
        fetch('/shipping/np/cities/?q=' + encodeURIComponent(query))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.configured || !data.results.length) {
              clearList(list);
              return;
            }
            fillSuggestions(list, data.results, function (row) {
              cityInput.value = row.name;
              if (cityRefInput) cityRefInput.value = row.ref;
              document.dispatchEvent(new CustomEvent('np-city-selected', { detail: row }));
            });
          })
          .catch(function () { clearList(list); });
      }, 250);
    });
  }
  setupCitySearch();

  document.addEventListener('np-city-selected', function (e) {
    selectedCityId = e.detail.id;
    warehouseListOpen = false;
    if (warehouseInput) warehouseInput.value = '';
    if (warehouseRefInput) warehouseRefInput.value = '';
    clearList(warehouseList);
  });

  if (warehouseInput) {
    warehouseInput.setAttribute('autocomplete', 'off');

    function openWarehouseSuggestions() {
      fetchWarehouses(warehouseInput.value.trim(), { show: true });
    }

    warehouseInput.addEventListener('focus', openWarehouseSuggestions);
    warehouseInput.addEventListener('click', openWarehouseSuggestions);

    warehouseInput.addEventListener('input', function () {
      if (warehouseRefInput) warehouseRefInput.value = '';
      fetchWarehouses(warehouseInput.value.trim(), { show: true });
    });

    warehouseInput.addEventListener('blur', function () {
      setTimeout(function () {
        if (document.activeElement !== warehouseInput) {
          warehouseListOpen = false;
          clearList(warehouseList);
        }
      }, 180);
    });
  }
});
