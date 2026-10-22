#!/usr/bin/env python3
"""Generuje strony sklepu z data/products.json.

- produkt/<slug>/index.html   podstrona każdego produktu (z templates/product.html)
- index.html                  wstawia header, footer i siatkę produktów między znaczniki build:*
- js/products.js              dane produktów dla koszyka
- assets/products/*.webp      wersje zdjęć do strony z assets/products/full/*.png
- assets/og/*.png             obrazki do podglądu linków (Discord, X, Messenger)

Po każdej zmianie w data/products.json albo templates/ uruchom:
    python3 tools/build_pages.py
"""
import hashlib
import html
import json
import os
import re
import shutil

from PIL import Image

# Adres strony po publikacji, potrzebny do linków kanonicznych i og:image.
SITE_URL = "https://pjotreek.github.io/szymonkondzior/"

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEMPLATES = os.path.join(ROOT, "templates")

esc = html.escape


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def write(text, *parts):
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def fill(template, values):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


def fill_block(page, name, content):
    pattern = re.compile(rf"(<!-- build:{name} -->\n).*?(<!-- /build:{name} -->)", re.S)
    assert pattern.search(page), f"brak znacznika build:{name}"
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), page)


def money(value):
    whole, frac = f"{value:.2f}".split(".")
    return f"{int(whole):,}".replace(",", " ") + f",{frac} zł"


TINT = "#46dcd3"
SIZES = (600, 1200)


def build_images(name, manifest):
    """Z assets/products/full/<name>.png robi lekkie WebP do strony.

    Regeneruje tylko gdy zmieniła się zawartość PNG (hash w manifest), bo różne
    wersje libwebp dają inne bajty i każdy build w CI robiłby zbędny commit.
    """
    src = os.path.join(ROOT, "assets", "products", "full", name + ".png")
    with open(src, "rb") as f:
        digest = hashlib.sha1(f.read()).hexdigest()
    outs = [os.path.join(ROOT, "assets", "products", f"{name}-{size}.webp") for size in SIZES]
    if manifest.get(name) == digest and all(os.path.exists(o) for o in outs):
        return
    img = Image.open(src).convert("RGBA")
    for size, out in zip(SIZES, outs):
        copy = img.copy()
        copy.thumbnail((size, size), Image.LANCZOS)
        copy.save(out, "WEBP", quality=88, method=6)
    manifest[name] = digest


def picture(name, root, sizes, eager=False):
    base = f"{root}assets/products/{name}"
    srcset = ", ".join(f"{base}-{w}.webp {w}w" for w in SIZES)
    loading = "" if eager else ' loading="lazy"'
    return f'<img src="{base}-{SIZES[0]}.webp" srcset="{srcset}" sizes="{sizes}" alt=""{loading} decoding="async">'


def card(p, root):
    badge = f'<span class="badge">{esc(p["badge"])}</span>' if p.get("badge") else ""
    img = picture(p["images"][0], root, "(max-width: 700px) 50vw, 280px")
    return f"""<a class="card" href="{root}produkt/{p['slug']}/" data-category="{p['category']}">
  <div class="media">{badge}{img}</div>
  <div class="card-body">
    <h3>{esc(p['name'])}</h3>
    <p class="price">{money(p['price'])}</p>
  </div>
</a>
"""


def size_field(p):
    sizes = p.get("sizes")
    if not sizes:
        return ""
    single = len(sizes) == 1
    opts = "".join(f'<label class="size"><input type="radio" name="size" value="{esc(s)}"{" checked" if single else ""}>'
                   f'<span>{esc(s)}</span></label>' for s in sizes)
    return f"""<fieldset class="field" data-size-field>
          <legend>{esc(p.get("size_label", "Rozmiar"))}</legend>
          <div class="sizes">{opts}</div>
        </fieldset>"""


def thumbs(p, root):
    if len(p["images"]) < 2:
        return ""
    items = "".join(
        f'<button type="button" class="thumb media{" is-active" if i == 0 else ""}" data-thumb="{name}" '
        f'aria-label="Zdjęcie {i + 1}">{picture(name, root, "96px")}</button>'
        for i, name in enumerate(p["images"]))
    return f'<div class="thumbs">{items}</div>'


