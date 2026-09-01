(function () {
  const money = (n) =>
    new Intl.NumberFormat("uk-UA", {
      style: "currency",
      currency: "UAH",
      maximumFractionDigits: 0,
    }).format(n);

  function stars(rating) {
    const full = Math.round(rating);
    return "★".repeat(full) + "☆".repeat(Math.max(0, 5 - full));
  }

  function badgeHtml(badge) {
    if (badge === "sale") return '<span class="badge badge--sale product-card__badge">Акція</span>';
    if (badge === "new") return '<span class="badge badge--new product-card__badge">New</span>';
    if (badge === "hit") return '<span class="badge badge--new product-card__badge">Хіт</span>';
    return "";
  }

  function productCard(p) {
    const old =
      p.oldPrice != null
        ? `<span class="price--old">${money(p.oldPrice)}</span>`
        : "";
    return `
<article class="product-card">
  <div class="product-card__media">
    ${badgeHtml(p.badge)}
    <a href="product.html?id=${encodeURIComponent(p.id)}" aria-label="${p.titleShort}">
      <img src="${p.image}" alt="${p.titleShort}" loading="lazy" width="400" height="400">
    </a>
    <button class="product-card__wish" type="button" aria-label="В обране" data-wish="${p.id}">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7-4.6-9.5-9A5.4 5.4 0 0 1 12 5.2 5.4 5.4 0 0 1 21.5 12C19 16.4 12 21 12 21z"/></svg>
    </button>
  </div>
  <div class="product-card__body">
    <div class="product-card__brand">${p.brand}</div>
    <a class="product-card__title" href="product.html?id=${encodeURIComponent(p.id)}">${p.titleShort}</a>
    <div class="rating"><span class="rating__stars" aria-hidden="true">${stars(p.rating)}</span> (${p.reviews})</div>
    <div class="product-card__meta">
      <div class="product-card__prices">
        <span class="price">${money(p.price)}</span>
        ${old}
      </div>
      <a class="btn btn--icon" href="product.html?id=${encodeURIComponent(p.id)}" aria-label="До кошика">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 7h15l-1.5 9h-12z"/><path d="M6 7 5 3H2"/><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/></svg>
      </a>
    </div>
  </div>
</article>`;
  }

  function renderProducts(target, products) {
    const el = typeof target === "string" ? document.querySelector(target) : target;
    if (!el) return;
    el.innerHTML = products.map(productCard).join("");
  }

  function initMobileMenu() {
    const panel = document.querySelector("[data-mobile-panel]");
    const openBtn = document.querySelector("[data-open-menu]");
    const closeBtn = document.querySelector("[data-close-menu]");
    if (!panel || !openBtn) return;

    const open = () => {
      panel.classList.add("is-open");
      document.body.style.overflow = "hidden";
    };
    const close = () => {
      panel.classList.remove("is-open");
      document.body.style.overflow = "";
    };

    openBtn.addEventListener("click", open);
    closeBtn?.addEventListener("click", close);
    panel.querySelector("[data-mobile-backdrop]")?.addEventListener("click", close);
  }

  function initWish() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-wish]");
      if (!btn) return;
      e.preventDefault();
      btn.classList.toggle("is-active");
    });
  }

  window.NinesiUI = {
    money,
    stars,
    productCard,
    renderProducts,
    initMobileMenu,
    initWish,
  };

  document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initWish();
  });
})();
