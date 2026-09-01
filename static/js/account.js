document.addEventListener('DOMContentLoaded', function () {
  /* --- Автодоповнення міста/відділення НП у профілі (той самий /shipping/np/ API, що на checkout) --- */
  var cityInput = document.getElementById('id_saved_np_city_name');
  var cityRefInput = document.getElementById('id_saved_np_city_ref');
  var citySuggestions = document.getElementById('saved-np-city-suggestions');
  var warehouseInput = document.getElementById('id_saved_np_warehouse_name');
  var warehouseRefInput = document.getElementById('id_saved_np_warehouse_ref');
  var warehouseSuggestions = document.getElementById('saved-np-warehouse-suggestions');
  var selectedCityId = null;

  function fetchWarehouses(cityId, query) {
    fetch('/shipping/np/warehouses/?city=' + encodeURIComponent(cityId) + '&q=' + encodeURIComponent(query || ''))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        warehouseSuggestions.innerHTML = '';
        if (!data.configured || !data.results.length) return;
        var ul = document.createElement('ul');
        ul.className = 'suggestions-list';
        data.results.forEach(function (row) {
          var li = document.createElement('li');
          li.textContent = row.name;
          li.addEventListener('click', function () {
            warehouseInput.value = row.name;
            warehouseRefInput.value = row.ref;
            warehouseSuggestions.innerHTML = '';
          });
          ul.appendChild(li);
        });
        warehouseSuggestions.appendChild(ul);
      })
      .catch(function () { warehouseSuggestions.innerHTML = ''; });
  }

  if (cityInput) {
    var timer = null;
    cityInput.addEventListener('input', function () {
      cityRefInput.value = '';
      clearTimeout(timer);
      var query = cityInput.value.trim();
      timer = setTimeout(function () {
        fetch('/shipping/np/cities/?q=' + encodeURIComponent(query))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            citySuggestions.innerHTML = '';
            if (!data.configured || !data.results.length) return;
            var ul = document.createElement('ul');
            ul.className = 'suggestions-list';
            data.results.forEach(function (row) {
              var li = document.createElement('li');
              li.textContent = row.name;
              li.addEventListener('click', function () {
                cityInput.value = row.name;
                cityRefInput.value = row.ref;
                citySuggestions.innerHTML = '';
                selectedCityId = row.id;
                fetchWarehouses(selectedCityId, '');
              });
              ul.appendChild(li);
            });
            citySuggestions.appendChild(ul);
          })
          .catch(function () { citySuggestions.innerHTML = ''; });
      }, 250);
    });
  }

  if (warehouseInput) {
    warehouseInput.addEventListener('input', function () {
      warehouseRefInput.value = '';
      if (selectedCityId) {
        fetchWarehouses(selectedCityId, warehouseInput.value.trim());
      }
    });
  }

  /* --- Обране для гостя на /obrane/: рендер карток за id з localStorage --- */
  var guestGrid = document.getElementById('guest-wishlist-grid');
  if (guestGrid) {
    var ids = [];
    try {
      var raw = window.localStorage.getItem('nanesi_wishlist');
      ids = raw ? JSON.parse(raw) : [];
    } catch (e) {
      ids = [];
    }
    fetch('/obrane/render/?ids=' + encodeURIComponent(ids.join(',')))
      .then(function (r) { return r.text(); })
      .then(function (html) { guestGrid.innerHTML = html; })
      .catch(function () {
        guestGrid.innerHTML = '<p class="text-muted">Не вдалося завантажити обране.</p>';
      });
  }
});
