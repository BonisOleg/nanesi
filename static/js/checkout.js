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

  function setupCitySearch() {
    var input = document.getElementById('id_np_city_name');
    var refInput = document.getElementById('id_np_city_ref');
    var list = document.getElementById('np-city-suggestions');
    if (!input) return;
    var timer = null;
    input.setAttribute('autocomplete', 'off');
    input.addEventListener('input', function () {
      refInput.value = '';
      clearTimeout(timer);
      var query = input.value.trim();
      timer = setTimeout(function () {
        fetch('/shipping/np/cities/?q=' + encodeURIComponent(query))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.configured || !data.results.length) {
              list.innerHTML = '';
              return;
            }
            fillSuggestions(list, data.results, function (row) {
              input.value = row.name;
              refInput.value = row.ref;
              document.dispatchEvent(new CustomEvent('np-city-selected', { detail: row }));
            });
          })
          .catch(function () { list.innerHTML = ''; });
      }, 250);
    });
  }
  setupCitySearch();

  var selectedCityId = null;
  var warehouseInput = document.getElementById('id_np_warehouse_name');
  var warehouseRefInput = document.getElementById('id_np_warehouse_ref');
  var warehouseList = document.getElementById('np-warehouse-suggestions');

  function fetchWarehouses(cityId, query) {
    fetch('/shipping/np/warehouses/?city=' + encodeURIComponent(cityId) + '&q=' + encodeURIComponent(query || ''))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.configured || !data.results.length) {
          warehouseList.innerHTML = '';
          return;
        }
        fillSuggestions(warehouseList, data.results, function (row) {
          warehouseInput.value = row.name;
          warehouseRefInput.value = row.ref;
        });
      })
      .catch(function () { warehouseList.innerHTML = ''; });
  }

  document.addEventListener('np-city-selected', function (e) {
    selectedCityId = e.detail.id;
    if (warehouseInput) warehouseInput.value = '';
    if (warehouseRefInput) warehouseRefInput.value = '';
    fetchWarehouses(selectedCityId, '');
  });

  if (warehouseInput) {
    warehouseInput.setAttribute('autocomplete', 'off');
    warehouseInput.addEventListener('input', function () {
      warehouseRefInput.value = '';
      if (selectedCityId) {
        fetchWarehouses(selectedCityId, warehouseInput.value.trim());
      }
    });
  }
});
