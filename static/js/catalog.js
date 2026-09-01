(function () {
  var filtersRoot = document.querySelector("[data-filters]");
  var form = document.getElementById("catalog-filter-form");

  var toggleBtn = document.querySelector("[data-filters-toggle]");
  if (toggleBtn && filtersRoot) {
    toggleBtn.addEventListener("click", function () {
      filtersRoot.classList.toggle("is-open");
    });
  }

  if (form) {
    form.addEventListener("change", function (e) {
      var target = e.target;
      if (target.matches('input[type="checkbox"]')) {
        form.requestSubmit();
      }
    });
  }

  /* Сортування живе поза <form> (щоб не гніздити форми карток товару всередині
     фільтрів), звʼязок лише через атрибут form="catalog-filter-form". */
  var sortSelect = document.querySelector("[data-catalog-sort]");
  if (sortSelect && form) {
    sortSelect.addEventListener("change", function () {
      form.requestSubmit();
    });
  }
})();
