(function () {
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id") || "pdrn-cream";
  const product = window.NANESI_PRODUCTS.find((p) => p.id === id) || window.NANESI_PRODUCTS[0];
  const main = document.querySelector("[data-product-main]");
  const crumb = document.querySelector("[data-crumb-title]");

  if (crumb) crumb.textContent = product.titleShort;
  document.title = `${product.titleShort} — NANESI`;

  const old =
    product.oldPrice != null
      ? `<span class="price--old">${NinesiUI.money(product.oldPrice)}</span>
         <span class="badge badge--sale">−${Math.round(
           ((product.oldPrice - product.price) / product.oldPrice) * 100
         )}%</span>`
      : "";

  const extraAttrs = [];
  if (product.spf) extraAttrs.push(`<div><dt>SPF</dt><dd>${product.spf}</dd></div>`);
  if (product.shade) extraAttrs.push(`<div><dt>Відтінок</dt><dd>${product.shade}</dd></div>`);
  if (product.finish) extraAttrs.push(`<div><dt>Фініш</dt><dd>${product.finish}</dd></div>`);
  if (product.hairType) extraAttrs.push(`<div><dt>Тип волосся</dt><dd>${product.hairType}</dd></div>`);

  main.innerHTML = `
    <div class="gallery">
      <div class="gallery__main">
        <img src="${product.image}" alt="${product.titleShort}" width="640" height="640" data-gallery-main>
      </div>
      <div class="gallery__thumbs">
        <button type="button" class="is-active" data-thumb="${product.image}" aria-label="Фото 1">
          <img src="${product.image}" alt="">
        </button>
        <button type="button" data-thumb="${product.image}" aria-label="Фото 2">
          <img src="${product.image}" alt="">
        </button>
      </div>
    </div>
    <div class="product-info">
      <div class="product-info__brand">${product.brand}</div>
      <h1 class="product-info__title">${product.title}</h1>
      <p class="product-info__sku">Артикул: ${product.sku}${product.ean ? ` · EAN: ${product.ean}` : ""}</p>
      <div class="product-info__rating rating">
        <span class="rating__stars" aria-hidden="true">${NinesiUI.stars(product.rating)}</span>
        <span>${product.rating} · ${product.reviews} відгуків</span>
      </div>
      <div class="product-info__prices">
        <span class="price">${NinesiUI.money(product.price)}</span>
        ${old}
      </div>
      <p class="product-info__stock">${product.inStock ? "В наявності" : "Немає в наявності"}</p>
      <dl class="product-info__attrs">
        <div><dt>Категорія</dt><dd>${product.categoryLabel}</dd></div>
        <div><dt>Об’єм</dt><dd>${product.volume}</dd></div>
        <div><dt>Країна</dt><dd>${product.country}</dd></div>
        <div><dt>Тип шкіри</dt><dd>${product.skinType}</dd></div>
        ${extraAttrs.join("")}
        <div><dt>Проблема / призначення</dt><dd>${product.concerns}</dd></div>
      </dl>
      <div class="product-info__actions">
        <div class="qty" data-qty>
          <button type="button" data-qty-minus aria-label="Менше">−</button>
          <span data-qty-value>1</span>
          <button type="button" data-qty-plus aria-label="Більше">+</button>
        </div>
        <button class="btn btn--primary" type="button">До кошика</button>
        <button class="btn btn--ghost" type="button" data-wish="${product.id}">В обране</button>
      </div>
    </div>
  `;

  document.querySelector('[data-panel="desc"]').innerHTML = `
    <h3>Опис</h3>
    <p>${product.description}</p>
    <h3>Постачальник</h3>
    <p>Cosmetics Factory (відображається лише в адмінці на продакшені; у макеті для перевірки).</p>
  `;
  document.querySelector('[data-panel="usage"]').innerHTML = `<p>${product.usage}</p>`;
  document.querySelector('[data-panel="actives"]').innerHTML = `<p>${product.actives}</p>`;
  document.querySelector('[data-panel="inci"]').innerHTML = `<p class="inci">${product.inci}</p>`;

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      document.querySelectorAll("[data-tab]").forEach((b) => {
        b.classList.toggle("is-active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      });
      document.querySelectorAll("[data-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.getAttribute("data-panel") === tab);
      });
    });
  });

  let qty = 1;
  const qtyValue = document.querySelector("[data-qty-value]");
  document.querySelector("[data-qty-minus]")?.addEventListener("click", () => {
    qty = Math.max(1, qty - 1);
    qtyValue.textContent = String(qty);
  });
  document.querySelector("[data-qty-plus]")?.addEventListener("click", () => {
    qty += 1;
    qtyValue.textContent = String(qty);
  });

  const related = window.NANESI_PRODUCTS.filter((p) => p.id !== product.id).slice(0, 4);
  NinesiUI.renderProducts("[data-related-grid]", related);
})();
