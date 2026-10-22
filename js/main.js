// GDi Merch: produkty (placeholdery), filtry, koszyk w hotbarze.

const FREE_SHIPPING = 200;

// Rzadkość = kolor nazwy jak w grze.
const RARITY = {
  common: "#ffffff",
  uncommon: "#ffff55",
  rare: "#55ffff",
  epic: "#ff55ff",
};

// PLACEHOLDERY: podmień nazwy, ceny, opisy i obrazki (img) na prawdziwe.
const PRODUCTS = [
  { id: "bluza-creeper-smile", name: "Bluza GDi Smile", category: "ubrania", price: 179.99, rarity: "rare", badge: "Nowość",
    img: "assets/items/hoodie_green.png", lore: ["Gruba bawełna, kaptur, kangurka", "Odporność na zimno +3"] },
  { id: "koszulka-classic", name: "Koszulka GDi Classic", category: "ubrania", price: 89.99, rarity: "uncommon",
    img: "assets/items/tshirt_cyan.png", lore: ["100% bawełna", "Logo z przodu, nick z tyłu"] },
  { id: "czapka", name: "Czapka z daszkiem", category: "ubrania", price: 69.99, rarity: "common",
    img: "assets/items/cap_blue.png", lore: ["Haftowane logo", "Ochrona przed słońcem I"] },
  { id: "dresy", name: "Dresy Simon Gaming", category: "ubrania", price: 149.99, rarity: "rare",
    img: "assets/items/pants_sky.png", lore: ["Miękki dres, ściągacze", "Szybkość II na kanapie"] },
  { id: "skarpetki", name: "Skarpetki Pixel", category: "ubrania", price: 29.99, rarity: "common",
    img: "assets/items/shoes_green.png", lore: ["2 pary w zestawie", "Ciche skradanie +1"] },
  { id: "figurka", name: "Figurka GDi", category: "akcesoria", price: 59.99, rarity: "epic", badge: "Limit",
    img: "assets/textures/item/totem_of_undying.png", lore: ["Edycja limitowana", "Ratuje przed nudą raz dziennie"] },
  { id: "plakat", name: "Plakat A2", category: "akcesoria", price: 39.99, rarity: "uncommon",
    img: "assets/textures/item/painting.png", lore: ["Matowy papier 200 g", "Wygląda lepiej niż obraz z gry"] },
  { id: "naklejki", name: "Naklejki (10 szt.)", category: "akcesoria", price: 19.99, rarity: "common",
    img: "assets/textures/item/paper.png", lore: ["Wodoodporne", "Na laptopa, telefon, wszystko"] },
  { id: "brelok", name: "Brelok z logo", category: "akcesoria", price: 24.99, rarity: "common",
    img: "assets/textures/item/name_tag.png", lore: ["Metal + emalia", "Nie zgubisz kluczy (chyba)"] },
  { id: "paczka", name: "Paczka niespodzianka", category: "akcesoria", price: 99.99, rarity: "epic",
    img: "assets/textures/item/bundle.png", lore: ["Losowe 3-5 produktów", "Wartość większa niż cena"] },
];

const SPLASHES = [
  "Nowy merch!", "100% kwadratowy!", "Teraz z pikselami!", "Subskrybuj!", "Craftowane z miłością!",
  "Lepsze niż diamenty!", "Bez creeperów!", "Też w realu!", "Edycja limitowana!", "GG!",
];

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const byId = Object.fromEntries(PRODUCTS.map((p) => [p.id, p]));
const money = (v) => v.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " zł";
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// ---------- koszyk ----------

const CART_KEY = "gdi-cart";
let cart = loadCart();

function loadCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY));
    return Array.isArray(raw) ? raw.filter((r) => byId[r.id] && r.qty > 0) : [];
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

function addToCart(id, delta = 1) {
  const row = cart.find((r) => r.id === id);
  if (row) row.qty += delta;
  else if (delta > 0) cart.push({ id, qty: delta });
  cart = cart.filter((r) => r.qty > 0);
  saveCart();
  renderCart();
}

function cartTotal() {
  return cart.reduce((sum, r) => sum + byId[r.id].price * r.qty, 0);
}

function renderCart() {
  const count = cart.reduce((n, r) => n + r.qty, 0);
  const total = cartTotal();
  $$("[data-cart-count]").forEach((el) => (el.textContent = count));

  // hotbar: 9 slotów, każdy slot 20px co 20px, ikona od x=3
  const hotbar = $("[data-hotbar]");
  hotbar.innerHTML =
    cart.slice(0, 9).map((r, i) => {
      const p = byId[r.id];
      return `<div class="hotbar-item" style="left:calc(${3 + i * 20}px * var(--s))">
        <img src="${p.img}" alt="${esc(p.name)}">${r.qty > 1 ? `<b>${r.qty}</b>` : ""}</div>`;
    }).join("") +
    (cart.length ? `<div class="hotbar-sel" style="left:calc(${(Math.min(cart.length, 9) - 1) * 20 - 1}px * var(--s))"></div>` : "") +
    (cart.length > 9 ? `<span class="hotbar-more">+${cart.length - 9}</span>` : "");

  const progress = Math.min(total / FREE_SHIPPING, 1);
  $("[data-xp-fill]").style.width = progress * 100 + "%";
  $("[data-xp-level]").textContent = count;
  $("[data-xp-label]").textContent =
    progress >= 1 ? "Darmowa dostawa odblokowana!" : `Do darmowej dostawy: ${money(FREE_SHIPPING - total)}`;

  $("[data-cart-list]").innerHTML = cart.map((r) => {
    const p = byId[r.id];
    return `<li class="cart-row">
      <div class="slot"><img src="${p.img}" alt=""></div>
      <p>${esc(p.name)}<small>${money(p.price)} / szt.</small></p>
      <div class="qty">
        <button class="mc-btn" type="button" data-qty="${p.id}" data-delta="-1" aria-label="Mniej">-</button>
        <span>${r.qty}</span>
        <button class="mc-btn" type="button" data-qty="${p.id}" data-delta="1" aria-label="Więcej">+</button>
      </div>
    </li>`;
  }).join("");
  $("[data-cart-empty]").hidden = cart.length > 0;
  $("[data-cart-total]").textContent = money(total);
}

