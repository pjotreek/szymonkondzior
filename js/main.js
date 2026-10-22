// GDi Merch: koszyk, filtry, strona produktu. Dane produktów: js/products.js (generowane).

const { freeShipping: FREE_SHIPPING, products: PRODUCTS } = window.GDI;
const ROOT = document.body.dataset.root || "./";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const money = (v) => v.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " zł";
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const imageFor = (p) => ROOT + "assets/products/" + p.image + "-600.webp";

const SPLASHES = [
  "Nowy merch!", "100% kwadratowy!", "Teraz z pikselami!", "Subskrybuj!",
  "Lepsze niż diamenty!", "Bez creeperów!", "Też w realu!", "GG!",
];

// ---------- koszyk ----------

const CART_KEY = "gdi-cart-v3";
let cart = loadCart();

function loadCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY));
    return Array.isArray(raw) ? raw.filter((r) => PRODUCTS[r.slug] && r.qty > 0) : [];
  } catch {
    return [];
  }
}

function saveCart() {
  try {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  } catch {
    // brak storage (tryb prywatny itp.), koszyk działa do odświeżenia
  }
}

const keyOf = (r) => [r.slug, r.size || ""].join("|");

function addToCart(item, qty) {
  const row = cart.find((r) => keyOf(r) === keyOf(item));
  if (row) row.qty = Math.min(row.qty + qty, 99);
  else cart.push({ ...item, qty });
  saveCart();
  renderCart();
  const count = $("[data-cart-count]");
  count.classList.remove("is-bump");
  void count.offsetWidth;
  count.classList.add("is-bump");
}

function changeQty(key, delta) {
  const row = cart.find((r) => keyOf(r) === key);
  if (!row) return;
  row.qty += delta;
  cart = cart.filter((r) => r.qty > 0);
  saveCart();
  renderCart();
}

function renderCart() {
  const count = cart.reduce((n, r) => n + r.qty, 0);
  const total = cart.reduce((sum, r) => sum + PRODUCTS[r.slug].price * r.qty, 0);
  $$("[data-cart-count]").forEach((el) => (el.textContent = count));

  $("[data-cart-list]").innerHTML = cart.map((r) => {
    const p = PRODUCTS[r.slug];
    return `<li class="cart-item">
      <div class="media"><img src="${imageFor(p)}" alt=""></div>
      <div>
        <h3><a href="${ROOT}produkt/${r.slug}/">${esc(p.name)}</a></h3>
        ${r.size ? `<small>${esc(r.size)}</small>` : ""}
        <div class="qty">
          <button class="qty-btn" type="button" data-qty="${esc(keyOf(r))}" data-delta="-1" aria-label="Mniej">-</button>
          <span>${r.qty}</span>
          <button class="qty-btn" type="button" data-qty="${esc(keyOf(r))}" data-delta="1" aria-label="Więcej">+</button>
        </div>
      </div>
      <div class="cart-item-side">
        <p class="price">${money(p.price * r.qty)}</p>
        <button class="remove" type="button" data-qty="${esc(keyOf(r))}" data-delta="-${r.qty}">Usuń</button>
      </div>
    </li>`;
  }).join("");

  $("[data-cart-empty]").hidden = cart.length > 0;
  $("[data-cart-total]").textContent = money(total);
  const left = FREE_SHIPPING - total;
  $("[data-shipping-fill]").style.width = Math.min(total / FREE_SHIPPING, 1) * 100 + "%";
  $("[data-shipping-label]").textContent = left <= 0
    ? "Masz darmową dostawę!"
    : cart.length ? `Brakuje ${money(left)} do darmowej dostawy` : `Darmowa dostawa od ${FREE_SHIPPING} zł`;
}

// ---------- szuflada koszyka ----------

const drawer = $("[data-cart]");
let lastFocus = null;

function openCart() {
  lastFocus = document.activeElement;
  drawer.hidden = false;
  document.body.style.overflow = "hidden";
  $(".drawer-head [data-close-cart]").focus();
}

function closeCart() {
  drawer.hidden = true;
  document.body.style.overflow = "";
  lastFocus?.focus();
}

// ---------- strona główna ----------

function setFilter(cat) {
  $$("[data-filter]").forEach((b) => {
    const on = b.dataset.filter === cat;
    b.classList.toggle("is-active", on);
    b.setAttribute("aria-pressed", on);
  });
  $$(".grid [data-category]").forEach((c) => (c.hidden = cat !== "all" && c.dataset.category !== cat));
}

const splash = $("[data-splash]");
if (splash) splash.textContent = SPLASHES[Math.floor(Math.random() * SPLASHES.length)];

// Staty kanału: data/stats.json aktualizuje GitHub Action (tools/fetch_stats.py).
const statsEl = $("[data-stats]");
if (statsEl) {
  fetch(ROOT + "data/stats.json", { cache: "no-cache" })
    .then((r) => (r.ok ? r.json() : Promise.reject()))
    .then((stats) => {
      const compact = new Intl.NumberFormat("pl-PL", { notation: "compact", maximumFractionDigits: 1 });
      const fmt = { format: (n) => (n < 10000 ? n.toLocaleString("pl-PL") : compact.format(n)) };
      $$("[data-stat]", statsEl).forEach((el) => {
        const value = stats[el.dataset.stat];
        if (value == null) el.parentElement.remove();
        else el.textContent = fmt.format(value);
      });
      statsEl.hidden = !$("[data-stat]", statsEl);
    })
    .catch(() => {});
}

$("[data-drop-form]")?.addEventListener("submit", (e) => {
  e.preventDefault();
  $("[data-form-note]").hidden = false;
});

// ---------- strona produktu ----------

const productEl = $("[data-product]");
if (productEl) initProduct(productEl);

function initProduct(root) {
  const slug = root.dataset.product;
  const form = $("[data-buy]", root);
  const qtyInput = form.elements.qty;
  const sizeField = $("[data-size-field]", form);
  const error = $("[data-buy-error]", form);

  // galeria: miniatury podmieniają główne zdjęcie
  const mainImg = $("[data-media] img", root);
  $$("[data-thumb]", root).forEach((t) => t.addEventListener("click", () => {
    const img = $("img", t);
    mainImg.srcset = img.srcset;
    mainImg.src = img.src;
    $$("[data-thumb]", root).forEach((x) => x.classList.toggle("is-active", x === t));
  }));

  form.addEventListener("change", (e) => {
    if (e.target.name === "size") {
      sizeField.classList.remove("is-error");
      error.hidden = true;
    }
  });

  $$("[data-step]", form).forEach((b) => b.addEventListener("click", () => {
    qtyInput.value = Math.min(20, Math.max(1, (parseInt(qtyInput.value, 10) || 1) + Number(b.dataset.step)));
  }));

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const size = form.elements.size ? form.elements.size.value : "";
    if (sizeField && !size) {
      sizeField.classList.add("is-error");
      error.hidden = false;
      $("input", sizeField).focus();
      return;
    }
    const qty = Math.min(20, Math.max(1, parseInt(qtyInput.value, 10) || 1));
    addToCart({ slug, size }, qty);
    openCart();
  });
}

// ---------- zdarzenia ----------

renderCart();

document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-filter],[data-qty],[data-open-cart],[data-close-cart]");
  if (!t) return;
  if (t.dataset.filter) setFilter(t.dataset.filter);
  else if (t.dataset.qty) changeQty(t.dataset.qty, Number(t.dataset.delta));
  else if (t.hasAttribute("data-open-cart")) openCart();
  else if (t.hasAttribute("data-close-cart")) closeCart();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !drawer.hidden) closeCart();
});
