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
    cityInput.setAttribute('autocomplete', 'off');

    cityInput.addEventListener('focus', function () {
      warehouseListOpen = false;
      clearList(warehouseList);
    });

    cityInput.addEventListener('input', function () {
      if (cityRefInput) cityRefInput.value = '';
      clearWarehouseSelection();
      clearTimeout(timer);
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