// ---------- produkty ----------

function renderProducts() {
  $("[data-products]").innerHTML = PRODUCTS.map((p) => `
    <article class="card panel" data-category="${p.category}">
      <div class="card-slot slot" data-tip="${p.id}">
        ${p.badge ? `<span class="badge">${esc(p.badge)}</span>` : ""}
        <img src="${p.img}" alt="${esc(p.name)}" loading="lazy">
      </div>
      <h3>${esc(p.name)}</h3>
      <p class="price"><img src="assets/textures/item/emerald.png" alt="">${money(p.price)}</p>
      <button class="mc-btn" type="button" data-add="${p.id}" aria-label="Dodaj do koszyka: ${esc(p.name)}">Do koszyka</button>
    </article>`).join("");
}

function setFilter(cat) {
  $$("[data-filter]").forEach((b) => b.classList.toggle("is-active", b.dataset.filter === cat));
  $$("[data-category]").forEach((c) => (c.hidden = cat !== "all" && c.dataset.category !== cat));
}

// ---------- tooltip ----------

const tooltip = $("[data-tooltip]");

function showTooltip(id, x, y) {
  const p = byId[id];
  tooltip.innerHTML = `
    <p class="t-name" style="color:${RARITY[p.rarity]}">${esc(p.name)}</p>
    ${p.lore.map((l) => `<p class="t-lore">${esc(l)}</p>`).join("")}
    <p class="t-price">${money(p.price)}</p>
    <p class="t-id">gdi:${p.id}</p>`;
  tooltip.hidden = false;
  moveTooltip(x, y);
}

function moveTooltip(x, y) {
  const r = tooltip.getBoundingClientRect();
  const left = x + 16 + r.width > innerWidth ? x - 16 - r.width : x + 16;
  const top = Math.min(y - 12, innerHeight - r.height - 8);
  tooltip.style.left = Math.max(8, left) + "px";
  tooltip.style.top = Math.max(8, top) + "px";
}

// ---------- toast ----------

let toastTimer;
function toast(p) {
  const el = $("[data-toast]");
  $("[data-toast-icon]").src = p.img;
  $("[data-toast-text]").textContent = p.name;
  el.classList.add("is-on");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("is-on"), 2200);
}

// ---------- modal ----------

const modal = $("[data-cart-modal]");
let lastFocus = null;

function openCart() {
  lastFocus = document.activeElement;
  modal.hidden = false;
  $("[data-close-cart].mc-btn", modal).focus();
}
function closeCart() {
  modal.hidden = true;
  lastFocus?.focus();
}

// ---------- start ----------

renderProducts();
renderCart();

$("[data-splash]").textContent = SPLASHES[Math.floor(Math.random() * SPLASHES.length)];

document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-add],[data-filter],[data-qty],[data-open-cart],[data-close-cart],[data-placeholder-link]");
  if (!t) return;
  if (t.dataset.add) {
    addToCart(t.dataset.add);
    toast(byId[t.dataset.add]);
  } else if (t.dataset.filter) {
    setFilter(t.dataset.filter);
  } else if (t.dataset.qty) {
    addToCart(t.dataset.qty, Number(t.dataset.delta));
  } else if (t.hasAttribute("data-open-cart")) {
    openCart();
  } else if (t.hasAttribute("data-close-cart")) {
    closeCart();
  } else if (t.hasAttribute("data-placeholder-link")) {
    e.preventDefault(); // TODO: wstaw link do kanału
  }
});

$(".hud").addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    openCart();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modal.hidden) closeCart();
});

document.addEventListener("pointerover", (e) => {
  const slot = e.target.closest("[data-tip]");
  if (slot && e.pointerType === "mouse") showTooltip(slot.dataset.tip, e.clientX, e.clientY);
});
document.addEventListener("pointermove", (e) => {
  if (!tooltip.hidden) moveTooltip(e.clientX, e.clientY);
});
document.addEventListener("pointerout", (e) => {
  const slot = e.target.closest("[data-tip]");
  if (slot && !slot.contains(e.relatedTarget)) tooltip.hidden = true;
});

$("[data-drop-form]").addEventListener("submit", (e) => {
  e.preventDefault();
  $("[data-form-note]").hidden = false;
});
