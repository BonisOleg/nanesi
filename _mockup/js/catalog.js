(function () {
  const params = new URLSearchParams(window.location.search);
  const grid = document.querySelector("[data-catalog-grid]");
  const empty = document.querySelector("[data-catalog-empty]");
  const countEl = document.querySelector("[data-catalog-count]");
  const sortEl = document.querySelector("[data-catalog-sort]");
  const filtersRoot = document.querySelector("[data-filters]");
  const searchEl = document.querySelector("[data-catalog-search]");

  function selectedValues(name) {
    return [...document.querySelectorAll(`[data-filter][name="${name}"]:checked`)].map(
      (el) => el.value
    );
  }

  function applyUrlParams() {
    const cat = params.get("cat");
    const sale = params.get("sale");
    const q = params.get("q");

    if (cat) {
      const map = {
        "face-creams": ["face-creams", "serums"],
      };
      const values = map[cat] || [cat];
      values.forEach((value) => {
        const input = document.querySelector(
          `[data-filter][name="category"][value="${value}"]`
        );
        if (input) input.checked = true;
      });
    }
    if (sale === "1") {
      // show only discounted via filter logic flag
      filtersRoot?.setAttribute("data-sale-only", "1");
    }
    if (q && searchEl) searchEl.value = q;
  }

  function getFiltered() {
    let list = [...window.NANESI_PRODUCTS];
    const brands = selectedValues("brand");
    const cats = selectedValues("category");
    const stockOnly = selectedValues("stock").includes("1");
    const saleOnly = filtersRoot?.getAttribute("data-sale-only") === "1";
    const q = (searchEl?.value || "").trim().toLowerCase();

    if (brands.length) list = list.filter((p) => brands.includes(p.brand));
    if (cats.length) list = list.filter((p) => cats.includes(p.category));
    if (stockOnly) list = list.filter((p) => p.inStock);
    if (saleOnly) list = list.filter((p) => p.oldPrice != null);
    if (q) {
      list = list.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.brand.toLowerCase().includes(q) ||
          String(p.sku).toLowerCase().includes(q)
      );
    }

    const sort = sortEl?.value || "popular";
    if (sort === "price-asc") list.sort((a, b) => a.price - b.price);
    if (sort === "price-desc") list.sort((a, b) => b.price - a.price);
    if (sort === "name") list.sort((a, b) => a.titleShort.localeCompare(b.titleShort, "uk"));
    if (sort === "popular") list.sort((a, b) => b.rating - a.rating || b.reviews - a.reviews);

    return list;
  }

  function render() {
    const list = getFiltered();
    if (countEl) countEl.textContent = `Знайдено ${list.length} товарів`;
    if (!list.length) {
      grid.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    NinesiUI.renderProducts(grid, list);
  }

  document.querySelector("[data-filters-toggle]")?.addEventListener("click", () => {
    filtersRoot?.classList.toggle("is-open");
  });

  document.querySelectorAll("[data-filter]").forEach((el) => {
    el.addEventListener("change", () => {
      filtersRoot?.removeAttribute("data-sale-only");
      render();
    });
  });

  sortEl?.addEventListener("change", render);
  searchEl?.addEventListener("input", render);

  applyUrlParams();
  render();
})();
