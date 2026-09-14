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
        list.innerHTML = '';
      });
      ul.appendChild(li);
    });
    list.appendChild(ul);
  }

  function clearList(el) {
    if (el) el.innerHTML = '';
  }

  var selectedCityId = null;
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

  function fetchWarehouses(cityId, query, opts) {
    opts = opts || {};
    var show = opts.show === true;
    if (!show && !warehouseListOpen) {
      clearList(warehouseList);
      return;
    }
    if (show) warehouseListOpen = true;
    var seq = ++warehouseFetchSeq;
    var expectedCity = cityId;
    fetch('/shipping/np/warehouses/?city=' + encodeURIComponent(cityId) + '&q=' + encodeURIComponent(query || ''))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (seq !== warehouseFetchSeq) return;
        if (expectedCity !== selectedCityId || !warehouseListOpen) {
          clearList(warehouseList);
          return;
        }
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
    var input = document.getElementById('id_np_city_name');
    var refInput = document.getElementById('id_np_city_ref');
    var list = document.getElementById('np-city-suggestions');
    if (!input) return;
    var timer = null;
    input.setAttribute('autocomplete', 'off');

    input.addEventListener('focus', function () {
      warehouseListOpen = false;
      clearList(warehouseList);
    });

    input.addEventListener('input', function () {
      refInput.value = '';
      clearWarehouseSelection();
      clearTimeout(timer);
      var query = input.value.trim();
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
              input.value = row.name;
              refInput.value = row.ref;
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
    // Список відділень — лише після фокусу/кліку в полі, не одразу після міста.
  });

  if (warehouseInput) {
    warehouseInput.setAttribute('autocomplete', 'off');

    function openWarehouseSuggestions() {
      if (!selectedCityId) {
        clearList(warehouseList);
        return;
      }
      fetchWarehouses(selectedCityId, warehouseInput.value.trim(), { show: true });
    }

    warehouseInput.addEventListener('focus', openWarehouseSuggestions);
    warehouseInput.addEventListener('click', openWarehouseSuggestions);

    warehouseInput.addEventListener('input', function () {
      warehouseRefInput.value = '';
      if (selectedCityId) {
        fetchWarehouses(selectedCityId, warehouseInput.value.trim(), { show: true });
      } else {
        clearList(warehouseList);
      }
    });

    warehouseInput.addEventListener('blur', function () {
      // Даємо час на click по пункті списку.
      setTimeout(function () {
        if (document.activeElement !== warehouseInput) {
          warehouseListOpen = false;
          clearList(warehouseList);
        }
      }, 180);
    });
  }
});
