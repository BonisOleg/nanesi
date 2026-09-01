document.addEventListener('DOMContentLoaded', function () {
  var deliverySelect = document.getElementById('id_delivery_method');
  var npFields = document.getElementById('np-fields');
  var npWarehouseField = document.getElementById('np-warehouse-field');
  var ukrposhtaFields = document.getElementById('ukrposhta-fields');

  function toggleClass(el, isVisible) {
    if (!el) return;
    el.classList.toggle('is-hidden', !isVisible);
  }

  function updateVisibility() {
    var value = deliverySelect ? deliverySelect.value : '';
    var isNp = value.indexOf('np_') === 0;
    toggleClass(npFields, isNp);
    toggleClass(npWarehouseField, value === 'np_warehouse');
    toggleClass(ukrposhtaFields, value === 'ukrposhta');
  }
  if (deliverySelect) {
    deliverySelect.addEventListener('change', updateVisibility);
  }
  updateVisibility();

  function setupCitySearch() {
    var input = document.getElementById('id_np_city_name');
    var refInput = document.getElementById('id_np_city_ref');
    var list = document.getElementById('np-city-suggestions');
    if (!input) return;
    var timer = null;
    input.addEventListener('input', function () {
      refInput.value = '';
      clearTimeout(timer);
      var query = input.value.trim();
      timer = setTimeout(function () {
        fetch('/shipping/np/cities/?q=' + encodeURIComponent(query))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            list.innerHTML = '';
            if (!data.configured || !data.results.length) return;
            var ul = document.createElement('ul');
            ul.className = 'suggestions-list';
            data.results.forEach(function (row) {
              var li = document.createElement('li');
              li.textContent = row.name;
              li.addEventListener('click', function () {
                input.value = row.name;
                refInput.value = row.ref;
                list.innerHTML = '';
                document.dispatchEvent(new CustomEvent('np-city-selected', { detail: row }));
              });
              ul.appendChild(li);
            });
            list.appendChild(ul);
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
        warehouseList.innerHTML = '';
        if (!data.configured || !data.results.length) return;
        var ul = document.createElement('ul');
        ul.className = 'suggestions-list';
        data.results.forEach(function (row) {
          var li = document.createElement('li');
          li.textContent = row.name;
          li.addEventListener('click', function () {
            warehouseInput.value = row.name;
            warehouseRefInput.value = row.ref;
            warehouseList.innerHTML = '';
          });
          ul.appendChild(li);
        });
        warehouseList.appendChild(ul);
      })
      .catch(function () { warehouseList.innerHTML = ''; });
  }

  document.addEventListener('np-city-selected', function (e) {
    selectedCityId = e.detail.id;
    fetchWarehouses(selectedCityId, '');
  });

  if (warehouseInput) {
    warehouseInput.addEventListener('input', function () {
      warehouseRefInput.value = '';
      if (selectedCityId) {
        fetchWarehouses(selectedCityId, warehouseInput.value.trim());
      }
    });
  }
});