def size_chart(p):
    sizes = p.get("sizes") or []
    if p["category"] != "ubrania" or len(sizes) < 2 or not sizes[0][0].isalpha():
        return ""
    rows = "".join(f"<tr><td>{esc(s)}</td><td>{50 + 3 * i}</td><td>{68 + 2 * i}</td></tr>" for i, s in enumerate(sizes))
    return f"""<details>
          <summary>Rozmiarówka</summary>
          <table class="size-table"><thead><tr><th>Rozmiar</th><th>Szerokość (cm)</th><th>Długość (cm)</th></tr></thead><tbody>{rows}</tbody></table>
          <p class="muted">Wymiary przykładowe, do podmiany.</p>
        </details>"""


def related(p, products, root):
    same = [q for q in products if q is not p and q["category"] == p["category"]]
    other = [q for q in products if q is not p and q["category"] != p["category"]]
    return "".join(card(q, root) for q in (same + other)[:4])


def og_image(img_name, out_name, manifest):
    """1200x630: zdjęcie produktu na kaflu w kolorze marki, logo po lewej."""
    path = os.path.join(ROOT, "assets", "og", out_name + ".png")
    key = f"og:{out_name}"
    if manifest.get(key) == manifest.get(img_name) and os.path.exists(path):
        return
    tint = tuple(int(TINT[i:i + 2], 16) for i in (1, 3, 5))
    bg = (13, 20, 28)
    canvas = Image.new("RGB", (1200, 630), bg)
    canvas.paste(Image.new("RGB", (560, 560), tuple(int(b + (t - b) * 0.18) for b, t in zip(bg, tint))), (600, 35))
    photo = Image.open(os.path.join(ROOT, "assets", "products", "full", img_name + ".png")).convert("RGBA")
    photo.thumbnail((480, 480), Image.LANCZOS)
    canvas.paste(photo, (600 + (560 - photo.width) // 2, 35 + (560 - photo.height) // 2), photo)
    logo = Image.open(os.path.join(ROOT, "assets", "img", "logo.png")).resize((320, 320), Image.NEAREST)
    canvas.paste(logo, (140, 155))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path, optimize=True)
    manifest[key] = manifest.get(img_name)


def main():
    data = json.loads(read("data", "products.json"))
    products = data["products"]
    header, footer = read("templates", "header.html"), read("templates", "footer.html")

    def chrome(page, root):
        page = fill_block(page, "header", fill(header, {"root": root}))
        return fill_block(page, "footer", fill(footer, {"root": root}))

    manifest_path = os.path.join(ROOT, "assets", "products", "manifest.json")
    manifest = json.loads(read("assets", "products", "manifest.json")) if os.path.exists(manifest_path) else {}
    for p in products:
        for name in p["images"]:
            build_images(name, manifest)

    # podstrony produktów
    shutil.rmtree(os.path.join(ROOT, "produkt"), ignore_errors=True)
    template = read("templates", "product.html")
    root = "../../"
    for p in products:
        page = fill(template, {
            "root": root,
            "slug": p["slug"],
            "name": esc(p["name"]),
            "short": esc(p["short"]),
            "url": f"{SITE_URL}produkt/{p['slug']}/",
            "og_image": f"{SITE_URL}assets/og/{p['slug']}.png",
            "category_name": esc(data["categories"][p["category"]]),
            "price": money(p["price"]),
            "picture": picture(p["images"][0], root, "(max-width: 960px) 100vw, 600px", eager=True),
            "badge": f'<span class="badge">{esc(p["badge"])}</span>' if p.get("badge") else "",
            "thumbs": thumbs(p, root),
            "size_field": size_field(p),
            "description": "\n          ".join(f"<p>{esc(t)}</p>" for t in p["description"]),
            "material": esc(p["material"]),
            "size_chart": size_chart(p),
            "related": related(p, products, root),
        })
        write(chrome(page, root), "produkt", p["slug"], "index.html")
        og_image(p["images"][0], p["slug"], manifest)

    # strona główna
    index = read("index.html")
    index = fill_block(index, "products", "".join(card(p, "") for p in products))
    index = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{SITE_URL}assets/og/home.png\g<2>", index)
    write(chrome(index, "./"), "index.html")
    og_image(products[0]["images"][0], "home", manifest)

    # dane dla koszyka
    js_data = {
        "freeShipping": 200,
        "products": {p["slug"]: {"name": p["name"], "price": p["price"], "image": p["images"][0]} for p in products},
    }
    write("// Wygenerowane przez tools/build_pages.py z data/products.json. Nie edytuj ręcznie.\n"
          f"window.GDI = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n", "js", "products.js")
    write(json.dumps(manifest, indent=2, sort_keys=True) + "\n", "assets", "products", "manifest.json")
    print(f"zbudowano {len(products)} podstron")


if __name__ == "__main__":
    main()
